if __name__ == '__main__':

    from balancer import balancer
    from parser import parse_equation

    equation = 'H2 + O2 -> H2O'
    reaction, production, substance_list = parse_equation(equation)
    print(balancer(reaction, production, substance_list))
