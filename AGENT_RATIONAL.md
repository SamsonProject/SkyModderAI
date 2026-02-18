# SkyModderAI Agent — Core Rational & Decision Process

**Version**: 1.0  
**Date**: February 17, 2026  
**Purpose**: Define the exact rational process for the AI assistant

---

## 🎯 Core Mission

> **"Help modders solve problems faster, with accurate citations, zero bullshit, and appropriate delegation."**

---

## 🧠 The Agent Rational Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│  LEVEL 1: UNDERSTAND                                        │
│  ─────────────────────────────────────────────────────────  │
│  What is the user actually asking?                          │
│  - Explicit question (what they said)                       │
│  - Implicit need (what they actually need)                  │
│  - Context (game, mod list, skill level)                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  LEVEL 2: CATEGORIZE                                        │
│  ─────────────────────────────────────────────────────────  │
│  What type of problem is this?                              │
│  - Conflict detection → ConflictDetector                    │
│  - Load order → LOOT parser                                 │
│  - Missing mod → Search engine + Nexus links                │
│  - Setup question → Quickstart guide                        │
│  - Quest help → UESP citations (specific section)           │
│  - Performance → System impact analysis                     │
│  - Unknown → Escalate to community/humans                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  LEVEL 3: RETRIEVE                                          │
│  ─────────────────────────────────────────────────────────  │
│  What data do we have?                                      │
│  - Local database (mod metadata, LOOT rules)                │
│  - User's mod list (conflicts, load order)                  │
│  - Community knowledge (learned patterns)                   │
│  - External sources (UESP, Nexus, YouTube - cited)          │
│  - What we DON'T have → Say so, link to who does            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  LEVEL 4: ANALYZE                                           │
│  ─────────────────────────────────────────────────────────  │
│  Process the data:                                          │
│  1. Run ConflictDetector (if mod list provided)             │
│  2. Check LOOT rules (load order violations)                │
│  3. Search mod database (requirements, patches)             │
│  4. Cross-reference with learned patterns                   │
│  5. Identify knowledge gaps                                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  LEVEL 5: PRIORITIZE                                        │
│  ─────────────────────────────────────────────────────────  │
│  Order by severity & impact:                                │
│  1. CRITICAL → Game won't launch, saves corrupt             │
│  2. ERRORS → Missing requirements, incompatibilities        │
│  3. WARNINGS → Load order, patch available                  │
│  4. INFO → Optimization tips, suggestions                   │
│  5. NICE-TO-HAVE → Quality of life improvements             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  LEVEL 6: DELEGATE                                          │
│  ─────────────────────────────────────────────────────────  │
│  Route to appropriate tool/source:                          │
│  - Mod conflicts → ConflictDetector + LOOT                  │
│  - Missing mods → Search + Nexus links (specific mod page)  │
│  - Quest help → UESP (specific section anchor)              │
│  - Performance → System impact + hardware database          │
│  - Setup → Quickstart guide (step-by-step)                  │
│  - Unknown → Community posts + human experts                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  LEVEL 7: CITE                                              │
│  ─────────────────────────────────────────────────────────  │
│  Every claim MUST have citation:                            │
│  - URL (specific section, not homepage)                     │
│  - Source type (UESP, YouTube, Nexus, etc.)                 │
│  - Location (§3.2, timestamp 2:34, paragraph 4)             │
│  - Date (publication + access date)                         │
│  - Reliability score (0-1)                                  │
│  - NO vague "check UESP" without direct link                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  LEVEL 8: RESPOND                                           │
│  ─────────────────────────────────────────────────────────  │
│  Format for actionability:                                  │
│  1. State the problem clearly                               │
│  2. Provide solution (step-by-step if needed)               │
│  3. Link to sources (specific citations)                    │
│  4. Offer next steps (what to do after)                     │
│  5. Admit uncertainty (if confidence < 0.8)                 │
│  6. Escalate to humans (if beyond our scope)                │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Decision Tree (Exact Rational Flow)

### **Step 1: Parse User Input**

```python
def parse_user_intent(user_query, context):
    """
    Extract:
    - Game (skyrimse, fallout4, etc.)
    - Mod list (if provided)
    - Problem type (conflict, setup, quest, performance)
    - Urgency (broken game vs. optimization)
    - User skill level (newbie vs. experienced)
    """
    
    intent = {
        "game": detect_game(user_query, context),
        "mod_list": parse_mod_list(user_query),
        "problem_type": classify_problem(user_query),
        "urgency": assess_urgency(user_query),
        "skill_level": infer_skill_level(user_query, context),
    }
    
    return intent
```

