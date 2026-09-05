from collections import defaultdict


def parser_info(data: str) -> dict:
    element_list = []
    element_dict = defaultdict(int)
    element_list.append(element_dict)

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

        else:
            # 其它字符（孤立的小写字母、数字等）跳过
            i += 1

    return dict(element_dict)


if __name__ == "__main__":
    element_dict = parser_info('CH3COOH')
    print(element_dict)
