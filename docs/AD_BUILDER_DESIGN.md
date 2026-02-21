# SkyModderAI Ad Builder

**The People's Ad Tool** — Free, powerful, accessible advertising creation for everyone.

---

## 🎯 Vision

> **"We will have completely unrelated businesses relying on our site over whatever the leading tool for making ads simply because we care much more about serving our communities and business partners and access to information and tools than we care about charging."**

The Ad Builder is **not just an ad creation tool**. It's a statement that:
- Great advertising shouldn't require a marketing budget
- Small businesses deserve the same tools as corporations
- Community trust is more valuable than extraction
- If we ever struggle, our users will support us because we've earned it

---

## 🌟 Core Principles

### 1. **Accessible to All**
- ✅ **No account required** for basic ad creation
- ✅ Account unlocks: save drafts, analytics, A/B testing, bulk creation
- ✅ Guest ads watermarked but fully functional
- ✅ Export in all formats regardless of account status

### 2. **Hell of a Tool**
- ✅ Professional templates (flyers, social, video, display, print)
- ✅ AI-assisted copywriting (optional, free)
- ✅ Smart resizing (one design → all formats)
- ✅ Brand kit (colors, fonts, logos) — free forever
- ✅ Stock photo integration (free + paid tiers)
- ✅ Real-time collaboration (account feature)

### 3. **Multi-Format Support**

| Format | Sizes | Use Cases |
|--------|-------|-----------|
| **Social Media** | Instagram (post, story, reel), Facebook (post, story, cover), TikTok, Twitter/X, LinkedIn, Pinterest | Organic + paid social |
| **Digital Ads** | Google Display (all IAB sizes), Google Ads (responsive), YouTube (banner, thumbnail, end screen) | PPC campaigns |
| **Print** | Flyers (A4, Letter, Tabloid), Business cards, Postcards, Posters, Banners | Local marketing |
| **Video** | YouTube Shorts, TikTok, Instagram Reels, Facebook Stories (9:16, 1:1, 16:9) | Video ads |
| **Email** | Header images, email banners, newsletter templates | Email marketing |
| **Web** | Website headers, hero images, blog graphics | Content marketing |

### 4. **Community-First Business Model**

| Feature | Free | Account (Free) | Pro (Optional) |
|---------|------|----------------|----------------|
| Create ads | ✅ Unlimited | ✅ Unlimited | ✅ Unlimited |
| Templates | ✅ All | ✅ All | ✅ All + Premium |
| Export (PNG/JPG) | ✅ Watermarked | ✅ Clean | ✅ Clean + Batch |
| Export (PDF/SVG) | ❌ | ✅ Standard | ✅ Premium |
| Save drafts | ❌ | ✅ 10 drafts | ✅ Unlimited |
| Brand kit | ❌ | ✅ 1 brand | ✅ 5 brands |
| Stock photos | ❌ | ✅ Free collection | ✅ Premium + Free |
| AI copywriting | ❌ | ✅ 10/month | ✅ Unlimited |
| A/B testing | ❌ | ❌ | ✅ 5 variants |
| Analytics | ❌ | ❌ | ✅ Basic |
| Team collaboration | ❌ | ❌ | ✅ 3 members |
| API access | ❌ | ❌ | ✅ Limited |
| White-label export | ❌ | ❌ | ✅ Available |

**Pro tier: $9/month or $90/year** — but we'll never gate essential features.

---

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        Ad Builder Frontend                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │   Canvas    │ │  Templates  │ │   Assets    │ │   Export  │ │
│  │   Editor    │ │   Library   │ │   Manager   │ │   Engine  │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                       Ad Builder Backend                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │   Design    │ │   Asset     │ │   Export    │ │   Guest   │ │
│  │   Service   │ │   Service   │ │   Service   │ │  Session  │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                         Data Layer                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │  Designs DB │ │ Assets (S3) │ │  Templates  │ │  Sessions │ │
│  │             │ │             │ │     DB      │ │  (Redis)  │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Database Schema

