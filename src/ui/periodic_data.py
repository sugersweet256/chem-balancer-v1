"""118 种元素数据（UI 层自带，不修改核心代码）。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Element:
    number: int
    symbol: str
    name_zh: str
    name_en: str
    mass: float
    category: str
    period: int
    group: int  # 0 表示镧系/锕系

    @property
    def display_name(self) -> str:
        return self.name_zh or self.name_en

    @property
    def mass_text(self) -> str:
        if self.mass.is_integer():
            return str(int(self.mass))
        return f"{self.mass:.3f}".rstrip("0").rstrip(".")


CATEGORY_LABELS = {
    "alkali": "碱金属", "alkaline": "碱土金属", "transition": "过渡金属",
    "post": "主族金属", "metalloid": "类金属", "nonmetal": "非金属",
    "halogen": "卤素", "noble": "稀有气体", "lanthanide": "镧系",
    "actinide": "锕系", "unknown": "性质未知",
}

CATEGORY_COLORS = {
    "alkali": ("#FFF4E5", "#F0D3A2", "#8A5A12"),
    "alkaline": ("#FFF8DA", "#E8D693", "#7B6413"),
    "transition": ("#EAF2FF", "#C7D9F3", "#285A9E"),
    "post": ("#EDF4FA", "#C9DCEA", "#3C647F"),
    "metalloid": ("#E8F8F2", "#B8E2D1", "#176B58"),
    "nonmetal": ("#EAF8E9", "#BDE5C0", "#2F6D3A"),
    "halogen": ("#E8F7FB", "#B7E0ED", "#1E6A80"),
    "noble": ("#F3ECFF", "#D8C7F2", "#5B3A93"),
    "lanthanide": ("#FCEFF3", "#EFC6D1", "#8C3D54"),
    "actinide": ("#F8EEFF", "#E0C6F0", "#6B3A89"),
    "unknown": ("#F3F5F7", "#DCE2E8", "#5C6D7E"),
}

_DATA = """
1|H|氢|Hydrogen|1.008|nonmetal|1|1
2|He|氦|Helium|4.0026|noble|1|18
3|Li|锂|Lithium|6.94|alkali|2|1
4|Be|铍|Beryllium|9.0122|alkaline|2|2
5|B|硼|Boron|10.81|metalloid|2|13
6|C|碳|Carbon|12.011|nonmetal|2|14
7|N|氮|Nitrogen|14.007|nonmetal|2|15
8|O|氧|Oxygen|15.999|nonmetal|2|16
9|F|氟|Fluorine|18.998|halogen|2|17
10|Ne|氖|Neon|20.180|noble|2|18
11|Na|钠|Sodium|22.990|alkali|3|1
12|Mg|镁|Magnesium|24.305|alkaline|3|2
13|Al|铝|Aluminium|26.982|post|3|13
14|Si|硅|Silicon|28.085|metalloid|3|14
15|P|磷|Phosphorus|30.974|nonmetal|3|15
16|S|硫|Sulfur|32.06|nonmetal|3|16
17|Cl|氯|Chlorine|35.45|halogen|3|17
18|Ar|氩|Argon|39.948|noble|3|18
19|K|钾|Potassium|39.098|alkali|4|1
20|Ca|钙|Calcium|40.078|alkaline|4|2
21|Sc|钪|Scandium|44.956|transition|4|3
22|Ti|钛|Titanium|47.867|transition|4|4
23|V|钒|Vanadium|50.942|transition|4|5
24|Cr|铬|Chromium|51.996|transition|4|6
25|Mn|锰|Manganese|54.938|transition|4|7
26|Fe|铁|Iron|55.845|transition|4|8
27|Co|钴|Cobalt|58.933|transition|4|9
28|Ni|镍|Nickel|58.693|transition|4|10
29|Cu|铜|Copper|63.546|transition|4|11
30|Zn|锌|Zinc|65.38|transition|4|12
31|Ga|镓|Gallium|69.723|post|4|13
32|Ge|锗|Germanium|72.630|metalloid|4|14
33|As|砷|Arsenic|74.922|metalloid|4|15
34|Se|硒|Selenium|78.971|nonmetal|4|16
35|Br|溴|Bromine|79.904|halogen|4|17
36|Kr|氪|Krypton|83.798|noble|4|18
37|Rb|铷|Rubidium|85.468|alkali|5|1
38|Sr|锶|Strontium|87.62|alkaline|5|2
39|Y|钇|Yttrium|88.906|transition|5|3
40|Zr|锆|Zirconium|91.224|transition|5|4
41|Nb|铌|Niobium|92.906|transition|5|5
42|Mo|钼|Molybdenum|95.95|transition|5|6
43|Tc|锝|Technetium|98|transition|5|7
44|Ru|钌|Ruthenium|101.07|transition|5|8
45|Rh|铑|Rhodium|102.91|transition|5|9
46|Pd|钯|Palladium|106.42|transition|5|10
47|Ag|银|Silver|107.87|transition|5|11
48|Cd|镉|Cadmium|112.41|transition|5|12
49|In|铟|Indium|114.82|post|5|13
50|Sn|锡|Tin|118.71|post|5|14
51|Sb|锑|Antimony|121.76|metalloid|5|15
52|Te|碲|Tellurium|127.60|metalloid|5|16
53|I|碘|Iodine|126.90|halogen|5|17
54|Xe|氙|Xenon|131.29|noble|5|18
55|Cs|铯|Caesium|132.91|alkali|6|1
56|Ba|钡|Barium|137.33|alkaline|6|2
57|La|镧|Lanthanum|138.91|lanthanide|6|0
58|Ce|铈|Cerium|140.12|lanthanide|6|0
59|Pr|镨|Praseodymium|140.91|lanthanide|6|0
60|Nd|钕|Neodymium|144.24|lanthanide|6|0
61|Pm|钷|Promethium|145|lanthanide|6|0
62|Sm|钐|Samarium|150.36|lanthanide|6|0
63|Eu|铕|Europium|151.96|lanthanide|6|0
64|Gd|钆|Gadolinium|157.25|lanthanide|6|0
65|Tb|铽|Terbium|158.93|lanthanide|6|0
66|Dy|镝|Dysprosium|162.50|lanthanide|6|0
67|Ho|钬|Holmium|164.93|lanthanide|6|0
68|Er|铒|Erbium|167.26|lanthanide|6|0
69|Tm|铥|Thulium|168.93|lanthanide|6|0
70|Yb|镱|Ytterbium|173.05|lanthanide|6|0
71|Lu|镥|Lutetium|174.97|lanthanide|6|0
72|Hf|铪|Hafnium|178.49|transition|6|4
73|Ta|钽|Tantalum|180.95|transition|6|5
74|W|钨|Tungsten|183.84|transition|6|6
75|Re|铼|Rhenium|186.21|transition|6|7
76|Os|锇|Osmium|190.23|transition|6|8
77|Ir|铱|Iridium|192.22|transition|6|9
78|Pt|铂|Platinum|195.08|transition|6|10
79|Au|金|Gold|196.97|transition|6|11
80|Hg|汞|Mercury|200.59|transition|6|12
81|Tl|铊|Thallium|204.38|post|6|13
82|Pb|铅|Lead|207.2|post|6|14
83|Bi|铋|Bismuth|208.98|post|6|15
84|Po|钋|Polonium|209|metalloid|6|16
85|At|砹|Astatine|210|halogen|6|17
86|Rn|氡|Radon|222|noble|6|18
87|Fr|钫|Francium|223|alkali|7|1
88|Ra|镭|Radium|226|alkaline|7|2
89|Ac|锕|Actinium|227|actinide|7|0
90|Th|钍|Thorium|232.04|actinide|7|0
91|Pa|镤|Protactinium|231.04|actinide|7|0
92|U|铀|Uranium|238.03|actinide|7|0
93|Np|镎|Neptunium|237|actinide|7|0
94|Pu|钚|Plutonium|244|actinide|7|0
95|Am|镅|Americium|243|actinide|7|0
96|Cm|锔|Curium|247|actinide|7|0
97|Bk|锫|Berkelium|247|actinide|7|0
98|Cf|锎|Californium|251|actinide|7|0
99|Es|锿|Einsteinium|252|actinide|7|0
100|Fm|镄|Fermium|257|actinide|7|0
101|Md|钔|Mendelevium|258|actinide|7|0
102|No|锘|Nobelium|259|actinide|7|0
103|Lr|铹|Lawrencium|266|actinide|7|0
104|Rf||Rutherfordium|267|transition|7|4
105|Db||Dubnium|268|transition|7|5
106|Sg||Seaborgium|269|transition|7|6
107|Bh||Bohrium|270|transition|7|7
108|Hs||Hassium|269|transition|7|8
109|Mt||Meitnerium|278|transition|7|9
110|Ds||Darmstadtium|281|transition|7|10
111|Rg||Roentgenium|282|transition|7|11
112|Cn||Copernicium|285|transition|7|12
113|Nh||Nihonium|286|unknown|7|13
114|Fl||Flerovium|289|unknown|7|14
115|Mc||Moscovium|290|unknown|7|15
116|Lv||Livermorium|293|unknown|7|16
117|Ts||Tennessine|294|halogen|7|17
118|Og||Oganesson|294|noble|7|18
"""

ELEMENTS: list[Element] = []
for _line in _DATA.strip().splitlines():
    _number, _symbol, _zh, _en, _mass, _category, _period, _group = _line.split("|")
    ELEMENTS.append(
        Element(
            int(_number), _symbol, _zh, _en, float(_mass), _category,
            int(_period), int(_group),
        )
    )

BY_NUMBER = {element.number: element for element in ELEMENTS}


def search_elements(query: str) -> list[Element]:
    query = query.strip().lower()
    if not query:
        return []
    exact = [
        element for element in ELEMENTS
        if str(element.number) == query or element.symbol.lower() == query
    ]
    if exact:
        return exact
    results = []
    for element in ELEMENTS:
        haystack = (
            element.symbol.lower(), element.name_zh,
            element.name_en.lower(), str(element.number),
        )
        if any(query in value for value in haystack):
            results.append(element)
    return results
