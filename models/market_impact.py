import numpy as np
from typing import Dict, List, Tuple
from utils.logger import setup_logger

class MarketImpactModel:
    def __init__(self):
        self.logger = setup_logger("market_impact_model")
        self.volatility = 0.02  # Default volatility
        self.risk_aversion = 0.1  # Default risk aversion
        self.eta = 0.1  # Linear market impact coefficient
        self.gamma = 0.1  # Square root market impact coefficient
        
        # Pre-compute constants for optimization
        self._update_constants()
    
    def _update_constants(self):
        """Update pre-computed constants"""
        self.sqrt_eta = np.sqrt(self.eta)
        self.sqrt_gamma = np.sqrt(self.gamma)
        self.vol_sqrt_T = self.volatility * np.sqrt(1.0)  # T = 1 day
    
    def update_parameters(self, volatility: float = None, risk_aversion: float = None):
        """Update model parameters"""
        if volatility is not None:
            self.volatility = volatility
        if risk_aversion is not None:
            self.risk_aversion = risk_aversion
        
        self._update_constants()
    
    
    def _calculate_temporary_impact(self, order_size: float, orderbook: Dict) -> float:
        """
        Calculate temporary market impact using real orderbook volume.
        """
        # Estimate volume from top N levels of the book
        N = 5
        ask_volumes = [ask[1] for ask in orderbook.get("asks", [])[:N]]
        bid_volumes = [bid[1] for bid in orderbook.get("bids", [])[:N]]
        avg_volume = np.mean(ask_volumes + bid_volumes) * N if ask_volumes and bid_volumes else 1e6

        # Impact
        impact = self.eta * np.sqrt(np.abs(order_size) / avg_volume)
        return impact * np.sign(order_size)

    def _calculate_permanent_impact(self, order_size: float, orderbook: Dict) -> float:
        """
        Calculate permanent market impact using real orderbook volume.
        """
        # Estimate volume from orderbook
        N = 5
        ask_volumes = [ask[1] for ask in orderbook.get("asks", [])[:N]]
        bid_volumes = [bid[1] for bid in orderbook.get("bids", [])[:N]]
        avg_volume = np.mean(ask_volumes + bid_volumes) * N if ask_volumes and bid_volumes else 1e6

        # Impact
        impact = self.gamma * (np.abs(order_size) / avg_volume)
        return impact * np.sign(order_size)

    def calculate_impact(self, orderbook: Dict, order_size: float, volatility: float = None) -> float:
        try:
            if volatility is not None:
                self.volatility = volatility
                self._update_constants()

            best_ask = orderbook["asks"][0][0]
            best_bid = orderbook["bids"][0][0]
            mid_price = (best_ask + best_bid) / 2

            temp_impact = self._calculate_temporary_impact(order_size, orderbook)
            perm_impact = self._calculate_permanent_impact(order_size, orderbook)

            total_impact = (temp_impact + perm_impact) / mid_price * 10000  # in basis points
            return total_impact

        except Exception as e:
            self.logger.error(f"Error calculating market impact: {e}")
            return 0.0

    def optimize_execution(self, order_size: float, time_horizon: float) -> List[Tuple[float, float]]:
        """
        Optimize execution schedule using Almgren-Chriss model
        
        Parameters:
        - order_size: Total order size
        - time_horizon: Trading horizon in days
        
        Returns:
        - List of (time, size) tuples representing optimal execution schedule
        """
        try:
            # Number of trading intervals
            n_intervals = 10
            
            # Time points
            t = np.linspace(0, time_horizon, n_intervals + 1)
            
            # Calculate optimal trading rate
            k = np.sqrt(self.risk_aversion * self.volatility**2 / self.eta)
            
            # Calculate optimal schedule
            x = order_size * np.cosh(k * (time_horizon - t)) / np.cosh(k * time_horizon)
            
            # Calculate trade sizes
            trade_sizes = np.diff(x)
            
            # Create schedule
            schedule = list(zip(t[1:], trade_sizes))
            
            return schedule
            
        except Exception as e:
            self.logger.error(f"Error optimizing execution: {e}")
            return [] 