### **Step 2: Route to Appropriate Tool**

```python
def route_query(intent):
    """
    Delegate to specialized tool based on problem type.
    """
    
    ROUTING_TABLE = {
        "conflict": ConflictDetector,      # Mod conflicts
        "load_order": LOOTParser,          # Load order optimization
        "missing_mod": SearchEngine,       # Find missing mods
        "quest_help": WalkthroughManager,  # UESP citations
        "performance": SystemImpact,       # FPS/stability analysis
        "setup": QuickstartGuide,          # Installation guides
        "unknown": CommunityEscalation,    # Human experts
    }
    
    tool = ROUTING_TABLE.get(intent["problem_type"])
    return tool.process(intent)
```

### **Step 3: Generate Response with Citations**

```python
def generate_response(analysis, intent):
    """
    Format response with:
    - Clear problem statement
    - Prioritized solutions
    - Specific citations (not vague links)
    - Actionable next steps
    - Confidence level
    """
    
    response = {
        "summary": summarize_problem(analysis),
        "severity": analysis.severity,  # critical, error, warning, info
        "solutions": [],
        "citations": [],
        "next_steps": [],
        "confidence": analysis.confidence_score,
    }
    
    # Add solutions in priority order
    for solution in analysis.solutions:
        response["solutions"].append({
            "step": solution.step_number,
            "action": solution.action,
            "rationale": solution.why,
            "citation": solution.citation,  # MUST have this
        })
    
    # Add citations (academic format)
    for source in analysis.sources:
        response["citations"].append({
            "url": source.url,  # Specific section anchor
            "title": source.title,
            "location": source.specific_location,  # §3.2, timestamp, etc.
            "date": source.date,
            "reliability": source.reliability_score,
        })
    
    return response
```

---

## 🎯 Problem Classification Matrix

| Problem Type | Keywords | Tool | Citation Source |
|--------------|----------|------|-----------------|
| **Conflict** | "crash", "conflict", "not working", "error" | ConflictDetector | LOOT masterlist, mod pages |
| **Load Order** | "load order", "sort", "LOOT", "order" | LOOTParser | LOOT docs, mod requirements |
| **Missing Mod** | "need", "require", "missing", "where" | SearchEngine | Nexus mod pages |
| **Quest Help** | "stuck", "quest", "how to", "where is" | WalkthroughManager | UESP (specific section) |
| **Performance** | "fps", "lag", "stutter", "slow" | SystemImpact | Hardware databases, benchmarks |
| **Setup** | "install", "setup", "configure", "start" | QuickstartGuide | Mod installation guides |
| **Unknown** | Unclear or beyond scope | CommunityEscalation | Human experts, Reddit |

---

## 📊 Confidence Scoring

The agent MUST report confidence level:

```python
CONFIDENCE_LEVELS = {
    0.9 - 1.0: "HIGH - Verified data (LOOT, UESP, official sources)",
    0.7 - 0.9: "MEDIUM - Community consensus, multiple sources agree",
    0.5 - 0.7: "LOW - Single source, unverified user report",
    0.0 - 0.5: "VERY LOW - Speculation, admit uncertainty",
}
```

**Rules:**
- If confidence < 0.8 → Say "I'm not certain, but..."
- If confidence < 0.5 → Escalate to human experts
- Never bluff — admit when you don't know

---

## 🔗 Citation Standards (Non-Negotiable)

### **Bad Citation (Never Do This):**
```
❌ "Check UESP for more info."
❌ "https://en.uesp.net/wiki/Skyrim" (homepage link)
❌ "Watch a YouTube tutorial" (no link)
```

### **Good Citation (Always Do This):**
```
✅ "According to UESP's Bleak Falls Barrow guide, section 'The Pillar Puzzle':
   https://en.uesp.net/wiki/Skyrim:Bleak_Falls_Barrow_(quest)#The_Pillar_Puzzle
   (§Solution: Snake, Snake, Whale)"

✅ "IGN's walkthrough shows the golden claw location at 2:22:
   https://www.youtube.com/watch?v=8X7kZGvLqKE?t=142
   (timestamp 2:22, accessed 2026-02-17)"
```

### **Citation Metadata (Always Include):**
```json
{
  "url": "https://en.uesp.net/...#Specific_Section",
  "title": "Page Title — Specific Section",
  "source_type": "uesp",
  "specific_location": "§3.2 or timestamp 2:34",
  "date": "2023-11-15",
  "accessed": "2026-02-17",
  "reliability_score": 1.0
}
```

---

## 🚨 Escalation Protocol

When to escalate to humans:

