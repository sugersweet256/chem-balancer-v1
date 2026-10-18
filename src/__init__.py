if __name__ == '__main__':
    # 只在直接运行本文件时执行，被 import src 时不会触发
    from balancer import balancer
    from parser import parse_equation

    equation = 'H2 + O2 -> H2O'
    reaction, production, substance_list = parse_equation(equation)
    print(balancer(reaction, production, substance_list))
