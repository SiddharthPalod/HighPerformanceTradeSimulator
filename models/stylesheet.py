dark_stylesheet = """
* {
    font-size: 13px;
}

QMainWindow {
    background-color: #121212;
}

QGroupBox {
    border: 1px solid #3a3a3a;
    border-radius: 10px;
    margin-top: 20px;
    background-color: #1e1e1e;
    color: #f0f0f0;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 3px 3px;
    font-weight: bold;
    font-size: 18px;
}

QLabel {
    color: #dddddd;
}

QLineEdit, QPlainTextEdit, QComboBox {
    background-color: #2c2c2c;
    color: #f0f0f0;
    border: 1px solid #444;
    border-radius: 6px;
    padding: 4px;
}

QLineEdit:focus, QComboBox:focus {
    border: 1px solid #00ea75;
}

QPushButton {
    background-color: #3c3c3c;
    color: #ffffff;
    border: 1px solid #555;
    border-radius: 8px;
    padding: 5px 15px;
}

QPushButton:hover {
    background-color: #505050;
    border: 1px solid #00ea75;
}

QPushButton:pressed {
    background-color: #00ea75;
}

/* Disabled button state */
QPushButton:disabled {
    background-color: #2c2c2c;
    color: #777777;
    border: 1px solid #333;
}

QPushButton#startButton[active="true"] {
    background-color: #00ea75;
    color: #000;
    border: 1px solid #00ea75;
}

QPushButton#stopButton:enabled {
    background-color: #ff5c5c;
    color: #ffffff;
    border: 1px solid #ff8a8a;
}


QStatusBar {
    background-color: #1a1a1a;
    color: #c0c0c0;
    border-top: 1px solid #444;
}

QProgressBar {
    background-color: #2c2c2c;
    border: 1px solid #444;
    border-radius: 5px;
    text-align: center;
    color: #f0f0f0;
}

QProgressBar::chunk {
    background-color: #00ea75;
    border-radius: 5px;
}
"""
