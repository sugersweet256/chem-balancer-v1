"""ChemLab 主窗口控制器。

界面由 Qt Designer 文件 ``main_window.ui`` 描述；配平和解析逻辑来自现有
``src/parser.py`` 与 ``src/balancer.py``，通过 ``legacy_adapter.py`` 调用。
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    QTimer,
    Qt,
)
from PySide6.QtGui import (
    QColor,
    QFont,
    QGuiApplication,
    QIcon,
    QKeySequence,
    QPixmap,
    QShortcut,
)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QHeaderView,
    QLabel,
    QLayout,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QWidget,
)

from .legacy_adapter import (
    LegacyChemistryError,
    UIBalanceResult as BalanceResult,
    balance_equation,
)
from . import render

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[1]
ASSETS = PROJECT_ROOT / "assets" / "icons"

EXAMPLES = [
    "H2 + O2 → H2O",
    "CH4 + O2 → CO2 + H2O",
    "Fe + O2 → Fe2O3",
    "C2H6 + O2 → CO2 + H2O",
    "Al + CuSO4 → Al2(SO4)3 + Cu",
    "Ca(OH)2 + HCl → CaCl2 + H2O",
    "Fe2O3 + CO → Fe + CO2",
    "CuSO4·5H2O → CuSO4 + H2O",
]


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._result: BalanceResult | None = None
        self._toast_animation: QPropertyAnimation | None = None
        self._toast_effect: QGraphicsOpacityEffect | None = None
        self._favorite = False
        self._periodic_window = None

        self._load_designer_ui()
        self._find_widgets()
        self._configure_window()
        self._configure_widgets()
        self._connect_signals()

        self.input.setText(EXAMPLES[0])
        self._run_balance()

    # ------------------------------------------------------------------ UI
    def _load_designer_ui(self) -> None:
        loader = QUiLoader()
        ui_path = BASE_DIR / "main_window.ui"
        loaded = loader.load(str(ui_path))
        if loaded is None:
            raise RuntimeError(f"无法加载 Qt Designer 界面：{loader.errorString()}")

        window_title = loaded.windowTitle()
        window_size = loaded.size()
        central = loaded.takeCentralWidget()
        if central is None:
            raise RuntimeError("main_window.ui 缺少 centralWidget")
        self.setCentralWidget(central)
        self.resize(window_size)
        self.setWindowTitle(window_title)
        loaded.deleteLater()

    def _find_widgets(self) -> None:
        def widget(name: str, kind):
            found = self.findChild(kind, name)
            if found is None:
                raise RuntimeError(f"界面缺少控件：{name}")
            return found

        self.input = widget("equationInput", QLineEdit)
        self.clear_button = widget("clearButton", QPushButton)
        self.copy_button = widget("copyButton", QPushButton)
        self.favorite_button = widget("favoriteButton", QPushButton)
        self.equation_label = widget("equationLabel", QLabel)
        self.status_pill = widget("statusPill", QLabel)
        self.result_meta = widget("resultMeta", QLabel)
        self.coefficient_row = widget("coefficientRow", QWidget)
        self.coefficient_chips = widget("coefficientChips", QWidget)
        self.coefficient_layout = self.coefficient_chips.layout()
        self.conservation_stack = widget("conservationStack", QStackedWidget)
        self.conservation_table = widget("conservationTable", QTableWidget)
        self.conservation_hint = widget("conservationHint", QLabel)
        self.steps_browser = widget("stepsBrowser", QTextBrowser)
        self.page = widget("page", QWidget)
        self.body = widget("body", QWidget)
        self.left_column = widget("leftColumn", QWidget)
        self.center_column = widget("centerColumn", QWidget)

    def _configure_window(self) -> None:
        self.setMinimumSize(1280, 760)
        self.setWindowIcon(QIcon(str(ASSETS / "logo.svg")))

        screen = QGuiApplication.primaryScreen()
        if screen is not None:
            available = screen.availableGeometry()
            target_width = min(1480, max(1280, available.width() - 60))
            target_height = min(1000, max(760, available.height() - 40))
            self.resize(target_width, target_height)
            frame = self.frameGeometry()
            frame.moveCenter(available.center())
            self.move(frame.topLeft())

    def _configure_widgets(self) -> None:
        self.setStyleSheet((BASE_DIR / "styles.qss").read_text(encoding="utf-8"))

        self.status_pill.setProperty("state", "idle")
        self.result_meta.setProperty("state", "idle")
        self.copy_button.setEnabled(False)
        self.favorite_button.setProperty("active", False)
        self.coefficient_row.setVisible(False)
        self.conservation_stack.setCurrentIndex(0)
        self.conservation_stack.setFixedHeight(120)
        self.steps_browser.setHtml(render.steps_placeholder_html())

        self.input.setAccessibleName("化学方程式输入框")
        self.input.setClearButtonEnabled(False)

        page = self.findChild(QWidget, "page")
        if page is not None and page.layout() is not None:
            page.layout().setSizeConstraint(QLayout.SetMinimumSize)

        table = self.conservation_table
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setFixedHeight(31)
        header.setDefaultAlignment(Qt.AlignCenter)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(34)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.NoSelection)
        table.setFocusPolicy(Qt.NoFocus)
        table.setShowGrid(False)
        table.setAlternatingRowColors(False)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        for name in ("inputCard", "syntaxCard", "conservationCard", "stepsCard"):
            card = self.findChild(QFrame, name)
            if card is not None:
                self._add_shadow(card, 18)

        for index in range(1, 9):
            button = self.findChild(QPushButton, f"exampleButton{index}")
            if button is not None:
                button.setToolTip(EXAMPLES[index - 1])
                button.setCursor(Qt.PointingHandCursor)

        self._set_icon("brandMark", "logo.svg", 38)
        self._set_icon("heroIcon", "flask.svg", 42)

        self._shortcut_clear = QShortcut(QKeySequence("Ctrl+L"), self)
        self._shortcut_clear.activated.connect(self._clear)

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(320)
        self._debounce.timeout.connect(self._run_balance)

        self._toast = QLabel(self)
        self._toast.setObjectName("toast")
        self._toast.setAlignment(Qt.AlignCenter)
        self._toast.hide()
        self._toast_effect = QGraphicsOpacityEffect(self._toast)
        self._toast_effect.setOpacity(0.0)
        self._toast.setGraphicsEffect(self._toast_effect)
        self._toast_timer = QTimer(self)
        self._toast_timer.setSingleShot(True)
        self._toast_timer.timeout.connect(self._hide_toast)

        self._copy_timer = QTimer(self)
        self._copy_timer.setSingleShot(True)
        self._copy_timer.timeout.connect(lambda: self.copy_button.setText("复制"))

        # QScrollArea 的 widgetResizable 会把内容压进视口。显式同步列的最小
        # 高度，离子方程式的“电荷”行增加时才不会被卡片裁掉。
        self._page_sync_timer = QTimer(self)
        self._page_sync_timer.setSingleShot(True)
        self._page_sync_timer.setInterval(0)
        self._page_sync_timer.timeout.connect(self._sync_page_height)

    def _set_icon(self, label_name: str, icon_name: str, size: int) -> None:
        label = self.findChild(QLabel, label_name)
        if label is None:
            return
        pixmap = QPixmap(str(ASSETS / icon_name))
        if pixmap.isNull():
            return
        label.setText("")
        label.setPixmap(
            pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )

    @staticmethod
    def _add_shadow(widget: QWidget, blur: int) -> None:
        effect = QGraphicsDropShadowEffect(widget)
        effect.setBlurRadius(blur)
        effect.setOffset(0, 6)
        effect.setColor(QColor(20, 45, 70, 22))
        widget.setGraphicsEffect(effect)

    def _connect_signals(self) -> None:
        self.input.textChanged.connect(self._on_text_changed)
        self.input.returnPressed.connect(self._run_balance)
        self.clear_button.clicked.connect(self._clear)
        self.copy_button.clicked.connect(self._copy_result)
        self.favorite_button.clicked.connect(self._toggle_favorite)

        for index in range(1, 9):
            button = self.findChild(QPushButton, f"exampleButton{index}")
            if button is not None:
                button.clicked.connect(
                    lambda checked=False, i=index - 1: self._use_example(i)
                )

        for name in ("navMolar",):
            button = self.findChild(QPushButton, name)
            if button is not None:
                button.clicked.connect(
                    lambda checked=False, b=button: self._show_toast(
                        f"「{b.text()}」将在后续版本加入"
                    )
                )

        nav_periodic = self.findChild(QPushButton, "navPeriodic")
        if nav_periodic is not None:
            nav_periodic.setCursor(Qt.PointingHandCursor)
            nav_periodic.clicked.connect(self._open_periodic_table)

    # -------------------------------------------------------------- states
    def _on_text_changed(self, _text: str) -> None:
        self._debounce.start()

    def _use_example(self, index: int) -> None:
        self.input.setText(EXAMPLES[index])
        self.input.setFocus()
        self._run_balance()

    def _clear(self) -> None:
        self.input.clear()
        self.input.setFocus()
        self._reset_empty()

    def _run_balance(self) -> None:
        text = self.input.text().strip()
        if not text:
            self._reset_empty()
            return

        try:
            result = balance_equation(text)
        except LegacyChemistryError as error:
            self._show_error(str(error))
            return
        except Exception as error:  # pragma: no cover - 界面兜底
            print(f"[ChemLab] 未预期错误：{error}", file=sys.stderr)
            self._show_error("解析时出现未预期的问题，请检查方程式写法")
            return

        self._result = result
        self._show_result(result)

    def _reset_empty(self) -> None:
        self._result = None
        self.equation_label.setText(
            render.placeholder_equation_html("输入化学方程式后，配平结果会显示在这里")
        )
        self.coefficient_row.setVisible(False)
        self.copy_button.setEnabled(False)
        self._set_status("等待输入", "idle")
        self._set_meta("结果会随输入实时更新", "idle")
        self._clear_table()
        self.conservation_stack.setCurrentIndex(0)
        self.conservation_stack.setFixedHeight(120)
        self.conservation_hint.setText("两侧原子数一致")
        self.steps_browser.setHtml(render.steps_placeholder_html())
        self._clear_chips()
        self._schedule_page_sync()

    def _show_result(self, result: BalanceResult) -> None:
        self.equation_label.setText(render.equation_html(result))
        self._set_status("已配平", "ok")
        self.copy_button.setEnabled(True)

        if result.equation.is_ionic:
            self._set_meta("原子守恒 · 电荷守恒", "ok")
        else:
            self._set_meta("每种元素的原子数在两侧相同", "ok")

        self._populate_coefficients(result)
        self._populate_table(result)
        self.steps_browser.setHtml(render.steps_html(result))
        self.steps_browser.verticalScrollBar().setValue(0)
        self._schedule_page_sync()

    def _show_error(self, message: str) -> None:
        self._result = None
        self.equation_label.setText(
            render.placeholder_equation_html("这个方程式暂时无法配平", error=True)
        )
        self.coefficient_row.setVisible(False)
        self.copy_button.setEnabled(False)
        self._set_status("无法配平", "error")
        self._set_meta(message, "error")
        self._clear_table()
        self.conservation_stack.setCurrentIndex(0)
        self.conservation_stack.setFixedHeight(120)
        self.conservation_hint.setText("等待有效方程式")
        self.steps_browser.setHtml(render.steps_error_html(message))
        self._clear_chips()
        self._schedule_page_sync()

    # ------------------------------------------------------------ result UI
    def _clear_chips(self) -> None:
        while self.coefficient_layout.count():
            item = self.coefficient_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _clear_table(self) -> None:
        self.conservation_table.clearContents()
        self.conservation_table.setRowCount(0)

    def _populate_coefficients(self, result: BalanceResult) -> None:
        self._clear_chips()
        for coefficient in result.coefficients:
            chip = QLabel(str(coefficient))
            chip.setObjectName("coefficientChip")
            chip.setAlignment(Qt.AlignCenter)
            chip.setToolTip(f"该物质的配平系数为 {coefficient}")
            self.coefficient_layout.addWidget(chip)
        self.coefficient_layout.addStretch(1)
        self.coefficient_row.setVisible(True)

    def _populate_table(self, result: BalanceResult) -> None:
        table = self.conservation_table
        rows = len(result.left_totals) + (1 if result.equation.is_ionic else 0)
        table.clearContents()
        table.setRowCount(rows)

        for row, element in enumerate(result.left_totals):
            left = result.left_totals[element]
            right = result.right_totals[element]
            self._set_table_row(row, element, left, right, left == right)

        if result.equation.is_ionic:
            row = rows - 1
            self._set_table_row(
                row,
                "电荷",
                self._charge_text(result.charge_left),
                self._charge_text(result.charge_right),
                result.charge_left == result.charge_right,
            )

        height = max(120, 31 + rows * 34 + 5)
        table.setFixedHeight(height)
        self.conservation_stack.setFixedHeight(height)
        self.conservation_stack.setCurrentIndex(1)

        element_count = len(result.left_totals)
        if result.equation.is_ionic:
            self.conservation_hint.setText(f"{element_count} 种元素 + 电荷 · 已守恒")
        else:
            self.conservation_hint.setText(f"{element_count} 种元素 · 已守恒")

    def _set_table_row(
        self, row: int, name: str, left, right, balanced: bool
    ) -> None:
        table = self.conservation_table
        values = (name, str(left), str(right))
        for column, value in enumerate(values):
            item = QTableWidgetItem(value)
            item.setFlags(Qt.ItemIsEnabled)
            if column == 0:
                item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                item.setForeground(QColor("#4B5F72"))
                font = QFont("Microsoft YaHei UI")
                font.setPointSize(9)
                font.setWeight(QFont.Medium)
                item.setFont(font)
            else:
                item.setTextAlignment(Qt.AlignCenter)
                item.setForeground(QColor("#0F8A78" if balanced else "#C2414B"))
                font = QFont("Microsoft YaHei UI")
                font.setPointSize(9)
                font.setWeight(QFont.DemiBold)
                item.setFont(font)
            table.setItem(row, column, item)

    @staticmethod
    def _charge_text(value: int) -> str:
        if value > 0:
            return f"+{value}"
        return str(value).replace("-", "−")

    def _set_status(self, text: str, state: str) -> None:
        self.status_pill.setText(text)
        self._set_dynamic_state(self.status_pill, state)

    def _set_meta(self, text: str, state: str) -> None:
        self.result_meta.setText(text)
        self._set_dynamic_state(self.result_meta, state)

    @staticmethod
    def _set_dynamic_state(widget: QWidget, state: str) -> None:
        widget.setProperty("state", state)
        style = widget.style()
        style.unpolish(widget)
        style.polish(widget)
        widget.update()

    # ------------------------------------------------------------- actions
    def _copy_result(self) -> None:
        if self._result is None:
            return
        QGuiApplication.clipboard().setText(self._result.plain_equation)
        self.copy_button.setText("已复制")
        self._copy_timer.start(1500)
        self._show_toast("配平结果已复制到剪贴板")

    def _toggle_favorite(self) -> None:
        self._favorite = not self._favorite
        self.favorite_button.setText("★  已收藏" if self._favorite else "☆  收藏")
        self.favorite_button.setProperty("active", self._favorite)
        self._set_dynamic_state(self.favorite_button, "idle")
        self._show_toast("已收藏这个工具" if self._favorite else "已取消收藏")

    def _open_periodic_table(self) -> None:
        if self._periodic_window is None:
            from .periodic_window import PeriodicTableWindow

            self._periodic_window = PeriodicTableWindow(self)
        self._periodic_window.show()
        self._periodic_window.raise_()
        self._periodic_window.activateWindow()

    # --------------------------------------------------------------- toast
    def _show_toast(self, message: str) -> None:
        self._toast.setText(message)
        self._toast.setMinimumWidth(0)
        self._toast.setMaximumWidth(16777215)
        self._toast.adjustSize()
        if self._toast.width() > self.width() - 80:
            self._toast.setFixedWidth(self.width() - 80)
        self._toast_effect.setOpacity(0.0)
        self._toast.show()
        self._toast.raise_()
        self._position_toast()

        if self._toast_animation is not None:
            self._toast_animation.stop()
        self._toast_animation = QPropertyAnimation(self._toast_effect, b"opacity", self)
        self._toast_animation.setDuration(160)
        self._toast_animation.setStartValue(0.0)
        self._toast_animation.setEndValue(1.0)
        self._toast_animation.setEasingCurve(QEasingCurve.OutCubic)
        self._toast_animation.start()
        self._toast_timer.start(1500)

    def _hide_toast(self) -> None:
        if self._toast_animation is not None:
            self._toast_animation.stop()
        self._toast_animation = QPropertyAnimation(self._toast_effect, b"opacity", self)
        self._toast_animation.setDuration(220)
        self._toast_animation.setStartValue(1.0)
        self._toast_animation.setEndValue(0.0)
        self._toast_animation.setEasingCurve(QEasingCurve.InCubic)
        self._toast_animation.finished.connect(self._toast.hide)
        self._toast_animation.start()

    def _position_toast(self) -> None:
        x = (self.width() - self._toast.width()) // 2
        y = self.height() - self._toast.height() - 34
        self._toast.move(max(20, x), max(20, y))

    # --------------------------------------------------------------- layout
    def _schedule_page_sync(self) -> None:
        if hasattr(self, "_page_sync_timer"):
            self._page_sync_timer.start(0)

    def _sync_page_height(self) -> None:
        if self.page is None or self.page.layout() is None:
            return

        for column in (self.left_column, self.center_column):
            if column.layout() is not None:
                column.layout().activate()
                required = column.layout().minimumSize().height()
                if column.minimumHeight() != required:
                    column.setMinimumHeight(required)

        if self.body.layout() is not None:
            self.body.layout().activate()
            body_required = self.body.layout().minimumSize().height()
            if self.body.minimumHeight() != body_required:
                self.body.setMinimumHeight(body_required)

        self.page.layout().activate()
        required = self.page.layout().minimumSize().height()
        if self.page.minimumHeight() != required:
            self.page.setMinimumHeight(required)

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt API
        super().resizeEvent(event)
        if hasattr(self, "_toast") and self._toast.isVisible():
            self._position_toast()
        if hasattr(self, "_page_sync_timer") and self.centralWidget() is not None:
            self._schedule_page_sync()

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt API
        self._debounce.stop()
        self._toast_timer.stop()
        self._copy_timer.stop()
        if self._periodic_window is not None:
            self._periodic_window.close()
        super().closeEvent(event)


def create_application(argv: list[str] | None = None) -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(argv or sys.argv)
    app.setApplicationName("ChemLab")
    app.setOrganizationName("ChemLab")
    app.setApplicationDisplayName("ChemLab · 化学方程式配平器")
    app.setFont(QFont("Microsoft YaHei UI", 10))
    return app
