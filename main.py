"""ChemLab UI 入口
动态加载ui
"""

from __future__ import annotations

import sys

from src.ui.main_window import MainWindow, create_application

def main() -> int:
    app = create_application(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
