import sys
import asyncio
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from ui.layout import MainWindow
from ui.controller import SimulationController
from utils.logger import setup_logger

def main():
    # Set up logging
    logger = setup_logger("main")
    logger.info("Starting Trade Simulator")
    
    try:
        # Create Qt application
        app = QApplication(sys.argv)
        
        # Create main window
        window = MainWindow()
        window.show()
        
        # Create and set up event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Create controller with window as parent
        controller = SimulationController(parent=window, loop=loop)
        
        # Connect signals
        window.start_simulation.connect(controller.start_simulation)
        window.stop_simulation.connect(controller.stop_simulation)
        controller.update_status.connect(window.update_status)
        controller.update_metrics.connect(window.update_metrics)


        # Set up timer for asyncio event loop
        timer = QTimer()
        timer.timeout.connect(lambda: loop.run_until_complete(asyncio.sleep(0)))
        timer.start(50)  # 50ms interval
        
        # Run application
        exit_code = app.exec_()
        
        # Graceful shutdown
        async def shutdown():
            try:
                # Stop simulation (if running)
                await controller.stop_simulation_async()
                # Wait a short time for async tasks to finish
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"Error during shutdown: {e}")
        
        # Run shutdown
        loop.run_until_complete(shutdown())
        loop.close()
        
        logger.info("Trade Simulator stopped")
        return exit_code
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
