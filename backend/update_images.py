#!/usr/bin/env python3
"""Update product images in MongoDB with local SVG paths."""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

MONGO_URI = "mongodb://mongodb:27017"
DB_NAME = "catalog"

# Mapping of SKU to image filename
PRODUCT_IMAGES = {
    "ORG-001": "/products/ORG-001.svg",
    "NBT-001": "/products/NBT-001.svg",
    "WM-001": "/products/WM-001.svg",
    "MK-001": "/products/MK-001.svg",
    "CHR-001": "/products/CHR-001.svg",
    "DSK-001": "/products/DSK-001.svg",
    "EAR-001": "/products/EAR-001.svg",
    "HUB-001": "/products/HUB-001.svg",
    # Add more as created
}

async def update_images():
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    products = db.products
    
    updated = 0
    for sku, image_url in PRODUCT_IMAGES.items():
        result = await products.update_one(
            {"sku": sku},
            {"$set": {"image_url": image_url}}
        )
        if result.modified_count > 0:
            print(f"Updated {sku} with {image_url}")
            updated += 1
        else:
            print(f"SKU not found: {sku}")
    
    print(f"\nTotal updated: {updated}")
    
    # Verify
    print("\nVerifying updated products:")
    async for product in products.find({"image_url": {"$ne": None}}, {"sku": 1, "title": 1, "image_url": 1}):
        print(f"  {product['sku']}: {product['title']} -> {product['image_url']}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(update_images())