"""把配平结果渲染成 Qt 富文本。"""

from __future__ import annotations

from html import escape
import re

from .legacy_adapter import UIBalanceResult as BalanceResult
from .legacy_adapter import UISpecies as Species


def _charge_html(charge: int) -> str:
    if not charge:
        return ""
    sign = "+" if charge > 0 else "−"
    magnitude = abs(charge)
    text = sign if magnitude == 1 else f"{magnitude}{sign}"
    return f'<sup style="font-size:58%; color:#0F766E;">{text}</sup>'


def _core_formula_html(formula: str) -> str:
    output: list[str] = []
    index = 0
    while index < len(formula):
        char = formula[index]
        if char.isdigit():
            end = index
            while end < len(formula) and formula[end].isdigit():
                end += 1
            output.append(f"<sub>{formula[index:end]}</sub>")
            index = end
            continue
        if char in "·*":
            output.append('<span style="color:#7D8D9B;">·</span>')
            index += 1
            continue
        output.append(escape(char))
        index += 1
    return "".join(output)


def formula_html(formula: str) -> str:
    segments = re.split(r"([·*.])", formula)
    output: list[str] = []
    for index, segment in enumerate(segments):
        if segment in ("·", "*", "."):
            output.append('<span style="color:#7D8D9B;">·</span>')
            continue
        if index > 0:
            match = re.match(r"^(\d+)(.+)$", segment)
            if match:
                output.append(match.group(1))
                output.append(_core_formula_html(match.group(2)))
                continue
        output.append(_core_formula_html(segment))
    return "".join(output)


def species_html(species: Species, coefficient: int = 1) -> str:
    prefix = ""
    if coefficient != 1:
        prefix = f'<span style="color:#41566A;">{coefficient}</span>'
    return prefix + formula_html(species.formula) + _charge_html(species.charge)


def equation_html(result: BalanceResult, font_size: int | None = None) -> str:
    if font_size is None:
        length = len(result.plain_equation)
        if length <= 28:
            font_size = 31
        elif length <= 42:
            font_size = 27
        elif length <= 62:
            font_size = 23
        else:
            font_size = 20

    left_count = result.reactant_count
    left = (
        ' <span style="color:#9AA8B6; font-size:75%;">+</span> '.join(
            species_html(item, coefficient)
            for item, coefficient in zip(
                result.equation.reactants, result.coefficients[:left_count]
            )
        )
    )
    right = (
        ' <span style="color:#9AA8B6; font-size:75%;">+</span> '.join(
            species_html(item, coefficient)
            for item, coefficient in zip(
                result.equation.products, result.coefficients[left_count:]
            )
        )
    )
    arrow = (
        '<span style="color:#0F9D8A; font-size:85%; font-weight:500;">'
        "&nbsp;⟶&nbsp;</span>"
    )
    return (
        f'<div style="text-align:center; color:#0B1F33; '
        f"font-family:'Cambria Math','Times New Roman',serif; "
        f'font-size:{font_size}px; font-weight:600;">{left}{arrow}{right}</div>'
    )


def placeholder_equation_html(text: str, error: bool = False) -> str:
    color = "#C2414B" if error else "#93A2B0"
    return (
        f'<div style="text-align:center; color:{color}; '
        f"font-family:'Microsoft YaHei UI'; font-size:11px; "
        f'font-weight:400;">{escape(text)}</div>'
    )


def _unknown_species(label: str, species: Species) -> str:
    return (
        f'<span style="font-style:italic; color:#0F8A78; font-weight:600;">'
        f"{label}</span>&nbsp;{formula_html(species.formula)}"
        f"{_charge_html(species.charge)}"
    )


def steps_html(result: BalanceResult) -> str:
    labels = result.labels
    left_count = result.reactant_count

    unknown_left = (
        ' <span style="color:#9AA8B6;">+</span> '.join(
            _unknown_species(label, species)
            for label, species in zip(labels[:left_count], result.equation.reactants)
        )
    )
    unknown_right = (
        ' <span style="color:#9AA8B6;">+</span> '.join(
            _unknown_species(label, species)
            for label, species in zip(
                labels[left_count:], result.equation.products
            )
        )
    )

    equations = "".join(
        '<div style="margin:3px 0 3px 2px;">'
        f'<span style="color:#7D8D9B; font-family:\'Microsoft YaHei UI\'; '
        f'font-size:10px;">{escape(name)}：</span>'
        f'<span style="font-family:\'Cambria Math\',serif; color:#2D4257; '
        f'font-size:13px;">{escape(equation)}</span>'
        "</div>"
        for name, equation in result.element_equations
    )

    solution = '<span style="color:#8A99A8;">，</span>'.join(
        '<span style="color:#0F766E; font-weight:600; '
        "font-family:'Cambria Math',serif; font-size:12px; "
        f'">{escape(label)} = {coefficient}</span>'
        for label, coefficient in zip(labels, result.coefficients)
    )

    ratio = " : ".join(str(value) for value in result.coefficients)
    note = ""
    if result.note:
        note = (
            '<div style="margin:6px 0 0 0; padding:6px 8px; border-radius:6px; '
            'background:#FFF9EC; color:#8A6418; font-size:10px;">'
            f"{escape(result.note)}</div>"
        )

    return f"""
    <div style="font-family:'Microsoft YaHei UI'; color:#54687A; font-size:11px;">
      <div style="margin:0 0 4px 0;">
        <span style="color:#0F9D8A; font-weight:700;">01</span>
        <span style="margin-left:5px; color:#33495E; font-weight:600;">设未知系数</span>
      </div>
      <div style="margin:0 0 9px 0; font-family:'Cambria Math',serif; font-size:13px; color:#263C50;">
        {unknown_left}
        <span style="color:#0F9D8A;">&nbsp;⟶&nbsp;</span>
        {unknown_right}
      </div>

      <div style="margin:0 0 3px 0;">
        <span style="color:#0F9D8A; font-weight:700;">02</span>
        <span style="margin-left:5px; color:#33495E; font-weight:600;">按元素列守恒方程</span>
      </div>
      <div style="margin:0 0 9px 0;">{equations}</div>

      <div style="margin:0 0 4px 0;">
        <span style="color:#0F9D8A; font-weight:700;">03</span>
        <span style="margin-left:5px; color:#33495E; font-weight:600;">取最小正整数解</span>
      </div>
      <div style="margin:0 0 5px 0;">{solution}</div>
      <div style="color:#8595A4; font-size:10px;">最简系数比&nbsp;&nbsp;{escape(ratio)}</div>
      {note}
    </div>
    """


def steps_placeholder_html() -> str:
    return """
    <div style="font-family:'Microsoft YaHei UI'; color:#94A3B1; font-size:11px; padding-top:42px; text-align:center;">
      配平后，这里会显示<br/>
      <span style="color:#738494;">“设未知系数 → 列守恒方程 → 取整数解”</span><br/>
      的完整过程
    </div>
    """


def steps_error_html(message: str) -> str:
    return f"""
    <div style="font-family:'Microsoft YaHei UI'; color:#7B8C9C; font-size:11px; padding-top:34px; text-align:center;">
      <div style="color:#C2414B; font-size:12px; font-weight:600; margin-bottom:6px;">暂时无法求解</div>
      <div>{escape(message)}</div>
      <div style="margin-top:10px; color:#98A6B4; font-size:10px;">修正输入后，这里会自动刷新</div>
    </div>
    """
