from sklearn.preprocessing import StandardScaler
import numpy as np
from typing import Dict
from utils.logger import setup_logger

class MakerTakerModel:
    def __init__(self):
        self.logger = setup_logger("maker_taker_model")

        # Initial model parameters
        self.alpha = 0.5  # base linear influence
        self.beta = 0.1   # spread sensitivity
        self.gamma = 0.2  # volume sensitivity

        # Explicit weights for feature vector (learned over time)
        self.weights = np.ones(5)

        # Pre-compute constants
        self._update_constants()

        # History for online learning
        self.max_history = 1000
        self.feature_history = []
        self.maker_prop_history = []

        # Stats for simulation
        self.maker_count = 0
        self.taker_count = 0
        self.scaler = StandardScaler()

    def _update_constants(self):
        self.sqrt_alpha = np.sqrt(self.alpha)
        self.sqrt_beta = np.sqrt(self.beta)

    def _extract_features(self, orderbook: Dict, volume: float) -> np.ndarray:
        try:
            best_ask = orderbook["asks"][0][0]
            best_bid = orderbook["bids"][0][0]
            mid_price = (best_ask + best_bid) / 2.0

            spread = best_ask - best_bid
            spread_ratio = spread / mid_price if mid_price > 0 else 0.0

            ask_depth = sum(size for _, size in orderbook["asks"][:5])
            bid_depth = sum(size for _, size in orderbook["bids"][:5])
            total_depth = ask_depth + bid_depth
            depth_imbalance = (ask_depth - bid_depth) / total_depth if total_depth > 0 else 0.0

            volume_ratio = volume / total_depth if total_depth > 0 else 0.0

            features = np.array([
                spread_ratio,
                depth_imbalance,
                volume_ratio,
                np.log1p(volume),
                np.log1p(total_depth)
            ])
            return features  # Transform (not fit_transform) 
        except Exception as e:
            self.logger.error(f"Error extracting features: {e}")
            return np.zeros(5)

    def _predict_maker_prop(self, features: np.ndarray) -> float:
        try:
            linear_term = self.alpha * np.dot(features, self.weights)
            spread_term = self.beta * features[0]
            volume_term = self.gamma * features[2]

            maker_prop = linear_term - spread_term - volume_term
            maker_prop = np.clip(maker_prop, 0.0, 1.0)  # Ensure it's within [0,1]
            return maker_prop
        except Exception as e:
            self.logger.error(f"Error predicting maker proportion: {e}")
            return 0.5

    def _update_model(self, features: np.ndarray, actual_maker_prop: float):
        try:
            # Add feature and maker proportion to history for online learning
            self.feature_history.append(features)
            self.maker_prop_history.append(actual_maker_prop)

            # If the history exceeds the maximum allowed size, trim it
            if len(self.feature_history) > self.max_history:
                self.feature_history.pop(0)
                self.maker_prop_history.pop(0)

            # Update model parameters if there is enough history (at least 10 entries)
            if len(self.feature_history) >= 10:
                self._fit_parameters()
        except Exception as e:
            self.logger.error(f"Error updating model: {e}")

    def _fit_parameters(self):
        try:
            # Convert the feature history and maker proportion history to numpy arrays
            X = np.array(self.feature_history)
            y = np.array(self.maker_prop_history)

            # Linear term for regularization and model fitting
            linear_term = np.dot(X, self.weights)

            # Prepare the feature matrix for the fitting process
            A = np.column_stack([
                linear_term,
                X[:, 0],  # spread_ratio
                X[:, 2]   # volume_ratio
            ])

            # Ridge regularization parameter
            lambda_reg = 1e-4  # Regularization term to prevent overfitting

            # Perform ridge regression fitting using the normal equation
            A_T_A = A.T @ A + lambda_reg * np.eye(A.shape[1])
            A_T_y = A.T @ y
            params = np.linalg.solve(A_T_A, A_T_y)

            self.alpha = max(0.0, params[0])
            self.beta = max(0.0, params[1])
            self.gamma = max(0.0, params[2])

            # Optionally update feature weights via least squares
            self.weights = np.linalg.lstsq(X, y, rcond=None)[0]

            # Update constants after the parameter fit
            self._update_constants()
            self.logger.info(f"Updated params → alpha={self.alpha:.3f}, beta={self.beta:.3f}, gamma={self.gamma:.3f}")
        except Exception as e:
            self.logger.error(f"Error fitting parameters: {e}")

    def predict_maker_proportion(self, orderbook: Dict, volume: float) -> float:
        try:
            features = self._extract_features(orderbook, volume)
            maker_prop = self._predict_maker_prop(features)
            self._update_model(features, maker_prop)
            return maker_prop
        except Exception as e:
            self.logger.error(f"Error predicting maker proportion: {e}")
            return 0.5

    def sample_maker_or_taker(self, orderbook: Dict, volume: float) -> str:
        maker_prop = self.predict_maker_proportion(orderbook, volume)
        is_maker = np.random.rand() < maker_prop

        # Update the respective counts
        if is_maker:
            self.maker_count += 1
        else:
            self.taker_count += 1

        self.logger.info(f"Simulated trade: {'maker' if is_maker else 'taker'} (p={maker_prop:.2f})")
        return "maker" if is_maker else "taker"

    def get_maker_proportion(self) -> float:
        total = self.maker_count + self.taker_count
        return self.maker_count / total if total > 0 else 0.0

    def get_taker_proportion(self) -> float:
        total = self.maker_count + self.taker_count
        return self.taker_count / total if total > 0 else 0.0

    def get_model_parameters(self) -> Dict[str, float]:
        return {
            "alpha": self.alpha,
            "beta": self.beta,
            "gamma": self.gamma,
            "maker_ratio": self.get_maker_proportion(),
            "taker_ratio": self.get_taker_proportion(),
        }

    def reset_counts(self):
        self.maker_count = 0
        self.taker_count = 0
