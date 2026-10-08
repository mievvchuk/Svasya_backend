from datetime import datetime, timezone

from app.database import db


PRODUCTS_COLLECTION = "products"
VARIANTS_COLLECTION = "product_variants"


PRODUCTS = [
    {
        "id": "product_tshirt_basic",
        "name": "Basic T-Shirt",
        "description": "Basic cotton t-shirt with a simple design.",
        "category": "tshirt",
        "price": 24.99,
        "is_available": True,
        "created_at": datetime.now(timezone.utc),
    },
    {
        "id": "product_hoodie_classic",
        "name": "Classic Hoodie",
        "description": "Comfortable everyday hoodie with a relaxed fit.",
        "category": "hoodie",
        "price": 54.99,
        "is_available": True,
        "created_at": datetime.now(timezone.utc),
    },
    {
        "id": "product_sweatshirt_basic",
        "name": "Basic Sweatshirt",
        "description": "Warm sweatshirt suitable for everyday wear.",
        "category": "sweatshirt",
        "price": 44.99,
        "is_available": True,
        "created_at": datetime.now(timezone.utc),
    },
    {
        "id": "product_longsleeve_basic",
        "name": "Basic Longsleeve",
        "description": "Long sleeve cotton shirt for casual outfits.",
        "category": "longsleeve",
        "price": 34.99,
        "is_available": True,
        "created_at": datetime.now(timezone.utc),
    },
    {
        "id": "product_cap_classic",
        "name": "Classic Cap",
        "description": "Classic everyday baseball cap.",
        "category": "cap",
        "price": 19.99,
        "is_available": True,
        "created_at": datetime.now(timezone.utc),
    },
    {
        "id": "product_tote_bag_basic",
        "name": "Basic Tote Bag",
        "description": "Reusable cotton tote bag for everyday use.",
        "category": "tote_bag",
        "price": 14.99,
        "is_available": True,
        "created_at": datetime.now(timezone.utc),
    },
    {
        "id": "product_mug_basic",
        "name": "Basic Mug",
        "description": "Simple ceramic mug for hot and cold drinks.",
        "category": "mug",
        "price": 12.99,
        "is_available": True,
        "created_at": datetime.now(timezone.utc),
    },
]


PRODUCT_VARIANTS = [
    # T-SHIRT
    {
        "id": "variant_tshirt_black_s",
        "product_id": "product_tshirt_basic",
        "color": "black",
        "size": "S",
        "image_url": "https://placehold.co/600x600/png?text=Black+T-Shirt",
        "stock": 15,
    },
    {
        "id": "variant_tshirt_black_m",
        "product_id": "product_tshirt_basic",
        "color": "black",
        "size": "M",
        "image_url": "https://placehold.co/600x600/png?text=Black+T-Shirt",
        "stock": 20,
    },
    {
        "id": "variant_tshirt_black_l",
        "product_id": "product_tshirt_basic",
        "color": "black",
        "size": "L",
        "image_url": "https://placehold.co/600x600/png?text=Black+T-Shirt",
        "stock": 18,
    },
    {
        "id": "variant_tshirt_white_m",
        "product_id": "product_tshirt_basic",
        "color": "white",
        "size": "M",
        "image_url": "https://placehold.co/600x600/png?text=White+T-Shirt",
        "stock": 12,
    },

    # HOODIE
    {
        "id": "variant_hoodie_black_m",
        "product_id": "product_hoodie_classic",
        "color": "black",
        "size": "M",
        "image_url": "https://placehold.co/600x600/png?text=Black+Hoodie",
        "stock": 10,
    },
    {
        "id": "variant_hoodie_black_l",
        "product_id": "product_hoodie_classic",
        "color": "black",
        "size": "L",
        "image_url": "https://placehold.co/600x600/png?text=Black+Hoodie",
        "stock": 14,
    },
    {
        "id": "variant_hoodie_gray_l",
        "product_id": "product_hoodie_classic",
        "color": "gray",
        "size": "L",
        "image_url": "https://placehold.co/600x600/png?text=Gray+Hoodie",
        "stock": 8,
    },
    {
        "id": "variant_hoodie_navy_xl",
        "product_id": "product_hoodie_classic",
        "color": "navy",
        "size": "XL",
        "image_url": "https://placehold.co/600x600/png?text=Navy+Hoodie",
        "stock": 6,
    },

    # SWEATSHIRT
    {
        "id": "variant_sweatshirt_gray_m",
        "product_id": "product_sweatshirt_basic",
        "color": "gray",
        "size": "M",
        "image_url": "https://placehold.co/600x600/png?text=Gray+Sweatshirt",
        "stock": 11,
    },
    {
        "id": "variant_sweatshirt_charcoal_l",
        "product_id": "product_sweatshirt_basic",
        "color": "charcoal",
        "size": "L",
        "image_url": "https://placehold.co/600x600/png?text=Charcoal+Sweatshirt",
        "stock": 9,
    },

    # LONGSLEEVE
    {
        "id": "variant_longsleeve_white_s",
        "product_id": "product_longsleeve_basic",
        "color": "white",
        "size": "S",
        "image_url": "https://placehold.co/600x600/png?text=White+Longsleeve",
        "stock": 7,
    },
    {
        "id": "variant_longsleeve_navy_m",
        "product_id": "product_longsleeve_basic",
        "color": "navy",
        "size": "M",
        "image_url": "https://placehold.co/600x600/png?text=Navy+Longsleeve",
        "stock": 13,
    },

    # CAP
    {
        "id": "variant_cap_black",
        "product_id": "product_cap_classic",
        "color": "black",
        "size": "ONE_SIZE",
        "image_url": "https://placehold.co/600x600/png?text=Black+Cap",
        "stock": 20,
    },
    {
        "id": "variant_cap_navy",
        "product_id": "product_cap_classic",
        "color": "navy",
        "size": "ONE_SIZE",
        "image_url": "https://placehold.co/600x600/png?text=Navy+Cap",
        "stock": 16,
    },

    # TOTE BAG
    {
        "id": "variant_tote_black",
        "product_id": "product_tote_bag_basic",
        "color": "black",
        "size": None,
        "image_url": "https://placehold.co/600x600/png?text=Black+Tote+Bag",
        "stock": 25,
    },
    {
        "id": "variant_tote_beige",
        "product_id": "product_tote_bag_basic",
        "color": "beige",
        "size": None,
        "image_url": "https://placehold.co/600x600/png?text=Beige+Tote+Bag",
        "stock": 18,
    },

    # MUG
    {
        "id": "variant_mug_white",
        "product_id": "product_mug_basic",
        "color": "white",
        "size": None,
        "image_url": "https://placehold.co/600x600/png?text=White+Mug",
        "stock": 30,
    },
    {
        "id": "variant_mug_black",
        "product_id": "product_mug_basic",
        "color": "black",
        "size": None,
        "image_url": "https://placehold.co/600x600/png?text=Black+Mug",
        "stock": 22,
    },
]


async def seed_products():
    products_collection = db[PRODUCTS_COLLECTION]
    variants_collection = db[VARIANTS_COLLECTION]

    for product in PRODUCTS:
        await products_collection.update_one(
            {"id": product["id"]},
            {"$set": product},
            upsert=True,
        )

    for variant in PRODUCT_VARIANTS:
        await variants_collection.update_one(
            {"id": variant["id"]},
            {"$set": variant},
            upsert=True,
        )

    print(
        f"Seed completed: "
        f"{len(PRODUCTS)} products, "
        f"{len(PRODUCT_VARIANTS)} variants"
    )