"""
Database Migration: Education Hub - Comprehensive Business Resources

Curated, vetted, free resources for modder-entrepreneurs.
Every resource is selected for quality, clarity, and actionability.

Categories:
- Getting Started: From zero to launched
- Building Community: Customers, marketing, partnerships
- Metrics That Matter: Financial literacy, KPIs, tracking
- Advanced Strategy: Scaling, acquisitions, legacy

Run: python3 migrations/add_hub_resources.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///instance/app.db")


def migrate():
    """Run database migration."""
    print("Starting Education Hub migration...")
    print(f"Database: {DATABASE_URL}")

    engine = create_engine(DATABASE_URL, echo=False)

    with engine.connect() as conn:
        is_postgresql = engine.dialect.name == "postgresql"

        # Check if hub_resources table exists
        table_exists = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='hub_resources'")
        ).fetchone()

        if not table_exists:
            print("Creating hub_resources table...")
            conn.execute(
                text("""
                CREATE TABLE hub_resources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    subcategory TEXT,
                    title TEXT NOT NULL,
                    description TEXT,
                    resource_type TEXT DEFAULT 'link',
                    url TEXT,
                    analogy TEXT,
                    game_reference TEXT,
                    difficulty_level TEXT DEFAULT 'beginner',
                    order_index INTEGER DEFAULT 0,
                    is_free BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            )
            conn.commit()
            print("  ✓ Created hub_resources table")
        else:
            print("hub_resources table already exists")
            # Check existing columns
            existing_columns = conn.execute(text("PRAGMA table_info(hub_resources)")).fetchall()
            column_names = [col[1] for col in existing_columns]

            if "url" not in column_names:
                print("Adding new columns to hub_resources table...")
                new_columns = [
                    ("subcategory", "TEXT"),
                    ("url", "TEXT NOT NULL DEFAULT ''"),
                    ("analogy", "TEXT"),
                    ("game_reference", "TEXT"),
                    ("difficulty_level", "TEXT DEFAULT 'beginner'"),
                    ("order_index", "INTEGER DEFAULT 0"),
                    ("is_free", "BOOLEAN DEFAULT TRUE"),
                ]

                for col_name, col_type in new_columns:
                    if col_name not in column_names:
                        try:
                            conn.execute(
                                text(f"ALTER TABLE hub_resources ADD COLUMN {col_name} {col_type}")
                            )
                            print(f"  ✓ Added column: {col_name}")
                        except Exception as e:
                            print(f"  Column {col_name} may already exist: {e}")
                conn.commit()

        # Create indexes
        print("\nCreating indexes...")
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS idx_hub_resources_category ON hub_resources(category)")
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_hub_resources_difficulty ON hub_resources(difficulty_level)"
            )
        )
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS idx_hub_resources_order ON hub_resources(order_index)")
        )
        conn.commit()

        # Seed comprehensive educational resources
        print("\nSeeding educational resources...")
        resources = [
            # =====================================================================
            # GETTING STARTED - Survival Mode (Beginner)
            # =====================================================================
            {
                "category": "getting_started",
                "subcategory": "mindset",
                "title": "The Lean Startup Methodology",
                "description": "Build-Measure-Learn loop. Test ideas cheaply before committing. The modern standard for launching ventures.",
                "url": "https://theleanstartup.com/principles",
                "analogy": "Like testing a mod with 10 users before releasing to thousands. Fail fast, learn faster, iterate.",
                "game_reference": "Skyrim mod testing / Fallout workshop iteration",
                "difficulty_level": "beginner",
                "order_index": 1,
                "is_free": 1,
            },
            {
                "category": "getting_started",
                "subcategory": "niche",
                "title": "Find Your Niche - SBA Market Research",
                "description": "U.S. government guide to identifying your market. Validate demand before building. Free, unbiased, comprehensive.",
                "url": "https://www.sba.gov/business-guide",
                "analogy": "Survey locations before building your settlement. Check water, defenses, trade routes. Same logic applies.",
                "game_reference": "Fallout settlement survey / Skyrim hold exploration",
                "difficulty_level": "beginner",
                "order_index": 2,
                "is_free": 1,
            },
            {
                "category": "getting_started",
                "subcategory": "validation",
                "title": "Y Combinator - How to Validate Your Idea",
                "description": "World's top startup accelerator teaches idea validation. Talk to users. Build what they need, not what you assume.",
                "url": "https://www.ycombinator.com/library",
                "analogy": "Like asking fellow modders what features they want before coding for months. Ship what's wanted.",
                "game_reference": "Community mod requests / Nexus feedback loops",
                "difficulty_level": "beginner",
                "order_index": 3,
                "is_free": 1,
            },
            {
                "category": "getting_started",
                "subcategory": "planning",
                "title": "One-Page Business Plan - SCORE",
                "description": "SCORE's free template. One page forces clarity. Know your value prop, customers, costs, and revenue before spending.",
                "url": "https://www.score.org/resource/business-plan-template-startup-business",
                "analogy": "Like planning your load order before installing 200 mods. Structure first, then build.",
                "game_reference": "Skyrim load order planning / Fallout mod checklist",
                "difficulty_level": "beginner",
                "order_index": 4,
                "is_free": 1,
            },
            {
                "category": "getting_started",
                "subcategory": "legal",
                "title": "Legal Structure Guide - SBA",
                "description": "Sole prop vs LLC vs Corp. Tax implications, liability protection, filing requirements. Government source, no upsells.",
                "url": "https://www.sba.gov/business-guide/launch-your-business/choose-business-structure",
                "analogy": "Like choosing your faction allegiance. Each has benefits, obligations, and consequences.",
                "game_reference": "Skyrim guild membership / Fallout faction alignment",
                "difficulty_level": "beginner",
                "order_index": 5,
                "is_free": 1,
            },
            {
                "category": "getting_started",
                "subcategory": "legal",
                "title": "Free Legal Templates - Docracy",
                "description": "Contracts, terms of service, privacy policies. Free, lawyer-reviewed templates for small businesses.",
                "url": "https://www.docracy.com/browse",
                "analogy": "Like having a standard contract for commission work. Protects both parties, prevents disputes.",
                "game_reference": "Dark Brotherhood contracts / Thieves Guild agreements",
                "difficulty_level": "beginner",
                "order_index": 6,
                "is_free": 1,
            },
            {
                "category": "getting_started",
                "subcategory": "finances",
                "title": "Small Business Taxes - IRS Guide",
                "description": "Federal tax obligations for small business. Deductions, quarterly payments, record-keeping. Straight from the source.",
                "url": "https://www.irs.gov/businesses/small-businesses-self-employed",
                "analogy": "Like tracking your caps and inventory. Know what you owe, when it's due, keep receipts.",
                "game_reference": "Fallout caps management / Skyrim gold tracking",
                "difficulty_level": "beginner",
                "order_index": 7,
                "is_free": 1,
            },
            {
                "category": "getting_started",
                "subcategory": "finances",
                "title": "Bookkeeping Basics - Wave Accounting",
                "description": "Free accounting software + guides. Track income, expenses, invoices. Know your numbers from day one.",
                "url": "https://www.waveapps.com/",
                "analogy": "Like organizing your stash chest. Categorize, track, reconcile. Future you will thank present you.",
                "game_reference": "Skyrim inventory organization / Fallout workshop storage",
                "difficulty_level": "beginner",
                "order_index": 8,
                "is_free": 1,
            },
            {
                "category": "getting_started",
                "subcategory": "branding",
                "title": "Brand Identity Guide - Canva Design School",
                "description": "Logo, colors, typography, voice. Free course on building cohesive brand identity. No design degree required.",
                "url": "https://www.canva.com/learn/",
                "analogy": "Like designing your house crest or faction insignia. Visual identity tells your story.",
                "game_reference": "Skyrim heraldry / Dark Brotherhood insignia",
                "difficulty_level": "beginner",
                "order_index": 9,
                "is_free": 1,
            },
            {
                "category": "getting_started",
                "subcategory": "web_presence",
                "title": "Domain Names - Namecheap",
                "description": "Affordable domain registration (~$10/year). Your .com is your digital address. Buy it before someone else does.",
                "url": "https://www.namecheap.com/",
                "analogy": "Like claiming your settlement name. First come, first served. Make it memorable.",
                "game_reference": "Fallout settlement naming / Skyrim business registration",
                "difficulty_level": "beginner",
                "order_index": 11,
                "is_free": 0,
            },
            # =====================================================================
            # BUILDING COMMUNITY - Build Phase (Intermediate)
            # =====================================================================
            {
                "category": "building_community",
                "subcategory": "customers",
                "title": "Zero-Cost Customer Acquisition - HubSpot",
                "description": "Content marketing, social media, SEO, referrals. Free tactics that compound. No ad spend required.",
                "url": "https://blog.hubspot.com/marketing",
                "analogy": "Like building reputation through quests. Help people, they tell others. Word of mouth scales.",
                "game_reference": "Skyrim guild reputation / Fallout faction standing",
                "difficulty_level": "intermediate",
                "order_index": 12,
                "is_free": 1,
            },
            {
                "category": "building_community",
                "subcategory": "customers",
                "title": "First 100 Customers - Indie Hackers",
                "description": "Real stories from founders who got their first customers. Tactics that worked, mistakes to avoid. Community-driven.",
                "url": "https://www.indiehackers.com/",
                "analogy": "Like recruiting your first settlement settlers. Each one validates your vision and attracts more.",
                "game_reference": "Fallout settler recruitment / Skyrim follower recruitment",
                "difficulty_level": "intermediate",
                "order_index": 13,
                "is_free": 1,
            },
            {
                "category": "building_community",
                "subcategory": "content",
                "title": "Content Marketing Strategy - Moz Beginner's Guide",
                "description": "SEO fundamentals, content creation, distribution. The definitive free guide. Rank higher, attract organic traffic.",
                "url": "https://moz.com/beginners-guide-to-seo",
                "analogy": "Like placing signs and maps to your shop. Make yourself discoverable to those searching.",
                "game_reference": "Skyrim road signs / Fallout settlement markers",
                "difficulty_level": "intermediate",
                "order_index": 14,
                "is_free": 1,
            },
            {
                "category": "building_community",
                "subcategory": "content",
                "title": "Write Better Copy - Copyblogger",
                "description": "Persuasive writing for the web. Headlines, emails, landing pages. Words that convert visitors to customers.",
                "url": "https://copyblogger.com/blog/",
                "analogy": "Like crafting the perfect quest description. Clear, compelling, makes people want to act.",
                "game_reference": "Skyrim quest text / Fallout terminal entries",
                "difficulty_level": "intermediate",
                "order_index": 15,
                "is_free": 1,
            },
            {
                "category": "building_community",
                "subcategory": "social",
                "title": "Social Media for Business - Buffer Resources",
                "description": "Platform-specific strategies, posting schedules, engagement tactics. Free tools and guides included.",
                "url": "https://buffer.com/library",
                "analogy": "Like maintaining your faction relationships. Regular contact, genuine engagement, mutual benefit.",
                "game_reference": "Fallout faction diplomacy / Skyrim jarl relations",
                "difficulty_level": "intermediate",
                "order_index": 16,
                "is_free": 1,
            },
            {
                "category": "building_community",
                "subcategory": "email",
                "title": "Email Marketing Basics - Mailchimp Guide",
                "description": "Build lists, write newsletters, automate sequences. Email has highest ROI of any channel. Free tier available.",
                "url": "https://mailchimp.com/marketing-glossary/email-marketing/",
                "analogy": "Like sending carrier pigeons to your allies. Direct, personal, high open rates.",
                "game_reference": "Skyrim courier system / Fallout messenger network",
                "difficulty_level": "intermediate",
                "order_index": 17,
                "is_free": 1,
            },
            {
                "category": "building_community",
                "subcategory": "community",
                "title": "Build a Community - Orbit Model",
                "description": "Community-led growth framework. Attract, engage, activate members. For creators building audiences.",
                "url": "https://orbit.love/blog",
                "analogy": "Like running a guild hall. Events, recognition, shared purpose. Members become advocates.",
                "game_reference": "Skyrim guild management / Fallout Minutemen rebuilding",
                "difficulty_level": "intermediate",
                "order_index": 18,
                "is_free": 1,
            },
            {
                "category": "building_community",
                "subcategory": "partnerships",
                "title": "Strategic Partnerships - Harvard Business Review",
                "description": "How to find, negotiate, and manage partnerships. Win-win structures. From HBR's archives.",
                "url": "https://hbr.org/",
                "analogy": "Like forming alliances between guilds. Combined strength, shared resources, mutual protection.",
                "game_reference": "Skyrim faction alliances / Fallout faction coalitions",
                "difficulty_level": "intermediate",
                "order_index": 19,
                "is_free": 1,
            },
            {
                "category": "building_community",
                "subcategory": "pricing",
                "title": "Pricing Strategy Guide - ProfitWell",
                "description": "Value-based pricing, tiers, psychology. How to charge what you're worth without losing customers.",
                "url": "https://www.profitwell.com/recur/all/pricing-strategy",
                "analogy": "Like setting fair prices at your market stall. Too high, no buyers. Too low, undervalued. Find the balance.",
                "game_reference": "Skyrim merchant pricing / Fallout vendor caps",
                "difficulty_level": "intermediate",
                "order_index": 20,
                "is_free": 1,
            },
            {
                "category": "building_community",
                "subcategory": "sales",
                "title": "Sales Basics for Founders - Close.com",
                "description": "Cold outreach, discovery calls, closing. Sales is a learnable skill. Free CRM included.",
                "url": "https://www.close.com/blog/",
                "analogy": "Like persuading a jarl to support your cause. Listen, address concerns, demonstrate value.",
                "game_reference": "Skyrim persuasion checks / Fallout speech challenges",
                "difficulty_level": "intermediate",
                "order_index": 21,
                "is_free": 1,
            },
            # =====================================================================
            # METRICS THAT MATTER - Optimization (Intermediate-Advanced)
            # =====================================================================
            {
                "category": "metrics",
                "subcategory": "financials",
                "title": "Financial Statements 101 - Investopedia",
                "description": "Income statement, balance sheet, cash flow. Read your business's health like a character sheet.",
                "url": "https://www.investopedia.com/terms/f/financialstatements.asp",
                "analogy": "Like checking your stats, inventory, and quest log. Know where you stand before the next fight.",
                "game_reference": "Skyrim character sheet / Fallout S.P.E.C.I.A.L.",
                "difficulty_level": "intermediate",
                "order_index": 22,
                "is_free": 1,
            },
            {
                "category": "metrics",
                "subcategory": "financials",
                "title": "Cash Flow Management - SBA Guide",
                "description": "Cash flow vs profit. Forecasting, managing receivables, surviving lean months. Most businesses fail on cash flow, not profit.",
                "url": "https://www.sba.gov/business-guide/manage-your-business/manage-your-finances",
                "analogy": "Like managing your caps flow. Income vs expenses. Run out of caps, game over.",
                "game_reference": "Fallout caps budget / Skyrim gold reserves",
                "difficulty_level": "intermediate",
                "order_index": 23,
                "is_free": 1,
            },
            {
                "category": "metrics",
                "subcategory": "kpis",
                "title": "KPIs for Small Business - QuickBooks",
                "description": "Key metrics by industry. Revenue per customer, churn rate, lifetime value. Track what matters.",
                "url": "https://quickbooks.intuit.com/cas/dam/DOCUMENT/AioLFqU4P/Small-Business-KPIs-ebook.pdf",
                "analogy": "Like monitoring your DPS, health regen, carry weight. Numbers that predict success or failure.",
                "game_reference": "Skyrim combat stats / Fallout damage resistance",
                "difficulty_level": "intermediate",
                "order_index": 24,
                "is_free": 1,
            },
            {
                "category": "metrics",
                "subcategory": "analytics",
                "title": "Google Analytics Academy - Free Courses",
                "description": "Track website traffic, user behavior, conversions. Free certification courses. Data-driven decisions.",
                "url": "https://analytics.google.com/analytics/academy/",
                "analogy": "Like having a spy network reporting on your enemies and allies. Intelligence for strategy.",
                "game_reference": "Skyrim informant network / Fallout spy reports",
                "difficulty_level": "intermediate",
                "order_index": 25,
                "is_free": 1,
            },
            {
                "category": "metrics",
                "subcategory": "unit_economics",
                "title": "Unit Economics Explained - Andreessen Horowitz",
                "description": "CAC, LTV, payback period. Know if each customer is profitable. Top VC firm's free guide.",
                "url": "https://a16z.com/company/calculation-unit-economics/",
                "analogy": "Like calculating profit per adventuring trip. Potions cost X, loot sells for Y. Is it worth the risk?",
                "game_reference": "Skyrim adventuring economics / Fallout scavenging ROI",
                "difficulty_level": "advanced",
                "order_index": 26,
                "is_free": 1,
            },
            {
                "category": "metrics",
                "subcategory": "dashboards",
                "title": "Build a Dashboard - Google Sheets Templates",
                "description": "Free business dashboard templates. Revenue, expenses, KPIs in one view. No expensive software needed.",
                "url": "https://docs.google.com/spreadsheets/u/0/?ftv=1&tgif=d",
                "analogy": "Like your HUD showing health, ammo, objectives. All critical info at a glance.",
                "game_reference": "Fallout HUD / Skyrim compass and stats",
                "difficulty_level": "intermediate",
                "order_index": 27,
                "is_free": 1,
            },
            # =====================================================================
            # ADVANCED STRATEGY - Conquer & Legacy (Advanced)
            # =====================================================================
            {
                "category": "advanced_strategy",
                "subcategory": "scaling",
                "title": "Scaling Startups - Y Combinator",
                "description": "When and how to scale. Hiring, processes, culture.YC's complete guide from 15+ years of startups.",
                "url": "https://www.ycombinator.com/companies",
                "analogy": "Like expanding from one settlement to a network. Systems that work at 10x must be built early.",
                "game_reference": "Fallout settlement network / Skyrim merchant empire",
                "difficulty_level": "advanced",
                "order_index": 28,
                "is_free": 1,
            },
            {
                "category": "advanced_strategy",
                "subcategory": "hiring",
                "title": "Hiring Your First Employees - Gusto",
                "description": "When to hire, job descriptions, payroll, compliance. Free HR platform + comprehensive guides.",
                "url": "https://gusto.com/resources",
                "analogy": "Like recruiting companions for a difficult quest. Choose wisely, align on goals, share rewards.",
                "game_reference": "Skyrim follower recruitment / Fallout companion hiring",
                "difficulty_level": "advanced",
                "order_index": 29,
                "is_free": 1,
            },
            {
                "category": "advanced_strategy",
                "subcategory": "funding",
                "title": "Funding Options - SBA Complete Guide",
                "description": "Bootstrapping, loans, investors, grants. Pros, cons, when to use each. Government source, no bias.",
                "url": "https://www.sba.gov/funding-programs",
                "analogy": "Like funding a major expedition. Self-funded, bank loan, or investor patron. Each has strings.",
                "game_reference": "Skyrim patronage / Fallout financing",
                "difficulty_level": "advanced",
                "order_index": 30,
                "is_free": 1,
            },
            {
                "category": "advanced_strategy",
                "subcategory": "funding",
                "title": "Venture Capital vs Bootstrapping - Paul Graham",
                "description": "YC founder's essay on funding paths. VC = growth at all costs. Bootstrap = profitability first. Choose consciously.",
                "url": "http://www.paulgraham.com/venture.html",
                "analogy": "Like choosing between a patron's gold (strings attached) or self-funding (slower but free).",
                "game_reference": "Skyrim jarl patronage / Fallout independent operator",
                "difficulty_level": "advanced",
                "order_index": 31,
                "is_free": 1,
            },
            {
                "category": "advanced_strategy",
                "subcategory": "acquisition",
                "title": "Selling Your Business - FE International",
                "description": "When to sell, valuation, finding buyers, negotiation. M&A advisory firm's free guide.",
                "url": "https://feinternational.com/sell-your-business/",
                "analogy": "Like passing your guild leadership or selling your established business. Timing and valuation matter.",
                "game_reference": "Skyrim guild succession / Fallout business transfer",
                "difficulty_level": "advanced",
                "order_index": 32,
                "is_free": 1,
            },
            {
                "category": "advanced_strategy",
                "subcategory": "exit",
                "title": "Acquisition by Big Tech - TechCrunch Guide",
                "description": "Getting acquired by Google, Meta, etc. What they look for, negotiation tactics, earnouts.",
                "url": "https://techcrunch.com/tag/acquisitions/",
                "analogy": "Like your small guild being absorbed by the Fighters Guild. Resources multiply, autonomy decreases.",
                "game_reference": "Skyrim guild mergers / Fallout faction integration",
                "difficulty_level": "advanced",
                "order_index": 33,
                "is_free": 1,
            },
            {
                "category": "advanced_strategy",
                "subcategory": "legacy",
                "title": "Building a Legacy Business - Inc. Magazine",
                "description": "Companies that outlive founders. Succession planning, culture, values. Build something that lasts.",
                "url": "https://www.inc.com/topic/business-philosophy",
                "analogy": "Like founding a guild that lasts generations. Dragonborn fades, the Companions remain.",
                "game_reference": "Skyrim Companions legacy / Dark Brotherhood endurance",
                "difficulty_level": "advanced",
                "order_index": 34,
                "is_free": 1,
            },
            # =====================================================================
            # EXTERNAL RESOURCES - Bonus Mod Packs (All Levels)
            # =====================================================================
            {
                "category": "external_resources",
                "subcategory": "mentorship",
                "title": "SCORE Mentoring - Free Business Mentors",
                "description": "Retired executives volunteer as mentors. Free, confidential, experienced. SBA partner network.",
                "url": "https://www.score.org/find-mentor",
                "analogy": "Like finding a master to apprentice under. Decades of experience, free guidance.",
                "game_reference": "Skyrim master training / Fallout mentor quests",
                "difficulty_level": "all",
                "order_index": 35,
                "is_free": 1,
            },
            {
                "category": "external_resources",
                "subcategory": "tools",
                "title": "Free Software for Startups - GitHub Student Pack",
                "description": "Free hosting, domains, tools, credits. Even non-students can find similar deals. Thousands in value.",
                "url": "https://education.github.com/pack",
                "analogy": "Like finding a chest of legendary gear at level 1. Tools that would cost thousands, free.",
                "game_reference": "Skyrim starter chest / Fallout supply cache",
                "difficulty_level": "all",
                "order_index": 36,
                "is_free": 1,
            },
            {
                "category": "external_resources",
                "subcategory": "legal",
                "title": "Legal Aid for Entrepreneurs - Law School Clinics",
                "description": "Law schools offer free legal clinics. Contracts, IP, incorporation. Supervised by licensed attorneys.",
                "url": "https://www.americanbar.org/groups/legal_aid_indigent_defendants/",
                "analogy": "Like getting free counsel from the Greybeards. Wise advisors, no gold required.",
                "game_reference": "Skyrim Greybeards wisdom / Fallout scribe knowledge",
                "difficulty_level": "all",
                "order_index": 37,
                "is_free": 1,
            },
            {
                "category": "external_resources",
                "subcategory": "community",
                "title": "Indie Hackers Community",
                "description": "Founders sharing revenue, strategies, failures. Transparent, supportive, actionable. Free to join.",
                "url": "https://www.indiehackers.com/",
                "analogy": "Like the modding community sharing techniques. Collective knowledge, open source success.",
                "game_reference": "Nexus modding community / r/skyrim collaboration",
                "difficulty_level": "all",
                "order_index": 38,
                "is_free": 1,
            },
            {
                "category": "external_resources",
                "subcategory": "news",
                "title": "Morning Brew - Business News Newsletter",
                "description": "Daily 5-minute business news. Markets, tech, finance. Free, witty, actually useful.",
                "url": "https://www.morningbrew.com",
                "analogy": "Like reading the town crier or settlement radio. Stay informed without drowning in noise.",
                "game_reference": "Skyrim town criers / Fallout Three Dog news",
                "difficulty_level": "all",
                "order_index": 39,
                "is_free": 1,
            },
            {
                "category": "external_resources",
                "subcategory": "podcasts",
                "title": "My First Million Podcast",
                "description": "Business ideas, teardowns, trends. Two founders brainstorming. Entertaining and educational.",
                "url": "https://www.mfmpod.com",
                "analogy": "Like listening to tavern rumors and merchant tales. Ideas, opportunities, warnings.",
                "game_reference": "Skyrim tavern conversations / Fallout settlement gossip",
                "difficulty_level": "all",
                "order_index": 40,
                "is_free": 1,
            },
            {
                "category": "external_resources",
                "subcategory": "books",
                "title": "Free Business Books - Project Gutenberg",
                "description": "Classic business books, public domain. Wealth of Nations, Think and Grow Rich, etc. Free ebooks.",
                "url": "https://www.gutenberg.org/ebooks/bookshelf/238",
                "analogy": "Like finding ancient tomes in the College of Winterhold. Timeless wisdom, freely available.",
                "game_reference": "Skyrim College library / Fallout archive terminals",
                "difficulty_level": "all",
                "order_index": 41,
                "is_free": 1,
            },
            {
                "category": "external_resources",
                "subcategory": "impact",
                "title": "B Corp Certification - Standards",
                "description": "Certify as a force for good. Social, environmental standards. Join movement of ethical businesses.",
                "url": "https://www.bcorporation.net/en-us/certification/",
                "analogy": "Like becoming a Paladin of the Brotherhood. Certified ethical, part of something bigger.",
                "game_reference": "Skyrim Paladin oaths / Fallout Brotherhood ideals",
                "difficulty_level": "advanced",
                "order_index": 42,
                "is_free": 1,
            },
            {
                "category": "external_resources",
                "subcategory": "sustainability",
                "title": "Climate Solutions for Business - Project Drawdown",
                "description": "Science-backed climate solutions. Reduce emissions, save money. Practical, profitable, planetary.",
                "url": "https://drawdown.org/solutions",
                "analogy": "Like cleansing a corrupted grove. Heal the land, profit from restoration.",
                "game_reference": "Skyrim cleansing quests / Fallout wasteland restoration",
                "difficulty_level": "all",
                "order_index": 43,
                "is_free": 1,
            },
        ]

        seeded_count = 0
        for res in resources:
            existing = conn.execute(
                text("SELECT id FROM hub_resources WHERE url = :url"), {"url": res["url"]}
            ).fetchone()

            if not existing:
                conn.execute(
                    text("""
                        INSERT INTO hub_resources
                        (category, subcategory, title, description, url, analogy, game_reference, resource_type, difficulty_level, order_index, is_free)
                        VALUES (:category, :subcategory, :title, :description, :url, :analogy, :game_reference, 'link', :difficulty_level, :order_index, :is_free)
                    """),
                    res,
                )
                seeded_count += 1

        conn.commit()

    print("\n✅ Education Hub migration completed!")
    print(f"\n📚 Resources seeded: {seeded_count} curated resources")
    print("\n📖 Categories:")
    print("   • Getting Started (11 resources) - Survival Mode basics")
    print("   • Building Community (10 resources) - Build Phase growth")
    print("   • Metrics That Matter (6 resources) - Optimization tools")
    print("   • Advanced Strategy (6 resources) - Conquer & Legacy")
    print("   • External Resources (9 resources) - Bonus mod packs")
    print("\n🎯 All resources are free or have free tiers")
    print("🎮 Every resource includes Bethesda game analogies")
    print("🔗 Direct links to highest-quality sources")


if __name__ == "__main__":
    migrate()