```sql
-- Ad designs
CREATE TABLE ad_designs (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),  -- NULL for guest designs
    guest_session_id VARCHAR(64),  -- For guest designs
    name VARCHAR(255) NOT NULL,
    description TEXT,
    template_id UUID,
    
    -- Design data (JSON)
    design_data JSONB NOT NULL,  -- Canvas state, layers, elements
    brand_kit JSONB,  -- Colors, fonts, logos
    
    -- Metadata
    format_type VARCHAR(50),  -- instagram_post, flyer_a4, etc.
    width INTEGER,
    height INTEGER,
    
    -- Status
    status VARCHAR(20) DEFAULT 'draft',  -- draft, published, archived
    is_public BOOLEAN DEFAULT FALSE,  -- Shareable with community
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    published_at TIMESTAMP,
    
    -- Analytics (for Pro)
    view_count INTEGER DEFAULT 0,
    download_count INTEGER DEFAULT 0
);

-- Asset library (images, fonts, etc.)
CREATE TABLE ad_assets (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),  -- NULL for system assets
    name VARCHAR(255) NOT NULL,
    asset_type VARCHAR(50),  -- image, font, logo, icon
    file_url VARCHAR(512) NOT NULL,
    thumbnail_url VARCHAR(512),
    file_size INTEGER,  -- bytes
    dimensions JSONB,  -- {width, height} for images
    tags TEXT[],  -- Searchable tags
    is_premium BOOLEAN DEFAULT FALSE,  -- Pro feature
    license_type VARCHAR(50),  -- free, creative_commons, premium
    created_at TIMESTAMP DEFAULT NOW()
);

-- Templates
CREATE TABLE ad_templates (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50),  -- social, print, video, display
    format_type VARCHAR(50),  -- instagram_post, flyer_a4, etc.
    thumbnail_url VARCHAR(512),
    
    -- Template data
    template_data JSONB NOT NULL,  -- Pre-designed layout
    preview_data JSONB,  -- Rendered preview
    
    -- Metadata
    tags TEXT[],
    difficulty VARCHAR(20),  -- easy, intermediate, advanced
    estimated_time INTEGER,  -- minutes to customize
    
    -- Community
    is_official BOOLEAN DEFAULT TRUE,  -- Official vs community
    author_id UUID REFERENCES users(id),  -- For community templates
    download_count INTEGER DEFAULT 0,
    favorite_count INTEGER DEFAULT 0,
    
    -- Status
    status VARCHAR(20) DEFAULT 'active',  -- active, archived
    created_at TIMESTAMP DEFAULT NOW()
);

-- Guest sessions (for non-authenticated users)
CREATE TABLE guest_ad_sessions (
    session_id VARCHAR(64) PRIMARY KEY,
    fingerprint_hash VARCHAR(64),  -- Anti-abuse
    design_data JSONB,  -- Current design state
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,  -- 7 days from creation
    last_accessed TIMESTAMP DEFAULT NOW()
);

-- Brand kits
CREATE TABLE brand_kits (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    
    -- Brand colors
    primary_color VARCHAR(7),  -- #RRGGBB
    secondary_color VARCHAR(7),
    accent_color VARCHAR(7),
    text_color VARCHAR(7),
    
    -- Brand fonts
    heading_font VARCHAR(100),
    body_font VARCHAR(100),
    
    -- Brand assets
    logo_url VARCHAR(512),
    logo_square_url VARCHAR(512),
    
    -- Brand voice (for AI copywriting)
    brand_voice TEXT,  -- Description for AI
    
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Analytics (Pro feature)
CREATE TABLE ad_analytics (
    id UUID PRIMARY KEY,
    design_id UUID REFERENCES ad_designs(id),
    
    -- Metrics
    views INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    downloads INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    
    -- A/B testing
    variant_id VARCHAR(50),  -- A, B, C, etc.
    test_id UUID,  -- Links to A/B test
    
    -- Time series (aggregated daily)
    date DATE NOT NULL,
    
    UNIQUE(design_id, date, variant_id)
);
```

---

## 🎨 Features

### 1. **Template Library**