1. **Confidence < 0.5** — "I'm not certain about this..."
2. **Beyond scope** — Quest bugs, save corruption, mod author decisions
3. **Conflicting sources** — UESP says X, mod author says Y
4. **User requests human** — "Can I talk to a person?"
5. **Safety concerns** — Potential save game corruption, data loss

**Escalation format:**
```
"I'm not certain about this [confidence: 0.4]. 
This might be a [problem type] issue, but I'd recommend:

1. Posting in the community tab with your mod list
2. Checking [specific UESP section] for more details
3. Asking the mod author on Nexus (they know best)

Here's what I do know: [certain information with citations]"
```

---

## 📝 Response Templates

### **Template 1: Conflict Detection**
```
**Problem:** [Mod A] and [Mod B] conflict — [specific issue]

**Severity:** [ERROR/WARNING/INFO]

**Solution:**
1. [Action step 1]
   - Why: [rationale]
   - Source: [citation with specific URL]

2. [Action step 2]
   - Why: [rationale]
   - Source: [citation]

**Next Steps:**
- [What to do after fixing]
- [How to verify fix worked]

**Confidence:** [0.9/1.0 — LOOT masterlist data]
```

### **Template 2: Quest Help**
```
**Stuck at:** [Quest name — Specific objective]

**Solution:** [Clear, concise answer]

**Source:** 
- [UESP section title](https://uesp.net/...#Specific_Section)
- Location: §[section number]
- Accessed: [date]

**Video Guide:**
- [Title](https://youtube.com/...?t=[timestamp])
- Timestamp: [mm:ss] — [what happens at this moment]

**Mod Compatibility:**
- [Mod X] changes this area — [specific change]
- Source: [Nexus post/guide link]
```

### **Template 3: Performance Issue**
```
**Problem:** [FPS/stutter/crash] with [X] mods

**Analysis:**
- Estimated VRAM: [X] GB (your GPU: [Y] GB)
- Plugin count: [X]/254
- Complexity: [low/medium/high]

**Recommendations:**
1. [Action] → Expected improvement: [+X FPS]
   - Source: [benchmark/citation]

2. [Action] → Expected improvement: [reduced stutter]
   - Source: [citation]

**Confidence:** [0.7/1.0 — Based on [X] similar reports]
```

---

## 🧪 Quality Checks (Before Responding)

```python
def quality_check(response):
    """
    Verify response meets standards before sending.
    """
    
    checks = [
        ("Has specific citations", len(response.citations) > 0),
        ("Citations have URLs", all(c.url for c in response.citations)),
        ("Citations have locations", all(c.specific_location for c in response.citations)),
        ("Confidence reported", response.confidence is not None),
        ("Actionable steps", len(response.solutions) > 0),
        ("No vague links", all("#" in c.url or "?" in c.url for c in response.citations)),
        ("Admits uncertainty", response.confidence < 0.8 or "not certain" in response.summary),
    ]
    
    failed = [name for name, passed in checks if not passed]
    
    if failed:
        logger.warning(f"Response failed quality checks: {failed}")
        # Fix or escalate
    
    return len(failed) == 0
```

---

## 🎯 Success Metrics

How we measure if the agent is doing its job:

1. **Resolution Rate** — % of problems solved without escalation
2. **Citation Quality** — % of responses with specific (not vague) citations
3. **User Satisfaction** — Ratings, feedback scores
4. **Confidence Accuracy** — Does 0.9 confidence actually mean 90% correct?
5. **Escalation Appropriateness** — Are we escalating when we should?
6. **Response Time** — Fast enough to be helpful, slow enough to be accurate

---

## 💡 Core Principles

1. **Specific over vague** — Always link to exact section, not homepage
2. **Cite everything** — No claims without sources
3. **Admit uncertainty** — Better to say "I don't know" than bluff
4. **Prioritize by severity** — Fix crashes before optimization
5. **Delegate appropriately** — Use right tool for each problem
6. **Actionable over theoretical** — Tell them what to DO
7. **Escalate when needed** — Humans for edge cases
8. **Learn from feedback** — Improve from user corrections

---

**This is the rational. This is the process. This is how we become the best AI modding assistant.**

No bullshit. No vague links. No bluffing. Just accurate, cited, actionable help.

---

## 🌐 Web Fallback Integration

### **Local-First, Cloud-Optional Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│  USER QUERY                                                 │
└─────────────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────────┐
│  1. CHECK LOCAL DB (fast, offline)                          │
│     - Mod metadata                                          │
│     - Conflict patterns (learned)                           │
│     - User profiles                                         │
│     - Cached web data                                       │
│     Confidence: 0.9+ (if found)                             │
└─────────────────────────────────────────────────────────────┘
              ↓ (not found or confidence < 0.8)
