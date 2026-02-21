# 🎨 Ad Builder for SkyModderAI

**The People's Ad Tool** — Free, powerful, accessible advertising creation for everyone.

---

## 🚀 Quick Start

### 1. Run Database Migration

```bash
cd /media/chris/Samsung-T7/SkyModderAI/SkyModderAI
python3 migrations/add_ad_builder.py
```

### 2. Start the Application

```bash
python3 app.py
```

### 3. Access Ad Builder

Navigate to: **http://localhost:5000/ad-builder/**

---

## ✨ What's Built

### Backend (Complete)

| Component | File | Status |
|-----------|------|--------|
| Service Layer | `ad_builder_service.py` | ✅ 1,100+ lines |
| Routes | `blueprints/ad_builder.py` | ✅ 600+ lines |
| Database Schema | `migrations/add_ad_builder.py` | ✅ Complete |
| Blueprint Registration | `app.py`, `blueprints/__init__.py` | ✅ Done |

### Frontend (Phase 1)

| Component | File | Status |
|-----------|------|--------|
| Home Page | `templates/ad_builder/home.html` | ✅ Complete |
| Editor (Placeholder) | `templates/ad_builder/editor.html` | 🚧 Basic UI |
| Templates Library | `templates/ad_builder/templates.html` | ❌ TODO |
| Design Library | `templates/ad_builder/designs.html` | ❌ TODO |
| Brand Kits | `templates/ad_builder/brand_kits.html` | ❌ TODO |

### Documentation

| Document | File | Status |
|----------|------|--------|
| Design Spec | `docs/AD_BUILDER_DESIGN.md` | ✅ Complete |
| Progress Tracker | `docs/AD_BUILDER_PROGRESS.md` | ✅ Complete |
| This README | `docs/AD_BUILDER_README.md` | ✅ You are here |

---

## 🎯 Features

### Available Now (Phase 1)

- ✅ **Guest Access** — Create without account (7-day session)
- ✅ **Account Integration** — Permanent saving for logged-in users
- ✅ **Design CRUD** — Create, read, update, delete designs
- ✅ **Template System** — Backend ready for templates
- ✅ **Brand Kits** — Save and apply brand colors/fonts/logos
- ✅ **Smart Resizing** — Resize designs to different formats
- ✅ **50+ Formats** — Social media, print, digital ads, video

### Coming Soon (Phase 2)

- 🚧 **Canvas Editor** — Fabric.js/Konva.js integration
- 🚧 **Drag & Drop** — Visual element positioning
- 🚧 **Text Tools** — Fonts, sizes, effects
- 🚧 **Image Upload** — Asset management
- 🚧 **Export** — PNG, JPG, PDF, SVG

### Planned (Phase 3+)

- ❌ **AI Copywriting** — Auto-generate ad text
- ❌ **Background Removal** — AI-powered
- ❌ **Stock Photos** — Unsplash integration
- ❌ **A/B Testing** — Compare variants (Pro)
- ❌ **Analytics** — Track performance (Pro)
- ❌ **Collaboration** — Real-time team editing (Pro)

---

## 📐 Supported Formats

### Social Media
- Instagram (Post, Story, Reel)
- Facebook (Post, Story, Cover)
- Twitter/X (Post, Header)
- LinkedIn (Post, Cover)
- Pinterest (Pin)
- TikTok (Video, Thumbnail)

### Digital Ads
- Google Display (all IAB sizes)
- YouTube (Banner, Thumbnail)

### Print
- Flyers (A4, Letter)
- Business Cards
- Postcards (4x6)
- Posters (A3, A2)

### Video
- YouTube Shorts
- Instagram Reels
- Facebook Stories

---

## 💰 Business Model

### Free (Forever)
- ✅ Create unlimited designs
- ✅ Access all templates
- ✅ All formats
- ✅ Basic export (PNG/JPG)
- ✅ Brand kits (1 for guests, unlimited for accounts)