**Categories:**
- Social Media (Instagram, Facebook, TikTok, Twitter, LinkedIn, Pinterest)
- Digital Advertising (Google Display, YouTube, Facebook Ads)
- Print Materials (Flyers, Business Cards, Posters, Banners)
- Video Templates (Shorts, Reels, TikTok, Stories)
- Email & Web (Headers, Banners, Blog Graphics)

**Template Features:**
- Fully customizable (colors, fonts, images, text)
- Smart placeholders (auto-resize images)
- Industry-specific (restaurants, retail, services, tech, etc.)
- Seasonal templates (holidays, sales, events)
- Community templates (users can share)

### 2. **Canvas Editor**

**Core Tools:**
- Drag-and-drop interface
- Layers panel (reorder, group, lock)
- Alignment guides (smart snapping)
- Grid and ruler tools
- Undo/redo (unlimited for accounts, 10 for guests)
- Zoom (25% - 400%)

**Elements:**
- Text (heading, subheading, body, custom)
- Images (upload, stock library, URL)
- Shapes (rectangles, circles, lines, arrows)
- Icons (FontAwesome, Material Icons)
- Logos (upload, brand kit)
- QR codes (auto-generate from URL)
- Barcodes (for print)
- Charts/graphs (simple data visualization)

**Text Tools:**
- Font library (Google Fonts integration)
- Font size, weight, style
- Letter spacing, line height
- Text effects (shadow, outline, background)
- Text alignment
- Curved text (for circular designs)

**Image Tools:**
- Crop, resize, rotate, flip
- Filters (brightness, contrast, saturation, blur)
- Background removal (AI-powered, Pro feature)
- Image effects (shadows, borders, rounded corners)
- Image masking (shapes, text)

### 3. **Smart Resizing**

**One Design → All Formats:**
- Design once, export to multiple sizes
- Smart content repositioning
- Format-specific optimizations
- Batch export (Pro feature)

**Example Workflow:**
1. Design Instagram post (1080x1080)
2. Click "Resize for..."
3. Select: Instagram Story, Facebook Post, Twitter Post, TikTok
4. AI adjusts layout for each format
5. Export all at once

### 4. **AI-Powered Features**

**AI Copywriting:**
- Headline suggestions
- Body copy generation
- CTA optimization
- Tone adjustment (professional, friendly, urgent, playful)
- Character count optimization (for Twitter, etc.)

**AI Design Assistance:**
- Color palette suggestions
- Font pairing recommendations
- Layout improvements
- Image suggestions based on content
- Accessibility checker (contrast ratios, font sizes)

**AI Background Removal:**
- One-click background removal
- Edge refinement
- Shadow preservation

### 5. **Brand Kit**

**What's Included:**
- Brand colors (primary, secondary, accent, text)
- Brand fonts (heading, body)
- Logo uploads (standard + square)
- Brand voice description (for AI)

**Features:**
- Auto-apply to templates
- One-click brand switching
- Multiple brands (Pro: up to 5)
- Team sharing (Pro)

### 6. **Stock Asset Library**

**Free Collection:**
- 10,000+ free photos (Unsplash, Pexels integration)
- 5,000+ free icons
- 1,000+ free illustrations
- All free fonts (Google Fonts)

**Premium Collection (Pro):**
- 1M+ premium photos (Shutterstock integration)
- Premium illustrations
- Premium icons
- Premium fonts

### 7. **Export Options**

**Free:**
- PNG (watermarked for guests)
- JPG (watermarked for guests)
- Standard quality

**Account (Free):**
- PNG (clean)
- JPG (clean)
- PDF (standard)
- Standard quality

**Pro:**
- PNG (clean, transparent background)
- JPG (maximum quality)
- PDF (print-ready, CMYK)
- SVG (vector)
- MP4 (for video templates)
- Batch export
- White-label (no SkyModderAI branding)

### 8. **Collaboration (Pro)**

**Features:**
- Share designs with team
- Comment and feedback
- Version history
- Real-time editing (Google Docs style)
- Permission levels (view, comment, edit)

