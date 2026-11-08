'''
反应能量变化图
根据配平后的方程式（balancer 的返回值，如 "2H2 + O2->2H2O"），
用标准生成焓算反应热 ΔH，画一张"反应物 -> 过渡态 -> 生成物"的能量变化图。
标准生成焓数据统一放在 substances_energy.py 里。

前端用法（Qt）：
    from src.energe_change_pic import energy_change_figure, energy_change_canvas
    fig = energy_change_figure('2H2 + O2->2H2O')      # 返回 matplotlib Figure
    canvas = energy_change_canvas('2H2 + O2->2H2O')   # 直接返回可放进布局的控件
'''
import re

import matplotlib
from matplotlib.figure import Figure

try:  # 作为包的一部分被导入
    from .substances_energy import SUBSTANCES_ENERGY
except ImportError:  # 直接运行本文件
    from substances_energy import SUBSTANCES_ENERGY

matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei',
                                          'PingFang SC', 'Noto Sans CJK SC']
matplotlib.rcParams['axes.unicode_minus'] = False

COEFF = re.compile(r'^(\d+)(.*)$')
STATE = re.compile(r'^(.+?)\((g|l|s|aq)\)$')


def split_terms(equation: str):
    """把配平后的方程式拆成 [(系数, 物质), ...]，返回 (反应物, 生成物)"""
    if '->' not in equation:
        raise ValueError('缺少 -> 箭头，请传入 balancer 配平后的方程式')
    left, right = equation.split('->', 1)

    def one_side(side):
        terms = []
        for term in side.split(' + '):
            term = term.strip()
            if term:
                m = COEFF.match(term)
                terms.append((int(m.group(1)), m.group(2)) if m else (1, term))
        return terms

    return one_side(left), one_side(right)


def formation_enthalpy(species: str):
    """查标准生成焓，带 (g)/(l)/(aq) 状态写法也认，查不到返回 None"""
    if species in SUBSTANCES_ENERGY:
        return SUBSTANCES_ENERGY[species]
    m = STATE.match(species)
    if m and m.group(1) in SUBSTANCES_ENERGY:
        return SUBSTANCES_ENERGY[m.group(1)]
    return None


def reaction_delta_h(reactants, products):
    """ΔH = 生成物的生成焓之和 - 反应物的生成焓之和"""
    delta = 0.0
    for coef, sp in products:
        v = formation_enthalpy(sp)
        if v is None:
            raise ValueError(f'标准生成焓表里没有「{sp}」，算不出 ΔH')
        delta += coef * v
    for coef, sp in reactants:
        v = formation_enthalpy(sp)
        if v is None:
            raise ValueError(f'标准生成焓表里没有「{sp}」，算不出 ΔH')
        delta -= coef * v
    return delta


def energy_change_figure(equation: str, activation_energy: float = 80.0,
                         figsize: tuple = (6, 4.2)) -> Figure:
    """画反应能量变化图，返回 Figure，可直接塞进 Qt 的 FigureCanvasQTAgg"""
    reactants, products = split_terms(equation)
    delta_h = reaction_delta_h(reactants, products)
    exo = delta_h < 0

    # 拿 ΔH 当比例尺，图里反应物和生成物的高度差和 ΔH 成正比
    span = max(abs(delta_h), 100.0)
    y_r = 0.0
    y_p = delta_h / span
    y_peak = max(y_r, y_p) + max(activation_energy / span, 0.18)

    fig = Figure(figsize=figsize)
    ax = fig.add_subplot(111)

    # 反应物 -> 过渡态 -> 生成物
    x = [0, 3, 5, 7, 10]
    y = [y_r, y_r, y_peak, y_p, y_p]
    ax.plot(x, y, color='#2166ac', lw=2.5, solid_capstyle='round')
    ax.fill_between(x, y, min(y_r, y_p) - 0.08, color='#a6cee3', alpha=0.35)

    ax.text(0.3, y_r + 0.06, '反应物', color='#2166ac', fontsize=11)
    ax.text(8.3, y_p + 0.06, '生成物', color='#b2182b', fontsize=11)
    ax.text(5, y_peak + 0.06, '过渡态', color='#333333', fontsize=10, ha='center')

    # ΔH 箭头（左侧）
    ax.annotate('', xy=(1.6, y_p), xytext=(1.6, y_r),
                arrowprops=dict(arrowstyle='<->', color='#333333', lw=1.2))
    ax.text(1.75, (y_r + y_p) / 2 + 0.02,
            f'ΔH = {delta_h:.0f} kJ/mol', fontsize=10, va='center', color='#333333')

    # Ea 箭头（反应物上方）
    ax.annotate('', xy=(2.9, y_peak), xytext=(2.9, y_r),
                arrowprops=dict(arrowstyle='<->', color='#555555', lw=1.0, ls='--'))
    ax.text(3.05, (y_r + y_peak) / 2, f'Ea ≈ {activation_energy:.0f} kJ/mol',
            fontsize=9, va='center', color='#555555')

    kind = '放热反应' if exo else ('吸热反应' if delta_h > 0 else '能量不变')
    ax.set_title(f'{equation.replace("->", " → ")}  （{kind}）', fontsize=10)
    ax.set_xlabel('反应进程')
    ax.set_ylabel('能量')
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlim(-0.3, 10.4)
    ax.set_ylim(min(y_r, y_p) - 0.18, y_peak + 0.3)
    fig.tight_layout()
    return fig


def energy_change_canvas(equation: str, parent=None, **kwargs):
    """给 Qt 前端用：直接返回一个 FigureCanvasQTAgg 控件（可加进布局）"""
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
    canvas = FigureCanvasQTAgg(energy_change_figure(equation, **kwargs))
    if parent is not None:
        canvas.setParent(parent)
    return canvas


if __name__ == '__main__':
    # 直接运行本文件：把两张示例图存成 PNG
    energy_change_figure('2H2 + O2->2H2O').savefig('放热演示.png', dpi=110)
    energy_change_figure('CaCO3->CaO + CO2').savefig('吸热演示.png', dpi=110)
    print('已保存 放热演示.png / 吸热演示.png')
