import asyncio
import time  # For measuring time
from PyQt5.QtCore import QObject, pyqtSignal
from data.websocket_client import WebSocketClient
from models.slippage import SlippageModel
from models.market_impact import MarketImpactModel
from models.maker_taker import MakerTakerModel
from models.fee import FeeModel
from analysis.latency import LatencyMonitor
from utils.logger import setup_logger

class SimulationController(QObject):
    update_status = pyqtSignal(str)
    update_metrics = pyqtSignal(dict)

    def __init__(self, parent=None, loop=None):
        super().__init__(parent)
        self.logger = setup_logger("simulation_controller")
        self.loop = loop or asyncio.get_event_loop()

        self.slippage_model = SlippageModel()
        self.market_impact_model = MarketImpactModel()
        self.maker_taker_model = MakerTakerModel()
        self.fee_model = FeeModel(maker_fee_rate=0.001, taker_fee_rate=0.002) # Example fee rates

        self.ws_client = WebSocketClient()
        self.latency_monitor = LatencyMonitor()

        self.is_running = False
        self.current_orderbook = None
        self.processing_task = None

    def start_simulation(self, inputs):
        try:
            if self.is_running:
                return
            self.is_running = True
            self.inputs = inputs
            self.logger.info("Simulation start requested. Emitting status...")
            self.update_status.emit("Starting simulation...")
            self.loop.create_task(self._start_simulation_async(inputs))
        except Exception as e:
            self.logger.error(f"Failed to start simulation: {e}")
            self.update_status.emit(f"Error: {str(e)}")
            self.stop_simulation()

    async def _start_simulation_async(self, inputs):
        try:
            self.logger.info("Starting WebSocket client...")
            await self.ws_client.start()
            self.logger.info("Starting orderbook processing loop...")
            self.processing_task = self.loop.create_task(self._process_orderbook())
            self.update_status.emit("Simulation started")
        except Exception as e:
            self.logger.error(f"Failed to start simulation: {e}")
            self.update_status.emit(f"Error: {str(e)}")
            await self.stop_simulation_async()
        except asyncio.CancelledError:
            self.logger.info("WebSocket client connection closed unexpectedly. Retrying...")
            await asyncio.sleep(5)  # Retry after a brief wait
            self.loop.create_task(self._start_simulation_async(inputs))

    def stop_simulation(self):
        if self.is_running:
            self.loop.create_task(self.stop_simulation_async())

    async def stop_simulation_async(self):
        try:
            if not self.is_running:
                return
            self.is_running = False
            self.logger.info("Stopping simulation: processing final orderbook and closing WebSocket.")
            await asyncio.sleep(0.5)
            await self._process_final_orderbook_once()
            if self.ws_client:
                await self.ws_client.stop()
                await asyncio.sleep(0.5)
            self.update_status.emit("Simulation stopped after final output.")
        except Exception as e:
            self.logger.error(f"Error during stop: {e}")
            self.update_status.emit(f"Error: {str(e)}")

    async def _process_orderbook(self):
        self.logger.info("Orderbook processing loop started.")
        # orderbook = await self.ws_client.get_latest_orderbook()
        # self.logger.info(f"Received orderbook: {orderbook}")
        while self.is_running:
            try:
                self.latency_monitor.start_tick()
                self.logger.debug("Waiting for latest orderbook...")
                orderbook = await self.ws_client.get_latest_orderbook()

                if not orderbook:
                    self.logger.debug("No orderbook data available, waiting...")
                    await asyncio.sleep(0.1)
                    continue

                self.logger.debug(f"Orderbook received: {orderbook}")
                self.current_orderbook = orderbook
                self.latency_monitor.end_data_processing()

                metrics = await self._calculate_metrics(orderbook)
                self.logger.debug(f"Emitting metrics: {metrics}")
                self.update_metrics.emit(metrics)


                self.latency_monitor.end_simulation_loop()
                self.latency_monitor.log_statistics()

                await asyncio.sleep(0.1)

            except asyncio.CancelledError:
                self.logger.info("Orderbook processing cancelled")
                break
            except Exception as e:
                self.logger.error(f"Error processing orderbook: {e}")
                self.update_status.emit(f"Error: {str(e)}")
                await asyncio.sleep(1)

    async def _process_final_orderbook_once(self):
        try:
            self.logger.info("Processing final orderbook tick before shutdown...")
            orderbook = await self.ws_client.get_latest_orderbook()
            if not orderbook:
                self.logger.warning("No orderbook available for final processing.")
                return
            self.current_orderbook = orderbook
            metrics = await self._calculate_metrics(orderbook)
            self.update_metrics.emit(metrics)
            self.logger.info(f"Final metrics emitted: {metrics}")
        except Exception as e:
            self.logger.error(f"Error processing final orderbook: {e}")

    async def _calculate_metrics(self, orderbook):
        try:
            if not orderbook:
                self.logger.warning("Orderbook is None, skipping metrics calculation")
                return {"slippage": 0, "market_impact": 0, "fees": 0, "total_cost": 0}

            # Use the updated inputs
            spot_asset = self.inputs.get("spot_asset", "BTC-USDT")
            order_type = self.inputs.get("order_type", "market")
            quantity = float(self.inputs.get("quantity", 100.0))
            volatility = float(self.inputs.get("volatility", 0.01))

            self.logger.debug(f"Spot Asset: {spot_asset}, Order Type: {order_type}, Quantity: {quantity}, Volatility: {volatility}")

            if not all(key in orderbook for key in ["asks", "bids"]):
                self.logger.warning("Orderbook missing required keys: asks, bids")
                return {}

            # Start measuring the time for the internal latency calculation
            start_time = time.time()

            self.logger.debug("Calculating slippage...")
            slippage = self.slippage_model.calculate_slippage(orderbook, quantity)
            self.logger.debug(f"Calculated slippage: {slippage}")

            self.logger.debug("Calculating market impact...")
            impact = self.market_impact_model.calculate_impact(orderbook, quantity)
            self.logger.debug(f"Calculated market impact: {impact}")

            self.logger.debug("Sampling maker/taker classification...")
            order_type = self.maker_taker_model.sample_maker_or_taker(orderbook, quantity)
            maker_prop = self.maker_taker_model.get_maker_proportion()
            taker_prop = self.maker_taker_model.get_taker_proportion()
            self.logger.debug(f"Sampled order type: {order_type}")
            self.logger.debug(f"Current maker proportion: {maker_prop}")
            self.logger.debug(f"Current taker proportion: {taker_prop}")

            fees = self.fee_model.calculate_expected_fees(maker_prop, taker_prop, quantity)
            self.logger.debug(f"Calculated fees: {fees}")

            total_cost = slippage + impact + fees

            # Measure the time taken for internal latency
            internal_latency = time.time() - start_time
            self.logger.debug(f"Internal Latency (processing time per tick): {internal_latency} seconds")

            metrics = {
                "slippage": slippage,
                "market_impact": impact,
                "maker_proportion": maker_prop,
                "taker_proportion": taker_prop,
                "fees": fees,
                "total_cost": total_cost,
                "volatility": volatility,  # Include volatility in the metrics
                "internal_latency": internal_latency  # Include internal latency
            }

            self.logger.debug(f"Metrics calculated: {metrics}")
            return metrics

        except Exception as e:
            self.logger.error(f"Error calculating metrics: {e}")
            return {"slippage": 0, "market_impact": 0, "fees": 0, "total_cost": 0}  # Default fallback
