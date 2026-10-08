from app.common.enums import ProductCategory
from app.products.schemas import Product, ProductVariant


def get_all_products() -> list[Product]:
    raise NotImplementedError("Products API will be implemented in a feature branch")


def get_product_by_id(product_id: str) -> Product | None:
    raise NotImplementedError("Products API will be implemented in a feature branch")


def filter_products(
    category: ProductCategory | None = None,
    is_available: bool | None = None,
) -> list[Product]:
    raise NotImplementedError("Product filtering will be implemented in a feature branch")


def get_product_variants(product_id: str) -> list[ProductVariant]:
    raise NotImplementedError("Variant handling will be implemented in a feature branch")
