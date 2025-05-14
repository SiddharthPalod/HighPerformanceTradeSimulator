import time
import numpy as np
from collections import deque
from typing import Dict, List, Optional
from utils.logger import setup_logger

class LatencyMonitor:
    def __init__(self, window_size: int = 1000):
        self.logger = setup_logger("latency_monitor")
        self.window_size = window_size
        
        # Latency measurements
        self.data_processing_latencies = deque(maxlen=window_size)
        self.ui_update_latencies = deque(maxlen=window_size)
        self.simulation_loop_latencies = deque(maxlen=window_size)
        
        # Timestamps for end-to-end tracking
        self.last_tick_time = None
        self.last_processing_time = None
        self.last_ui_update_time = None
    
    def start_tick(self):
        """Start timing a new tick"""
        self.last_tick_time = time.perf_counter()
    
    def end_data_processing(self):
        """Record data processing latency"""
        if self.last_tick_time is None:
            return
        
        current_time = time.perf_counter()
        latency = (current_time - self.last_tick_time) * 1000  # Convert to ms
        self.data_processing_latencies.append(latency)
        self.last_processing_time = current_time
    
    def end_ui_update(self):
        """Record UI update latency"""
        if self.last_processing_time is None:
            return
        
        current_time = time.perf_counter()
        latency = (current_time - self.last_processing_time) * 1000  # Convert to ms
        self.ui_update_latencies.append(latency)
        self.last_ui_update_time = current_time
    
    def end_simulation_loop(self):
        """Record end-to-end simulation loop latency"""
        if self.last_tick_time is None:
            return
        
        current_time = time.perf_counter()
        latency = (current_time - self.last_tick_time) * 1000  # Convert to ms
        self.simulation_loop_latencies.append(latency)
        
        # Reset timestamps
        self.last_tick_time = None
        self.last_processing_time = None
        self.last_ui_update_time = None
    
    def get_statistics(self) -> Dict[str, Dict[str, float]]:
        """Get latency statistics"""
        stats = {}
        
        for name, latencies in [
            ("data_processing", self.data_processing_latencies),
            ("ui_update", self.ui_update_latencies),
            ("simulation_loop", self.simulation_loop_latencies)
        ]:
            if latencies:
                latencies_array = np.array(latencies)
                stats[name] = {
                    "mean": float(np.mean(latencies_array)),
                    "std": float(np.std(latencies_array)),
                    "min": float(np.min(latencies_array)),
                    "max": float(np.max(latencies_array)),
                    "p95": float(np.percentile(latencies_array, 95)),
                    "p99": float(np.percentile(latencies_array, 99))
                }
            else:
                stats[name] = {
                    "mean": 0.0,
                    "std": 0.0,
                    "min": 0.0,
                    "max": 0.0,
                    "p95": 0.0,
                    "p99": 0.0
                }
        
        return stats
    
    def log_statistics(self):
        """Log current latency statistics"""
        stats = self.get_statistics()
        for metric, values in stats.items():
            self.logger.info(f"{metric} latency (ms):")
            for stat, value in values.items():
                self.logger.info(f"  {stat}: {value:.2f}") 