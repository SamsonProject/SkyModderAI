# 📖 Mod Author Documentation

**Welcome to SkyModderAI's Mod Author Hub!**

This documentation is specifically for mod authors who want to:
- Claim and verify their mods
- Manage compatibility data
- Engage with the community
- Improve mod quality

---

## 🚀 Quick Start

### Step 1: Create Account

1. Go to [SkyModderAI](https://skymodderai.com)
2. Click **Sign In** → **Sign Up**
3. Enter email and password
4. Verify email

### Step 2: Claim Your Mod

1. Go to **Mod Authors** in navigation
2. Click **Claim New Mod**
3. Fill in:
   - Mod name (exact as it appears on Nexus)
   - Game (Skyrim SE, Fallout 4, etc.)
   - Nexus ID (optional, from mod page URL)
   - Nexus profile URL
   - Mod page URL

### Step 3: Get Verified

Choose verification method:

**A. Nexus API (Recommended)**
- Fastest (instant)
- Requires Nexus API key
- Get key from: https://www.nexusmods.com/users/myaccount?tab=api+access

**B. File Upload**
- Upload your mod file (.esp/.esm/.esl)
- System verifies hash
- Takes 1-2 minutes

**C. Manual Review**
- Admin reviews claim
- Takes 24-48 hours
- Use if other methods fail

### Step 4: Access Dashboard

Once verified:
- View compatibility reports
- Manage webhooks
- Access author tools
- Get analytics

---

## 📋 Table of Contents

### Core Features
- [Claiming Your Mod](#claiming-your-mod)
- [Verification Methods](#verification-methods)
- [Dashboard Overview](#dashboard-overview)
- [Notifications](#notifications)

### Tools
- [Compatibility Checker](#compatibility-checker)
- [LOOT Metadata Generator](#loot-metadata-generator)
- [Batch Testing](#batch-testing)
- [Patch Finder](#patch-finder)

### Advanced
- [Webhooks](#webhooks)
- [RSS Feeds](#rss-feeds)
- [Embeddable Widgets](#embeddable-widgets)
- [API Access](#api-access)

### Best Practices
- [Writing Compatibility Reports](#writing-compatibility-reports)
- [Responding to Issues](#responding-to-issues)
- [Maintaining Mod Pages](#maintaining-mod-pages)

---

## 🎯 Claiming Your Mod

### What You Can Claim

You can claim mods that you:
- Created yourself
- Co-authored
- Have permission to manage

### Required Information

| Field | Required | Description |
|-------|----------|-------------|
| Mod Name | ✅ | Exact name as on Nexus |
| Game | ✅ | Which game the mod is for |
| Author Name | ✅ | Your author name |
| Nexus ID | ❌ | From mod page URL |
| Nexus Profile | ❌ | Your Nexus profile URL |
| Mod Page | ❌ | Direct link to mod |

### Where to Find Nexus ID

From mod page URL:
```
https://www.nexusmods.com/skyrimspecialedition/mods/12345
                                                    ^^^^^
                                                 Nexus ID
```

---

## 🔐 Verification Methods

### Method 1: Nexus API (Instant)

**Pros:**
- ✅ Instant verification
- ✅ No file upload needed
- ✅ Most secure

**Cons:**
- ❌ Requires Nexus API key
- ❌ Author name must match exactly

**Steps:**
1. Get Nexus API key from [Account Settings](https://www.nexusmods.com/users/myaccount?tab=api+access)
2. Enter API key in verification form
3. System checks author name
4. Verified instantly if match

### Method 2: File Upload (1-2 minutes)

**Pros:**
- ✅ No API key needed
- ✅ Works for any mod

**Cons:**
- ❌ Requires mod file
- ❌ File size limit (100MB)

**Steps:**
1. Upload your mod file (.esp/.esm/.esl)
2. System calculates SHA256 hash
3. Compares with uploaded file
4. Verified if hash matches

**Accepted File Types:**
- `.esp` (Elder Scrolls Plugin)
- `.esm` (Elder Scrolls Master)
- `.esl` (Elder Scrolls Light)
- `.ba2` (Bethesda Archive)

### Method 3: Manual Review (24-48 hours)

**Pros:**
- ✅ Works for all cases
- ✅ Human verification

**Cons:**
- ❌ Slowest method
- ❌ Requires admin availability

**Steps:**
1. Submit claim with proof of ownership
2. Admin reviews within 48 hours
3. Email notification when verified

**Accepted Proof:**
- Screenshot of Creation Kit with mod open
- Nexus mod page showing you as author
- GitHub repository (for open source mods)

---

## 📊 Dashboard Overview

### Stats Panel

Shows:
- **Verified Mods** - Number of mods you've claimed
- **Pending Claims** - Claims awaiting verification
- **Unread Notifications** - New updates
- **Total Upvotes** - Community engagement

### Quick Actions

- **Claim New Mod** - Add another mod
- **Author Tools** - Access testing tools
- **Submit Report** - Add compatibility report

### Recent Activity

- Latest compatibility reports
- New votes on your reports
- Patch releases
- Mod updates

---

## 🔔 Notifications

### Types of Notifications

| Type | Description | Example |
|------|-------------|---------|
| `new_conflict` | New incompatibility reported | "YourMod + OtherMod incompatible" |
| `patch_released` | Patch available for your mod | "PatchMod released for YourMod" |
| `vote_received` | Report received votes | "Your report got 10 upvotes" |
| `claim_verified` | Claim successfully verified | "YourMod claim verified" |

### Notification Settings

Configure how you receive notifications:

**In-App:**
- Enabled by default
- View in dashboard

**Email:**
- Optional
- Configure in Profile → Settings

**Webhook:**
- For automation
- Configure per mod

---

## 🛠️ Compatibility Checker

### What It Does

Tests your mod against:
- Popular mod lists
- Known incompatible mods
- LOOT rules

### How to Use

1. Go to **Mod Authors** → **Tools** → **Compatibility Checker**
2. Enter your mod name
3. Paste mod list to test against
4. Click **Check for Conflicts**
5. Review results

### Understanding Results

**Compatible (✓)**
- No conflicts detected
- Safe to use together

**Needs Patch (⚠)**
- Conflicts exist but can be resolved
- Patch available or load order fix

**Incompatible (✗)**
- Fundamental incompatibility
- Cannot use together

---

## 📝 LOOT Metadata Generator

### What It Does

Generates YAML metadata for LOOT masterlist:
- Requirements
- Load order rules
- Tags
- Incompatibilities
- Messages

### How to Use

1. Go to **Mod Authors** → **Tools** → **LOOT Generator**
2. Fill in:
   - Mod file name
   - Author name
   - Requirements
   - Load after rules
   - Tags
3. Click **Generate YAML**
4. Copy to clipboard or download

### Example Output

```yaml
- name: "YourMod.esp"
  author: "YourName"
  url: "https://nexusmods.com/skyrimspecialedition/mods/12345"
  tags:
    - CBBP
    - NPC
    - Quest
  req:
    - name: "USSEP.esp"
      display: "Unofficial Skyrim Special Edition Patch"
  after:
    - "USSEP.esp"
    - "SkyUI.esp"
  inc:
    - name: "ConflictingMod.esp"
      reason: "Both edit same NPC"
  patch:
    - name: "CompatibilityPatch.esp"
      url: "https://nexusmods.com/skyrimspecialedition/mods/67890"
  msg:
    - type: warning
      content: "Requires SKSE64"
```

### Submitting to LOOT

1. Generate YAML
2. Test locally in LOOT
3. Submit to [LOOT masterlist](https://github.com/loot/skyrim)
4. Include link to your mod page

---

## 🧪 Batch Testing

### What It Does

Test your mod against multiple load orders:
- Popular builds (Wabbajack lists)
- Community submissions
- Custom configurations

### How to Use

1. Go to **Mod Authors** → **Tools** → **Batch Test**
2. Enter your mod name
3. Select load orders to test against
4. Click **Run Tests**
5. Review results for each

### Export Results

Results can be exported as:
- JSON (for API use)
- CSV (for spreadsheets)
- PDF (for documentation)

---

## 🔍 Patch Finder

### What It Does

Searches for existing patches:
- Nexus Mods
- GitHub
- Community databases

### How to Use

1. Go to **Mod Authors** → **Tools** → **Patch Finder**
2. Enter your mod name
3. Select game
4. Click **Search**
5. Review results

### If No Patch Found

- Click **Request Patch**
- Creates GitHub issue template
- Community can collaborate

---

## 🔌 Webhooks

### What They Do

Real-time HTTP notifications when:
- New compatibility report
- Vote on your report
- Patch released
- Mod updated

### Configuration

1. Go to **Mod Authors** → **Settings** → **Webhooks**
2. Click **Add Webhook**
3. Configure:
   - Mod name
   - Game
   - Webhook URL
   - Events to subscribe to
4. Save

### Webhook Payload

```json
{
  "event": "compatibility_report",
  "report_id": 123,
  "mod_a": "YourMod",
  "mod_b": "OtherMod",
  "game": "skyrimse",
  "status": "incompatible",
  "timestamp": "2026-02-21T12:00:00Z"
}
```

### Example Integrations

**Discord Bot:**
```python
@bot.event
async def on_webhook(data):
    if data['event'] == 'compatibility_report':
        await channel.send(
            f"New report: {data['mod_a']} + {data['mod_b']} = {data['status']}"
        )
```

**CI/CD Pipeline:**
```yaml
on:
  webhook:
    event: compatibility_report
    status: incompatible

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: pytest tests/compatibility/
```

---

## 📡 RSS Feeds

### Available Feeds

**Mod Feed:**
```
https://skymodderai.com/feed/mod/YourMod.xml
```

**Compatibility Feed:**
```
https://skymodderai.com/feed/compatibility.xml
```

**Author Feed (requires auth):**
```
https://skymodderai.com/feed/author.xml
```

### Parameters

All feeds support:
- `?game=skyrimse` - Filter by game
- `?limit=50` - Number of items
- `?status=compatible` - Filter by status

### Usage

Subscribe in:
- Feed reader (Feedly, Inoreader)
- Discord (RSS bot)
- Email (IFTTT, Zapier)

---

## 🎨 Embeddable Widgets

### What They Do

Show compatibility score on:
- Nexus mod pages
- Personal websites
- Forums

### How to Embed

**HTML:**
```html
<iframe 
  src="https://skymodderai.com/mod/YourMod/embed?theme=dark"
  width="300"
  height="200"
  frameborder="0">
</iframe>
```

**Parameters:**
- `?theme=dark` or `?theme=light`
- `?game=skyrimse`
- `?show_reports=true`

### Customization

CSS variables for custom styling:
```css
--skymodderai-primary: #3b82f6;
--skymodderai-bg: #1e293b;
--skymodderai-text: #f8fafc;
```

---

## 🔑 API Access

### Getting API Key

1. Go to **Profile** → **API Keys**
2. Click **Generate New Key**
3. Copy key (shown once)
4. Store securely

### Rate Limits

| Tier | Requests/Minute | Requests/Day |
|------|-----------------|--------------|
| Free | 60 | 1,000 |
| Verified Author | 120 | 10,000 |
| Premium | 300 | Unlimited |

### Example Usage

**Python:**
```python
import requests

API_KEY = "your_api_key"
BASE_URL = "https://skymodderai.com/api/v1"

headers = {"Authorization": f"Bearer {API_KEY}"}

# Get compatibility
response = requests.get(
    f"{BASE_URL}/compatibility/USSEP/vs/SkyUI",
    headers=headers
)
data = response.json()

# Submit report
response = requests.post(
    f"{BASE_URL}/compatibility/report",
    json={
        "mod_a": "YourMod",
        "mod_b": "OtherMod",
        "status": "incompatible",
        "description": "CTD on startup"
    },
    headers=headers
)
```

**JavaScript:**
```javascript
const API_KEY = "your_api_key";
const BASE_URL = "https://skymodderai.com/api/v1";

// Get compatibility
fetch(`${BASE_URL}/compatibility/USSEP/vs/SkyUI`, {
  headers: {
    "Authorization": `Bearer ${API_KEY}`
  }
})
.then(r => r.json())
.then(data => console.log(data));
```

---

## ✍️ Writing Compatibility Reports

### Best Practices

**Be Specific:**
```
❌ Bad: "These mods don't work together"
✅ Good: "CTD when entering Whiterun with both mods active"
```

**Include Details:**
- Game version
- Mod versions
- Load order position
- Steps to reproduce

**Provide Solution:**
- Link to patch
- Suggest load order
- Recommend alternative

### Report Template

```
**Issue:** [Brief description]

**Steps to Reproduce:**
1. Install Mod A
2. Install Mod B
3. Load game
4. [Specific action]

**Expected:** [What should happen]
**Actual:** [What actually happens]

**Solution:** [Patch, load order, or workaround]

**Versions:**
- Game: [e.g., Skyrim SE 1.6.640]
- Mod A: [e.g., 2.1.0]
- Mod B: [e.g., 1.5.3]
```

---

## 💬 Responding to Issues

### Best Practices

**Be Professional:**
- Thank users for reports
- Acknowledge issues
- Provide timeline for fixes

**Be Transparent:**
- Admit when it's your mod's fault
- Explain technical limitations
- Share workarounds

**Be Responsive:**
- Reply within 48 hours
- Update when fix available
- Close the loop

### Response Templates

**Acknowledging Issue:**
```
Thanks for reporting this! I've reproduced the issue and am working on a fix.
Expected timeline: 1-2 weeks.

Workaround: Disable [specific feature] until patch is released.
```

**Providing Fix:**
```
Patch 1.0.1 is now available! This fixes the reported conflict with [OtherMod].

Download: [link]
Changelog: [link]
```

**Not a Bug:**
```
This is actually intended behavior. [Mod A] and [Mod B] both edit the same records,
so you need to choose one or use a compatibility patch.

Recommended patch: [link]
```

---

## 📄 Maintaining Mod Pages

### What to Include

**Requirements Section:**
- List all required mods
- Link to dependencies
- Specify versions if needed

**Incompatibilities:**
- List known conflicts
- Link to patches
- Provide workarounds

**Load Order:**
- Where your mod should load
- What it must load after
- What must load after it

### Example Mod Page

```markdown
## Requirements
- [USSEP](link) - Required
- [SkyUI](link) - Required
- [Address Library](link) - Required

## Incompatibilities
- [Other Mod A](link) - Incompatible (use [patch](link))
- [Other Mod B](link) - Load after this mod

## Load Order
- Load **after**: USSEP, SkyUI
- Load **before**: Any compatibility patches

## Installation
1. Install with mod manager
2. Enable in plugins.txt
3. Run [tool] if needed

## Uninstallation
1. Disable in mod manager
2. Remove from plugins.txt
3. Clean save with [tool]
```

---

## 🎓 Advanced Topics

### xEdit Integration

Export conflict data from xEdit:
1. Install xEdit script (provided)
2. Run on your mod
3. Upload JSON to SkyModderAI
4. Get detailed conflict report

### CI/CD Integration

Automate testing:
```yaml
# GitHub Actions
name: Mod Tests

on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run SkyModderAI tests
        run: |
          curl -X POST https://skymodderai.com/api/v1/test \
            -H "Authorization: Bearer ${{ secrets.API_KEY }}" \
            -d @mod_list.txt
```

### Mod Manager Plugins

**MO2 Extension:**
- One-click analysis
- Export/import mod lists
- Real-time monitoring

**Vortex Extension:**
- Automatic conflict detection
- Load order suggestions
- Patch recommendations

---

## 📞 Support

### Getting Help

**Documentation:**
- This guide
- [Compatibility Database Guide](/docs/CONFLICT_DATABASE_GUIDE.md)
- [LOOT Documentation](https://loot.github.io/docs/)

**Community:**
- [Discord](https://discord.gg/skyrimmods)
- [Reddit](https://reddit.com/r/skyrimmods)
- [Nexus Forums](https://forums.nexusmods.com/)

**Direct Support:**
- Email: authors@skymodderai.com
- GitHub Issues: [Report bug](https://github.com/SamsonProject/SkyModderAI/issues)

---

## 📈 Analytics

### Dashboard Metrics

**Engagement:**
- Total upvotes
- Report views
- Widget embeds

**Compatibility:**
- Compatibility score trend
- Conflict count over time
- Patch adoption rate

**Audience:**
- Top games
- Most reported conflicts
- Popular mod pairs

---

## 🏆 Recognition Program

### Verified Author Badge

Earn badge for:
- 5+ verified mods
- 100+ upvotes on reports
- Active community participation

### Benefits

- Priority support
- Higher API rate limits
- Featured author spotlights
- Early access to new features

---

**Happy Modding!** 🛡️

*Last updated: February 21, 2026*