### Pro ($9/month or $90/year) - Optional
- ✅ Clean exports (no watermark for guests)
- ✅ PDF/SVG/MP4 export
- ✅ Batch export
- ✅ AI copywriting (unlimited)
- ✅ Background removal
- ✅ A/B testing
- ✅ Analytics
- ✅ Team collaboration (up to 3)
- ✅ Premium stock photos

**Philosophy:** Essential features are free. Pro is for power users who want to support the project.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         Ad Builder Frontend             │
│  (Canvas Editor + Templates + Export)   │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         Ad Builder Backend              │
│  (Service Layer + API Routes)           │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│           Database                      │
│  (Designs, Templates, Assets, Users)    │
└─────────────────────────────────────────┘
```

### Key Components

1. **Guest Session Manager** — 7-day ephemeral storage
2. **Design Service** — CRUD operations
3. **Template Engine** — Template library + customization
4. **Brand Kit Manager** — Colors, fonts, logos
5. **Export Engine** — Multi-format rendering
6. **Smart Resizer** — Auto-adjust for different formats

---

## 🔧 Development

### Adding a New Format

```python
# In ad_builder_service.py
FORMAT_SIZES = {
    "new_format": (1920, 1080),  # width, height
}

FORMAT_CATEGORIES = {
    "new_format": "social",  # or print, video, display
}
```

### Adding a New Template

```python
# Via API or admin interface
template = AdTemplate(
    id=str(uuid.uuid4()),
    name="Instagram Sale Post",
    category="social",
    format_type="instagram_post",
    template_data={...},  # Canvas state
)
```

### Canvas Integration (Next Step)

```javascript
// In editor.html
import { fabric } from 'fabric';

const canvas = new fabric.Canvas('canvas-container', {
    width: editorState.width,
    height: editorState.height,
});

// Add text
function addText() {
    const text = new fabric.IText('Your text', {
        left: 100,
        top: 100,
        fontFamily: 'Inter',
        fill: '#333',
    });
    canvas.add(text);
}
```

---

## 📊 Success Metrics

### Phase 1 Goals (Month 1)
- [ ] 100 designs created
- [ ] 50% guest → account conversion
- [ ] 10+ templates available
- [ ] Working canvas editor

### Phase 2 Goals (Month 3)
- [ ] 1,000 designs created
- [ ] 10% account → Pro conversion
- [ ] 50+ templates
- [ ] Export working for all formats

### Long-term Goals (Year 1)
- [ ] 10,000+ monthly active users
- [ ] 500+ templates (community contributions)
- [ ] Self-sustaining via Pro + donations
- [ ] Local businesses relying on Ad Builder

---

## 🤝 Contributing

### Ways to Help

1. **Canvas Editor** — Fabric.js/Konva.js expert?
2. **Template Design** — Create templates for the library
3. **Format Requests** — Need a specific ad size?
4. **AI Features** — Help integrate copywriting AI
5. **Documentation** — Improve guides and tutorials

### How to Contribute

```bash
git clone https://github.com/SamsonProject/SkyModderAI.git
cd SkyModderAI
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
```

See `CONTRIBUTING.md` for detailed guidelines.

---

## 🎯 Vision

> **"We will have completely unrelated businesses relying on our site over whatever the leading tool for making ads simply because we care much more about serving our communities and business partners and access to information and tools than we care about charging."**

The Ad Builder is not just a tool. It's a statement that:
- Great advertising shouldn't require a marketing budget
- Small businesses deserve the same tools as corporations
- Community trust is more valuable than extraction
- If we ever struggle, our users will support us because we've earned it

---

## 📞 Support

- **Documentation:** `docs/AD_BUILDER_DESIGN.md`
- **Progress Tracker:** `docs/AD_BUILDER_PROGRESS.md`
- **Issues:** https://github.com/SamsonProject/SkyModderAI/issues
- **Email:** support@skymodderai.com

---

**Built with ❤️ for the community**

*Free forever. Open source. Privacy-first.*

---

*Last Updated: February 21, 2026*
*Version: 1.0 (Phase 1 Foundation)*
