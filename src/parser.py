# 化学方程式配平器
import re
from collections import defaultdict


def parser_info(data: str) -> dict:
    element_list = []
    element_dict = defaultdict(int)
    element_list.append(element_dict)
    water_time = ''

    i = 0
    while i < len(data):
        ch = data[i]
        # 大写字母是元素的开始
        if ch.isupper():
            element = ch
            i += 1
            # 后面跟小写字母则属于当前元素
            if i < len(data) and data[i].islower():
                element += data[i]
                i += 1
            # 读取数字下标
            count = 1
            j = i
            while j < len(data) and data[j].isdigit():
                j += 1
            if j > i:
                count = int(data[i:j])
                i = j
            element_list[-1][element] += count

        elif ch == '(':
            # 进入括号，压一层新字典
            element_list.append(defaultdict(int))
            i += 1

        elif ch == ')':
            i += 1
            # 读取括号后的倍数（可能多位，如 (SO4)3）
            times = 1
            j = i
            while j < len(data) and data[j].isdigit():
                j += 1
            if j > i:
                times = int(data[i:j])
                i = j
            # 弹出括号内字典，乘倍数后并入上一层
            inner = element_list.pop()
            for element, count in inner.items():
                element_list[-1][element] += count * times

        # 水合物的情况
        elif ch == '·':
            # 将其看作括号一样的栈处理
            element_list.append(defaultdict(int))
            j = i+1
            # 获取水合物倍数
            while j < len(data) and data[j].isdigit():
                water_time += data[j]
                j+=1

            if j==i+1:
                water_time = 1
            water_time = int(water_time)

            i += 1

        elif ch == '^':
            charge_ = data[i+1: len(data)]
            num = re.findall(r'\d*', charge_)[0]
            if num == '':
                num = 1
            num = (int(num)*-1 if '-' in charge_ else int(num))
            element_list[-1]['charge'] += num
            break

        else:
            # 其它字符（孤立的小写字母、数字等）跳过
            i += 1




    # 到最后把水合物的部分弹栈再加回第一级栈
    if len(element_list) > 1:
        water_part = element_list.pop()
        for element, count in water_part.items():
            element_list[-1][element] += count * water_time

    return dict(element_list[0])


# 把不带 ^ 的电荷写法规范成 ^ 写法（Fe2+ -> Fe^2+，SO4- -> SO4^-，H+ -> H^+）
def normalize_charge(substance: str) -> str:
    if '^' in substance:
        return substance
    # 简单离子：单元素 + 电荷数字（Fe2+ / Cu2+ / Al3+）
    m = re.match(r'^([A-Z][a-z]?)(\d+)([+-])$', substance)
    if m:
        return f'{m.group(1)}^{m.group(2)}{m.group(3)}'
    # 其余：多原子离子，末尾数字是下标（SO4- / NH4+ / H2PO4-）
    m = re.match(r'^(.+?)([+-])$', substance)
    if m:
        return f'{m.group(1)}^{m.group(2)}'
    return substance


# 将元素从化学方程式里面解析出来
def parse_equation(eq_str: str):
    eq_str = eq_str.strip()
    # 把离子电荷（带 ^ 和不带 ^ 两种写法）临时替换掉，避免与物质分隔符 + 混淆
    protected = re.sub(r'\^(\d*)\+', r'^\1plus', eq_str)
    protected = re.sub(r'\^(\d*)-', r'^\1minus', protected)
    protected = re.sub(r'(?<=[A-Za-z0-9\)])\+(?=\s|$)', 'plus', protected)
    protected = re.sub(r'(?<=[A-Za-z0-9\)])-(?=\s|$)', 'minus', protected)

    left, right = protected.split("->")
    reactants = [x.strip() for x in left.split("+")]
    products = [x.strip() for x in right.split("+")]

    # 还原，并规范成 ^ 写法
    reactant_strs = [normalize_charge(r.replace("plus", "+").replace("minus", "-")) for r in reactants]
    product_strs = [normalize_charge(p.replace("plus", "+").replace("minus", "-")) for p in products]

    reactant = []
    for substance in reactant_strs:
        element_dict = parser_info(substance)
        reactant.append(element_dict)
    product = []
    for substance in product_strs:
        element_dict = parser_info(substance)
        product.append(element_dict)

    return reactant, product, (reactant_strs, product_strs)




if __name__ == "__main__":
    element_dict, a, b = parse_equation('MnO^4- + Fe^2+ + H^+ -> Mn^2+ + Fe^3+ + H2O')
    print(element_dict, a, b)
