# SkyModderAI Feature Map

**Last Updated**: February 17, 2026  
**Model**: 100% Free + Donations (No Tiers, No Subscriptions, No Bullshit)

---

## 🎯 What We Are (And What We're Not)

### ✅ What We ARE:
1. **Mod Compatibility Engine** — LOOT-based conflict detection + AI learning
2. **Link Aggregator** — Connects to Nexus, UESP, wikis, guides (we don't duplicate)
3. **Specialized Data Center** — Mod interactions, conflicts, load order data (unique to us)
4. **AI Training Platform** — OpenCLAW learns from anonymized user sessions

### ❌ What We're NOT:
1. **Bethesda game database** — No quest walkthroughs, item databases, NPC info (UESP does this better)
2. **Content repository** — No tutorials, build guides, screenshots (link instead)
3. **Search engine** — No general web search (Google does this)
4. **Mod hosting** — No mod files (Nexus does this)

**Philosophy:** *"We don't store what others already maintain better. We specialize in what ONLY we can do."*

---

## 💰 Business Model: Free + Donations

**Everything is free. Forever. No catches.**

- ✅ No paywalls
- ✅ No tiers (free, pro, premium, etc.)
- ✅ No subscriptions
- ✅ No "upgrade to unlock"
- ✅ No bullshit

**How we survive:**
- ☕ One-time donations (buy me a coffee)
- 💰 Patreon (optional monthly support)
- 🤝 GitHub Sponsors (optional monthly support)
- 💳 PayPal donations (one-time)

**What donations pay for:**
- Server costs (~$50/mo)
- API costs (~$100/mo)
- Developer ramen budget (~$1,200/mo)

**Philosophy:**
> Modding should be accessible to everyone. This tool is free for every modder, everywhere. If it helps you and you can afford to support it, great. If you're broke (like I was), use it free — no hard feelings, no feature locks, no nagging.
>
> Everyone gets the full power of the site. Period.

---

## Core User Flows

### 1. Mod Analysis Workflow
**Entry Point**: Analyze tab
**Goal**: Identify conflicts, warnings, and optimize load order

**Flow Steps**:
1. User pastes mod list (ESP/ESM files) into text area
2. Selects game, game version, and masterlist version
3. Clicks "Analyze" button
4. System processes list through LOOT data and ConflictDetector
5. Results display with predictive errors, warnings, and deep-dive suggestions
6. User can view suggested load order and fix guides
7. Results include "What to do next" actions

**Key Components**:
- `userContext` maintains current mod list and analysis results
- Context trail shows current state (game, version, warnings)
- HAL+JSON links provide related resources

### 2. Search and Discovery Workflow
**Entry Point**: Search input in Analyze tab
**Goal**: Find mods and quickly add to list or analyze individually

**Flow Steps**:
1. User types mod name in search
2. System queries local database and web suggestions
3. Results show mod names with action buttons:
   - "Add" - Quick add to current list
   - "Analyze" - Analyze single mod for conflicts
   - "Nexus" - Open mod page on Nexus Mods
4. Search added to recent searches in userContext
5. Context trail updates with mod count

**Enhanced Features**:
- Recent searches persistence across sessions
- Quick Add to List functionality
- Single mod analysis with auto-tab switching
- HAL+JSON links in search results

### 3. Saved Lists (Library) Workflow
**Entry Point**: Library tab
**Goal**: Save, organize, and revisit mod configurations with rich metadata

**Flow Steps**:
1. After analysis, user saves list with name, tags, notes
2. System stores full analysis snapshot with:
   - Conflict counts and details
   - Plugin limit warnings
   - System impact analysis
   - Suggested load order
   - Game/version/masterlist metadata
3. Library displays cards showing:
   - Health indicators (Clean/Warnings/Errors)
   - Analysis date and mod count
   - Tags and notes
4. User can load, rename, edit metadata, or delete lists
5. One-click re-analysis of saved lists

**Enhanced Features**:
- Analysis snapshots preserved as research artifacts (The "Bins")
- Health indicators for quick assessment
- Rich metadata filtering and search
- Cross-tab synchronization via userContext

### 4. Build-a-List Workflow
**Entry Point**: Build a List tab
**Goal**: Generate mod lists based on preferences

**Flow Steps**:
1. User selects preference options (gameplay style, mods types)
2. System generates base mod list
3. AI generates bespoke setup variations tailored to user specs
4. List can be analyzed and saved to Library

### 5. Community Engagement Workflow
**Entry Point**: Community tab
**Goal**: Share knowledge and get help

**Flow Steps**:
1. Browse community posts by tags or search
2. Post questions or share solutions
3. View community health metrics

## Technical Architecture

### Unified User Context (`userContext`)
**Location**: `static/js/app.js` (lines 16-185)
**Purpose**: Single source of truth for application state

**Properties**:
- `selectedGame`, `gameVersion`, `masterlistBranch`
- `currentModList`, `currentModListParsed`
- `lastAnalysisResult`, `lastAnalysisTime`
- `savedLists`, `currentSavedList`
- `searchQuery`, `searchResults`, `recentSearches`
- `activeTab`, `filterState`

**Features**:
- localStorage persistence
- Cross-tab synchronization via storage events
- Automatic UI updates via custom events

### Context-Aware Navigation
**Location**: Sticky header (templates/index.html + CSS/JS)
**Purpose**: Show current context path and provide quick navigation

**Display Elements**:
- Game selector (clickable)
- Game version (clickable)
- Masterlist branch (clickable)
- Mod count (clickable - focuses input)
- Error/warning counts (clickable - scrolls to sections)
- Current saved list (clickable - opens Library)

### HAL+JSON API Links
**Purpose**: Hypermedia-driven API navigation

**Endpoints with Links**:
- `/api/analyze` - Links to search, build, save, solutions
- `/api/search` - Links to Nexus, conflicts, solutions, add to list
- `/api/info` - Self-documenting API discovery

**Link Types**:
- `self` - Current resource
- `search` - Related search endpoints
- `analyze` - Analysis actions
- `solutions` - Conflict resolution searches
- `nexus` - External mod pages
- `add_to_list` - Client-side actions

### Database Schema

#### user_saved_lists Table
```sql
CREATE TABLE user_saved_lists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT NOT NULL,
    name TEXT NOT NULL,
    game TEXT,
    game_version TEXT,
    masterlist_version TEXT,
    tags TEXT,
    notes TEXT,
    preferences_json TEXT,
    source TEXT,
    list_text TEXT NOT NULL,
    analysis_snapshot TEXT,  -- JSON of full analysis results
    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_email, name)
)
```

## API Endpoints

### Core Analysis
- `POST /api/analyze` - Analyze mod list for conflicts
- `GET /api/games` - Get supported games list
- `GET /api/info` - Machine-readable feature discovery

### Search and Discovery
- `GET /api/search` - Search mods with BM25 ranking
- `GET /api/mod-search` - Legacy mod search endpoint
- `GET /api/recommendations` - Get mod recommendations

### List Management
- `GET /api/list-preferences` - List saved mod lists
- `POST /api/list-preferences` - Save new mod list with analysis
- `PATCH /api/list-preferences` - Update metadata
- `DELETE /api/list-preferences` - Delete saved list

### Build and Community
- `POST /api/build-list` - Generate mod lists from preferences
- `GET|POST /api/community/posts` - Community posts
- `GET /api/list-preferences/options` - Build preference options

## Frontend Components

### Tab System
**Main Tabs**: Analyze, Quick Start, Build a List, Library, Community, Dev Tools
**Implementation**: Vanilla JS with event delegation
**State Management**: userContext.activeTab

### Search System
**Components**:
- Search input with debouncing
- Results dropdown with action buttons
- Recent searches persistence

**Features**:
- Quick Add to List
- Single Mod Analysis
- Web suggestions (fallback)

### Library System
**The "Bins"**:
- Organized storage for user configurations
- Data refinement cycle for learning new conflicts

**Components**:
- Filter controls (game, version, masterlist)
- Card grid with health indicators
- Modal for editing metadata

**Features**:
- Analysis snapshot display
- Health-based visual indicators
- Rich metadata search

## CSS Architecture

### Design System
**CSS Variables**: Centralized color scheme and spacing
**Responsive Design**: Mobile-first approach with breakpoints
**Component Styles**: Modular, reusable component classes

### Key Style Categories
- **Context Trail**: Breadcrumb navigation with hover states
- **Search Results**: Action buttons and hover interactions
- **Library Cards**: Health indicators and metadata display
- **Analysis Results**: Color-coded conflict items

## Integration Points

### Assistant-Friendly Features
1. **`/api/info` Endpoint**: Complete API documentation
2. **Structured Comments**: Code organized with clear sections
3. **HAL+JSON Links**: Discoverable related resources
4. **Agent Window**: Context-aware AI companion reading the page
4. **Feature Map**: This documentation file

### Cross-Tab Features
1. **userContext Sync**: Shared state across browser tabs
2. **Analysis Persistence**: Results available in all tabs
3. **Search History**: Recent searches shared globally

### Automation Support
1. **OpenClaw Integration**: Advanced automation features
2. **API Consistency**: Standardized response formats
3. **Error Handling**: Comprehensive error responses
4. **Rate Limiting**: Fair usage enforcement

## Development Guidelines

### Code Organization
- **Backend**: Flask app with modular route handlers
- **Frontend**: Vanilla JS with component-like functions
- **Database**: SQLite with migration support
- **Styling**: CSS variables and modular classes

### Best Practices
1. **User Context First**: Always update userContext for state changes
2. **HAL+JSON Links**: Include related resources in API responses
3. **Error Boundaries**: Graceful degradation for missing features
4. **Progressive Enhancement**: Core functionality works without JS

### Testing Considerations
1. **Cross-Tab Sync**: Test userContext synchronization
2. **API Links**: Verify HAL+JSON link accessibility
3. **Analysis Snapshots**: Test save/load of analysis data
4. **Mobile Responsive**: Test all flows on mobile devices

## Future Enhancements

### Planned Features
1. **Research Cards**: Enhanced search result presentation
2. **Advanced Filtering**: More granular library search
3. **Export/Import**: List sharing between users
4. **Real-time Collaboration**: Multi-user list editing

### Technical Debt
1. **Component Framework**: Consider migration to component library
2. **State Management**: Evaluate Redux/Zustand for complex state
3. **API Versioning**: Implement versioned API endpoints
4. **Testing Suite**: Add comprehensive test coverage

---

This feature map serves as a guide for understanding SkyModderAI's capabilities and architecture. It's designed to help developers, assistants, and contributors navigate the codebase and extend functionality effectively.
