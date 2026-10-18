import sys
from PySide6.QtWidgets import *


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("化学方程式配平器")
        self.resize(500, 300)

        w = QWidget()
        self.setCentralWidget(w)
        layout = QVBoxLayout(w)

        self.input = QLineEdit()
        self.input.setPlaceholderText("输入方程式，如: H2 + O2 -> H2O")
        layout.addWidget(self.input)

        btn = QPushButton("配平")
        btn.clicked.connect(self.balance)
        layout.addWidget(btn)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output)

    def balance(self):
        eq = self.input.text()
        try:
            from src.parser import parse_equation
            from src.balancer import balancer
            reactants, products, (r_strs, p_strs) = parse_equation(eq)
            result = balancer(reactants, products, (r_strs, p_strs))
            self.output.setText(result)
        except Exception as e:
            self.output.setText(f"错误: {e}")


app = QApplication(sys.argv)
w = Window()
w.show()
sys.exit(app.exec())
