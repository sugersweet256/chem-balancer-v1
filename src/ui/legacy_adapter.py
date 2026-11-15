"""UI 适配层：只调用现有的 parser.py / balancer.py。

这个文件不改动核心代码，只负责：
1. 把界面输入整理成当前 parser 能接受的写法；
2. 调用现有 ``parse_equation`` 和 ``balancer``；
3. 把 balancer 返回的方程式字符串整理成界面需要的结构。
"""

from __future__ import annotations

import re
import string
from dataclasses import dataclass

from ..balancer import balancer
from ..parser import parse_equation


class LegacyChemistryError(ValueError):
    """可直接展示给用户的输入/配平错误。"""


@dataclass
class UISpecies:
    formula: str
    counts: dict[str, int]
    charge: int = 0
    raw: str = ""

    @property
    def has_charge(self) -> bool:
        return self.charge != 0


@dataclass
class UIParsedEquation:
    reactants: list[UISpecies]
    products: list[UISpecies]
    raw: str

    @property
    def species(self) -> list[UISpecies]:
        return [*self.reactants, *self.products]

    @property
    def elements(self) -> list[str]:
        elements: list[str] = []
        for item in self.species:
            for element in item.counts:
                if element not in elements:
                    elements.append(element)
        return elements

    @property
    def is_ionic(self) -> bool:
        return any(item.charge for item in self.species)


@dataclass
class UIBalanceResult:
    equation: UIParsedEquation
    coefficients: list[int]
    left_totals: dict[str, int]
    right_totals: dict[str, int]
    charge_left: int
    charge_right: int
    labels: list[str]
    element_equations: list[tuple[str, str]]
    nullity: int = 1
    note: str = ""

    @property
    def species(self) -> list[UISpecies]:
        return self.equation.species

    @property
    def reactant_count(self) -> int:
        return len(self.equation.reactants)

    @property
    def is_balanced(self) -> bool:
        return all(
            self.left_totals[element] == self.right_totals[element]
            for element in self.left_totals
        ) and self.charge_left == self.charge_right

    @property
    def plain_equation(self) -> str:
        left = " + ".join(
            _species_plain(item, coefficient)
            for item, coefficient in zip(
                self.equation.reactants, self.coefficients[: self.reactant_count]
            )
        )
        right = " + ".join(
            _species_plain(item, coefficient)
            for item, coefficient in zip(
                self.equation.products, self.coefficients[self.reactant_count :]
            )
        )
        return f"{left} → {right}"

    @property
    def solution_summary(self) -> str:
        return "，".join(
            f"{label} = {coefficient}"
            for label, coefficient in zip(self.labels, self.coefficients)
        )


_SUB_TRANS = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
_SUP_TRANS = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")
_ARROW_RE = re.compile(r"\s*(?:->|=>|→|⟶|⇌|＝|=)\s*")
_STATE_RE = re.compile(r"\((?:s|l|g|aq|aq\.)\)", re.IGNORECASE)


def _normalize_input(text: str) -> str:
    text = text.strip()
    if not text:
        raise LegacyChemistryError("请先输入化学方程式")

    text = text.replace("＋", "+").replace("－", "-").replace("−", "-")
    text = text.replace("\u00a0", " ").replace("\u3000", " ")
    text = text.replace("•", "·").replace("⋅", "·")

    # Unicode 上标电荷 -> ^ 写法，再处理下标。
    text = re.sub(
        r"([⁰¹²³⁴⁵⁶⁷⁸⁹]*)([⁺⁻])",
        lambda m: "^"
        + m.group(1).translate(_SUP_TRANS)
        + ("+" if m.group(2) == "⁺" else "-"),
        text,
    )
    text = text.translate(_SUB_TRANS).translate(_SUP_TRANS)

    # 状态符号不属于化学式；之后再把结晶水点号统一成原核心认识的 ·。
    text = _STATE_RE.sub("", text)
    text = text.replace("*", "·").replace(".", "·")

    if not _ARROW_RE.search(text):
        raise LegacyChemistryError("请用 →、-> 或 = 分隔方程式两侧")
    text = _ARROW_RE.sub(" -> ", text)
    if text.count("->") != 1:
        raise LegacyChemistryError("方程式只能有一个箭头")

    left, right = text.split("->")
    if not left.strip() or not right.strip():
        raise LegacyChemistryError("方程式有一侧是空的")

    # 粘贴已配平的方程式时，忽略物质前面的系数，重新配平。
    text = re.sub(r"(^|\+|->)\s*\d+(?=[A-Z\[\(])", r"\1", text)
    return text.strip()


def _split_charge(raw: str, counts: dict) -> tuple[str, dict[str, int], int]:
    charge = int(counts.get("charge", 0))
    base = raw.strip()

    match = re.match(r"^(.*?)\^(\d*)([+-])$", base)
    if match:
        base = match.group(1)
        charge = int(match.group(2) or 1)
        if match.group(3) == "-":
            charge = -charge

    atoms = {
        element: int(amount)
        for element, amount in counts.items()
        if element != "charge" and amount
    }
    if not atoms:
        raise LegacyChemistryError(f"“{raw}”不是有效的化学式")
    return base, atoms, charge


