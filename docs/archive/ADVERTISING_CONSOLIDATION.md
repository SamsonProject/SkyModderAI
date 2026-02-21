# Advertising System Consolidation Plan

**Date:** February 21, 2026  
**Status:** 🎯 **READY TO MERGE**

---

## 🔴 **CRITICAL DUPLICATION FOUND**

We have **TWO nearly identical advertising systems** running in parallel:

| Feature | Shopping System | Sponsor System | Duplicate? |
|---------|----------------|----------------|------------|
| **Blueprint** | `/business` + `/shopping` | `/sponsors` | ✅ YES |
| **Service** | `shopping_service.py` (836 lines) | `sponsor_service.py` (900 lines) | ✅ YES |
| **Pricing** | $5/1000 clicks | $5/1000 clicks | ✅ IDENTICAL |
| **First Month** | FREE | Not specified | ⚠️ Similar |
| **Click Tracking** | Server-side, fraud protection | Server-side, fraud protection | ✅ IDENTICAL |
| **Creative Rotation** | Yes | Yes (lowest-impressions first) | ✅ YES |
| **Democratic Ranking** | Yes (community + CTR) | Yes (community * 0.6 + CTR * 0.4) | ✅ YES |
| **Tables** | `ad_campaigns`, `ad_creatives`, `ad_clicks` | `sponsors`, `sponsor_creatives`, `sponsor_clicks` | ✅ DUPLICATE |

**Total Duplication:** ~1,736 lines of nearly identical code

---

## 🏆 **WINNER: Shopping System**

### **Why Shopping Wins:**

1. **Better Business Integration**
   - Tied to `businesses` table (existing directory)
   - Businesses can have multiple campaigns
   - Campaigns have budgets, start/end dates

2. **More Flexible Architecture**
   - Campaign-based (not sponsor-based)
   - Supports multiple creatives per campaign
   - Better for A/B testing

3. **First Month Free**
   - Automatic upon business approval
   - Better conversion funnel

4. **Cleaner Separation**
   - `/business` = Directory (free, networking)
   - `/shopping` = Advertising (paid, promotional)
   - Clear user mental model

### **What Sponsor System Does Better:**

1. **Community Voting**
   - `sponsor_votes` table with community scores
   - Democratic ranking formula
   - User engagement

2. **Ethical Charter**
   - `sponsor_charter.yaml` - excellent documentation
   - Community curation process
   - Flag/review system

---

## 🔄 **MERGE PLAN**

### **Phase 1: Keep Shopping as Base** ✅

**Keep:**
- `shopping_service.py` (rename to `advertising_service.py`)
- `/shopping` blueprint (rename to `/ads` or keep as-is)
- `ad_campaigns`, `ad_creatives`, `ad_clicks` tables

**Merge from Sponsors:**
- Community voting system (`sponsor_votes` → `ad_votes`)
- Ethical charter (`sponsor_charter.yaml` → `advertising_charter.yaml`)
- Flag/review system

### **Phase 2: Consolidate Templates** ✅

**Shopping templates to keep:**
- `shopping/home.html` → Main ads page
- `shopping/ads_directory.html` → All ads

**Sponsor templates to merge:**
- `sponsors/charter.html` → `shopping/charter.html` (ethical guidelines)
- `sponsors/apply.html` → `shopping/apply.html` (application form)

**Sponsor templates to archive:**
- `sponsors/list.html` → Merge into `shopping/home.html`
- `sponsors/applied.html` → Merge into `shopping/applied.html`
- `sponsors/dashboard.html` → Merge into `shopping/dashboard.html`

### **Phase 3: Update Routes** ✅

**Old Routes (to remove/redirect):**
- `/sponsors/` → Redirect to `/shopping/`
- `/sponsors/apply` → Redirect to `/shopping/apply`
- `/sponsors/charter` → Redirect to `/shopping/charter`
- `/sponsors/click/<id>` → Redirect to `/shopping/click/<id>`

**New Unified Routes:**
- `/shopping/` - Main ads page
- `/shopping/apply` - Apply to advertise
- `/shopping/charter` - Ethical advertising charter
- `/shopping/click/<id>` - Track click
- `/shopping/dashboard` - Advertiser dashboard
- `/shopping/vote/<id>` - Vote on ad (NEW from sponsors)

### **Phase 4: Database Migration** ✅

