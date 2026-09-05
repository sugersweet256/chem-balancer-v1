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


        else:
            # 其它字符（孤立的小写字母、数字等）跳过
            i += 1
    # 到最后把水合物的部分弹栈再加回第一级栈
    if len(element_list) > 1:
        water_part = element_list.pop()
        for element, count in water_part.items():
            element_list[-1][element] += count * water_time

    return dict(element_list[0])


if __name__ == "__main__":
    element_dict = parser_info('CuSO4·5H2O')
    print(element_dict)
