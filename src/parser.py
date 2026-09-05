import re

TOKEN_PATTERN = re.compile(r'([A-Z][a-z]*)(\d*)')

def parser_info(data:str) -> dict:
    element_dict = {}

    TOKEN_PATTERN = re.compile(r'([A-Z][a-z]*)(\d*)')
    parser_list = TOKEN_PATTERN.findall(data)

    for element_tuple in parser_list:

        element_dict[element_tuple[0]] = element_tuple[1]
        if element_tuple[1] == '':
            element_dict[element_tuple[0]] = '1'

    return element_dict




if __name__ == "__main__":
    element_dict = parser_info('H2O')
    print(element_dict)