```sql
-- Add community voting to ad_creatives
ALTER TABLE ad_creatives ADD COLUMN community_score REAL DEFAULT 0.0;
ALTER TABLE ad_creatives ADD COLUMN community_votes INTEGER DEFAULT 0;

-- Create ad_votes table (from sponsor_votes)
CREATE TABLE ad_votes (
    id SERIAL PRIMARY KEY,
    ad_creative_id INTEGER NOT NULL,
    voter_user_id TEXT NOT NULL,
    score INTEGER NOT NULL,  -- 1-5
    context TEXT,
    voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ad_creative_id, voter_user_id)
);

-- Create ad_flags table (from sponsor_flags)
CREATE TABLE ad_flags (
    id SERIAL PRIMARY KEY,
    ad_creative_id INTEGER NOT NULL,
    reporter_user_id TEXT NOT NULL,
    reason TEXT NOT NULL,
    detail TEXT,
    status TEXT DEFAULT 'pending',  -- pending, reviewed, resolved
    reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 📋 **IMPLEMENTATION CHECKLIST**

### **Code Changes**

- [ ] Rename `shopping_service.py` → `advertising_service.py`
- [ ] Rename `ShoppingService` → `AdvertisingService`
- [ ] Rename `get_shopping_service()` → `get_advertising_service()`
- [ ] Merge sponsor voting into advertising service
- [ ] Merge sponsor flagging into advertising service
- [ ] Update all imports in blueprints
- [ ] Update all imports in templates

### **Template Changes**

- [ ] Merge `sponsors/charter.html` → `shopping/charter.html`
- [ ] Merge `sponsors/apply.html` → `shopping/apply.html`
- [ ] Update all sponsor references to "advertising" or "ads"
- [ ] Add voting UI to `shopping/home.html`
- [ ] Add flagging UI to `shopping/home.html`

### **Route Changes**

- [ ] Add redirect: `/sponsors/` → `/shopping/`
- [ ] Add redirect: `/sponsors/*` → `/shopping/*`
- [ ] Update navigation links (base.html, index.html)
- [ ] Update sitemap.xml generation

### **Database Changes**

- [ ] Run migration: Add `community_score`, `community_votes` to `ad_creatives`
- [ ] Run migration: Create `ad_votes` table
- [ ] Run migration: Create `ad_flags` table
- [ ] Migrate existing sponsor data to ad tables (if any)
- [ ] Archive sponsor tables (don't delete yet)

### **Documentation**

- [ ] Update `sponsor_charter.yaml` → `advertising_charter.yaml`
- [ ] Update API documentation
- [ ] Update user-facing documentation
- [ ] Update deployment guides

---

## 🎯 **FINAL ARCHITECTURE**

```
SkyModderAI Advertising System
├── /business (FREE directory)
│   ├── Directory listing (no ads)
│   ├── Business profiles
│   └── Networking features
│
├── /shopping (PAID advertising)
│   ├── Ad showcase
│   ├── Apply to advertise
│   ├── Ethical charter
│   ├── Advertiser dashboard
│   ├── Community voting (from sponsors)
│   └── Flag/review system (from sponsors)
│
└── Backend
    ├── advertising_service.py (merged)
    ├── business_service.py (unchanged)
    └── Database tables
        ├── businesses
        ├── ad_campaigns
        ├── ad_creatives (+ community_score, community_votes)
        ├── ad_clicks
        ├── ad_impressions
        ├── ad_votes (NEW from sponsors)
        └── ad_flags (NEW from sponsors)
```

---

## 📊 **CODE REDUCTION**

| Before | After | Reduction |
|--------|-------|-----------|
| `shopping_service.py` (836 lines) | `advertising_service.py` (950 lines) | +114 (added features) |
| `sponsor_service.py` (900 lines) | **ARCHIVED** | -900 |
| `blueprints/shopping.py` (409 lines) | `blueprints/ads.py` (450 lines) | +41 |
| `blueprints/sponsors.py` (121 lines) | **MERGED** | -121 |
| **Total** | **Total** | **-866 lines** |

**Net Reduction:** ~866 lines of duplicate code removed!

---

## 🚀 **BENEFITS**

1. **Single Source of Truth**
   - One advertising system, not two
   - Clear documentation
   - Easier maintenance

2. **Better Features**
   - Shopping's campaign management
   - Sponsor's community voting
   - Best of both worlds

3. **Cleaner UX**
   - `/business` = Free directory
   - `/shopping` = Paid advertising
   - No confusion

4. **Future-Proof**
   - Easy to add more ad types
   - Scalable architecture
   - Clear upgrade path

---

## ⚠️ **RISKS**

1. **Existing Sponsors**
   - If any sponsors exist, need to migrate
   - Solution: Migration script + manual review

2. **Broken Links**
   - Old `/sponsors/*` URLs
   - Solution: 301 redirects

3. **User Confusion**
   - Regular users know "Sponsors"
   - Solution: Update UI text gradually

---

## 📅 **TIMELINE**

- **Day 1:** Code consolidation (shopping + sponsors → advertising)
- **Day 2:** Template consolidation
- **Day 3:** Database migration
- **Day 4:** Testing (local + staging)
- **Day 5:** Deploy to production

**Total:** 5 days for full consolidation

---

**Ready to consolidate?** Start with Phase 1 (code merge) and work through the checklist!
