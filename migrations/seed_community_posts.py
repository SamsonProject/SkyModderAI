"""
Seed Script for Community Posts

Creates sample community posts to make the community feel alive.
Run: python migrations/seed_community_posts.py
"""

import os
import sys
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask

from db import get_db

# Create minimal Flask app for db context
app = Flask(__name__)
app.config.from_object("config.Config")


def seed_community_posts():
    """Seed sample community posts."""
    print("Starting community posts seeding...")

    with app.app_context():
        db = get_db()

        # Sample posts - mix of questions, tips, and showcases
        sample_posts = [
            {
                "email": "robert.realpersono@example.com",
                "content": "Just hit 300+ mods on my Skyrim SE playthrough with zero crashes! 🎉 Key tips:\n\n1. Use LOOT religiously\n2. Read mod descriptions THOROUGHLY\n3. Test in batches of 20-30 mods\n4. SkyModderAI's conflict detection is a lifesaver\n\nHappy to share my load order if anyone wants it. Running on a 3080 Ti with 32GB RAM.",
                "tag": "showcase",
            },
            {
                "email": "modder.mike@example.com",
                "content": "PSA: If you're using ENB with Skyrim SE 1.6.640+, make sure to update your enbseries.dll! Older versions can cause CTDs when entering certain areas. Updated to 0.540 and butter smooth now.\n\nAlso, huge thanks to the SkyModderAI team for the free tools. This community is amazing! ❤️",
                "tag": "tips",
            },
            {
                "email": "newbie.nancy@example.com",
                "content": "First time modder here! 👋 Just installed Skyrim SE and I'm overwhelmed by the modding options.\n\nWhere should I start? My main interests are:\n- Better graphics (but still vanilla-ish)\n- Quality of life improvements\n- Maybe some new quests?\n\nBudget is tight so looking for free mods. Thanks in advance!",
                "tag": "help",
            },
            {
                "email": "veteran.victor@example.com",
                "content": "After 12 years of modding Bethesda games, here's my hot take: Mod Organizer 2 > Vortex for power users.\n\nWhy?\n- Portable installs\n- Profile switching\n- Better conflict visualization\n- Doesn't touch game registry\n\nThat said, Vortex is great for beginners. Use what works for you! What's your preference?",
                "tag": "discussion",
            },
            {
                "email": "tech.tina@example.com",
                "content": "Performance tip of the day: If you're getting stutter in cities, try these:\n\n1. Reduce shadow resolution\n2. Use SSE Display Tweaks\n3. Disable VSync in-game, use RTSS instead\n4. Check your SKSE plugins\n\nWent from 45fps to stable 60fps in Whiterun with these tweaks. System: 5800X3D + 6800XT",
                "tag": "tips",
            },
            {
                "email": "quest.quinn@example.com",
                "content": "Just finished the Enderal playthrough and WOW. 😭\n\nIf you haven't played this total conversion mod, you're missing out on one of the best RPG experiences ever made. Better writing than the base game, incredible voice acting, and a story that actually matters.\n\nNo spoilers, but that ending... *chef's kiss*\n\n10/10 would cry again.",
                "tag": "discussion",
            },
            {
                "email": "builder.bob@example.com",
                "content": 'Released my first mod! 🎊\n\n"Immersive Campfires Enhanced" adds 50+ new campfire locations with unique setups across Skyrim. Each location has:\n- Custom placed logs and stones\n- Cooking pot variants\n- Optional lanterns\n- No navmesh edits\n\nLink in my profile. Let me know what you think! Special thanks to SkyModderAI for the conflict checking tools.',
                "tag": "showcase",
            },
            {
                "email": "help.helen@example.com",
                "content": 'Getting a weird error with Nemesis Unlimited Behavior Engine. Keep getting "Error: File not found - animations\\0behavior.hkx"\n\nTried:\n✓ Running as admin\n✓ Verifying game files\n✓ Reinstalling Nemesis\n\nUsing MO2 if that matters. Any ideas? This is driving me crazy! 😫',
                "tag": "help",
            },
            {
                "email": "deals.dave@example.com",
                "content": "PSA: Nexus Mods Premium is 25% off this weekend! 💰\n\nJust grabbed lifetime premium for $60. Worth it for:\n- Fast downloads\n- No ads\n- Early access to new features\n- Supporting the platform\n\nNot sponsored, just a happy customer. What do you all think - premium worth it?",
                "tag": "discussion",
            },
            {
                "email": "artist.anna@example.com",
                "content": "Screenshot Saturday! 📸\n\nSpent 200+ hours on this photomode build. Every screenshot is with ENB, no filters. Mod list in comments.\n\n[Image: Dragon Priest mask collection displayed in player home]\n\nMods used:\n- JK's Skyrim\n- Lux\n- Static Mesh Improvements\n- Skyland AIO\n- And 247 more... 😅",
                "tag": "showcase",
            },
        ]

        # Check if we have users
        test_users = db.execute("SELECT email FROM users LIMIT 5").fetchall()

        if not test_users:
            print("⚠️  No users found. Creating test user accounts first...")
            # Create test users
            test_emails = [
                "robert.realpersono@example.com",
                "modder.mike@example.com",
                "newbie.nancy@example.com",
                "veteran.victor@example.com",
                "tech.tina@example.com",
                "quest.quinn@example.com",
                "builder.bob@example.com",
                "help.helen@example.com",
                "deals.dave@example.com",
                "artist.anna@example.com",
            ]

            for email in test_emails:
                try:
                    db.execute(
                        """
                        INSERT OR IGNORE INTO users (email, tier, email_verified, password_hash, created_at)
                        VALUES (?, 'free', 1, '', ?)
                    """,
                        (email, datetime.now(timezone.utc)),
                    )
                except Exception as e:
                    print(f"⚠️  Error creating user {email}: {e}")

            db.commit()
            print(f"✅ Created {len(test_emails)} test users")

        # Insert posts
        inserted = 0
        for post in sample_posts:
            try:
                db.execute(
                    """
                    INSERT INTO community_posts (user_email, content, tag, created_at, moderated)
                    VALUES (?, ?, ?, ?, 0)
                """,
                    (
                        post["email"],
                        post["content"],
                        post["tag"],
                        datetime.now(timezone.utc),
                    ),
                )
                inserted += 1
            except Exception as e:
                print(f"⚠️  Error inserting post: {e}")

        db.commit()

        print(f"\n✅ Seeded {inserted} community posts successfully!")
        print("\nPosts added:")
        for i, p in enumerate(sample_posts[:inserted], 1):
            preview = p["content"][:60].replace("\n", " ")
            print(f"  {i}. [{p['tag']}] {preview}...")

        print("\n💡 Tip: Posts are unmoderated. Review in admin panel before publishing.")


if __name__ == "__main__":
    seed_community_posts()
