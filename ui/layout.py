from PyQt5.QtWidgets import (QMainWindow, QWidget, QPlainTextEdit, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QComboBox, QPushButton, QProgressBar, QGroupBox, QFormLayout)
from PyQt5.QtCore import Qt, pyqtSignal
from utils.logger import setup_logger
from models.stylesheet import dark_stylesheet

class MainWindow(QMainWindow):
    # Define signals
    start_simulation = pyqtSignal(dict)
    stop_simulation = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.logger = setup_logger("main_window")
        self.setWindowTitle("Trade Simulator")
        self.setMinimumSize(900, 700)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        
        # Create input panel
        input_panel = self._create_input_panel()
        layout.addWidget(input_panel)
        
        # Create output panel
        output_panel = self._create_output_panel()
        layout.addWidget(output_panel)
        
        # Set up status bar
        self.statusBar().showMessage("Ready")
        self.setStyleSheet(dark_stylesheet)

    
    def _create_input_panel(self):
        """Create the input panel with controls"""
        panel = QGroupBox("Input Parameters")
        layout = QVBoxLayout(panel)
        
        # Exchange selection
        exchange_layout = QHBoxLayout()
        exchange_layout.addWidget(QLabel("Exchange:"))
        self.exchange_combo = QComboBox()
        self.exchange_combo.addItems(["OKX"])  # Add more exchanges if needed
        exchange_layout.addWidget(self.exchange_combo)
        layout.addLayout(exchange_layout)
        
        # Spot Asset input
        asset_layout = QHBoxLayout()
        asset_layout.addWidget(QLabel("Spot Asset:"))
        self.asset_input = QLineEdit("BTC-USDT")
        asset_layout.addWidget(self.asset_input)
        layout.addLayout(asset_layout)
        
        # Order Type input (default "Market")
        order_type_layout = QHBoxLayout()
        order_type_layout.addWidget(QLabel("Order Type:"))
        self.order_type_combo = QComboBox()
        self.order_type_combo.addItems(["Market", "Limit", "Stop"])  # Add more order types if needed
        order_type_layout.addWidget(self.order_type_combo)
        layout.addLayout(order_type_layout)
        
        # Quantity input (USD equivalent)
        quantity_layout = QHBoxLayout()
        quantity_layout.addWidget(QLabel("Quantity (USD equivalent):"))
        self.quantity_input = QLineEdit("100")  # Default 100 USD
        quantity_layout.addWidget(self.quantity_input)
        layout.addLayout(quantity_layout)
        
        # Volatility input (can be fetched from exchange API or input manually)
        volatility_layout = QHBoxLayout()
        volatility_layout.addWidget(QLabel("Volatility (%):"))
        self.volatility_input = QLineEdit("2.0")  # Default volatility, adjust as needed
        volatility_layout.addWidget(self.volatility_input)
        layout.addLayout(volatility_layout)
        
        # Fee tier selection
        fee_layout = QHBoxLayout()
        fee_layout.addWidget(QLabel("Fee Tier:"))
        self.fee_combo = QComboBox()
        self.fee_combo.addItems(["Low", "Mid", "High"])  # Example fee tiers
        fee_layout.addWidget(self.fee_combo)
        layout.addLayout(fee_layout)
        
        # Control buttons
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self._on_start)
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self._on_stop)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        layout.addLayout(button_layout)
        
        return panel

    def _create_output_panel(self):
        """Create the output panel with metrics display"""
        panel = QGroupBox("Simulation Output")
        layout = QVBoxLayout(panel)
        
        # Create metric labels
        self.metric_labels = {}
        metrics = [
            "slippage", "market_impact", "maker_proportion",
            "taker_proportion", "fees", "total_cost","internal_latency"
        ]
        
        for metric in metrics:
            metric_layout = QHBoxLayout()
            metric_layout.addWidget(QLabel(f"{metric.replace('_', ' ').title()}:"))
            label = QLabel("0.00")
            self.metric_labels[metric] = label
            metric_layout.addWidget(label)
            layout.addLayout(metric_layout)

        # Add the plain text output display here
        self.simulation_output = QPlainTextEdit()
        self.simulation_output.setReadOnly(True)
        layout.addWidget(self.simulation_output)
        
        # Add status label
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        return panel

    def _on_start(self):
        """Handle start button click"""
        try:
            # Get input values
            inputs = {
                "exchange": self.exchange_combo.currentText(),
                "asset": self.asset_input.text(),
                "order_type": self.order_type_combo.currentText(),
                "quantity_usd": float(self.quantity_input.text()),
                "volatility": float(self.volatility_input.text()),
                "fee_tier": self.fee_combo.currentText()
            }
            
            # Update UI state
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            
            # Emit start signal
            self.start_simulation.emit(inputs)
            
        except ValueError as e:
            self.logger.error(f"Invalid input: {e}")
            self.statusBar().showMessage(f"Error: Invalid input - {str(e)}")
    
    def _on_stop(self):
        """Handle stop button click"""
        # Update UI state
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
        # Emit stop signal
        self.stop_simulation.emit()
    
    def update_status(self, message: str):
        """Update status message"""
        self.statusBar().showMessage(message)
        self.status_label.setText(message)
    
    def update_metrics(self, metrics: dict):
        """Update metric displays"""
        for metric, value in metrics.items():
            if metric in self.metric_labels:
                self.metric_labels[metric].setText(f"{value:.4f}")
        
        # Also update simulation_output field visibly
        text = "\n".join(f"{k}: {v:.4f}" for k, v in metrics.items())
        self.simulation_output.setPlainText(text)
    
    def get_inputs(self):
        """Get input values from UI"""
        return {
            "exchange": self.exchange_combo.currentText(),
            "asset": self.asset_input.text(),
            "order_type": self.order_type_combo.currentText(),
            "quantity_usd": float(self.quantity_input.text()),
            "volatility": float(self.volatility_input.text()),
            "fee_tier": self.fee_combo.currentText()
        }
    
    def update_outputs(self, slippage: float, market_impact: float,
                      maker_taker: float, total_cost: float,
                      fee: float,internal_latency: float):
        """Update output values in UI"""
        self.metric_labels["slippage"].setText(f"{slippage:.6f}")
        self.metric_labels["market_impact"].setText(f"{market_impact:.6f}")
        self.metric_labels["maker_proportion"].setText(f"{maker_taker:.6f}")
        self.metric_labels["taker_proportion"].setText(f"{1 - maker_taker:.6f}")
        self.metric_labels["fees"].setText(f"{fee:.6f}")
        self.metric_labels["total_cost"].setText(f"{total_cost:.6f}")
        self.metric_labels["internal_latency"].setText(f"{internal_latency:.6f}")

