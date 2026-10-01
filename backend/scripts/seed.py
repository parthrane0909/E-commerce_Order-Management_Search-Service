"""Reproducible seed for the whole demonstration.

    python -m scripts.seed                # drop + recreate everything
    python -m scripts.seed --skip-search  # skip the Elasticsearch rebuild
    python -m scripts.seed --verify-only  # only run the acceptance checks

What it creates
--------------
1. **PostgreSQL**  — 9 users (8 customers + 1 admin) and 44 orders / 86 order lines with snapshot
   titles and prices, spread over the last 90 days and covering every
   required status, price band and search fixture.
2. **MongoDB**     — 27 products (26 active + 1 inactive) across
   peripherals / audio / cables / office with tags, attributes and
   variants.
3. **Elasticsearch** — every order indexed through the normal
   document builder (PostgreSQL → document).
4. **Snapshot demo** — after the orders exist, the MongoDB product
   *Wireless Mouse* ($50.16) is renamed to *Wireless Mouse Pro* ($60.00).
   PostgreSQL order lines and Elasticsearch documents keep the original
   title and price.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from decimal import Decimal

from app.core.config import get_settings
from app.core.database import SessionLocal, create_tables, drop_tables
from app.core.logging import configure_logging, get_logger
from app.models.postgres import ORDER_STATUSES, Order, OrderItem, User
from app.repositories.elasticsearch.orders_repo import count_documents, index_name
from app.repositories.mongo import product_repo
from app.repositories.postgres import order_repo
from app.services.order_service import to_money
from scripts.reindex_orders import reindex_orders

logger = get_logger(__name__)
settings = get_settings()

CENT = Decimal("0.01")
NOW = dt.datetime.now(dt.timezone.utc)

# =====================================================================
# Fixtures
# =====================================================================

USERS = [
    ("John Doe", "john.doe@example.com"),
    ("Jane Smith", "jane.smith@example.com"),
    ("Wendy Wireless", "wendy.wireless@example.com"),
    ("Alex Rivera", "alex.rivera@example.com"),
    ("Sam Patel", "sam.patel@example.com"),
    ("Casey Nguyen", "casey.nguyen@example.com"),
    ("Morgan Lee", "morgan.lee@example.com"),
    ("Riley Brooks", "riley.brooks@example.com"),
]

PRODUCTS: list[dict] = [
    # ------------------------------------------------------------ peripherals
    {
        "sku": "WM-001",
        "title": "Wireless Mouse",
        "description": "Ergonomic 2.4GHz wireless mouse with silent clicks and a 1600 DPI optical sensor.",
        "price": 50.16,
        "category": "peripherals",
        "tags": ["wireless", "usb", "office", "ergonomic"],
        "attributes": {"color": "black", "dpi": 1600, "battery": "AA", "connection": "2.4GHz"},
        "variants": [
            {"sku": "WM-001-BLK", "color": "black", "stock": 40},
            {"sku": "WM-001-WHT", "color": "white", "stock": 25},
        ],
        "active": True,
    },
    {
        "sku": "MK-001",
        "title": "Mechanical Keyboard",
        "description": "Tenkeyless mechanical keyboard with hot-swappable red switches and per-key lighting.",
        "price": 129.00,
        "category": "peripherals",
        "tags": ["mechanical", "wired", "rgb", "keyboard"],
        "attributes": {"layout": "TKL", "switch": "red linear", "backlight": "per-key RGB"},
        "variants": [{"sku": "MK-001-RED", "color": "dark grey", "stock": 30}],
        "active": True,
    },
    {
        "sku": "HUB-001",
        "title": "USB-C Hub 7-in-1",
        "description": "Aluminium USB-C hub with HDMI 4K, 100W power delivery, SD card and 3x USB 3.0.",
        "price": 45.50,
        "category": "peripherals",
        "tags": ["usb-c", "hub", "aluminium", "travel"],
        "attributes": {"ports": 7, "hdmi": "4K@60Hz", "power_delivery_w": 100},
        "variants": [{"sku": "HUB-001-SLV", "color": "silver", "stock": 60}],
        "active": True,
    },
    {
        "sku": "VM-002",
        "title": "Vertical Ergonomic Mouse",
        "description": "Wired vertical mouse that keeps the wrist in a natural handshake position.",
        "price": 22.40,
        "category": "peripherals",
        "tags": ["ergonomic", "wired", "office"],
        "attributes": {"color": "graphite", "dpi": 1200, "hand": "right"},
        "variants": [{"sku": "VM-002-GRF", "color": "graphite", "stock": 35}],
        "active": True,
    },
    {
        "sku": "CAM-001",
        "title": "HD Webcam Pro",
        "description": "1080p60 webcam with auto-focus, dual microphones and a privacy shutter.",
        "price": 89.99,
        "category": "peripherals",
        "tags": ["webcam", "usb", "video", "conference"],
        "attributes": {"resolution": "1080p60", "microphones": "dual", "mount": "clip"},
        "variants": [{"sku": "CAM-001-BLK", "color": "black", "stock": 22}],
        "active": True,
    },
    {
        "sku": "PAD-001",
        "title": "Gaming Mousepad XL",
        "description": "900x400mm stitched-edge cloth mousepad with a non-slip rubber base.",
        "price": 18.99,
        "category": "peripherals",
        "tags": ["mousepad", "desk", "gaming"],
        "attributes": {"size": "900x400mm", "surface": "cloth", "thickness_mm": 4},
        "variants": [{"sku": "PAD-001-BLK", "color": "black", "stock": 120}],
        "active": True,
    },
    {
        "sku": "PRS-001",
        "title": "Wireless Presenter Remote",
        "description": "2.4GHz presenter with red laser pointer, 30m range and plug-and-play USB receiver.",
        "price": 34.95,
        "category": "peripherals",
        "tags": ["wireless", "presenter", "office", "laser"],
        "attributes": {"range_m": 30, "laser": "red", "battery": "2xAAA"},
        "variants": [{"sku": "PRS-001-BLK", "color": "black", "stock": 45}],
        "active": True,
    },
    {
        "sku": "KBD-002",
        "title": "Wireless Keyboard Slim",
        "description": "Low-profile wireless keyboard with multi-device Bluetooth pairing.",
        "price": 89.00,
        "category": "peripherals",
        "tags": ["wireless", "bluetooth", "keyboard", "low-profile"],
        "attributes": {"layout": "full size", "battery": "rechargeable", "devices": 3},
        "variants": [{"sku": "KBD-002-GRY", "color": "grey", "stock": 28}],
        "active": True,
    },
    # ----------------------------------------------------------------- audio
    {
        "sku": "EAR-001",
        "title": "Wireless Earbuds",
        "description": "True wireless earbuds with 24h battery, USB-C case and IPX5 water resistance.",
        "price": 79.99,
        "category": "audio",
        "tags": ["wireless", "bluetooth", "in-ear", "sport"],
        "attributes": {"battery_hours": 24, "codec": "AAC", "rating": "IPX5"},
        "variants": [
            {"sku": "EAR-001-BLK", "color": "black", "stock": 55},
            {"sku": "EAR-001-WHT", "color": "white", "stock": 33},
        ],
        "active": True,
    },
    {
        "sku": "NCH-001",
        "title": "Noise Cancelling Headphones",
        "description": "Over-ear wireless headphones with hybrid ANC, 40h battery and multipoint pairing.",
        "price": 199.00,
        "category": "audio",
        "tags": ["wireless", "bluetooth", "anc", "over-ear"],
        "attributes": {"battery_hours": 40, "anc": "hybrid", "weight_g": 254},
        "variants": [{"sku": "NCH-001-BLK", "color": "black", "stock": 18}],
        "active": True,
    },
    {
        "sku": "SPK-001",
        "title": "Studio Monitor Speakers",
        "description": "Pair of 5-inch powered studio monitors with flat frequency response.",
        "price": 249.00,
        "category": "audio",
        "tags": ["studio", "wired", "speakers"],
        "attributes": {"driver_inch": 5, "power_w": 80, "pair": True},
        "variants": [{"sku": "SPK-001-BLK", "color": "black", "stock": 12}],
        "active": True,
    },
    {
        "sku": "MIC-001",
        "title": "USB Desk Microphone",
        "description": "Cardioid condenser microphone with mute button and zero-latency monitoring.",
        "price": 59.00,
        "category": "audio",
        "tags": ["usb", "podcast", "microphone"],
        "attributes": {"polar_pattern": "cardioid", "sample_rate_khz": 48, "connection": "USB-C"},
        "variants": [{"sku": "MIC-001-BLK", "color": "black", "stock": 26}],
        "active": True,
    },
    {
        "sku": "BSP-001",
        "title": "Portable Bluetooth Speaker",
        "description": "IPX7 waterproof Bluetooth speaker with 20h playtime and stereo pairing.",
        "price": 69.00,
        "category": "audio",
        "tags": ["wireless", "bluetooth", "portable", "outdoor"],
        "attributes": {"battery_hours": 20, "rating": "IPX7", "output_w": 12},
        "variants": [
            {"sku": "BSP-001-BLU", "color": "blue", "stock": 40},
            {"sku": "BSP-001-RED", "color": "red", "stock": 18},
        ],
        "active": True,
    },
    {
        "sku": "EAR-002",
        "title": "Wired Earbuds Basic",
        "description": "Lightweight 3.5mm earbuds with in-line microphone — the budget pick.",
        "price": 9.99,
        "category": "audio",
        "tags": ["wired", "budget", "in-ear"],
        "attributes": {"jack": "3.5mm", "cable_length_m": 1.2, "microphone": True},
        "variants": [{"sku": "EAR-002-WHT", "color": "white", "stock": 200}],
        "active": True,
    },
    # ---------------------------------------------------------------- cables
    {
        "sku": "CBL-001",
        "title": "USB-C to USB-C Cable 2m",
        "description": "Braided 100W USB-C cable rated for 10Gbps data and 4K video.",
        "price": 14.99,
        "category": "cables",
        "tags": ["usb-c", "braided", "charging"],
        "attributes": {"length_m": 2.0, "power_w": 100, "data_gbps": 10},
        "variants": [{"sku": "CBL-001-BLK", "color": "black", "stock": 150}],
        "active": True,
    },
    {
        "sku": "CBL-002",
        "title": "HDMI 2.1 Ultra Cable",
        "description": "48Gbps HDMI 2.1 cable for 4K 120Hz and 8K displays, 1.5m.",
        "price": 24.50,
        "category": "cables",
        "tags": ["hdmi", "8k", "gaming"],
        "attributes": {"length_m": 1.5, "bandwidth_gbps": 48, "version": "2.1"},
        "variants": [{"sku": "CBL-002-BLK", "color": "black", "stock": 90}],
        "active": True,
    },
    {
        "sku": "CBL-003",
        "title": "Thunderbolt 4 Cable 0.8m",
        "description": "Certified Thunderbolt 4 cable: 40Gbps, dual 4K, 100W power delivery.",
        "price": 39.00,
        "category": "cables",
        "tags": ["thunderbolt", "usb-c", "40gbps"],
        "attributes": {"length_m": 0.8, "speed_gbps": 40, "power_w": 100},
        "variants": [{"sku": "CBL-003-BLK", "color": "black", "stock": 70}],
        "active": True,
    },
    {
        "sku": "CBL-004",
        "title": "Ethernet Cat6 Cable 5m",
        "description": "Snagless Cat6 UTP patch cable for stable gigabit networking.",
        "price": 16.75,
        "category": "cables",
        "tags": ["network", "lan", "cat6"],
        "attributes": {"length_m": 5.0, "category": "Cat6", "speed_mbps": 1000},
        "variants": [{"sku": "CBL-004-BLU", "color": "blue", "stock": 110}],
        "active": True,
    },
    {
        "sku": "CBL-005",
        "title": "DisplayPort Cable 4K",
        "description": "DisplayPort 1.4 cable supporting 4K at 144Hz, 2m.",
        "price": 21.00,
        "category": "cables",
        "tags": ["displayport", "4k", "gaming"],
        "attributes": {"length_m": 2.0, "version": "1.4", "refresh_hz": 144},
        "variants": [{"sku": "CBL-005-BLK", "color": "black", "stock": 85}],
        "active": True,
    },
    {
        "sku": "CBL-006",
        "title": "Braided Lightning Cable",
        "description": "1m MFi certified Lightning cable with double-braided nylon jacket.",
        "price": 19.99,
        "category": "cables",
        "tags": ["lightning", "braided", "charging"],
        "attributes": {"length_m": 1.0, "certification": "MFi", "colour": "grey"},
        "variants": [{"sku": "CBL-006-GRY", "color": "grey", "stock": 95}],
        "active": True,
    },
    # ---------------------------------------------------------------- office
    {
        "sku": "LMP-001",
        "title": "Desk Lamp LED",
        "description": "Dimmable LED desk lamp with 5 brightness levels and adjustable colour temperature.",
        "price": 42.00,
        "category": "office",
        "tags": ["lighting", "desk", "led"],
        "attributes": {"brightness_levels": 5, "colour_temperature": "2700-6500K", "power_w": 9},
        "variants": [
            {"sku": "LMP-001-BLK", "color": "black", "stock": 48},
            {"sku": "LMP-001-WHT", "color": "white", "stock": 30},
        ],
        "active": True,
    },
    {
        "sku": "STN-001",
        "title": "Adjustable Monitor Stand",
        "description": "Steel monitor riser with cable tray and two height settings.",
        "price": 55.00,
        "category": "office",
        "tags": ["desk", "ergonomics", "monitor"],
        "attributes": {"material": "steel", "height_mm": 100, "max_weight_kg": 12},
        "variants": [{"sku": "STN-001-BLK", "color": "black", "stock": 34}],
        "active": True,
    },
    {
        "sku": "CHR-001",
        "title": "Ergonomic Office Chair",
        "description": "Breathable mesh chair with adjustable lumbar support and 4D armrests.",
        "price": 329.00,
        "category": "office",
        "tags": ["chair", "ergonomics", "mesh"],
        "attributes": {"material": "mesh", "armrests": "4D", "warranty_years": 5},
        "variants": [{"sku": "CHR-001-BLK", "color": "black", "stock": 14}],
        "active": True,
    },
    {
        "sku": "DSK-001",
        "title": "Standing Desk Converter",
        "description": "Gas-spring sit-stand converter that fits two 27-inch monitors.",
        "price": 189.00,
        "category": "office",
        "tags": ["desk", "standing", "ergonomics"],
        "attributes": {"lift_kg": 15, "surface_cm": "100x60", "mechanism": "gas spring"},
        "variants": [{"sku": "DSK-001-BLK", "color": "black", "stock": 20}],
        "active": True,
    },
    {
        "sku": "NBT-001",
        "title": "Notebook Set (3 Pack)",
        "description": "A5 dotted notebooks with 120gsm paper and lay-flat binding.",
        "price": 12.50,
        "category": "office",
        "tags": ["paper", "notes", "stationery"],
        "attributes": {"size": "A5", "pages": 160, "pack": 3},
        "variants": [{"sku": "NBT-001-MIX", "color": "assorted", "stock": 180}],
        "active": True,
    },
    {
        "sku": "ORG-001",
        "title": "Desk Organizer Bamboo",
        "description": "Bamboo desk tidy with five compartments and a phone slot.",
        "price": 27.50,
        "category": "office",
        "tags": ["desk", "storage", "eco"],
        "attributes": {"material": "bamboo", "compartments": 5},
        "variants": [{"sku": "ORG-001-NAT", "color": "natural", "stock": 65}],
        "active": True,
    },
    {
        "sku": "CHG-001",
        "title": "Wireless Charging Pad",
        "description": "15W Qi wireless charger with a non-slip surface — currently discontinued.",
        "price": 35.00,
        "category": "office",
        "tags": ["wireless", "charging", "qi"],
        "attributes": {"output_w": 15, "standard": "Qi", "surface": "silicone"},
        "variants": [{"sku": "CHG-001-BLK", "color": "black", "stock": 0}],
        "active": False,  # the single inactive product
    },
]

# Order line fixtures, referenced by SKU ------------------------------
FIXTURE_ITEMS: list[list[tuple[str, int]]] = [
    [("WM-001", 1), ("MK-001", 1), ("LMP-001", 1)],
    [("WM-001", 2), ("MK-001", 1)],
    [("WM-001", 1), ("MK-001", 1)],
    [("WM-001", 1), ("EAR-001", 1), ("CBL-003", 1)],
    [("WM-001", 1), ("LMP-001", 1)],
    [("WM-001", 3), ("ORG-001", 1)],
    [("WM-001", 1), ("HUB-001", 1), ("CBL-003", 1)],
    [("WM-001", 2), ("MIC-001", 1)],
]

CHEAP_ITEMS: list[list[tuple[str, int]]] = [
    [("EAR-002", 1)],  # 9.99
    [("NBT-001", 2)],  # 25.00
    [("CBL-001", 1)],  # 14.99
    [("CBL-004", 1), ("NBT-001", 1)],  # 29.25
    [("CBL-002", 1)],  # 24.50
    [("CBL-005", 1)],  # 21.00
]

MID_ITEMS: list[list[tuple[str, int]]] = [
    [("LMP-001", 1), ("ORG-001", 1)],
    [("HUB-001", 1), ("CBL-003", 1)],
    [("MIC-001", 1), ("LMP-001", 1)],
    [("EAR-001", 1), ("ORG-001", 1)],
    [("BSP-001", 1), ("CBL-003", 1)],
    [("CAM-001", 1), ("LMP-001", 1)],
    [("KBD-002", 1), ("PRS-001", 1)],
    [("STN-001", 1), ("HUB-001", 1)],
    [("WM-001", 1), ("LMP-001", 1)],
    [("MIC-001", 1), ("ORG-001", 1)],
    [("EAR-001", 1), ("CBL-003", 1)],
    [("BSP-001", 1), ("PRS-001", 1)],
    [("CAM-001", 1), ("ORG-001", 1)],
    [("KBD-002", 1), ("LMP-001", 1)],
    [("STN-001", 1), ("MIC-001", 1)],
    [("HUB-001", 1), ("BSP-001", 1)],
    [("WM-001", 1), ("HUB-001", 1)],
    [("CAM-001", 1), ("CBL-003", 1)],
    [("EAR-001", 1), ("LMP-001", 1)],
    [("KBD-002", 1), ("STN-001", 1)],
]

HIGH_ITEMS: list[list[tuple[str, int]]] = [
    [("CHR-001", 1), ("NBT-001", 1)],
    [("DSK-001", 1), ("HUB-001", 1)],
    [("NCH-001", 1), ("LMP-001", 1)],
    [("SPK-001", 1), ("CBL-003", 1)],
    [("MK-001", 1), ("NCH-001", 1)],
    [("CHR-001", 1), ("ORG-001", 1)],
    [("DSK-001", 1), ("CAM-001", 1)],
    [("SPK-001", 1), ("LMP-001", 1)],
    [("NCH-001", 1), ("EAR-001", 1)],
    [("MK-001", 1), ("CHR-001", 1)],
]

ORDER_ITEM_GROUPS = FIXTURE_ITEMS + CHEAP_ITEMS + MID_ITEMS + HIGH_ITEMS

SNAPSHOT_SKU = "WM-001"
SNAPSHOT_OLD_TITLE = "Wireless Mouse"
SNAPSHOT_NEW_TITLE = "Wireless Mouse Pro"
SNAPSHOT_OLD_PRICE = Decimal("50.16")
SNAPSHOT_NEW_PRICE = Decimal("60.00")


def age_days(index: int) -> int:
    """Deterministic date spread: >60d, <7d and the rest across 90 days."""
    if index <= 4:
        return 62 + index * 6  # 62, 68, 74, 80, 86  -> >60 days old
    if index <= 11:
        return index - 5  # 0..6 -> within the last 7 days
    return 7 + ((index * 7) % 54)  # 7..60


def build_order_specs() -> list[dict]:
    """Assemble the deterministic order plan."""
    specs: list[dict] = []
    for index, items in enumerate(ORDER_ITEM_GROUPS):
        days = age_days(index)
        order_date = NOW - dt.timedelta(
            days=days, hours=(index * 13) % 24, minutes=(index * 17) % 60
        )
        specs.append(
            {
                "index": index,
                "user_id": (index % 8) + 1,
                "status": ORDER_STATUSES[index % len(ORDER_STATUSES)],
                "order_date": order_date,
                "items": items,
            }
        )
    return specs


# =====================================================================
# Writers
# =====================================================================


def _hash_password(password: str) -> str:
    """Hash a password using bcrypt (matches app.core.auth.hash_password)."""
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.hash(password)


def seed_users() -> dict[int, User]:
    session = SessionLocal()
    try:
        session.begin()
        users = {}

        # Seed 8 demo customers with role=CUSTOMER, password = first name lowercase
        for position, (name, email) in enumerate(USERS, start=1):
            first_name = name.split()[0].lower()
            password_hash = _hash_password(first_name)
            user = User(name=name, email=email, password_hash=password_hash, role="CUSTOMER")
            session.add(user)
            session.flush()
            users[position] = user

        # Seed 1 admin user with role=ADMIN, password = "admin"
        admin_password_hash = _hash_password("admin")
        admin_user = User(
            name="Admin",
            email="admin@example.com",
            password_hash=admin_password_hash,
            role="ADMIN",
        )
        session.add(admin_user)
        session.flush()
        users[9] = admin_user  # admin gets id 9

        session.commit()
        return users
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def seed_products() -> dict[str, dict]:
    """Replace the catalog with the product fixtures (MongoDB)."""
    product_repo.delete_all_products()
    product_repo.ensure_indexes()

    inserted: dict[str, dict] = {}
    for offset, fixture in enumerate(PRODUCTS):
        document = dict(fixture)
        document["created_at"] = NOW - dt.timedelta(days=90 - offset)
        document["updated_at"] = document["created_at"]
        inserted[fixture["sku"]] = product_repo.create_product(document)
    return inserted


def seed_orders(products_by_sku: dict[str, dict]) -> list[int]:
    """Insert every planned order inside one explicit transaction."""
    specs = build_order_specs()
    order_ids: list[int] = []

    session = SessionLocal()
    try:
        session.begin()  # BEGIN
        for spec in specs:
            total = Decimal("0.00")
            order = Order(
                order_number=f"TMP-{spec['index']:04d}",
                user_id=spec["user_id"],
                order_date=spec["order_date"],
                status=spec["status"],
                total_amount=Decimal("0.00"),  # replaced below
                created_at=spec["order_date"],
                updated_at=spec["order_date"],
            )
            session.add(order)
            session.flush()
            order.order_number = f"ORD-{order.id:06d}"

            for sku, quantity in spec["items"]:
                product = products_by_sku[sku]
                unit_price = to_money(product["price"])
                total += unit_price * quantity
                session.add(
                    OrderItem(
                        order=order,
                        product_id=str(product["_id"]),
                        title=product["title"],  # snapshot
                        quantity=quantity,
                        unit_price=unit_price,  # snapshot
                    )
                )
            order.total_amount = total.quantize(CENT)
            order_ids.append(order.id)

        session.flush()
        session.commit()  # COMMIT
    except Exception:
        session.rollback()  # ROLLBACK
        raise
    finally:
        session.close()

    return order_ids


def apply_snapshot_demo() -> None:
    """Rename the catalog product AFTER the orders were snapshotted."""
    document = product_repo.get_product_by_sku(SNAPSHOT_SKU)
    if document is None:
        raise RuntimeError(f"snapshot product {SNAPSHOT_SKU} not found")

    product_repo.update_product(
        str(document["_id"]),
        {
            "title": SNAPSHOT_NEW_TITLE,
            "price": float(SNAPSHOT_NEW_PRICE),
            "description": (
                "Upgraded 2.4GHz wireless mouse with silent clicks, 3200 DPI "
                "sensor and 18-month battery life."
            ),
        },
    )
    print(
        f"\n  MongoDB product updated: {SNAPSHOT_OLD_TITLE} (${SNAPSHOT_OLD_PRICE}) "
        f"-> {SNAPSHOT_NEW_TITLE} (${SNAPSHOT_NEW_PRICE})\n"
        "  PostgreSQL order_items and Elasticsearch documents were NOT touched.\n"
    )


# =====================================================================
# Verification
# =====================================================================


def verify(*, expect_search: bool) -> list[str]:
    """Run every acceptance check and return a list of failures."""
    failures: list[str] = []

    def check(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    # ---- PostgreSQL -----------------------------------------------------
    session = SessionLocal()
    try:
        user_count = len(order_repo.list_users(session))
        order_count = order_repo.count_orders(session)
        item_count = order_repo.count_order_items(session)
        status_counts = order_repo.status_counts(session)

        orders = list(order_repo.iter_orders(session))
    finally:
        session.close()

    check(user_count == 9, f"expected 9 users (8 customers + 1 admin), found {user_count}")
    check(order_count >= 40, f"expected >=40 orders, found {order_count}")
    check(item_count >= 80, f"expected >=80 order items, found {item_count}")
    for status in ORDER_STATUSES:
        check(
            status_counts.get(status, 0) >= 10,
            f"expected >=10 {status} orders, found {status_counts.get(status, 0)}",
        )

    dates = [order.order_date for order in orders]
    check(
        sum(1 for d in dates if (NOW - d).days > 60) >= 5,
        "expected >=5 orders older than 60 days",
    )
    check(
        sum(1 for d in dates if (NOW - d).days <= 7) >= 5,
        "expected >=5 orders within the last 7 days",
    )

    totals = [float(order.total_amount) for order in orders]
    check(sum(1 for t in totals if t < 30) >= 5, "expected >=5 orders under $30")
    check(
        sum(1 for t in totals if 30 <= t <= 150) >= 5,
        "expected >=5 orders between $30 and $150",
    )
    check(sum(1 for t in totals if t > 200) >= 5, "expected >=5 orders over $200")

    # every total must equal SUM(quantity * unit_price)
    for order in orders:
        expected = sum(
            (Decimal(str(item.unit_price)) * item.quantity for item in order.items),
            Decimal("0.00"),
        ).quantize(CENT)
        if expected != Decimal(str(order.total_amount)).quantize(CENT):
            failures.append(
                f"order {order.order_number} total mismatch: "
                f"{order.total_amount} != {expected}"
            )

    # per-user coverage
    per_user: dict[int, int] = {}
    wendy_wireless_orders = 0
    for order in orders:
        per_user[order.user_id] = per_user.get(order.user_id, 0) + 1
        titles = [item.title.lower() for item in order.items]
        if order.user_id == 3:
            if any("wireless" in title for title in titles):
                wendy_wireless_orders += 1
    # Check the 8 demo customers (ids 1-8), not the admin (id 9)
    for user_id in range(1, 9):
        check(per_user.get(user_id, 0) >= 2, f"user {user_id} has <2 orders")
    check(per_user.get(3, 0) >= 3, "Wendy Wireless has <3 orders")
    check(
        wendy_wireless_orders >= 1,
        "Wendy Wireless has no order containing a wireless product",
    )

    # search fixtures (snapshots keep the ORIGINAL title)
    def has_title(order: Order, needle: str) -> bool:
        return any(needle.lower() in item.title.lower() for item in order.items)

    wireless_mouse_orders = [o for o in orders if has_title(o, SNAPSHOT_OLD_TITLE)]
    keyboard_orders = [o for o in orders if has_title(o, "Mechanical Keyboard")]
    both_orders = [
        o
        for o in orders
        if has_title(o, SNAPSHOT_OLD_TITLE) and has_title(o, "Mechanical Keyboard")
    ]
    check(len(wireless_mouse_orders) >= 8, f"'{SNAPSHOT_OLD_TITLE}' in {len(wireless_mouse_orders)} orders")
    check(len(keyboard_orders) >= 3, f"'Mechanical Keyboard' in {len(keyboard_orders)} orders")
    check(len(both_orders) >= 2, f"orders with both fixtures: {len(both_orders)}")

    # ---- MongoDB --------------------------------------------------------
    active = product_repo.count_products(visibility="active")
    inactive = product_repo.count_products(visibility="inactive")
    check(active >= 24, f"expected >=24 active products, found {active}")
    check(inactive == 1, f"expected exactly 1 inactive product, found {inactive}")

    facets = product_repo.list_facets()
    for bucket in facets["categories"]:
        check(bucket["count"] >= 5, f"category {bucket['value']} has only {bucket['count']}")
    category_names = {bucket["value"] for bucket in facets["categories"]}
    check(
        category_names >= {"peripherals", "audio", "cables", "office"},
        f"missing categories: { {'peripherals','audio','cables','office'} - category_names }",
    )

    all_docs, _ = product_repo.list_products(visibility="all", page=1, limit=200)
    wireless_products = [
        doc
        for doc in all_docs
        if "wireless" in doc["title"].lower() or "wireless" in [t.lower() for t in doc.get("tags", [])]
    ]
    check(len(wireless_products) >= 6, f"only {len(wireless_products)} 'wireless' products")

    cheap = [d for d in all_docs if d["price"] < 25]
    mid = [d for d in all_docs if 25 <= d["price"] < 100]
    premium = [d for d in all_docs if d["price"] >= 100]
    check(len(cheap) >= 4, f"only {len(cheap)} products under $25")
    check(len(mid) >= 4, f"only {len(mid)} products in $25-$99")
    check(len(premium) >= 4, f"only {len(premium)} products >= $100")

    required_titles = [
        SNAPSHOT_NEW_TITLE,
        "Mechanical Keyboard",
        "Wireless Earbuds",
        "USB-C Hub 7-in-1",
        "Desk Lamp LED",
        "Noise Cancelling Headphones",
    ]
    titles = {doc["title"] for doc in all_docs}
    for required in required_titles:
        check(required in titles, f"required product missing from catalog: {required}")
    check(
        product_repo.get_product_by_sku(SNAPSHOT_SKU) is not None,
        "snapshot product disappeared from the catalog",
    )

    # the snapshot mismatch itself
    pg_snapshot_lines = sum(len(o.items) for o in orders if has_title(o, SNAPSHOT_OLD_TITLE))
    check(pg_snapshot_lines >= 8, "PostgreSQL lost the historical title snapshots")
    catalog_doc = product_repo.get_product_by_sku(SNAPSHOT_SKU)
    if catalog_doc and catalog_doc["title"] == SNAPSHOT_OLD_TITLE:
        failures.append("MongoDB still shows the old title — snapshot demo not applied")

    # ---- Elasticsearch --------------------------------------------------
    if expect_search:
        es_count = count_documents()
        check(
            es_count == order_count,
            f"PostgreSQL orders ({order_count}) != ES documents ({es_count})",
        )

        from app.clients.elasticsearch import get_elasticsearch_client

        response = get_elasticsearch_client().search(
            index=index_name(),
            query={
                "nested": {
                    "path": "items",
                    "query": {"term": {"items.title.keyword": SNAPSHOT_OLD_TITLE}},
                }
            },
            size=100,
        )
        es_total = int(response["hits"]["total"]["value"])
        check(
            es_total == len(wireless_mouse_orders),
            f"ES has {es_total} '{SNAPSHOT_OLD_TITLE}' orders, PostgreSQL has {len(wireless_mouse_orders)}",
        )
        for hit in response["hits"]["hits"]:
            titles_in_doc = [item["title"] for item in hit["_source"]["items"]]
            if SNAPSHOT_NEW_TITLE in titles_in_doc:
                failures.append("Elasticsearch document was rewritten with the new title")

    return failures


# =====================================================================
# Entry point
# =====================================================================


def run(*, skip_search: bool = False) -> None:
    print("\n=== Seeding ===================================================")

    print("  [1/5] PostgreSQL schema")
    drop_tables()
    create_tables()

    print("  [2/5] PostgreSQL users")
    seed_users()

    print("  [3/5] MongoDB product catalog")
    products = seed_products()
    print(f"         {len(products)} products inserted")

    print("  [4/5] PostgreSQL orders (snapshot line items)")
    order_ids = seed_orders(products)
    print(f"         {len(order_ids)} orders inserted")

    if skip_search:
        print("  [5/5] Elasticsearch reindex skipped (--skip-search)")
    else:
        print("  [5/5] Elasticsearch reindex")
        stats = reindex_orders(recreate=True)
        print(
            f"         {stats['indexed']} documents indexed "
            f"({stats['failed']} failed)"
        )

    print("\n  Snapshot demonstration")
    apply_snapshot_demo()

    failures = verify(expect_search=not skip_search)
    if failures:
        print("\n=== Seed verification FAILED ================================\n")
        for failure in failures:
            print(f"  ✗ {failure}")
        raise SystemExit(1)

    print("=== Seed verification PASSED =================================")
    print(f"  users                9 (8 customers + 1 admin)")
    print(f"  products (active)    {product_repo.count_products(visibility='active')}")
    print(f"  products (inactive)  {product_repo.count_products(visibility='inactive')}")
    session = SessionLocal()
    try:
        print(f"  orders               {order_repo.count_orders(session)}")
        print(f"  order_items          {order_repo.count_order_items(session)}")
        print(f"  status counts        {order_repo.status_counts(session)}")
    finally:
        session.close()
    if not skip_search:
        print(f"  ES documents         {count_documents()}")
    print("===============================================================\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-search", action="store_true", help="Do not touch Elasticsearch")
    parser.add_argument(
        "--verify-only", action="store_true", help="Only run the acceptance checks"
    )
    args = parser.parse_args(argv)

    configure_logging("INFO")
    logger.info("seed starting (mongo db=%s, index=%s)", settings.mongo_db, index_name())

    if args.verify_only:
        failures = verify(expect_search=not args.skip_search)
        if failures:
            print("Verification FAILED:")
            for failure in failures:
                print(f"  ✗ {failure}")
            return 1
        print("Verification PASSED")
        return 0

    run(skip_search=args.skip_search)
    return 0


if __name__ == "__main__":
    sys.exit(main())
