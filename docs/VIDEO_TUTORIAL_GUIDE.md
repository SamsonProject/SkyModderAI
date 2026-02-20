# 🎬 Video Tutorial Guide

**Scripts and recording tips for SkyModderAI tutorials.**

---

## 📹 Video Types

### 1. Quick Start (2-3 minutes)
**Goal:** Show how to use SkyModderAI in under 3 minutes

**Audience:** Busy modders who want quick answers

**Platform:** YouTube, Discord, Reddit

---

### 2. Full Tutorial (8-10 minutes)
**Goal:** Complete walkthrough with explanations

**Audience:** New modders, detailed learners

**Platform:** YouTube, website embed

---

### 3. Feature Spotlight (3-5 minutes each)
**Goal:** Deep dive into specific features

**Audience:** Existing users wanting to learn more

**Platform:** YouTube playlist

---

## 📝 Quick Start Script (2-3 minutes)

### [0:00-0:15] Hook

**Visual:** Skyrim gameplay footage with heavy modding

**Audio:**
```
"Love modding Skyrim? Hate when conflicts break your save? 
Here's how to catch those problems in 2 minutes."
```

---

### [0:15-0:30] What Is SkyModderAI?

**Visual:** SkyModderAI logo + main screen

**Audio:**
```
"SkyModderAI is a free tool that analyzes your mod list 
and finds conflicts before they ruin your game."
```

**On-screen text:**
- ✅ Free
- ✅ Open-source
- ✅ Works with MO2, Vortex, Wabbajack

---

### [0:30-1:00] Step 1: Export Your Mod List

**Visual:** Screen recording of Mod Organizer 2

**Audio:**
```
"First, export your mod list. In Mod Organizer 2, 
go to Tools, Copy to Clipboard, Active Mods.

That's it - your mod list is copied!"
```

**On-screen text:**
```
Tools → Copy to clipboard → Active mods
```

---

### [1:00-1:30] Step 2: Analyze

**Visual:** SkyModderAI interface, pasting mod list

**Audio:**
```
"Paste your list into SkyModderAI, select your game, 
and click Analyze.

The tool checks your mods against LOOT's database 
plus community-sourced conflicts."
```

**On-screen text:**
```
Analyzing 150 mods...
```

---

### [1:30-2:00] Step 3: Review Results

**Visual:** Conflict report screen

**Audio:**
```
"And here's the magic - SkyModderAI found 3 conflicts 
in my supposedly perfect load order.

For each one, it tells you exactly what patch to download 
from Nexus Mods."
```

**On-screen text:**
```
⚠️ 3 Conflicts Found
→ Click for solutions
```

---

### [2:00-2:30] Apply Fixes

**Visual:** Clicking through recommendations

**Audio:**
```
"Click on a conflict for details. Download the recommended 
patch. Enable it in your mod manager.

Then re-analyze to confirm everything's fixed."
```

**On-screen text:**
```
Download → Install → Re-analyze
```

---

### [2:30-3:00] Wrap-Up

**Visual:** Clean load order, all green checkmarks

**Audio:**
```
"That's it! Three minutes that could save you hours of 
debugging.

SkyModderAI is free, no accounts needed. Link in the 
description.

Happy modding!"
```

**On-screen text:**
```
🛡️ SkyModderAI
https://github.com/SamsonProject/SkyModderAI

Mod Safely. Mod Smarter. Mod Longer.
```

---

## 📝 Full Tutorial Script (8-10 minutes)

### [0:00-0:30] Introduction

**Visual:** Epic Skyrim montage with mods

**Audio:**
```
"Hey everyone! Today I'm showing you a tool that could 
save your Skyrim playthrough.

I've lost count of how many times I've had to restart 
my game because of mod conflicts. This tool catches 
those problems before they break your save.

It's called SkyModderAI, and it's completely free."
```

---

### [0:30-1:30] What Is SkyModderAI?

**Visual:** Tool interface overview

**Audio:**
```
"SkyModderAI is a mod compatibility checker for Bethesda 
games - Skyrim, Fallout 4, and Oblivion.

Think of it like a spellchecker for your mod list. 
It finds conflicts, suggests fixes, and recommends 
patches from Nexus Mods.

It uses LOOT's database - the same tool modders have 
trusted for years - plus additional community-sourced 
conflict rules.

And it's 100% free. No accounts, no paywalls, no BS."
```

**On-screen text:**
- Built by modders, for modders
- Uses LOOT + community knowledge
- Free forever

---

### [1:30-2:30] Installation

**Visual:** Terminal/Command Prompt

**Audio:**
```
"Let's install it. SkyModderAI runs locally on your 
computer, which means your mod list stays private.

Open a terminal and run these commands...

[Show commands on screen]

That's cloning the repository, installing dependencies, 
and starting the app.

Once it's running, open your browser to 
localhost:5000."
```

