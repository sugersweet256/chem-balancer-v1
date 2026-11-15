"""元素周期表窗口。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QGuiApplication, QIcon, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .periodic_data import (
    BY_NUMBER,
    CATEGORY_COLORS,
    CATEGORY_LABELS,
    ELEMENTS,
    Element,
    search_elements,
)

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[1]
ASSETS = PROJECT_ROOT / "assets" / "icons"

CATEGORY_DESCRIPTIONS = {
    "alkali": "最外层通常有 1 个电子，化学性质活泼，容易失去电子形成 +1 价离子。",
    "alkaline": "最外层通常有 2 个电子，活泼程度略低于碱金属，常见 +2 价。",
    "transition": "包含 d 区金属，常呈现多种化合价，许多是重要的催化剂和结构材料。",
    "post": "位于过渡金属右侧的主族金属，熔点通常较低，常用于合金和镀层。",
    "metalloid": "性质介于金属与非金属之间，常见于半导体和合金材料。",
    "nonmetal": "电负性较高，倾向于获得或共用电子，是生命化学和有机化学的主角。",
    "halogen": "第 17 族元素，最外层有 7 个电子，容易获得 1 个电子形成 −1 价离子。",
    "noble": "最外层电子构型稳定，化学性质非常不活泼，通常以单原子气体存在。",
    "lanthanide": "镧系元素，包含 4f 轨道，常用于强磁体、荧光材料和特种合金。",
    "actinide": "锕系元素，多数具有放射性，在核能与核化学中非常重要。",
    "unknown": "超重元素，性质多由理论预测，实验数据仍在持续研究中。",
}


class ElementTile(QFrame):
    clicked = Signal(int)

    def __init__(self, element: Element, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.element = element
        self.setObjectName("elementTile")
        self.setProperty("category", element.category)
        self.setProperty("selected", False)
        self.setProperty("match", True)
        self.setFixedSize(50, 54)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover, True)
        self.setToolTip(
            f"{element.number}  {element.symbol}  {element.display_name}\n"
            f"{CATEGORY_LABELS.get(element.category, element.category)} · "
            f"相对原子质量 {element.mass_text}"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)

        self.number_label = QLabel(str(element.number), self)
        self.number_label.setObjectName("elementNumber")
        self.number_label.setAlignment(Qt.AlignCenter)

        self.symbol_label = QLabel(element.symbol, self)
        self.symbol_label.setObjectName("elementSymbol")
        self.symbol_label.setAlignment(Qt.AlignCenter)

        self.name_label = QLabel(element.name_zh or "", self)
        self.name_label.setObjectName("elementName")
        self.name_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.number_label)
        layout.addWidget(self.symbol_label, 1)
        layout.addWidget(self.name_label)

        for label in (self.number_label, self.symbol_label, self.name_label):
            label.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    def set_selected(self, selected: bool) -> None:
        self.setProperty("selected", selected)
        self._repolish(self)

    def set_match(self, matched: bool) -> None:
        self.setProperty("match", matched)
        self._repolish(self)
        for label in (self.number_label, self.symbol_label, self.name_label):
            self._repolish(label)

    @staticmethod
    def _repolish(widget: QWidget) -> None:
        style = widget.style()
        style.unpolish(widget)
        style.polish(widget)
        widget.update()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802 - Qt API
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.element.number)
        super().mouseReleaseEvent(event)


class PeriodicTableWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("ChemLab · 元素周期表")
        self.setWindowIcon(QIcon(str(ASSETS / "periodic.svg")))
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setMinimumSize(1280, 760)
        self._tiles: dict[int, ElementTile] = {}
        self._selected: Element | None = None
        self._build_ui()
        self._apply_styles()
        self._build_table()
        self.select_element(26)
        self._place_on_screen()

    # ---------------------------------------------------------------- build
    def _build_ui(self) -> None:
        root = QWidget(self)
        root.setObjectName("periodicRoot")
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        top_bar = QFrame(root)
        top_bar.setObjectName("topBar")
        top_bar.setFixedHeight(74)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(40, 0, 40, 0)
        top_layout.setSpacing(10)

        self.back_button = QPushButton("←  返回配平器", top_bar)
        self.back_button.setObjectName("backButton")
        self.back_button.setProperty("ghost", True)
        self.back_button.setCursor(Qt.PointingHandCursor)
        self.back_button.clicked.connect(self._go_back)
        top_layout.addWidget(self.back_button)
        top_layout.addSpacing(10)

        logo = QLabel(top_bar)
        logo.setFixedSize(36, 36)
        logo.setPixmap(
            QPixmap(str(ASSETS / "logo.svg")).scaled(
                36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        )
        top_layout.addWidget(logo)

        brand_box = QVBoxLayout()
        brand_box.setSpacing(0)
        brand = QLabel("ChemLab", top_bar)
        brand.setObjectName("brandName")
        brand_sub = QLabel("元素周期表", top_bar)
        brand_sub.setObjectName("brandSub")
        brand_box.addWidget(brand)
        brand_box.addWidget(brand_sub)
        top_layout.addLayout(brand_box)
        top_layout.addStretch(1)

        self.search = QLineEdit(top_bar)
        self.search.setObjectName("elementSearch")
        self.search.setFixedSize(300, 40)
        self.search.setPlaceholderText("搜索元素、符号或原子序数")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._on_search)
        self.search.returnPressed.connect(self._select_first_match)
        top_layout.addWidget(self.search)

        count = QLabel("118 种元素", top_bar)
        count.setObjectName("periodicCount")
        count.setAlignment(Qt.AlignCenter)
        count.setFixedHeight(28)
        count.setMinimumWidth(84)
        top_layout.addWidget(count)
        root_layout.addWidget(top_bar)

        scroll = QScrollArea(root)
        scroll.setObjectName("periodicScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        root_layout.addWidget(scroll, 1)

        page = QWidget(scroll)
        page.setObjectName("periodicPage")
        scroll.setWidget(page)
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(40, 22, 40, 24)
        page_layout.setSpacing(18)

        page_header = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(3)
        title = QLabel("元素周期表", page)
        title.setObjectName("periodicTitle")
        subtitle = QLabel(
            "118 种元素的标准长式排列。点击任意元素，查看原子量、周期、族和分类。",
            page,
        )
        subtitle.setObjectName("periodicSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        page_header.addLayout(title_box)
        page_header.addStretch(1)
        tag = QLabel("元素数据", page)
        tag.setObjectName("periodicTag")
        tag.setAlignment(Qt.AlignCenter)
        page_header.addWidget(tag)
        page_layout.addLayout(page_header)

        body = QHBoxLayout()
        body.setSpacing(18)
        page_layout.addLayout(body, 1)

        table_card = QFrame(page)
        table_card.setProperty("card", True)
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(18, 16, 18, 16)
        table_layout.setSpacing(9)

        table_header = QHBoxLayout()
        table_title = QLabel("标准长式周期表", table_card)
        table_title.setObjectName("tableTitle")
        table_header.addWidget(table_title)
        self.search_hint = QLabel("点击元素查看详情", table_card)
        self.search_hint.setObjectName("tableHint")
        table_header.addWidget(self.search_hint)
        table_header.addStretch(1)
        table_meta = QLabel("按 IUPAC 位置排列 · 镧系、锕系单独列出", table_card)
        table_meta.setObjectName("tableMeta")
        table_header.addWidget(table_meta)
        table_layout.addLayout(table_header)

        self.legend = QWidget(table_card)
        self.legend.setObjectName("legend")
        self.legend_layout = QGridLayout(self.legend)
        self.legend_layout.setContentsMargins(0, 2, 0, 2)
        self.legend_layout.setHorizontalSpacing(10)
        self.legend_layout.setVerticalSpacing(4)
        table_layout.addWidget(self.legend)

        self.element_scroll = QScrollArea(table_card)
        self.element_scroll.setObjectName("elementScroll")
        self.element_scroll.setFrameShape(QFrame.NoFrame)
        self.element_scroll.setWidgetResizable(False)
        self.element_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.element_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.element_scroll.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.element_scroll.setMinimumHeight(570)
        self.element_scroll.setMaximumHeight(570)
        table_layout.addWidget(self.element_scroll)

        note = QLabel(
            "原子量采用常见教学近似值；放射性元素采用半衰期最长同位素的质量数。",
            table_card,
        )
        note.setObjectName("tableNote")
        note.setWordWrap(True)
        table_layout.addWidget(note)
        body.addWidget(table_card, 1)

        detail_card = QFrame(page)
        detail_card.setProperty("card", True)
        detail_card.setFixedWidth(300)
        detail_layout = QVBoxLayout(detail_card)
        detail_layout.setContentsMargins(22, 20, 22, 18)
        detail_layout.setSpacing(0)

        detail_title = QLabel("元素详情", detail_card)
        detail_title.setObjectName("detailTitle")
        detail_layout.addWidget(detail_title)
        detail_layout.addSpacing(18)

        detail_top = QHBoxLayout()
        self.detail_symbol = QLabel("Fe", detail_card)
        self.detail_symbol.setObjectName("detailSymbol")
        self.detail_symbol.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        detail_top.addWidget(self.detail_symbol)
        detail_top.addStretch(1)
        self.detail_number = QLabel("026", detail_card)
        self.detail_number.setObjectName("detailNumber")
        self.detail_number.setAlignment(Qt.AlignRight | Qt.AlignTop)
        detail_top.addWidget(self.detail_number)
        detail_layout.addLayout(detail_top)

        self.detail_name = QLabel("铁", detail_card)
        self.detail_name.setObjectName("detailName")
        detail_layout.addWidget(self.detail_name)
        self.detail_name_en = QLabel("Iron", detail_card)
        self.detail_name_en.setObjectName("detailNameEn")
        detail_layout.addWidget(self.detail_name_en)
        detail_layout.addSpacing(12)

        self.detail_category = QLabel("过渡金属", detail_card)
        self.detail_category.setObjectName("detailCategory")
        self.detail_category.setAlignment(Qt.AlignCenter)
        self.detail_category.setFixedHeight(28)
        category_row = QHBoxLayout()
        category_row.setContentsMargins(0, 0, 0, 0)
        category_row.addWidget(self.detail_category)
        category_row.addStretch(1)
        detail_layout.addLayout(category_row)
        detail_layout.addSpacing(18)

        divider = QFrame(detail_card)
        divider.setObjectName("detailDivider")
        divider.setFixedHeight(1)
        detail_layout.addWidget(divider)
        detail_layout.addSpacing(14)

        info = QGridLayout()
        info.setHorizontalSpacing(10)
        info.setVerticalSpacing(10)
        self.detail_mass = QLabel("55.845", detail_card)
        self.detail_period = QLabel("第 4 周期", detail_card)
        self.detail_group = QLabel("第 8 族", detail_card)
        self.detail_block = QLabel("d 区", detail_card)
        self.detail_protons = QLabel("26", detail_card)
        self.detail_electrons = QLabel("26", detail_card)
        rows = [
            ("相对原子质量", self.detail_mass),
            ("周期", self.detail_period),
            ("族", self.detail_group),
            ("分区", self.detail_block),
            ("质子数", self.detail_protons),
            ("中性原子电子数", self.detail_electrons),
        ]
        for row, (key, value) in enumerate(rows):
            key_label = QLabel(key, detail_card)
            key_label.setObjectName("detailKey")
            value.setObjectName("detailValue")
            value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            info.addWidget(key_label, row, 0)
            info.addWidget(value, row, 1)
        info.setColumnStretch(1, 1)
        detail_layout.addLayout(info)
        detail_layout.addSpacing(18)

        divider2 = QFrame(detail_card)
        divider2.setObjectName("detailDivider")
        divider2.setFixedHeight(1)
        detail_layout.addWidget(divider2)
        detail_layout.addSpacing(14)

        self.detail_description = QLabel("", detail_card)
        self.detail_description.setObjectName("detailDescription")
        self.detail_description.setWordWrap(True)
        self.detail_description.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        detail_layout.addWidget(self.detail_description)
        detail_layout.addStretch(1)

        hint = QLabel("点击周期表中的其他元素切换详情", detail_card)
        hint.setObjectName("detailHint")
        hint.setWordWrap(True)
        detail_layout.addWidget(hint)
        body.addWidget(detail_card)

        footer = QHBoxLayout()
        footer_left = QLabel("ChemLab · 元素周期表", page)
        footer_left.setObjectName("periodicFooter")
        footer_right = QLabel("元素数据仅用于学习与化学计算参考", page)
        footer_right.setObjectName("periodicFooter")
        footer.addWidget(footer_left)
        footer.addStretch(1)
        footer.addWidget(footer_right)
        page_layout.addLayout(footer)

        self._shortcut_escape = QShortcut(QKeySequence("Esc"), self)
        self._shortcut_escape.activated.connect(self._go_back)

    def _apply_styles(self) -> None:
        base = (BASE_DIR / "styles.qss").read_text(encoding="utf-8")
        extra = (BASE_DIR / "periodic.qss").read_text(encoding="utf-8")
        self.setStyleSheet(base + "\n" + extra)

    def _build_table(self) -> None:
        grid_widget = QWidget(self.element_scroll)
        grid_widget.setObjectName("elementGrid")
        grid = QGridLayout(grid_widget)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(3)
        grid.setVerticalSpacing(3)
        grid.setColumnMinimumWidth(0, 28)
        grid.setRowMinimumHeight(0, 20)
        for column in range(1, 19):
            grid.setColumnMinimumWidth(column, 50)
        for row in range(1, 8):
            grid.setRowMinimumHeight(row, 54)

        for column in range(1, 19):
            label = QLabel(str(column), grid_widget)
            label.setObjectName("groupHeader")
            label.setAlignment(Qt.AlignCenter)
            grid.addWidget(label, 0, column)

        for period in range(1, 8):
            label = QLabel(str(period), grid_widget)
            label.setObjectName("periodLabel")
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            grid.addWidget(label, period, 0)

        for element in ELEMENTS:
            if element.group:
                row, column = element.period, element.group
            elif element.category == "lanthanide":
                row, column = 9, 3 + (element.number - 57)
            else:
                row, column = 10, 3 + (element.number - 89)
            tile = ElementTile(element, grid_widget)
            tile.clicked.connect(self.select_element)
            self._tiles[element.number] = tile
            grid.addWidget(tile, row, column)

        for period, text in ((6, "57–71"), (7, "89–103")):
            placeholder = QLabel(text, grid_widget)
            placeholder.setObjectName("fPlaceholder")
            placeholder.setFixedSize(50, 54)
            placeholder.setAlignment(Qt.AlignCenter)
            grid.addWidget(placeholder, period, 3)

        for row, text in ((9, "镧系"), (10, "锕系")):
            label = QLabel(text, grid_widget)
            label.setObjectName("fBlockLabel")
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            grid.addWidget(label, row, 0)

        for row in (9, 10):
            grid.setRowMinimumHeight(row, 54)
        grid.setRowMinimumHeight(8, 10)
        grid.activate()
        grid_widget.adjustSize()
        self.element_scroll.setWidget(grid_widget)

        for index, category in enumerate(CATEGORY_LABELS):
            bg, border, fg = CATEGORY_COLORS[category]
            dot = QLabel(self.legend)
            dot.setFixedSize(9, 9)
            dot.setStyleSheet(
                f"background:{bg}; border:1px solid {border}; border-radius:4px;"
            )
            text = QLabel(CATEGORY_LABELS[category], self.legend)
            text.setObjectName("legendText")
            row, column = divmod(index, 6)
            self.legend_layout.addWidget(dot, row, column * 2)
            self.legend_layout.addWidget(text, row, column * 2 + 1)

    def _place_on_screen(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            self.resize(1480, 900)
            return
        available = screen.availableGeometry()
        width = min(1480, max(1280, available.width() - 60))
        height = min(900, max(760, available.height() - 50))
        self.resize(width, height)
        frame = self.frameGeometry()
        frame.moveCenter(available.center())
        self.move(frame.topLeft())

    # --------------------------------------------------------------- detail
    def select_element(self, number: int, ensure_visible: bool = True) -> None:
        element = BY_NUMBER.get(number)
        if element is None:
            return
        if self._selected is not None:
            old_tile = self._tiles.get(self._selected.number)
            if old_tile is not None:
                old_tile.set_selected(False)
        self._selected = element
        tile = self._tiles.get(number)
        if tile is not None:
            tile.set_selected(True)
            if ensure_visible:
                self.element_scroll.ensureWidgetVisible(tile, 10, 10)

        bg, border, fg = CATEGORY_COLORS[element.category]
        self.detail_symbol.setText(element.symbol)
        self.detail_symbol.setStyleSheet(f"color:{fg};")
        self.detail_number.setText(f"{element.number:03d}")
        self.detail_name.setText(element.name_zh or element.symbol)
        self.detail_name_en.setText(element.name_en)
        self.detail_category.setText(
            CATEGORY_LABELS.get(element.category, element.category)
        )
        self.detail_category.setStyleSheet(
            f"background:{bg}; color:{fg}; border:1px solid {border};"
            "border-radius:9px; padding:4px 9px; font-size:10px; font-weight:600;"
        )
        self.detail_mass.setText(element.mass_text)
        self.detail_period.setText(f"第 {element.period} 周期")
        if element.category in ("lanthanide", "actinide"):
            self.detail_group.setText(CATEGORY_LABELS[element.category])
        else:
            self.detail_group.setText(f"第 {element.group} 族")
        self.detail_block.setText(
            "f 区"
            if element.category in ("lanthanide", "actinide")
            else "s 区"
            if element.symbol == "He" or element.group in (1, 2)
            else "d 区"
            if 3 <= element.group <= 12
            else "p 区"
        )
        self.detail_protons.setText(str(element.number))
        self.detail_electrons.setText(str(element.number))
        self.detail_description.setText(CATEGORY_DESCRIPTIONS.get(element.category, ""))

    # --------------------------------------------------------------- search
    def _on_search(self, text: str) -> None:
        query = text.strip()
        if not query:
            for tile in self._tiles.values():
                tile.set_match(True)
            self.search_hint.setText("点击元素查看详情")
            return

        results = search_elements(query)
        matched_ids = {element.number for element in results}
        for number, tile in self._tiles.items():
            tile.set_match(number in matched_ids)

        if results:
            self.search_hint.setText(f"找到 {len(results)} 个匹配元素")
            self.select_element(results[0].number)
        else:
            self.search_hint.setText("没有匹配的元素")

    def _select_first_match(self) -> None:
        results = search_elements(self.search.text())
        if results:
            self.select_element(results[0].number)

    # ---------------------------------------------------------------- window
    def _go_back(self) -> None:
        parent = self.parent()
        self.close()
        if parent is not None and isinstance(parent, QWidget):
            parent.raise_()
            parent.activateWindow()

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt API
        if self.parent() is not None and hasattr(self.parent(), "_periodic_window"):
            self.parent()._periodic_window = None
        super().closeEvent(event)
