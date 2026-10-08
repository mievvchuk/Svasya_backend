from enum import Enum


class ProductCategory(str, Enum):
    TSHIRT = "tshirt"
    HOODIE = "hoodie"
    SWEATSHIRT = "sweatshirt"
    LONGSLEEVE = "longsleeve"
    CAP = "cap"
    TOTE_BAG = "tote_bag"
    MUG = "mug"


class ProductSize(str, Enum):
    S = "S"
    M = "M"
    L = "L"
    XL = "XL"
    ONE_SIZE = "ONE_SIZE"


class ProductColor(str, Enum):
    BLACK = "black"
    WHITE = "white"
    GRAY = "gray"
    CHARCOAL = "charcoal"
    RED = "red"
    BURGUNDY = "burgundy"
    NAVY = "navy"
    BLUE = "blue"
    GREEN = "green"
    FOREST_GREEN = "forest_green"
    OLIVE = "olive"
    BEIGE = "beige"