**On-screen text:**
```bash
git clone https://github.com/SamsonProject/SkyModderAI.git
cd SkyModderAI
pip install -r requirements.txt
python app.py
```

---

### [2:30-4:00] Exporting Your Mod List

**Visual:** Mod Organizer 2

**Audio:**
```
"Now let's analyze your mod list. I'm using Mod Organizer 2, 
but this works with Vortex and Wabbajack too.

In MO2, go to Tools, Copy to Clipboard, Active Mods. 
This copies your entire mod list.

[Show the exported list]

You can see all my mods here - USSEP, SkyUI, Immersive 
Armors, and about 150 more.

Copy this whole list and head over to SkyModderAI."
```

**On-screen text:**
```
Pro tip: Export your load order too!
Tools → Copy to clipboard → Load order
```

---

### [4:00-5:30] Analyzing Your Mods

**Visual:** SkyModderAI interface

**Audio:**
```
"Paste your mod list here. Select your game - I'm using 
Skyrim Special Edition.

Click Analyze, and wait a few seconds.

[Show analysis progress]

SkyModderAI is checking each mod against:
- LOOT's masterlist for load order rules
- A database of known conflicts
- Community reports from other modders

For a 150-mod list, this takes about 5 seconds."
```

**On-screen text:**
```
Analysis Progress:
✓ Parsing mod list
✓ Checking LOOT rules
✓ Finding conflicts
✓ Generating recommendations
```

---

### [5:30-7:00] Understanding Results

**Visual:** Results screen with conflicts

**Audio:**
```
"And here we go - SkyModderAI found 5 conflicts in my 
load order. Let's break these down.

First, a critical conflict: Ordinator and Adamant are 
both perk overhauls. They can't be used together - you 
need to choose one.

Second, a high-priority issue: Immersive Armors and 
Weapons need a compatibility patch. Here's the direct 
link to download it from Nexus.

Third, a medium issue: SMIM and SkyUI have a visual 
conflict. There's a patch available.

Click on each conflict for more details."
```

**On-screen text:**
```
🔴 Critical: Choose one perk overhaul
🟠 High: Install compatibility patch
🟡 Medium: Visual conflict, patch available
```

---

### [7:00-8:30] Applying Fixes

**Visual:** Downloading patches, adjusting load order

**Audio:**
```
"Let's fix these. For each conflict, SkyModderAI gives 
you a specific solution.

For the Ordinator-Adamant conflict, I'm keeping 
Ordinator. I'll disable Adamant in my mod manager.

For the Immersive Armors-Weapons issue, I'm downloading 
the compatibility patch. The link takes me straight to 
Nexus Mods.

After installing patches, I adjust my load order based 
on the recommendations.

Then I re-analyze to confirm everything's fixed."
```

**On-screen text:**
```
1. Download recommended patches
2. Install in mod manager
3. Adjust load order
4. Re-analyze to confirm
```

---

### [8:30-9:30] Advanced Features

**Visual:** Additional features

**Audio:**
```
"SkyModderAI has more features worth knowing about.

You can export your analysis as PDF or HTML - great for 
keeping records or sharing with friends.

The API lets you integrate SkyModderAI into your own 
tools or scripts.

And you can save your mod lists for later comparison."
```

**On-screen text:**
- Export to PDF/HTML/Markdown
- REST API available
- Save and compare lists

---

### [9:30-10:00] Conclusion

**Visual:** Clean results screen

**Audio:**
```
"And that's SkyModderAI! A few minutes of analysis can 
save you hours of debugging.

It's free, open-source, and built by modders who 
understand your pain.

Link in the description. If this helped, consider 
starring the GitHub repo or telling a friend.

Happy modding, and I'll see you in the next one!"
```

**On-screen text:**
```
🛡️ SkyModderAI
https://github.com/SamsonProject/SkyModderAI

Questions? Join our Discord!
[Discord QR code]
```

---

## 🎥 Recording Tips

### Screen Recording Software

**Free Options:**
- **OBS Studio** - Best overall, steep learning curve
- **ShareX** - Great for Windows, built-in editor
- **QuickTime** - Mac built-in, simple

**Paid Options:**
- **Camtasia** - Best editor included
- **ScreenFlow** - Mac, professional results

---

### Recommended Settings

**Resolution:**
- 1920x1080 (Full HD) minimum
- 2560x1440 (2K) for crisp text
- 3840x2160 (4K) if your system can handle it

**Frame Rate:**
- 30 FPS minimum
- 60 FPS for smooth gameplay footage

**Bitrate:**
- 10-20 Mbps for 1080p
- Higher for 4K

---

### Audio Tips

**Microphone:**
- USB mic (Blue Yeti, Audio-Technica) > headset mic
- Record in a quiet room
- Use a pop filter if possible