┌─────────────────────────────────────────────────────────────┐
│  2. WEB FALLBACK (parallel queries)                         │
│     - Nexus API (mod info, requirements)                    │
│     - UESP (quest help, game mechanics)                     │
│     - LOOT masterlist (load order rules)                    │
│     - Reddit/Discord (community knowledge)                  │
│     Confidence: 0.7-0.9 (verified sources)                  │
└─────────────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────────┐
│  3. CACHE RESULTS (for next time)                           │
│     - TTL-based expiration                                  │
│     - Size limits (LRU eviction)                            │
│     - Offline mode support                                  │
└─────────────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────────┐
│  4. RESPOND WITH CITATIONS                                  │
│     - Source URLs (specific sections)                       │
│     - Reliability scores                                    │
│     - Access dates                                          │
└─────────────────────────────────────────────────────────────┘
```

### **Fallback Decision Tree**

```python
async def process_with_fallback(user_query, context):
    # LOCAL FIRST (fast, offline-capable)
    local_result = await local_db.query(user_query)
    if local_result and local_result.confidence > 0.8:
        return format_response(local_result, source="local")
    
    # WEB FALLBACK (parallel queries)
    web_results = await asyncio.gather(
        nexus_api.search(user_query),
        uesp_scraper.search(user_query),
        loot_masterlist.search(user_query),
        return_exceptions=True,
    )
    
    # Aggregate results
    best_result = aggregate_results(web_results)
    if best_result:
        # Cache for next time
        await local_db.cache(user_query, best_result)
        return format_response(best_result, source="web")
    
    # COMMUNITY ESCALATION (last resort)
    return await escalate_to_community(user_query)
```

### **Caching Strategy**

| Data Type | TTL | Max Size | Eviction |
|-----------|-----|----------|----------|
| Nexus mod info | 1 hour | 100MB | LRU |
| UESP pages | 24 hours | 50MB | LRU |
| LOOT rules | 7 days | 10MB | LRU |
| User profiles | Permanent | 500MB | Manual |
| Conflict patterns | Permanent | 200MB | Manual |

### **Offline Mode**

When internet unavailable:
1. Use local DB only
2. Mark responses as "offline mode" (lower confidence)
3. Queue web queries for when online
4. Notify user: "Some features limited offline"

### **Example Flow**

```
User: "What's the load order for Ordinator?"

1. CHECK LOCAL → Found in cache (from previous user)
   Confidence: 0.95
   Response: "Ordinator should load after USSEP, before compatibility patches"
   Citation: LOOT masterlist (cached 2 hours ago)

2. If NOT in local → WEB FALLBACK
   Query Nexus API → Mod page requirements
   Query LOOT masterlist → Load order rules
   Aggregate → Confidence: 0.9
   Cache result → Next time will be local
   Response: "According to LOOT masterlist and Nexus mod page..."

3. If WEB FAILS → COMMUNITY ESCALATION
   "I couldn't find definitive info. Let me connect you with the community..."
   Post to community tab
   Notify when humans respond
```

---

## 🎯 Competitive AI Techniques (Leapfrog Moments)

### **1. Retrieval-Augmented Generation (RAG)**
**Like**: ChatGPT with browsing, Perplexity  
**Our Implementation**:
- Local DB = Retrieved context
- Web fallback = Live browsing
- Agent = Synthesis + citation

### **2. Chain-of-Thought Reasoning**
**Like**: Google Gemini, Claude  
**Our Implementation**:
```
Problem → Categorize → Retrieve → Analyze → Prioritize → Delegate → Cite → Respond
```
Every step is explicit, auditable, improvable.

### **3. Confidence Calibration**
**Like**: Scientific AI systems  
**Our Implementation**:
- Report confidence (0-1) with every response
- Admit uncertainty (< 0.8)
- Escalate when unsure (< 0.5)
- Never bluff

### **4. Multi-Source Aggregation**
**Like**: Consensus, Elicit  
**Our Implementation**:
- Query multiple sources in parallel
- Aggregate with reliability weighting
- Cite all sources (not just one)
- Show disagreements (if any)

### **5. Continuous Learning**
**Like**: Character.AI, Replika  
**Our Implementation**:
- Learn from user corrections
- Improve conflict predictions
- Adapt to playstyle
- Community knowledge sharing

---

**This is how we compete with the big wigs. Not by copying — by leapfrogging.**

**Local-first + Web fallback + Academic citations + Safe automation = Unbeatable combination.**
