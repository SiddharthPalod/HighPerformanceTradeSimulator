import numpy as np
from typing import Dict, List, Tuple
from utils.logger import setup_logger

class SlippageModel:
    def __init__(self):
        self.logger = setup_logger("slippage_model")
        
        # Model parameters
        self.alpha = 0.1  # Linear coefficient
        self.beta = 0.5   # Square root coefficient
        self.gamma = 0.01 # Constant coefficient
        
        # Pre-compute constants
        self._update_constants()
        
        # Feature history for online learning
        self.max_history = 1000
        self.feature_history = []
        self.slippage_history = []
    
    def _update_constants(self):
        """Update pre-computed constants"""
        self.sqrt_alpha = np.sqrt(self.alpha)
        self.sqrt_beta = np.sqrt(self.beta)
    
    def calculate_slippage(self, orderbook: Dict, order_size: float) -> float:
        """
        Calculate expected slippage using regression model
        
        Parameters:
        - orderbook: Dictionary containing 'asks' and 'bids' arrays
        - order_size: Size of the order
        
        Returns:
        - Estimated slippage in basis points
        """
        try:
            # Extract features
            features = self._extract_features(orderbook, order_size)
            
            # Calculate slippage using regression model
            slippage = self._predict_slippage(features)
            
            # Update model with new data
            self._update_model(features, slippage)
            
            return slippage
            
        except Exception as e:
            self.logger.error(f"Error calculating slippage: {e}")
            return 0.0
    
    def _extract_features(self, orderbook: Dict, order_size: float) -> np.ndarray:
        """Extract features from orderbook for slippage prediction"""
        try:
            # Get best bid/ask
            best_ask = orderbook["asks"][0][0]
            best_bid = orderbook["bids"][0][0]
            mid_price = (best_ask + best_bid) / 2
            
            # Calculate spread
            spread = best_ask - best_bid
            
            # Calculate depth at best bid/ask
            depth_at_best = min(
                orderbook["asks"][0][1],
                orderbook["bids"][0][1]
            )
            
            # Calculate total depth (sum of first 10 levels)
            total_depth = (
                sum(size for _, size in orderbook["asks"][:10]) +
                sum(size for _, size in orderbook["bids"][:10])
            )
            
            # Calculate order size relative to depth
            size_to_depth = order_size / total_depth if total_depth > 0 else 0
            
            # Create feature vector
            features = np.array([
                spread / mid_price,  # Normalized spread
                size_to_depth,      # Relative order size
                depth_at_best / total_depth,  # Relative depth at best
                np.log1p(order_size),  # Log of order size
                np.log1p(total_depth)  # Log of total depth
            ])
            
            return features
            
        except Exception as e:
            self.logger.error(f"Error extracting features: {e}")
            return np.zeros(5)
    
    def _predict_slippage(self, features: np.ndarray) -> float:
        """Predict slippage using regression model"""
        try:
            # Linear component
            linear_term = self.alpha * np.dot(features, np.ones_like(features))
            
            # Square root component
            sqrt_term = self.beta * np.sqrt(np.abs(linear_term))
            
            # Constant component
            constant_term = self.gamma
            
            # Total slippage in basis points
            slippage = (linear_term + sqrt_term + constant_term) * 10000
            
            return max(0.0, slippage)  # Ensure non-negative
            
        except Exception as e:
            self.logger.error(f"Error predicting slippage: {e}")
            return 0.0
    
    def _update_model(self, features: np.ndarray, actual_slippage: float):
        """Update model parameters using online learning"""
        try:
            # Add new data point to history
            self.feature_history.append(features)
            self.slippage_history.append(actual_slippage)
            
            # Keep history within bounds
            if len(self.feature_history) > self.max_history:
                self.feature_history.pop(0)
                self.slippage_history.pop(0)
            
            # Update model parameters if we have enough data
            if len(self.feature_history) >= 10:
                self._fit_parameters()
                
        except Exception as e:
            self.logger.error(f"Error updating model: {e}")
    
    def _fit_parameters(self):
        """Fit model parameters using least squares regression"""
        try:
            # Convert history to numpy arrays
            X = np.array(self.feature_history)
            y = np.array(self.slippage_history)
            
            # Calculate linear term
            linear_term = np.dot(X, np.ones_like(X[0]))
            
            # Fit parameters using numpy's least squares
            A = np.column_stack([
                linear_term,
                np.sqrt(np.abs(linear_term)),
                np.ones_like(linear_term)
            ])
            
            # Solve least squares problem
            params, _, _, _ = np.linalg.lstsq(A, y, rcond=None)
            
            # Update parameters
            self.alpha = max(0.0, params[0])
            self.beta = max(0.0, params[1])
            self.gamma = max(0.0, params[2])
            
            # Update constants
            self._update_constants()
            
        except Exception as e:
            self.logger.error(f"Error fitting parameters: {e}")
        
    def _calculate_mid_price(self, asks: List[List[float]], bids: List[List[float]]) -> float:
        """Calculate the mid price from the best bid and ask"""
        if not asks or not bids:
            return 0.0
        best_ask = asks[0][0]
        best_bid = bids[0][0]
        return (best_ask + best_bid) / 2
        
    def _calculate_depth_features(self, orders: List[List[float]], side: str) -> np.ndarray:
        """Calculate depth features from order book"""
        if not orders:
            return np.zeros((1, 3))
            
        prices = np.array([order[0] for order in orders])
        sizes = np.array([order[1] for order in orders])
        
        # Calculate cumulative size
        cum_size = np.cumsum(sizes)
        
        # Calculate weighted average price
        wap = np.sum(prices * sizes) / np.sum(sizes)
        
        # Calculate price spread
        price_spread = prices[-1] - prices[0]
        
        return np.array([[wap, price_spread, cum_size[-1]]])
        
    def train(self, historical_data: List[Tuple[List[List[float]], List[List[float]], float]]):
        """
        Train the slippage model on historical data
        
        Args:
            historical_data: List of tuples containing (asks, bids, actual_slippage)
        """
        X = []
        y = []
        
        for asks, bids, actual_slippage in historical_data:
            mid_price = self._calculate_mid_price(asks, bids)
            ask_features = self._calculate_depth_features(asks, 'ask')
            bid_features = self._calculate_depth_features(bids, 'bid')
            
            features = np.concatenate([ask_features, bid_features], axis=1)
            X.append(features.flatten())
            y.append(actual_slippage)
            
        X = np.array(X)
        y = np.array(y)
        
        self.model.fit(X, y)
        self.is_trained = True
        
    def predict_slippage(self, asks: List[List[float]], bids: List[List[float]], 
                        quantity: float) -> float:
        """
        Predict expected slippage for a given order size
        
        Args:
            asks: List of [price, size] for ask orders
            bids: List of [price, size] for bid orders
            quantity: Order quantity
            
        Returns:
            float: Predicted slippage in basis points
        """
        if not self.is_trained:
            return 0.0
            
        mid_price = self._calculate_mid_price(asks, bids)
        ask_features = self._calculate_depth_features(asks, 'ask')
        bid_features = self._calculate_depth_features(bids, 'bid')
        
        features = np.concatenate([ask_features, bid_features], axis=1)
        features = np.append(features, quantity)
        
        predicted_slippage = self.model.predict(features.reshape(1, -1))[0]
        return predicted_slippage
        
    def calculate_immediate_slippage(self, asks: List[List[float]], bids: List[List[float]], 
                                   quantity: float, side: str) -> float:
        """
        Calculate immediate slippage for a market order
        
        Args:
            asks: List of [price, size] for ask orders
            bids: List of [price, size] for bid orders
            quantity: Order quantity
            side: 'buy' or 'sell'
            
        Returns:
            float: Immediate slippage in basis points
        """
        if not asks or not bids:
            return 0.0
            
        mid_price = self._calculate_mid_price(asks, bids)
        orders = asks if side == 'buy' else bids
        remaining_quantity = quantity
        total_cost = 0.0
        
        for price, size in orders:
            if remaining_quantity <= 0:
                break
                
            executed_size = min(remaining_quantity, size)
            total_cost += price * executed_size
            remaining_quantity -= executed_size
            
        if remaining_quantity > 0:
            return float('inf')  # Not enough liquidity
            
        avg_price = total_cost / quantity
        slippage = ((avg_price - mid_price) / mid_price) * 10000  # Convert to basis points
        
        return slippage if side == 'buy' else -slippage 