import asyncio
import json
import logging
import websockets
from datetime import datetime
from typing import Dict, Optional, List, Tuple
from utils.logger import setup_logger

class WebSocketClient:
    def __init__(self, symbol: str = "BTC-USDT-SWAP"):
        self.symbol = symbol
        self.logger = setup_logger("websocket_client")
        self.ws = None
        self.is_connected = False
        self.latest_orderbook = None
        self.start_time = None
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        self.url = f"YOUR_ORDERBOOK_URL"
        self.is_running = False
        self.retry_count = 0
        self._orderbook_event = asyncio.Event()
        self._lock = asyncio.Lock()  # Use a single asyncio lock for all operations
        self._message_queue = asyncio.Queue()  # Add message queue for processing
    
    async def start(self):
        """Start the WebSocket client and subscribe to orderbook data."""
        self.logger.info("Starting WebSocket client...")
        self.is_running = True
        self.start_time = datetime.now()
        
        # Start message processing task
        self._processing_task = asyncio.create_task(self._process_messages())
        
        while self.is_running and self.retry_count < self.max_retries:
            try:
                self.logger.info(f"Connecting to WebSocket at {self.url}")
                async with websockets.connect(self.url) as websocket:
                    self.ws = websocket
                    self.is_connected = True
                    self.logger.info("WebSocket connected successfully")
                    
                    # Send subscription message
                    subscribe_msg = {
                        "op": "subscribe",
                        "args": [{
                            "channel": "books",
                            "instId": self.symbol,
                            "depth": 25  # Request 25 levels of depth
                        }]
                    }
                    await websocket.send(json.dumps(subscribe_msg))
                    self.logger.info(f"Sent subscription message: {subscribe_msg}")
                    
                    # Reset retry count on successful connection
                    self.retry_count = 0
                    
                    # Start message receive loop
                    while self.is_running:
                        try:
                            message = await websocket.recv()
                            self.logger.debug(f"Received raw message: {message}")
                            
                            # Put message in queue for processing
                            await self._message_queue.put(message)
                            
                        except websockets.exceptions.ConnectionClosed:
                            self.logger.warning("WebSocket connection closed")
                            break
                        except Exception as e:
                            self.logger.error(f"Error receiving message: {e}")
                            continue
                            
            except Exception as e:
                self.logger.error(f"WebSocket connection error: {e}")
                self.retry_count += 1
                if self.retry_count < self.max_retries:
                    self.logger.info(f"Retrying in {self.retry_delay} seconds...")
                    await asyncio.sleep(self.retry_delay)
                else:
                    self.logger.error("Max retries reached, stopping WebSocket client")
                    self.is_running = False
                    break
                    
        self.is_connected = False
        self.logger.info("WebSocket client stopped")

    async def _process_messages(self):
        """Process messages from the queue."""
        while self.is_running:
            try:
                # Get message from queue
                message = await self._message_queue.get()
                
                async with self._lock:  # Use lock for processing
                    try:
                        # Parse and process the message
                        data = json.loads(message)
                        self.logger.debug(f"Parsed message structure: {json.dumps(data, indent=2)}")
                        
                        # Process the orderbook data
                        if all(key in data for key in ["timestamp", "asks", "bids"]):
                            await self._process_orderbook(data)
                        else:
                            self.logger.warning(f"Unexpected message format. Available keys: {list(data.keys())}")
                            
                    except json.JSONDecodeError as e:
                        self.logger.error(f"Failed to parse message: {e}")
                    except Exception as e:
                        self.logger.error(f"Error processing message: {e}")
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in message processing loop: {e}")
                continue

    async def _process_orderbook(self, data: Dict):
        """Process and store orderbook data."""
        try:
            # Extract timestamp and orderbook data
            timestamp = data.get("timestamp", datetime.now().isoformat())
            asks = data.get("asks", [])
            bids = data.get("bids", [])
            
            # Convert string prices and quantities to float
            asks = [[float(price), float(qty)] for price, qty in asks]
            bids = [[float(price), float(qty)] for price, qty in bids]
            
            # Store the latest orderbook
            self.latest_orderbook = {
                "timestamp": timestamp,
                "asks": asks,
                "bids": bids
            }
            
            # Set event to notify waiting tasks
            self._orderbook_event.set()
            self._orderbook_event.clear()
            
            self.logger.info(f"Processed orderbook update - Timestamp: {timestamp}")
            self.logger.debug(f"Processed orderbook: {self.latest_orderbook}")
            
        except Exception as e:
            self.logger.error(f"Error processing orderbook data: {e}")

    async def get_latest_orderbook(self) -> Optional[Dict]:
        """Get the latest orderbook data, waiting if necessary."""
        if not self.is_connected:
            self.logger.warning("WebSocket not connected")
            return None
            
        if not self.latest_orderbook:
            self.logger.info("Waiting for first orderbook update...")
            await self._orderbook_event.wait()
            
        async with self._lock:
            return self.latest_orderbook.copy() if self.latest_orderbook else None
    
    async def get_mid_price(self) -> Optional[float]:
        """Calculate the mid price from the latest orderbook"""
        async with self._lock:
            if not self.latest_orderbook:
                return None
            
            best_ask = self.latest_orderbook["asks"][0][0]
            best_bid = self.latest_orderbook["bids"][0][0]
            return (best_ask + best_bid) / 2
    
    async def get_spread(self) -> Optional[float]:
        """Calculate the spread from the latest orderbook"""
        async with self._lock:
            if not self.latest_orderbook:
                return None
            
            best_ask = self.latest_orderbook["asks"][0][0]
            best_bid = self.latest_orderbook["bids"][0][0]
            return best_ask - best_bid
    
    async def get_depth(self, levels: int = 10) -> Optional[Dict[str, List[Tuple[float, float]]]]:
        """Get the orderbook depth up to specified number of levels"""
        async with self._lock:
            if not self.latest_orderbook:
                return None
            
            return {
                "asks": self.latest_orderbook["asks"][:levels],
                "bids": self.latest_orderbook["bids"][:levels]
            }

    async def stop(self):
        """Stop the WebSocket client."""
        self.logger.info("Stopping WebSocket client...")
        self.is_running = False
        
        # Cancel the processing task
        if hasattr(self, '_processing_task'):
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        
        if self.ws:
            try:
                await self.ws.close()
                self.logger.info("WebSocket connection closed gracefully")
            except Exception as e:
                self.logger.error(f"Error closing WebSocket: {e}")
            finally:
                self.ws = None
                self.is_connected = False
        
        self.logger.info("WebSocket client stopped") 
