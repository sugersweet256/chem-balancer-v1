"""离屏生成 UI 预览图。

用法：
    python tools/screenshot.py preview.png 1480 1000
    python tools/screenshot.py preview-periodic.png 1480 900 --periodic
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QFontDatabase  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ui.main_window import MainWindow, create_application  # noqa: E402
from src.ui.periodic_window import PeriodicTableWindow  # noqa: E402

FONT_FILES = [
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\segoeui.ttf",
    r"C:\Windows\Fonts\segoeuib.ttf",
    r"C:\Windows\Fonts\cambria.ttc",
    r"C:\Windows\Fonts\cambriab.ttf",
    r"C:\Windows\Fonts\times.ttf",
]


def load_fonts() -> None:
    for path in FONT_FILES:
        if Path(path).exists():
            QFontDatabase.addApplicationFont(path)


def main() -> int:
    periodic = "--periodic" in sys.argv
    balance = "--balance" in sys.argv
    args = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
    output = Path(args[0]) if args else Path("preview.png")
    width = int(args[1]) if len(args) > 1 else 1480
    height = int(args[2]) if len(args) > 2 else (900 if periodic else 1000)

    app = create_application([])
    load_fonts()
    window = PeriodicTableWindow() if periodic else MainWindow()
    window.resize(width, height)
    window.show()
    if balance and hasattr(window, "balance_button"):
        window.balance_button.click()
    for _ in range(6):
        app.processEvents()

    pixmap = window.grab()
    if not pixmap.save(str(output), "PNG"):
        print(f"保存失败：{output}", file=sys.stderr)
        return 1
    print(f"已保存：{output} ({pixmap.width()}x{pixmap.height()})")
    window.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
