#!/usr/bin/env python3
"""Update product images in MongoDB with local SVG paths."""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

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
    "STN-001": "/products/STN-001.svg",
    "LMP-001": "/products/LMP-001.svg",
    "CBL-001": "/products/CBL-001.svg",
    "CBL-002": "/products/CBL-002.svg",
    "CBL-003": "/products/CBL-003.svg",
    "CBL-004": "/products/CBL-004.svg",
    "CBL-005": "/products/CBL-005.svg",
    "CBL-006": "/products/CBL-006.svg",
    "EAR-002": "/products/EAR-002.svg",
    "BSP-001": "/products/BSP-001.svg",
    "MIC-001": "/products/MIC-001.svg",
    "SPK-001": "/products/SPK-001.svg",
    "NCH-001": "/products/NCH-001.svg",
    "KBD-002": "/products/KBD-002.svg",
    "PRS-001": "/products/PRS-001.svg",
    "PAD-001": "/products/PAD-001.svg",
    "CAM-001": "/products/CAM-001.svg",
    "VM-002": "/products/VM-002.svg",
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
    
    # Check for products without images
    print("\nProducts without images:")
    async for product in products.find({"$or": [{"image_url": None}, {"image_url": ""}]}, {"sku": 1, "title": 1}):
        print(f"  {product['sku']}: {product['title']}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(update_images())