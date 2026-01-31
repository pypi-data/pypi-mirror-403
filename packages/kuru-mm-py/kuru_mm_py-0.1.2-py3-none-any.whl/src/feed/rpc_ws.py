import asyncio
from typing import Optional
from loguru import logger
from web3 import AsyncWeb3, Web3
from web3.providers.persistent import WebSocketProvider

from src.utils import load_abi
from src.utils.utils import normalize_hex, bytes32_to_string
from src.manager.orders_manager import OrdersManager
from src.manager.events import (
    OrderCreatedEvent,
    OrdersCanceledEvent,
    TradeEvent,
    BatchUpdateMMEvent,
)
from src.configs import (
    KuruTopicsSignature,
    MarketConfig,
    ConnectionConfig,
    WalletConfig,
    WebSocketConfig,
)


class RpcWebsocket:
    def __init__(
        self,
        connection_config: ConnectionConfig,
        market_config: MarketConfig,
        wallet_config: WalletConfig,
        websocket_config: WebSocketConfig,
        orders_manager: OrdersManager,
        shutdown_event: Optional[asyncio.Event] = None,
    ):
        """
        Initialize the RpcWebsocket class.

        Args:
            connection_config: Connection configuration (RPC URLs)
            market_config: Market configuration (contract addresses, precision)
            wallet_config: Wallet configuration (user address)
            websocket_config: WebSocket behavior configuration
            orders_manager: The orders manager to handle the orders
            shutdown_event: Optional asyncio.Event for graceful shutdown
        """
        # Store configs
        self.connection_config = connection_config
        self.market_config = market_config
        self.wallet_config = wallet_config
        self.websocket_config = websocket_config

        # Extract commonly used values
        self.rpc_url = connection_config.rpc_ws_url
        # Keep checksummed addresses for contract creation (web3.py requirement)
        self.orderbook_address = market_config.market_address
        self.mm_entrypoint_address = market_config.mm_entrypoint_address
        self.user_address = wallet_config.user_address

        # Store lowercase versions for event filtering (case-insensitive comparison)
        self.orderbook_address_lower = self.orderbook_address.lower()
        self.mm_entrypoint_address_lower = self.mm_entrypoint_address.lower()
        self.user_address_lower = self.user_address.lower()

        # Initialize Web3 with WebSocket provider
        self.w3 = AsyncWeb3(WebSocketProvider(self.rpc_url))

        # Create contract instances for both contracts (requires checksummed addresses)
        self.orderbook_contract = self.w3.eth.contract(
            address=self.orderbook_address, abi=load_abi("orderbook")
        )

        self.mm_entrypoint_contract = self.w3.eth.contract(
            address=self.mm_entrypoint_address, abi=load_abi("mm_entrypoint")
        )

        self.subscription = None
        self._connected = False
        self._shutdown_event = shutdown_event

        # Topic hash mapping for all contracts
        self.events_to_topic_hashes = {}
        self.orders_manager = orders_manager

        self.size_precision = market_config.size_precision
        self.price_precision = market_config.price_precision

    async def connect(self) -> None:
        """Connect to the WebSocket provider."""
        await self.w3.provider.connect()
        self._connected = True
        logger.debug("RpcWebsocket connected successfully")

    async def disconnect(self) -> None:
        """Disconnect from the WebSocket provider."""
        self._connected = False

        try:
            await asyncio.wait_for(self.w3.provider.disconnect(), timeout=5.0)
            logger.debug("RpcWebsocket disconnected successfully")
        except asyncio.TimeoutError:
            logger.warning("WebSocket disconnect timed out after 5s, forcing close")
        except Exception as e:
            logger.warning(f"Error during disconnect (may already be closed): {e}")

    async def create_log_subscription(self, kuru_topics: dict[str, str]) -> None:
        """
        Create a subscription to contract logs for specified event topics from multiple contracts.

        Args:
            kuru_topics: Dict mapping topic names to event signatures.
                        e.g., {"OrderCreated": "OrderCreated(address,uint256,bool)"}

        Returns:
            The web3 subscription object
        """
        # Compute topic hashes for all Kuru events
        topic_hashes = []
        events_to_topic_hashes = {}
        for name, signature in kuru_topics.items():
            topic_hash = Web3.keccak(text=signature).hex()
            topic_hashes.append(topic_hash)
            events_to_topic_hashes[name] = topic_hash

        self.events_to_topic_hashes = events_to_topic_hashes

        # Subscribe to logs from BOTH contracts with filter
        # Note: Passing list of addresses to subscribe to multiple contracts
        subscription = await self.w3.eth.subscribe(
            "logs",
            {
                "address": [self.orderbook_address, self.user_address],
                "topics": [topic_hashes],
            },
        )
        self.subscription = subscription

        logger.info(f"Created subscription for {len(kuru_topics)} Kuru events")

    async def _handle_log(self, log: dict) -> None:
        """
        Extract log metadata and route to appropriate contract handler.

        Args:
            log: The log object from the subscription
        """
        if not log:
            return

        topics = log.get("topics")
        topic0 = normalize_hex(topics[0]) if topics and len(topics) > 0 else None
        txhash = normalize_hex(log.get("transactionHash"))
        log_address = log.get("address").lower() if log.get("address") else None

        # Route to appropriate contract handler based on log address
        # Compare using lowercase versions for case-insensitive matching
        if log_address == self.orderbook_address_lower:
            await self._process_orderbook_log(log, topic0, txhash)
        elif log_address == self.user_address_lower:
            await self._batch_update_mm_log(log, topic0, txhash)
        elif log_address is not None:
            logger.warning(f"Log from unknown contract address: {log_address}")

    async def process_subscription_logs(self) -> None:
        """
        Process logs from WebSocket subscription.

        Listens for messages on the WebSocket connection and processes
        logs matching the subscription ID.
        """
        if self.subscription is None:
            logger.error(
                "Subscription is not created. Subscribe to the orderbook events first."
            )
            return

        if not hasattr(self.w3, "socket") or self.w3.socket is None:
            logger.error(
                "AsyncWeb3.socket is not available. Ensure connect() was called and you are using a persistent WebSocket provider."
            )
            return

        logger.info(f"Starting log processor for subscription: {self.subscription}")

        try:
            subscription_iterator = self.w3.socket.process_subscriptions()

            while self._connected:
                # Check shutdown signal if present
                if self._shutdown_event and self._shutdown_event.is_set():
                    logger.info("Shutdown signal received, stopping log processor...")
                    break

                try:
                    # Wait for next message with timeout to allow task cancellation
                    response = await asyncio.wait_for(
                        subscription_iterator.__anext__(),
                        timeout=1.0  # Wake up every second to check for cancellation
                    )

                    # Process the response
                    result = response.get("result")
                    if result:
                        await self._handle_log(result)

                except asyncio.TimeoutError:
                    # No message received in 1 second, loop continues
                    # This allows the task to be responsive to cancellation
                    continue

                except StopAsyncIteration:
                    logger.info("WebSocket subscription ended")
                    break

        except asyncio.CancelledError:
            logger.info("Log processor cancelled")
            raise

        except Exception as e:
            logger.error(f"Error processing subscription log: {e}", exc_info=True)
            raise

        finally:
            logger.info("Log processor stopped")

    async def _process_orderbook_log(self, log, topic0: str, txhash: str) -> None:
        """Process logs from orderbook contract."""
        if topic0 == self.events_to_topic_hashes.get("OrderCreated"):
            decoded = self.orderbook_contract.events.OrderCreated().process_log(log)
            args = decoded["args"]

            if args["owner"].lower() != self.user_address_lower:
                return

            logger.warning(f"OrderCreated event received price: {args["price"]}")
            event = OrderCreatedEvent(
                order_id=args["orderId"],
                owner=args["owner"],
                size=float(args["size"] / self.size_precision),
                price=args["price"],
                is_buy=args["isBuy"],
                txhash=txhash,
                log_index=log["logIndex"],
            )
            await self.orders_manager.on_order_created(event)

        elif topic0 == self.events_to_topic_hashes.get("OrdersCanceled"):
            decoded = self.orderbook_contract.events.OrdersCanceled().process_log(log)
            args = decoded["args"]

            if args["owner"].lower() != self.user_address_lower:
                return

            event = OrdersCanceledEvent(
                order_ids=list(args["orderId"]),
                owner=args["owner"],
                txhash=txhash,
            )
            await self.orders_manager.on_orders_cancelled(event)

        elif topic0 == self.events_to_topic_hashes.get("Trade"):
            decoded = self.orderbook_contract.events.Trade().process_log(log)
            args = decoded["args"]

            maker = args["makerAddress"].lower()
            taker = args["takerAddress"].lower()
            user = self.user_address_lower

            if maker != user and taker != user:
                return

            event = TradeEvent(
                order_id=args["orderId"],
                maker_address=args["makerAddress"],
                is_buy=args["isBuy"],
                price=args["price"],
                updated_size=float(args["updatedSize"] / self.size_precision),
                taker_address=args["takerAddress"],
                tx_origin=args["txOrigin"],
                filled_size=float(args["filledSize"] / self.size_precision),
                txhash=txhash,
            )
            await self.orders_manager.on_trade(event)

        else:
            logger.warning(f"Unknown orderbook topic: {topic0}")

    async def _batch_update_mm_log(self, log, topic0: str, txhash: str) -> None:
        """Process logs from MM entrypoint contract."""
        if topic0 == self.events_to_topic_hashes.get("batchUpdate"):
            decoded = self.mm_entrypoint_contract.events.batchUpdate().process_log(log)
            args = decoded["args"]

            # Extract cloid arrays (bytes32[])
            buy_cloids = [
                bytes32_to_string(cloid) if isinstance(cloid, bytes) else cloid
                for cloid in args["buyCloids"]
            ]
            sell_cloids = [
                bytes32_to_string(cloid) if isinstance(cloid, bytes) else cloid
                for cloid in args["sellCloids"]
            ]
            cancel_cloids = [
                bytes32_to_string(cloid) if isinstance(cloid, bytes) else cloid
                for cloid in args["cancelCloids"]
            ]

            logger.debug(f"Buy cloids: {buy_cloids}")
            logger.debug(f"Sell cloids: {sell_cloids}")
            logger.debug(f"Cancel cloids: {cancel_cloids}")
            logger.debug(f"Txhash: {txhash}")

            event = BatchUpdateMMEvent(
                buy_cloids=buy_cloids,
                sell_cloids=sell_cloids,
                cancel_cloids=cancel_cloids,
                txhash=txhash,
            )
            await self.orders_manager.on_batch_update_mm(event)

        else:
            logger.warning(f"Unknown MM entrypoint topic: {topic0}")