**Software:**
- Audacity (free) for cleanup
- Remove background noise
- Normalize to -3dB

**Speaking Tips:**
- Speak clearly and slowly
- Smile while talking (sounds more engaging)
- Take breaks between sections

---

### Visual Polish

**Cursor Effects:**
- Highlight cursor (yellow circle)
- Click effects (ripple animation)
- Available in Camtasia, OBS plugins

**Zoom/Pan:**
- Zoom in on important UI elements
- Pan smoothly between sections
- Don't overdo it

**Annotations:**
- Add arrows pointing to buttons
- Highlight text boxes
- Use consistent colors (red for issues, green for fixes)

---

## 📊 Video Optimization

### YouTube SEO

**Title:**
```
✅ "SkyModderAI Tutorial - Detect Mod Conflicts in 3 Minutes"
❌ "How to use this tool I made"
```

**Description:**
```markdown
SkyModderAI is a free mod conflict detector for Skyrim, 
Fallout 4, and Oblivion. This tutorial shows you how to 
find and fix mod conflicts before they break your game.

🔗 Download: https://github.com/SamsonProject/SkyModderAI
💬 Discord: [invite link]
📱 Reddit: r/skyrimmods

⏱️ Timestamps:
0:00 Introduction
0:30 What is SkyModderAI?
1:30 Installation
2:30 Export your mod list
4:00 Analyzing mods
5:30 Understanding results
7:00 Applying fixes
8:30 Advanced features
9:30 Conclusion

#Skyrim #Modding #Tutorial #Gaming
```

**Tags:**
```
skyrim modding, skyrim tutorial, mod conflicts, 
skymodderai, loot, mod organizer 2, vortex, 
bethesda mods, skyrim se, fallout 4
```

---

### Thumbnail Design

**Elements:**
- SkyModderAI logo (shield icon)
- Bold text: "MOD CONFLICTS SOLVED"
- Before/After split (red ❌ vs green ✅)
- Your face (optional, increases engagement)

**Tools:**
- Canva (free, templates)
- Photoshop (paid)
- GIMP (free, advanced)

---

## 📤 Distribution

### Where to Share

**YouTube:**
- Upload as public video
- Add to playlist with other modding tutorials
- Pin comment with links

**Discord:**
- Share in #tutorials channel
- Post in r/skyrimmods Discord
- SkyModderAI official server

**Reddit:**
- r/skyrimmods - Tutorial Tuesday
- r/gaming - If particularly polished
- r/youtube - For feedback

**Nexus Mods:**
- Post on Nexus Mods forums
- Add to mod manager integration pages

---

## 📈 Analytics to Track

**First Week:**
- Views (goal: 500+)
- Watch time (goal: 50%+ retention)
- Likes/dislikes (goal: 95%+ positive)
- Comments (engagement)

**First Month:**
- Subscribers gained
- GitHub stars from video
- Discord joins from video
- Tutorial mentions on social media

---

## 🎬 Feature Spotlight Series

### Episode Ideas

1. **"MO2 Integration Deep Dive"** (5 min)
   - Exporting from MO2
   - Profiles and testing
   - MO2-specific features

2. **"Vortex Users Guide"** (5 min)
   - Vortex export process
   - Using Vortex + SkyModderAI together
   - Resolving conflicts in Vortex

3. **"Advanced Conflict Detection"** (7 min)
   - Reading conflict details
   - Manual patch creation (xEdit)
   - Reporting new conflicts

4. **"Wabbajack + SkyModderAI"** (5 min)
   - Analyzing before building
   - Custom list creation
   - Post-build checks

5. **"Fallout 4 Specific Guide"** (5 min)
   - Fo4-specific conflicts
   - F4SE compatibility
   - Creation Club issues

---

## ✅ Pre-Recording Checklist

Before recording:

- [ ] Script finalized and rehearsed
- [ ] Desktop clean (no personal files visible)
- [ ] Notifications disabled
- [ ] Browser in incognito mode
- [ ] Mod list prepared (20-30 popular mods)
- [ ] Test recording (1 minute, check audio/video)
- [ ] Water/snack nearby
- [ ] Recording software settings confirmed
- [ ] Backup recording method ready

---

## ✅ Post-Recording Checklist

After recording:

- [ ] Watch full video (check for mistakes)
- [ ] Edit out long pauses/mistakes
- [ ] Add intro/outro music (royalty-free)
- [ ] Add annotations (arrows, highlights)
- [ ] Color correction (if needed)
- [ ] Export in multiple resolutions
- [ ] Create thumbnail
- [ ] Write description with timestamps
- [ ] Add captions/subtitles (YouTube auto + manual fix)
- [ ] Upload and schedule publish

---

**Good luck with your tutorial!** 🎬

Remember: The goal is to help modders, not to be perfect. 
Authentic enthusiasm beats polished production every time.

*Last updated: February 20, 2026*
