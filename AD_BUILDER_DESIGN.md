# Ad Builder Design Document

**Date:** February 21, 2026  
**Status:** 🚧 **BACKEND COMPLETE, FRONTEND PENDING**

---

## 🎯 **VISION**

**The People's Ad Tool** - Free, powerful, accessible advertising creation for everyone.

**Core Principles:**
- ✅ No account required for basic ad creation
- ✅ Professional templates for all formats
- ✅ Smart resizing (one design → all formats)
- ✅ AI-assisted features (copywriting, design suggestions)
- ✅ Community-first monetization (never gate essential features)

---

## 🏗️ **ARCHITECTURE**

```
Ad Builder System
├── Backend (Complete)
│   ├── ad_builder_service.py (1,124 lines)
│   │   ├── Guest sessions
│   │   ├── Design management
│   │   ├── Template library
│   │   ├── Brand kits
│   │   └── Export functionality
│   │
│   └── blueprints/ad_builder.py (635 lines)
│       ├── Editor routes
│       ├── Template routes
│       ├── Design routes
│       ├── Brand kit routes
│       └── API endpoints
│
└── Frontend (TODO)
    ├── templates/ad_builder/ (EMPTY - needs implementation)
    │   ├── home.html (editor home)
    │   ├── editor.html (canvas editor)
    │   ├── templates.html (template library)
    │   ├── designs.html (user's designs)
    │   └── brand_kits.html (brand management)
    │
    └── static/js/ad-builder/ (TODO)
        ├── editor.js (canvas logic)
        ├── templates.js (template browser)
        └── export.js (export functionality)
```

---

## 📋 **ROUTES**

### **Main Routes**

| Route | Method | Access | Description |
|-------|--------|--------|-------------|
| `/ad-builder/` | GET | Guest/Account | Editor home |
| `/ad-builder/editor/new` | GET | Guest/Account | New design (blank canvas) |
| `/ad-builder/editor/<design_id>` | GET/POST | Guest/Account | Edit existing design |
| `/ad-builder/templates` | GET | Guest/Account | Template library |
| `/ad-builder/templates/<id>` | GET | Guest/Account | Template detail + customize |
| `/ad-builder/designs` | GET | Account only | User's saved designs |
| `/ad-builder/designs/<id>` | GET/POST | Account only | Edit saved design |
| `/ad-builder/brand-kits` | GET/POST | Account only | Brand kit management |
| `/ad-builder/export/<id>` | POST | Guest/Account | Export design |

### **API Routes**

| Route | Method | Description |
|-------|--------|-------------|
| `/ad-builder/api/designs` | POST | Create new design |
| `/ad-builder/api/designs/<id>` | PUT | Update design |
| `/ad-builder/api/designs/<id>` | DELETE | Delete design |
| `/ad-builder/api/templates` | GET | List templates |
| `/ad-builder/api/brand-kits` | GET/POST | Manage brand kits |
| `/ad-builder/api/export/<id>` | POST | Export design |

---

## 🎨 **FEATURES**

### **Guest Access** (No Account Required)

- ✅ Create designs with temporary session (7-day expiry)
- ✅ Access all templates
- ✅ Basic export (PNG, JPG)
- ✅ Watermarked exports
- ❌ Cannot save designs permanently
- ❌ No brand kits
- ❌ No analytics

### **Account Features**

- ✅ Permanent design storage
- ✅ Brand kit management
- ✅ All export formats (PNG, JPG, PDF, SVG, MP4)
- ✅ No watermarks
- ✅ A/B testing (Pro)
- ✅ Analytics (Pro)

---

## 📊 **DATA MODELS**

### **AdDesign**
```python
{
    "id": str,
    "name": str,
    "design_data": dict,  # Canvas data (layers, elements, etc.)
    "user_id": str | None,
    "guest_session_id": str | None,
    "template_id": str | None,
    "brand_kit": dict | None,
    "format_type": str,  # instagram_post, flyer_a4, etc.
    "width": int,
    "height": int,
    "status": str,  # draft, published, archived
    "is_public": bool,
    "created_at": datetime,
    "updated_at": datetime
}
```

### **Template**
```python
{
    "id": str,
    "name": str,
    "category": str,  # social, print, video, display
    "format_type": str,
    "width": int,
    "height": int,
    "preview_url": str,
    "design_data": dict,  # Template canvas data
    "tags": list[str],
    "is_official": bool,
    "created_by": str | None
}
```

### **BrandKit**
```python
{
    "id": str,
    "user_id": str,
    "name": str,
    "colors": list[dict],  # [{name, hex}]
    "fonts": list[dict],   # [{name, family, weights}]
    "logos": list[dict],   # [{url, name}]
    "created_at": datetime
}
```

---

## 🎯 **IMPLEMENTATION STATUS**

### **Backend** ✅ COMPLETE

- [x] `ad_builder_service.py` (1,124 lines)
  - [x] Guest session management
  - [x] Design CRUD operations
  - [x] Template management
  - [x] Brand kit management
  - [x] Export functionality
  - [x] Service initialization

