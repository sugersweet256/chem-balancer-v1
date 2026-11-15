'''
摩尔质量计算 + 质量守恒检查
用 parser 的解析功能（parser_info 算元素个数、split_equation 拆方程式）。
配平后方程式两边的总质量应该相等，可以拿来验证配平。

用法：
    from src.moer_quality import molar_mass, mass_balance
    molar_mass('H2O')                 # 18.015 g/mol
    mass_balance('2H2 + O2->2H2O')    # 两边总质量对比
'''
import re

try:  # 作为包的一部分被导入
    from .parser import parser_info, parse_equation
except ImportError:  # 直接运行本文件
    from parser import parser_info, parse_equation

# 相对原子质量（g/mol），常用元素
ATOMIC_MASS = {
    'H': 1.008, 'He': 4.003, 'Li': 6.94, 'B': 10.81,
    'C': 12.011, 'N': 14.007, 'O': 15.999, 'F': 18.998, 'Na': 22.99,
    'Mg': 24.305, 'Al': 26.982, 'Si': 28.085, 'P': 30.974, 'S': 32.06,
    'Cl': 35.45, 'K': 39.098, 'Ca': 40.078, 'Cr': 52.00, 'Mn': 54.938,
    'Fe': 55.845, 'Co': 58.933, 'Ni': 58.693, 'Cu': 63.546, 'Zn': 65.38,
    'Br': 79.904, 'Ag': 107.868, 'Sn': 118.71, 'I': 126.904,
    'Ba': 137.327, 'Pt': 195.08, 'Au': 196.97, 'Hg': 200.59,
    'Pb': 207.2, 'U': 238.03,
}

COEFF = re.compile(r'^(\d+)(.*)$')


def molar_mass(formula: str) -> float:
    """算一个化学式的摩尔质量，单位 g/mol"""
    counts = parser_info(formula)
    total = 0.0
    for el, n in counts.items():
        if el == 'charge':      # 电荷不是元素
            continue
        if el not in ATOMIC_MASS:
            raise ValueError(f'没有收录元素 {el} 的相对原子质量')
        total += ATOMIC_MASS[el] * n
    return total


def split_coef(term: str):
    """把系数和物质拆开："2H2O" -> (2, "H2O")"""
    m = COEFF.match(term.strip())
    if m:
        return int(m.group(1)), m.group(2)
    return 1, term.strip()


def mass_balance(equation: str) -> dict:
    """配平式两边每个物质的质量和总质量，用来检查质量守恒"""
    _, _, (reactant_strs, product_strs) = parse_equation(equation)

    def side_mass(strs):
        rows = []
        total = 0.0
        for s in strs:
            coef, formula = split_coef(s)
            m = molar_mass(formula)
            rows.append((coef, formula, round(m, 2), round(coef * m, 2)))
            total += coef * m
        return rows, round(total, 2)

    r_rows, r_total = side_mass(reactant_strs)
    p_rows, p_total = side_mass(product_strs)
    return {
        'reactants': r_rows,
        'products': p_rows,
        'left': r_total,
        'right': p_total,
        'ok': abs(r_total - p_total) < 0.1,     # 浮点容差
    }


if __name__ == '__main__':
    print('H2O 的摩尔质量: %.3f g/mol' % molar_mass('H2O'))
    print('CuSO4·5H2O 的摩尔质量: %.3f g/mol' % molar_mass('CuSO4·5H2O'))

    eq = '2H2 + O2->2H2O'
    result = mass_balance(eq)
    print(eq)
    for name in ('reactants', 'products'):
        for coef, formula, m, mass in result[name]:
            print(f'  {coef}{formula}: 摩尔质量 {m} g/mol, 质量 {mass} g')
    print(f'  左边总质量 {result["left"]} g，右边总质量 {result["right"]} g',
          '-> 质量守恒' if result['ok'] else '-> 质量不守恒！')