def _extract_coefficients(result: str, formulas: list[str], reactant_count: int) -> list[int]:
    """从 result_print 生成的字符串中还原每个物质的系数。"""

    if not result:
        raise LegacyChemistryError("配平结果为空")

    # 当前 result_print 在 + 两侧会加空格，物质式内部不会有空格。
    result = result.replace(" ", "")
    coefficients: list[int] = []
    position = 0
    total = len(formulas)

    for index, formula in enumerate(formulas):
        prefix = re.match(r"(\d+)", result[position:])
        if prefix and not result.startswith(formula, position):
            coefficient = int(prefix.group(1))
            position += len(prefix.group(1))
        else:
            coefficient = 1

        if not result.startswith(formula, position):
            raise LegacyChemistryError("配平结果解析失败，请检查化学式写法")
        position += len(formula)
        coefficients.append(coefficient)

        if index < total - 1:
            separator = "->" if index == reactant_count - 1 else "+"
            if not result.startswith(separator, position):
                raise LegacyChemistryError("配平结果格式异常")
            position += len(separator)

    if position != len(result):
        raise LegacyChemistryError("配平结果格式异常")
    return coefficients


def _term(amount: int, label: str) -> str:
    if amount == 0:
        return ""
    magnitude = abs(amount)
    text = label if magnitude == 1 else f"{magnitude}{label}"
    return f"-{text}" if amount < 0 else text


def _join_terms(terms: list[str]) -> str:
    terms = [term for term in terms if term]
    if not terms:
        return "0"
    text = terms[0].replace("-", "−", 1) if terms[0].startswith("-") else terms[0]
    for term in terms[1:]:
        if term.startswith("-"):
            text += " − " + term[1:]
        else:
            text += " + " + term
    return text


def _labels(count: int) -> list[str]:
    labels = list(string.ascii_lowercase)
    if count <= len(labels):
        return labels[:count]
    return [f"x{i + 1}" for i in range(count)]


def _build_element_equations(
    equation: UIParsedEquation, labels: list[str]
) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    left_count = len(equation.reactants)
    species = equation.species

    for element in equation.elements:
        left_terms = [
            _term(item.counts.get(element, 0), labels[index])
            for index, item in enumerate(species[:left_count])
        ]
        right_terms = [
            _term(item.counts.get(element, 0), labels[index + left_count])
            for index, item in enumerate(species[left_count:])
        ]
        rows.append((element, f"{_join_terms(left_terms)} = {_join_terms(right_terms)}"))

    if equation.is_ionic:
        left_terms = [
            _term(item.charge, labels[index])
            for index, item in enumerate(species[:left_count])
        ]
        right_terms = [
            _term(item.charge, labels[index + left_count])
            for index, item in enumerate(species[left_count:])
        ]
        rows.append(("电荷", f"{_join_terms(left_terms)} = {_join_terms(right_terms)}"))
    return rows


def _species_plain(species: UISpecies, coefficient: int = 1) -> str:
    prefix = "" if coefficient == 1 else str(coefficient)
    formula = species.formula
    if species.charge:
        magnitude = abs(species.charge)
        formula += "^" + ("" if magnitude == 1 else str(magnitude))
        formula += "+" if species.charge > 0 else "-"
    return prefix + formula


def balance_equation(text: str) -> UIBalanceResult:
    normalized = _normalize_input(text)

    try:
        reactants, products, (left_strings, right_strings) = parse_equation(normalized)
        result_string = balancer(reactants, products, (left_strings, right_strings))
    except LegacyChemistryError:
        raise
    except ValueError as error:
        raise LegacyChemistryError(str(error)) from error
    except Exception as error:  # pragma: no cover - 原核心的兜底
        raise LegacyChemistryError(f"解析方程式时出错：{error}") from error

    all_strings = [*left_strings, *right_strings]
    if not all_strings:
        raise LegacyChemistryError("方程式里没有识别到物质")
    if any(not formula for formula in all_strings):
        raise LegacyChemistryError("存在空的物质，请检查“+”两侧")

    coefficients = _extract_coefficients(
        result_string, all_strings, len(reactants)
    )
    if len(coefficients) != len(all_strings):
        raise LegacyChemistryError("配平系数数量与物质数量不一致")

    left_species = [
        UISpecies(*_split_charge(raw, counts), raw=raw)
        for raw, counts in zip(left_strings, reactants)
    ]
    right_species = [
        UISpecies(*_split_charge(raw, counts), raw=raw)
        for raw, counts in zip(right_strings, products)
    ]
    equation = UIParsedEquation(
        reactants=left_species,
        products=right_species,
        raw=normalized,
    )

    left_count = len(left_species)
    left_totals = {element: 0 for element in equation.elements}
    right_totals = {element: 0 for element in equation.elements}
    for item, coefficient in zip(left_species, coefficients[:left_count]):
        for element, amount in item.counts.items():
            left_totals[element] += amount * coefficient
    for item, coefficient in zip(right_species, coefficients[left_count:]):
        for element, amount in item.counts.items():
            right_totals[element] += amount * coefficient

    charge_left = sum(
        item.charge * coefficient
        for item, coefficient in zip(left_species, coefficients[:left_count])
    )
    charge_right = sum(
        item.charge * coefficient
        for item, coefficient in zip(right_species, coefficients[left_count:])
    )

    labels = _labels(len(equation.species))
    result = UIBalanceResult(
        equation=equation,
        coefficients=coefficients,
        left_totals=left_totals,
        right_totals=right_totals,
        charge_left=charge_left,
        charge_right=charge_right,
        labels=labels,
        element_equations=_build_element_equations(equation, labels),
    )
    if not result.is_balanced:
        raise LegacyChemistryError("配平后两侧原子或电荷不守恒，请检查方程式")
    return result


__all__ = [
    "LegacyChemistryError",
    "UIBalanceResult",
    "UIParsedEquation",
    "UISpecies",
    "balance_equation",
]
