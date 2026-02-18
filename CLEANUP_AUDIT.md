# Repository Cleanup Audit

**Date**: 2026-02-18

---

## 🗑️ Recommended Deletions

### 1. Redundant Summary Documentation (6 files)
These served their purpose but are now historical clutter:

```
AGENT_RATIONAL.md                      # AI decision process (583 lines)
PROJECT_AUDIT.md                       # Session audit (494 lines)
COMPLETE_IMPLEMENTATION_SUMMARY.md     # Session 1 summary (575 lines)
IMPLEMENTATION_SUMMARY.md              # Implementation summary (291 lines)
CONTEXT_THREADING_SUMMARY.md           # Feature summary (410 lines)
OPENCLAW_COMING_SOON.md                # Outdated announcement (260 lines)
```

**Total**: ~2,600 lines of documentation to remove

**Keep instead**:
- `CLEANUP_SUMMARY.md` - Current status
- `FEATURE_MAP.md` - Active feature documentation
- `PHILOSOPHY.md` - Core principles
- `ARCHITECTURE_DECISION.md` - Architecture decisions
- `FREE_DONATIONS_MODEL.md` - Business model

---

### 2. Empty Folders (3 folders)

```
scripts/              # Empty
db_backups/           # Empty
research/ingest/      # Only has README.md
```

---

### 3. Dev Folder - Vision/Plan Docs (7 files)

OpenCLAW vision documents that are mostly aspirational:

```
dev/OPENCLAW_OPENSOURCE_AI.md          # 22KB - Vision doc
dev/OPENCLAW_LOCAL_PLAN.md             # 22KB - Implementation plan
dev/OPENCLAW_ML_COMPLETE.md            # 13KB - ML documentation
dev/OPENCLAW_INTEGRATION_GUIDE.md      # 14KB - Integration guide
dev/IMPROVEMENTS_SUMMARY.md            # 15KB - Improvements list
dev/SAMSON_VISION.md                   # 13KB - Vision doc
dev/THE_WEED_MODEL.md                  # 10KB - Model doc
```

**Keep**:
- `dev/README.md` - Main dev documentation
- `dev/openclaw/` - Actual code implementation

---

### 4. Migration Files (2 files - verify first)

Check if these have been applied:
```
migrations/0003_add_shared_load_orders.sql
migrations/0004_oauth_state_tokens.sql
```

If applied, can be removed or moved to `migrations/applied/`

---

### 5. Gitignore Updates

Add to `.gitignore`:
```
# Test caches
tests/__pycache__/
tests/.pytest_cache/

# Development
*.pyc
__pycache__/
*.swp
*.swo
*~

# IDE
.idea/
.vscode/
*.sublime-*

# OS
.DS_Store
Thumbs.db
```

---

## 📊 Impact Summary

### Before Cleanup
- **Root markdown files**: 14 files (4,362 lines)
- **Dev docs**: 7 files (~100KB)
- **Empty folders**: 3

### After Cleanup
- **Root markdown files**: 8 files (~2,000 lines)
- **Dev docs**: 1 file (README.md) + openclaw/ code
- **Empty folders**: 0

### Reduction
- **~50% less documentation clutter**
- **~2,600 lines removed**
- **3 empty folders deleted**
- **7 vision docs archived**

---

## ✅ What to Keep

### Core Documentation (8 files)
| File | Purpose |
|------|---------|
| `README.md` | Main entry point |
| `PHILOSOPHY.md` | Core principles |
| `FEATURE_MAP.md` | Feature architecture |
| `CONTRIBUTING.md` | Contribution guide |
| `SECURITY.md` | Security policy |
| `ARCHITECTURE_DECISION.md` | Architecture decisions |
| `FREE_DONATIONS_MODEL.md` | Business model |
| `CLEANUP_SUMMARY.md` | Current cleanup status |

### Technical Documentation (docs/ folder)
| File | Purpose |
|------|---------|
| `docs/README.md` | Docs index |
| `docs/architecture.md` | System architecture |
| `docs/build.md` | Build instructions |
| `docs/models.md` | Data models |
| `docs/SECURITY.md` | Technical security |
| `docs/RESEARCH_SUMMARY.md` | Research documentation |

### Development (dev/ folder)
| File | Purpose |
|------|---------|
| `dev/README.md` | Dev documentation |
| `dev/openclaw/` | OpenCLAW code |

---

## 🚀 Cleanup Commands

```bash
# Remove redundant summaries
rm AGENT_RATIONAL.md
rm PROJECT_AUDIT.md
rm COMPLETE_IMPLEMENTATION_SUMMARY.md
rm IMPLEMENTATION_SUMMARY.md
rm CONTEXT_THREADING_SUMMARY.md
rm OPENCLAW_COMING_SOON.md

# Remove empty folders
rmdir scripts
rmdir db_backups
rmdir research/ingest

# Remove dev vision docs (keep README and openclaw/)
rm dev/OPENCLAW_OPENSOURCE_AI.md
rm dev/OPENCLAW_LOCAL_PLAN.md
rm dev/OPENCLAW_ML_COMPLETE.md
rm dev/OPENCLAW_INTEGRATION_GUIDE.md
rm dev/IMPROVEMENTS_SUMMARY.md
rm dev/SAMSON_VISION.md
rm dev/THE_WEED_MODEL.md

# Update .gitignore (add test caches and IDE files)
```

---

## 📝 Notes

1. **Don't delete** `FEATURE_MAP.md` - It's actively used for feature planning
2. **Don't delete** `PHILOSOPHY.md` - Core principles document
3. **Don't delete** `ARCHITECTURE_DECISION.md` - Important architectural decisions
4. **Verify migrations** before deleting - check if they've been applied
5. **Keep dev/openclaw/** - Actual implementation code

---

**Status**: Ready for cleanup
**Estimated time**: 5 minutes
**Risk**: Low (all documentation, no code)
