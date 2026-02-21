#!/bin/bash
# SkyModderAI - Development Clutter Cleanup Script
# 
# This removes mid-development documentation that users don't need to see.
# Keeps: README, CONTRIBUTING, LICENSE, CODE_OF_CONDUCT, SECURITY, ARCHITECTURE, PHILOSOPHY, SCALING_GUIDE, SAMSON_MANIFESTO
# Removes: All other .md files that are development artifacts

set -e

echo "🧹 SkyModderAI - Cleaning up development clutter..."
echo ""

# Count files to be removed
FILES_TO_REMOVE=(
    "ACTUALLY_FREE.md"
    "ACTUAL_MARKETING.md"
    "ADS_QUARANTINED_COMPLETE.md"
    "ALL_ERRORS_FIXED.md"
    "AUTHENTIC_FREE_IMPLEMENTATION.md"
    "BESPOKE_DYNAMIC_AUDIT.md"
    "BUSINESS_IMPLEMENTATION_COMPLETE.md"
    "BUSINESS_OVERHAUL_COMPLETE.md"
    "BUSINESS_OVERHAUL_PLAN.md"
    "COMMUNITY_BUILDS_IMPLEMENTATION.md"
    "COMMUNITY_LINK_FIX.md"
    "COMMUNITY_TAB_FRONT_CENTER.md"
    "COMPLETE_FIXES_SUMMARY.md"
    "COMPLETE_REMEDIATION_PLAN.md"
    "CONSISTENCY_FIXES.md"
    "CONSISTENCY_GUIDE.md"
    "DEEP_CODEBASE_AUDIT.md"
    "DEPLOYMENT_CHECKLIST.md"
    "DEVELOPMENT_NOTES.md"
    "DONATION_BRANDING_UPDATE.md"
    "FEATURE_MAP.md"
    "FINAL_DOCUMENTATION.md"
    "FINAL_MARKETING_STRUCTURE.md"
    "FULL_LINK_AUDIT_FIXES.md"
    "FUTURE_DIRECTION.md"
    "IMPLEMENTATION_SPRINT_SUMMARY.md"
    "MARKETING_PASS_COMPLETE.md"
    "MARKETING_PASS_FINAL_SUMMARY.md"
    "MARKETING_STRATEGY.md"
    "NON_IMPLEMENTED_FEATURES_AUDIT.md"
    "QUICKSTART_DEVELOPER.md"
    "REMEDIATION_SUMMARY.md"
    "SAMSON_IMPLEMENTATION.md"
    "SHOPPING_IMPLEMENTATION_COMPLETE.md"
    "SPONSOR_SUPPORT_MESSAGE_COMPLETE.md"
    "STATUS_AND_ACTION_PLAN.md"
    "UX_IMPROVEMENTS_COMPLETE.md"
)

echo "📁 Files to remove: ${#FILES_TO_REMOVE[@]}"
echo ""

# Remove each file
for file in "${FILES_TO_REMOVE[@]}"; do
    if [ -f "$file" ]; then
        rm "$file"
        echo "✓ Removed: $file"
    else
        echo "⊘ Skipped (not found): $file"
    fi
done

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "📊 Remaining documentation:"
ls -la *.md 2>/dev/null | awk '{print "  " $NF}' || echo "  (no .md files found)"
echo ""
echo "💡 Tip: Run 'git status' to see what was cleaned up."
