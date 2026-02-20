# 📸 Screenshot Guide

**Help us make SkyModderAI look better! Screenshots for documentation and marketing.**

---

## 🎯 What We Need

### Priority 1: Core Features

#### Dashboard View
- **What:** Main analysis screen with mod list pasted
- **Resolution:** 1920x1080 or higher
- **Browser:** Chrome/Firefox (incognito for clean look)
- **Example mod list:** 20-30 popular mods

#### Conflict Report
- **What:** Screen showing detected conflicts
- **Best case:** Show 2-3 different conflict types
- **Annotations:** Arrow pointing to key info

#### Recommendations
- **What:** Mod suggestions and patches
- **Show:** Nexus links, download buttons
- **Context:** At least 3 recommendations visible

---

### Priority 2: Workflows

#### MO2 Integration
1. MO2 with mod list visible
2. SkyModderAI in browser beside it
3. Show export → analyze → fix flow

#### Vortex Integration
1. Vortex plugins tab
2. SkyModderAI analysis
3. Show conflict resolution

#### Before/After
1. **Before:** Conflicts, warnings, errors
2. **After:** Clean load order, all green

---

## 📷 Screenshot Tips

### Composition
- **Full window:** Show browser chrome for context
- **Clean desktop:** No personal tabs or bookmarks
- **Good contrast:** Ensure text is readable
- **Consistent theme:** Use dark mode for all screenshots

### Annotations
- **Tool:** Use arrows, boxes, numbers
- **Style:** Red for issues, green for fixes
- **Text:** Minimal, point to key elements
- **Format:** PNG with annotations baked in

### File Naming
```
screenshot-dashboard-skyrim.png
screenshot-conflicts-fallout4.png
screenshot-recommendations.png
screenshot-mo2-integration.png
screenshot-before-after.png
```

---

## 🎨 Creating Placeholder Images

For documentation, use these placeholders until real screenshots:

### Dashboard Placeholder
```
┌─────────────────────────────────────────────┐
│  SkyModderAI                    [Analyze]   │
├─────────────────────────────────────────────┤
│  Game: [Skyrim SE ▼]                        │
│  Version: [1.6.640 ▼]                       │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │ Paste your mod list here...         │   │
│  │ USSEP.esp                           │   │
│  │ SkyUI.esp                           │   │
│  │ Immersive Armors.esp                │   │
│  │ ...                                 │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  [Analyze Load Order]                       │
└─────────────────────────────────────────────┘
```

### Conflict Report Placeholder
```
┌─────────────────────────────────────────────┐
│  ⚠️ 3 Conflicts Found                       │
├─────────────────────────────────────────────┤
│  🔴 Critical                                │
│  ┌─────────────────────────────────────┐   │
│  │ SMIM vs. SkyUI                      │   │
│  │ → Install "SMIM SkyUI Patch"        │   │
│  │ [Download Patch] [Learn More]       │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  🟠 High                                    │
│  ┌─────────────────────────────────────┐   │
│  │ Ordinator vs. Apocalypse            │   │
│  │ → Load Ordinator AFTER              │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

---

## 🖼️ Image Optimization

### Before Uploading
```bash
# Compress PNGs
pngquant --quality=65-80 screenshot.png

# Resize if needed
convert screenshot.png -resize 1920x1080 screenshot-optimized.png

# Create thumbnails
convert screenshot.png -resize 300x169 screenshot-thumb.png
```

### Format Guidelines
- **Screenshots:** PNG (lossless for text)
- **Banners:** SVG or WebP
- **Thumbnails:** WebP (small file size)
- **Max size:** 500KB per image

---

## 📍 Where to Add Screenshots

### In Documentation
```markdown
![Feature Description](images/screenshot-feature.png)
*Caption explaining what's shown*
```

### In README
```markdown
### Main Analysis Dashboard
![Dashboard Screenshot](docs/images/screenshot-dashboard.png)
```

### For Social Media
- **Twitter:** 1200x675 (1.78:1)
- **Discord:** 1200x630 (1.91:1)
- **Reddit:** 1200x900 (4:3) or 1920x1080

---

## 🎬 GIF/Video Screenshots

### Recording GIFs
```
Tool: ShareX, LICEcap, or ScreenToGif
Resolution: 1280x720
Duration: 5-15 seconds
FPS: 10-15 (smaller file size)
```

### Example GIF Scenarios
1. **Paste → Analyze → Results** (10 seconds)
2. **Clicking through conflicts** (8 seconds)
3. **Installing a patch recommendation** (12 seconds)

---

## ✅ Screenshot Checklist

Before submitting screenshots:

- [ ] Resolution is 1920x1080 or higher
- [ ] Text is readable and not blurry
- [ ] No personal information visible
- [ ] Browser tabs/bookmarks hidden
- [ ] Consistent theme (dark mode)
- [ ] File size optimized (<500KB)
- [ ] Descriptive filename
- [ ] Added to correct directory (`docs/images/`)
- [ ] Updated documentation to reference image

---

## 📤 Submitting Screenshots

1. **Save to:** `docs/images/`
2. **Name:** `screenshot-[feature]-[game].png`
3. **PR:** Include in documentation PR
4. **Credit:** Add your name to caption (optional)

**Example:**
```markdown
![Dashboard](images/screenshot-dashboard-skyrim.png)
*Screenshot by @YourName*
```

---

**Thank you for helping make SkyModderAI look professional!** 📸

*Last updated: February 20, 2026*