- [x] `blueprints/ad_builder.py` (635 lines)
  - [x] Editor routes
  - [x] Template routes
  - [x] Design routes
  - [x] Brand kit routes
  - [x] API endpoints
  - [x] Guest session handling

### **Frontend** 🚧 TODO

- [ ] `templates/ad_builder/home.html` - Editor home page
- [ ] `templates/ad_builder/editor.html` - Canvas editor
- [ ] `templates/ad_builder/templates.html` - Template library
- [ ] `templates/ad_builder/designs.html` - User's designs
- [ ] `templates/ad_builder/brand_kits.html` - Brand management
- [ ] `static/js/ad-builder/editor.js` - Canvas logic
- [ ] `static/js/ad-builder/templates.js` - Template browser
- [ ] `static/js/ad-builder/export.js` - Export functionality

---

## 🚀 **NEXT STEPS**

### **Priority 1: Core Editor** (1-2 days)

1. **Create `home.html`**
   - Template browser
   - "Start New Design" button
   - Recent designs (if logged in)

2. **Create `editor.html`**
   - Canvas area (Fabric.js or similar)
   - Toolbar (text, shapes, images, upload)
   - Layers panel
   - Properties panel
   - Export button

3. **Create `editor.js`**
   - Canvas initialization
   - Element manipulation
   - Layer management
   - Save/load design

### **Priority 2: Templates** (1 day)

1. **Create `templates.html`**
   - Grid layout
   - Category filters
   - Search functionality

2. **Seed initial templates**
   - 10-20 starter templates
   - Various categories (social, print, etc.)

### **Priority 3: User Features** (1 day)

1. **Create `designs.html`**
   - User's saved designs
   - Search/filter
   - Edit/delete actions

2. **Create `brand_kits.html`**
   - Brand kit CRUD
   - Color picker
   - Font selector
   - Logo upload

### **Priority 4: Polish** (1 day)

1. **Responsive design**
2. **Keyboard shortcuts**
3. **Undo/redo**
4. **Auto-save**
5. **Export options**

---

## 🛠️ **TECH STACK RECOMMENDATIONS**

### **Canvas Library**

**Option 1: Fabric.js** (Recommended)
- ✅ Mature, well-documented
- ✅ Object model for canvas elements
- ✅ Built-in serialization
- ✅ Good performance
- ❌ Large bundle size (~65KB)

**Option 2: Konva.js**
- ✅ React/Vue bindings available
- ✅ Good performance
- ✅ Smaller than Fabric
- ❌ Less mature

**Option 3: Plain Canvas API**
- ✅ No dependencies
- ✅ Full control
- ❌ Reinvent the wheel
- ❌ More code to maintain

**Recommendation:** Use **Fabric.js** for rapid development

---

## 📐 **CANVAS SPECIFICATIONS**

### **Supported Formats**

| Category | Format | Dimensions (px) | Use Case |
|----------|--------|-----------------|----------|
| **Social** | Instagram Post | 1080x1080 | Square posts |
| | Instagram Story | 1080x1920 | Stories/Reels |
| | Facebook Post | 1200x630 | Link shares |
| | Twitter Post | 1200x675 | Tweets |
| | Pinterest Pin | 1000x1500 | Pins |
| **Print** | Flyer A4 | 2480x3508 | Flyers, posters |
| | Business Card | 1050x600 | Business cards |
| | Poster A3 | 3508x4961 | Large posters |
| **Display** | Leaderboard | 728x90 | Web banners |
| | Medium Rectangle | 300x250 | Web ads |
| | Wide Skyscraper | 160x600 | Side banners |

---

## 🎨 **TEMPLATE CATEGORIES**

### **Social Media**
- Instagram (Post, Story, Reel)
- Facebook (Post, Cover, Ad)
- Twitter/X (Post, Header)
- LinkedIn (Post, Banner)
- Pinterest (Pin, Story Pin)
- TikTok (Video Cover)

### **Print**
- Flyers
- Posters
- Business Cards
- Brochures
- Menus
- Invitations

### **Display Ads**
- Google Display Network
- Facebook Ads
- Instagram Ads
- LinkedIn Ads

### **Video Thumbnails**
- YouTube
- Vimeo
- Twitch

---

## 💰 **MONETIZATION** (Future)

### **Free Tier** (Always Free)
- All templates
- Basic export (PNG, JPG)
- Watermarked exports
- Guest access (7-day expiry)

### **Pro Tier** ($9/month or $99/year)
- No watermarks
- All export formats (PDF, SVG, MP4)
- Brand kits
- A/B testing
- Analytics
- Priority support

### **Community Aspect**
- Designers can sell templates (revenue share)
- Free tier never restricted
- Pro features are convenience, not necessity

---

## 📊 **SUCCESS METRICS**

- **Activation:** % of visitors who create at least one design
- **Retention:** % who return within 7 days
- **Conversion:** % who upgrade to Pro
- **Exports:** Total exports per day/week/month
- **Templates:** Most popular templates by category

---

**Ready to implement the frontend!** 🎨

Start with `home.html` and `editor.html` - the core experience.
