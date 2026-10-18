

'''
对于方程式配平器的代码部分
'''
from sympy import Matrix, lcm
from math import gcd
from functools import reduce
from itertools import product



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
    # 多个基向量说明有多组解，交给用户决定要不要取最简整数解
    else:
        a = input('该方程有多组解，是否选择最简的整数解，否则请重新修改方程式(y/n):')
        if a != 'y':
            raise ValueError('该方程式有多组解，请补充条件后重试')

        # 基向量自身不是配平结果（含负数或0），要用它们的整数组合拼出全为正的解
        limit = 20 if len(result) == 2 else 5
        for coef in product(range(-limit, limit + 1), repeat=len(result)):
            if not any(coef):
                continue
            vec = sum((c * v for c, v in zip(coef, result)),
                      Matrix.zeros(result[0].rows, 1))
            int_vec = simplify(vec)
            if all(c > 0 for c in int_vec):
                balance_result.append(int_vec)

        if not balance_result:
            raise ValueError('没有找到系数全为正的整数解')

        int_vec = compare_sum(balance_result)[0][2]

        equation = result_print(int_vec, substance_list[0], substance_list[1])
        return equation


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
    equation_str = '+'.join(new_reactants_l) + '->' + '+'.join(new_products_l)
    return equation_str