### 9. **A/B Testing (Pro)**

**Workflow:**
1. Create base design
2. Duplicate and modify (variant B, C, etc.)
3. Export all variants
4. Track performance (manual entry or API integration)
5. Statistical significance calculator

---

## 🚀 Implementation Plan

### Phase 1: Foundation (Weeks 1-2)

**Backend:**
- [ ] Create `ad_builder_service.py`
- [ ] Database migrations (tables above)
- [ ] Guest session management
- [ ] Basic CRUD for designs
- [ ] Asset upload service

**Frontend:**
- [ ] Canvas editor (Fabric.js or Konva.js)
- [ ] Basic template library
- [ ] Simple export (PNG/JPG)
- [ ] Guest access flow

**Templates:**
- [ ] 10 social media templates
- [ ] 5 flyer templates
- [ ] 3 business card templates

### Phase 2: Core Features (Weeks 3-4)

**Backend:**
- [ ] Smart resizing engine
- [ ] Template customization API
- [ ] Asset library integration (Unsplash API)
- [ ] Brand kit service

**Frontend:**
- [ ] Template customizer
- [ ] Asset manager
- [ ] Brand kit UI
- [ ] Export options

**Templates:**
- [ ] 50+ total templates
- [ ] All major social formats
- [ ] Print formats

### Phase 3: AI Features (Weeks 5-6)

**Backend:**
- [ ] AI copywriting integration (OpenAI)
- [ ] Color palette generator
- [ ] Font pairing suggestions
- [ ] Accessibility checker

**Frontend:**
- [ ] AI copywriting UI
- [ ] Design suggestions panel
- [ ] Accessibility warnings

### Phase 4: Advanced Features (Weeks 7-8)

**Backend:**
- [ ] Video export (FFmpeg)
- [ ] Background removal AI
- [ ] A/B testing service
- [ ] Analytics tracking

**Frontend:**
- [ ] Video editor (basic)
- [ ] A/B testing UI
- [ ] Analytics dashboard (Pro)

### Phase 5: Polish & Launch (Weeks 9-10)

**Both:**
- [ ] Performance optimization
- [ ] Mobile responsiveness
- [ ] Accessibility audit
- [ ] Documentation
- [ ] Marketing materials

---

## 💰 Monetization (Ethical)

### Revenue Streams

1. **Pro Subscriptions** ($9/month, $90/year)
   - Premium features only
   - Never gate essential tools

2. **Print-on-Demand** (future)
   - Order physical prints directly
   - We handle fulfillment
   - Transparent markup

3. **Premium Stock** (affiliate)
   - Shutterstock integration
   - We take small commission
   - Clearly marked as premium

4. **Voluntary Support**
   - "Buy us a mead" donations
   - Community sponsorship
   - Transparent about needs

### What We'll NEVER Do

- ❌ Sell user data
- ❌ Dark patterns for upgrades
- ❌ Watermark essential exports for account holders
- ❌ Hide features then charge to unlock
- ❌ Extractive advertising
- ❌ Paywall community templates

---

## 🎯 Success Metrics

### User Adoption
- 1,000 designs created in first month
- 50% guest → account conversion
- 10% account → Pro conversion
- 5,000+ monthly active users by month 6

### Community Trust
- Net Promoter Score > 50
- 80%+ satisfaction rating
- Voluntary donations cover 20%+ of costs by month 6
- Community templates > official templates by month 12

### Business Impact
- 100+ local businesses using regularly
- 10+ businesses credit Ad Builder for growth
- Featured in local business publications

---

## 📋 Next Steps

1. **Finalize design** — Review and iterate on this document
2. **Set up repo structure** — Create `blueprints/ad_builder.py`, `ad_builder_service.py`
3. **Database migration** — Run schema creation
4. **Build MVP** — Phase 1 features only
5. **Beta test** — Internal + community feedback
6. **Launch** — Public release with marketing push

---

**"We're not building an ad tool. We're building a community resource that happens to make ads."**

---

*Last Updated: February 21, 2026*
*Version: 1.0 (Draft)*
