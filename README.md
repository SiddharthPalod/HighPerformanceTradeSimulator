# Trade Simulator

A high-performance trade simulator that estimates transaction costs and market impact using real-time market data. This project implements sophisticated market impact models, slippage estimation, and maker/taker prediction with a focus on performance optimization and real-time processing.

## Features

- Real-time orderbook data via WebSocket
- Slippage estimation using quantile regression
- Market impact modeling using Almgren-Chriss model
- Maker/Taker ratio prediction
- Fee calculation based on tier
- Performance monitoring and latency tracking
- Modern PyQt5-based UI
- Comprehensive performance analysis and benchmarking
- Online learning capabilities for all models
- Asynchronous processing and efficient memory management

## Project Structure

```
trade-simulator/
│
├── main.py                   # Entry point
├── ui/
│   ├── layout.py            # UI layout (left inputs, right outputs)
│   └── controller.py        # UI → simulation logic bridge
│
├── data/
│   └── websocket_client.py  # WebSocket client for market data
│
├── models/
│   ├── slippage.py         # Slippage estimation model
│   ├── market_impact.py    # Almgren-Chriss model
│   └── maker_taker.py      # Maker/Taker prediction
│
├── utils/
│   └── logger.py           # Logging and error handling
│
├── analysis/
│   ├── latency.py          # Performance benchmarks
│   └── optimization.py     # Optimization logic
│
├── docs/
│   ├── performance_report.tex  # LaTeX performance report
│   └── Makefile               # LaTeX compilation rules
│
└── README.md
```

## Setup

1. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

## Usage

1. Launch the application
2. Configure input parameters:
   - Exchange (currently OKX only)
   - Asset (e.g., BTC-USDT-SWAP)
   - Order quantity
   - Volatility
   - Fee tier
3. Click "Start Simulation" to begin
4. Monitor real-time outputs:
   - Expected slippage
   - Expected fees
   - Expected market impact
   - Net cost
   - Maker/Taker ratio
   - Internal latency

## Models

### Slippage Model
- Uses quantile regression to estimate expected slippage
- Features:
  - Orderbook depth analysis
  - Size-to-depth ratio
  - Spread analysis
  - Online learning with limited history
  - Ridge regularization for stability

### Market Impact Model
- Implements Almgren-Chriss model
- Features:
  - Temporary and permanent impact components
  - Volume-based impact scaling
  - Risk-adjusted execution scheduling
  - Pre-computed constants for optimization
  - Dynamic parameter updates

### Maker/Taker Model
- Uses logistic regression to predict maker probability
- Features:
  - Spread analysis
  - Depth imbalance calculation
  - Volume ratio analysis
  - Online learning capabilities
  - Regularized parameter updates

## Performance Optimization

### Memory Management
- Limited history size (1000 samples)
- Efficient deque usage for tick buffers
- Automatic cleanup of old data
- Optimized data structures

### Network Communication
- Asynchronous WebSocket handling
- Efficient message buffering
- Robust error recovery
- Minimal data copying

### Thread Management
- Asyncio-based event loop
- Efficient task scheduling
- Signal-based UI updates
- Thread-safe operations

### Model Efficiency
- Pre-computed constants
- Efficient numpy operations
- Online learning optimization
- Regularization for stability

## Performance Monitoring

The simulator includes comprehensive performance monitoring:
- Data processing latency tracking
- UI update latency measurement
- End-to-end simulation loop timing
- Memory usage monitoring
- Network latency tracking

## Logging

Logs are stored in the `logs` directory with timestamps:
- WebSocket connection status
- Order processing latency
- Model inference times
- Error handling
- Performance metrics
- System resource usage

## Documentation

The project includes detailed documentation:
- Performance analysis report (LaTeX)
- Model implementation details
- Optimization strategies
- API documentation
- Usage examples

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Contributors

- Siddharth Palod - Lead Developer

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OKX for providing market data
- PyQt5 team for the UI framework
- NumPy and SciPy communities for scientific computing tools
