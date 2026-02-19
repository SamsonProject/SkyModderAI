"""
Seed Script for Shopping Marketplace

Creates sample products for testing the shopping feature.
Run: python migrations/seed_products.py
"""

import os
import sys
import uuid

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_db
from flask import Flask

# Create minimal Flask app for db context
app = Flask(__name__)
app.config.from_object('config.Config')


def seed_products():
    """Seed sample products."""
    print("Starting product seeding...")
    
    with app.app_context():
        db = get_db()
        
        # First, check if we have any businesses
        businesses = db.execute("SELECT id, name FROM businesses WHERE status = 'active' OR status = 'pending'").fetchall()
        
        if not businesses:
            print("⚠️  No businesses found. Please create businesses first.")
            print("   Run: python migrations/add_business_tables.py")
            return
        
        # Create a default business if needed
        default_business = None
        for biz in businesses:
            default_business = biz
            break
        
        if not default_business:
            print("❌ No active businesses available for seeding")
            return
        
        print(f"Using business: {default_business['name']} ({default_business['id']})")
        
        # Sample products
        sample_products = [
            {
                "name": "Dragon Scale Gaming Mouse Pad",
                "description": "Extra-large gaming mouse pad featuring iconic Dragon Scale armor design from Skyrim. Non-slip rubber base, smooth cloth surface for precise tracking.",
                "price": 29.99,
                "image_url": "https://images.unsplash.com/photo-1615663245857-acda5b0c4e02?w=400",
                "category": "hardware",
                "stock": 50,
            },
            {
                "name": "Mod Organizer Pro Setup Guide",
                "description": "Comprehensive digital guide for setting up Mod Organizer 2 with SkyModderAI. Includes video tutorials, troubleshooting tips, and best practices.",
                "price": 9.99,
                "image_url": "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?w=400",
                "category": "digital",
                "stock": 999,
            },
            {
                "name": "Skyrim Map Poster - Premium",
                "description": "High-quality 24x36 inch poster of Tamriel's Skyrim map. Perfect for planning your modded playthroughs. Printed on premium matte paper.",
                "price": 24.99,
                "image_url": "https://images.unsplash.com/photo-1572536147248-ac59a8abfa47?w=400",
                "category": "apparel",
                "stock": 30,
            },
            {
                "name": "Custom ENB Preset Configuration",
                "description": "Professional ENB preset configuration service. Optimized for performance and visual fidelity. Includes 30-day support and adjustments.",
                "price": 49.99,
                "image_url": "https://images.unsplash.com/photo-1538481199705-c710c4e965fc?w=400",
                "category": "digital",
                "stock": 10,
            },
            {
                "name": "Modding Tools Starter Kit",
                "description": "Physical USB drive with essential modding tools, documentation, and quick-start guides. Perfect for beginners getting into modding.",
                "price": 34.99,
                "image_url": "https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?w=400",
                "category": "hardware",
                "stock": 25,
            },
            {
                "name": "Gaming Headset Stand - Dragonborn Edition",
                "description": "Aluminum headset stand with RGB lighting. Features Dragonborn runes and sturdy base. Fits all gaming headset sizes.",
                "price": 44.99,
                "image_url": "https://images.unsplash.com/photo-1612739777429-1b2f78f5b5b7?w=400",
                "category": "hardware",
                "stock": 20,
            },
            {
                "name": "Custom Mod List Consultation",
                "description": "1-hour video consultation for building your perfect mod list. Expert advice on compatibility, load order, and performance optimization.",
                "price": 79.99,
                "image_url": "https://images.unsplash.com/photo-1573497019940-1c28c88b4f3e?w=400",
                "category": "digital",
                "stock": 5,
            },
            {
                "name": "SkyModderAI T-Shirt",
                "description": "Premium cotton t-shirt with SkyModderAI logo. Available in sizes S-XXL. Comfortable fit for long gaming sessions.",
                "price": 27.99,
                "image_url": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400",
                "category": "apparel",
                "stock": 100,
            },
            {
                "name": "Wabbajack Modlist Backup Service",
                "description": "Cloud backup service for your Wabbajack modlists. Never lose your configuration again. Includes version history and easy restore.",
                "price": 4.99,
                "image_url": "https://images.unsplash.com/photo-1558494949-ef526b0042a0?w=400",
                "category": "digital",
                "stock": 999,
            },
            {
                "name": "Mechanical Keyboard - Modder Switch",
                "description": "Custom mechanical keyboard with hot-swappable switches. Perfect for modders and gamers. RGB backlighting, programmable macros.",
                "price": 129.99,
                "image_url": "https://images.unsplash.com/photo-1595225476474-87563907a212?w=400",
                "category": "hardware",
                "stock": 15,
            },
        ]
        
        inserted = 0
        for product in sample_products:
            try:
                db.execute(
                    """
                    INSERT INTO products (business_id, name, description, price, image_url, category, stock, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, TRUE)
                """,
                    (
                        default_business['id'],
                        product['name'],
                        product['description'],
                        product['price'],
                        product['image_url'],
                        product['category'],
                        product['stock'],
                    ),
                )
                inserted += 1
            except Exception as e:
                print(f"⚠️  Error inserting '{product['name']}': {e}")
        
        db.commit()
        
        print(f"\n✅ Seeded {inserted} products successfully!")
        print("\nProducts added:")
        for p in sample_products[:inserted]:
            print(f"  - {p['name']} (${p['price']})")


if __name__ == "__main__":
    seed_products()
