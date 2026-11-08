

'''
对于方程式配平器的代码部分
'''
from sympy import Matrix, lcm
from math import gcd
from functools import reduce


# 常见元素的化合价（没列出来的元素就用“剩余法”现算）
VALENCE = {'H': 1, 'F': -1, 'O': -2, 'Cl': -1, 'Br': -1, 'I': -1,
           'K': 1, 'Na': 1, 'Ag': 1, 'Mg': 2, 'Ca': 2, 'Ba': 2, 'Zn': 2, 'Al': 3, 'S': 6}

# 电负性从大到小
ELECTRONEG = ['F', 'O', 'Cl', 'Br', 'I', 'N', 'S', 'C', 'P', 'H']



def compare_sum(ls:list)->list:
    standard_list = []
    for l in ls:
        adding = sum(l)
        the_large = max(l)
        standard_list.append((adding, the_large, l))
    standard_list.sort(key=lambda x: (x[0], x[1]))
    return standard_list



def found_ele(reactants:list, products:list) -> dict:
    result = {}
    sum_l = reactants + products
    count = len(sum_l)
    ele_set = set()
# 将方程式中出现过的元素都放进集合中去重
    for substances in sum_l:
        for element in substances:
            ele_set.add(element)
# 为创建矩阵用的，将矩阵中的数字全都初始化成0
    for element in ele_set:
        result[element] = [0]*count

    return result


def oxidation_num(species:dict):
    """算一个物质里每个元素的化合价，算不准就返回 None"""
    charge = species.get('charge', 0)
    os = {}
    rest = charge
    other = []
    for el, n in species.items():
        if el == 'charge':
            continue
        if el in VALENCE:
            os[el] = VALENCE[el]
            rest -= VALENCE[el] * n
        else:
            other.append(el)
    # 两个以上查不到表的元素，靠剩余法分不清，算不准
    if len(other) > 1:
        return None
    # 查不到表的元素，用剩下的电荷平分
    for el in other:
        os[el] = rest // species[el]
        rest -= os[el] * species[el]
        if os[el] < 0:      # 金属/非金属里冒负数，多半是表值套错了
            return None
    # 表里的化合价加起来对不上电荷时（比如过氧化氢里的氧），挨个换着试
    if rest != 0:
        cand = sorted(os, key=lambda e: (species[e], ELECTRONEG.index(e) if e in ELECTRONEG else 99))
        for el in cand:
            v = (charge - (sum(os[k]*species[k] for k in os) - os[el]*species[el])) // species[el]
            if v == 0 and len(species) > 1:     # 化合物里的元素显 0 价基本不对
                continue
            os[el] = v
            return os
        return None
    return os


def valence_balance(reactants:list, products:list, parse_list:list):
    """多解时用化合价升降守恒补一条电子守恒约束，能解出唯一正系数就返回"""
    left_os = [oxidation_num(s) for s in reactants]
    right_os = [oxidation_num(s) for s in products]
    if None in left_os or None in right_os:     # 有物质化合价算不准，就不硬算
        return None

    # 生成物里的原子，当作从左边“化合价最接近”的那个物质来的
    row = [0] * len(reactants)
    for i, species in enumerate(products):
        c = 0
        for el, n in species.items():
            if el == 'charge':
                continue
            q = right_os[i][el]
            source = [os[el] for os in left_os if el in os]
            if source:
                c += n * (q - min(source, key=lambda p: abs(p - q)))
        row.append(c)

    result = Matrix(parse_list + [row]).nullspace()
    if len(result) == 1:
        int_vec = simplify(result[0])
        if all(x > 0 for x in int_vec):
            return int_vec
    return None


# 正式配平函数
def balancer(reactants:list, products:list, substance_list):
    # 拿到所有元素出现的矩阵
    parse_dict = found_ele(reactants, products)

 # 此处把元素中的系数加进矩阵里面
    i = 0
    for substances in reactants:#反应物系数列表
        for element, count in substances.items():
            parse_dict[element][i] = count
        i += 1


    for substances in products:#生成物系数列表
        for element, count in substances.items():
            parse_dict[element][i] = -1*count
        i += 1

    parse_list = [value for value in parse_dict.values()]
   # 转换为真正的矩阵列表用高斯消元求解
    a = Matrix(parse_list)
    result = a.nullspace() #高斯消元求解零空间

    balance_result = []
    # 零空间为空说明方程式本身不守恒，直接报错
    if len(result) == 0:
        raise ValueError('该方程式无解，请检查方程式是否写错')
    # 解唯一，直接化简返回
    elif len(result) == 1:
        vec = result[0]
        int_vec = simplify(vec)
        # 方程里面存在负数，说明无解
        if any(c <= 0 for c in int_vec):
            raise ValueError('该方程式无法配平（不存在全为正的系数解）')
        return result_print(int_vec, substance_list[0], substance_list[1])
    # 多个基向量说明有多组解，用化合价守恒试试，定不下来就报警，不返回不确定的结果
    else:
        int_vec = valence_balance(reactants, products, parse_list)
        if int_vec is not None:
            return result_print(int_vec, substance_list[0], substance_list[1])
        raise ValueError('该方程式有多组配平解，化合价无法唯一确定，无法保证结果正确，请检查方程式或补充条件')


def simplify(result: Matrix):
    denoms = []
    # 传入的已经是一个列向量，直接取它的每个元素
    vec = result
    # 把分数化成整数
    for v in vec:
        # 把分数拆成 (分子, 分母)
        num, den = v.as_numer_denom()
        denoms.append(den)
    factor = lcm(denoms)

    int_vec = []
    # 化成最简
    for v in vec:
        int_vec.append(int(v * factor))

    # 零空间向量方向不定，整体为负时翻转成正数
    if all(c <= 0 for c in int_vec):
        int_vec = [-c for c in int_vec]

    g = reduce(gcd, int_vec)
    if g > 1:
        int_vec = [c // g for c in int_vec]


   #返回配平系数列表
    return int_vec


def result_print(num_list:list, reactants:list, products:list):
    substance_l = reactants + products


    i = 0
    new_substance_list = []

    for substances in substance_l:
        if num_list[i] > 1:
            new_substance_list.append(str(num_list[i])+substances)
        else:
            new_substance_list.append(substances)
        i+=1
    new_reactants_l:list = new_substance_list[:len(substance_l)-len(products)]
    new_products_l:list = new_substance_list[len(substance_l)-len(products):]
    equation_str =  ' + '.join(new_reactants_l) + '->' + ' + '.join(new_products_l)
    return equation_str









