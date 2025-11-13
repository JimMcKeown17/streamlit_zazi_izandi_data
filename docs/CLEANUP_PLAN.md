# Project Cleanup Plan

**Analysis Date:** November 13, 2025

This document provides a comprehensive analysis of files to clean up, organize, or archive in the project.

---

## 🔍 Analysis Summary

### Files Analyzed
- **Total .md files in root:** 5
- **Test files:** 9
- **Inspect files:** 2
- **Duplicate files:** 2
- **Old data files:** 1

---

## 📁 Recommended Actions

### 1. CREATE NEW FOLDERS

#### `/docs` - For Documentation Files
Move all markdown documentation here for better organization.

#### `/archive` - For Old/Unused Files
Safe place for files we're not ready to delete but don't need in root.

#### `/tests_and_utils` - For Test & Utility Scripts
Consolidate all test and inspection files.

---

## 📄 Markdown Files - Move to `/docs`

### Currently in Root (5 files)
| File | Status | Action | Priority |
|------|--------|--------|----------|
| `CLAUDE.md` | Documentation | Move to `/docs` | Medium |
| `database_notes.md` | Documentation | Move to `/docs` | Medium |
| `DATA_SOURCE_AUDIT.md` | Documentation | Move to `/docs` | Medium |
| `DATA_SOURCES_DOCUMENTATION.md` | Documentation | **Keep in root** or move to `/docs` | Low |
| `PARQUET_OPTIMIZATION_SUMMARY.md` | Documentation | Move to `/docs` | Medium |

### In Subdirectories (Keep these where they are)
- `api/New_Mentor_Survey_README.md` ✅
- `new_pages/2025/NMB_ENDLINE_COHORT_ANALYSIS_README.md` ✅
- All zazi_agents/*.md files ✅

**Recommendation:** Create `/docs` folder and move root-level markdown files there, EXCEPT `DATA_SOURCES_DOCUMENTATION.md` which could stay in root as it's the main reference.

---

## 🧪 Test Files - Move to `/tests_and_utils`

### Root Level Test Files (5 files)
| File | Used? | Action | Priority |
|------|-------|--------|----------|
| `test_letter_page.py` | ❌ No | Move to `/tests_and_utils` | **HIGH** |
| `test_east_london_api.py` | ❌ No | Move to `/tests_and_utils` | **HIGH** |
| `test_to_pdf.py` | ❌ No | Move to `/tests_and_utils` | **HIGH** |
| `teampact_inspect.py` | ❌ No | Move to `/tests_and_utils` | **HIGH** |
| `teampact_inspect_quick.py` | ❌ No | Move to `/tests_and_utils` | **HIGH** |

### In `/scripts` (Keep these - already organized)
- `scripts/test_agent.py` ✅
- `scripts/test_parquet_loading.py` ✅
- `scripts/verify_data_integrity.py` ✅
- `scripts/convert_to_parquet.py` ✅

### In Subdirectories (Keep these - part of their modules)
- `new_pages/ea_sessions_test.py` ✅ (Used in main.py)
- `older_pages/older pages/10_Test_Page.py` ✅ (Already archived)
- `zazi_agents/literacy_coach_mentor/test_agent.py` ✅ (Part of agent module)
- `older scripts/display_24_test.py` ✅ (Already archived)

---

## 🗑️ Files to DELETE (Safe to Remove)

### Duplicate Files
| File | Reason | Action | Priority |
|------|--------|--------|----------|
| `data_loader copy.py` | Duplicate of data_loader.py | **DELETE** | **HIGH** |

### Old Data Files
| File | Reason | Action | Priority |
|------|--------|--------|----------|
| `merged_data_2025-01-29.csv` | Old merged data from January | Move to `/archive` or **DELETE** | Medium |

### Utility Scripts (Move to `/tests_and_utils`)
| File | Used? | Action | Priority |
|------|-------|--------|----------|
| `print_tree.py` | Utility script | Move to `/tests_and_utils` | Medium |
| `structure.txt` | Old snapshot | Move to `/archive` or **DELETE** | Low |

---

## ⚠️ KEEP - Actively Used Files (DO NOT MOVE/DELETE)

### Core Processing Files (Root Level)
| File | Used By | Keep in Root |
|------|---------|--------------|
| `zz_data_processing.py` | 2024 pages, agents, Year Comparisons, Research | ✅ YES |
| `zz_data_process_23.py` | 2023 pages, agents, scripts | ✅ YES |
| `process_survey_cto_updated.py` | 2025 pages (SurveyCTO data) | ✅ YES |
| `process_teampact_data.py` | 2025 TeamPact pages | ✅ YES |
| `data_loader.py` | All pages (main data loader) | ✅ YES |
| `database_utils.py` | Database pages, sessions | ✅ YES |
| `db_api_get_sessions.py` | 2025 Sessions page | ✅ YES |
| `create_letter_tracker.py` | Midline, Baseline pages | ✅ YES |
| `letter_tracker_htmls.py` | Some baseline pages | ✅ YES |
| `grouping_logic.py` | process_survey_cto_updated.py | ✅ YES |
| `main.py` | Main app entry | ✅ YES |
| `requirements.txt` | Dependencies | ✅ YES |

### Possibly Unused (Need Verification)
| File | Check Usage | Action if Unused |
|------|-------------|------------------|
| `display_23.py` | Only imported once in display_23.py (circular?) | Move to `/archive` |
| `display_home.py` | Used by older_pages/pages_nav/home_page.py | Keep for now (older_pages compatibility) |

---

## 📦 Already Organized (Good Structure - Keep As Is)

### `/older_pages` ✅
- All old page versions properly archived
- Good separation from active code

### `/older scripts` ✅
- Old scripts properly separated
- Contains: main-orig.py, main-orig2.py, display_24.py, etc.

### `/scripts` ✅
- Utility and test scripts
- Convert to parquet, test loaders, verify integrity

### `/api` ✅
- API integration code
- Well organized with own subfolder

### `/zazi_agents` ✅
- Agent code with own structure
- Each agent has own folder with docs

### `/data_utility_functions` ✅
- Data utility code
- Clean separation of concerns

---

## 📋 Recommended Folder Structure After Cleanup

```
/Users/jimmckeown/Development/ZZ Data Site/
├── docs/                              # NEW - All documentation
│   ├── CLAUDE.md
│   ├── database_notes.md
│   ├── DATA_SOURCE_AUDIT.md
│   ├── PARQUET_OPTIMIZATION_SUMMARY.md
│   └── cleanup_history/               # Optional: track cleanup changes
│       └── CLEANUP_PLAN.md
│
├── tests_and_utils/                   # NEW - Test & utility files
│   ├── test_letter_page.py
│   ├── test_east_london_api.py
│   ├── test_to_pdf.py
│   ├── teampact_inspect.py
│   ├── teampact_inspect_quick.py
│   ├── print_tree.py
│   └── structure.txt
│
├── archive/                           # NEW - Old files not ready to delete
│   ├── merged_data_2025-01-29.csv
│   ├── display_23.py (if unused)
│   └── display_home.py (if unused)
│
├── api/                               # Keep as is
├── assets/                            # Keep as is
├── data/                              # Keep as is
├── data_utility_functions/            # Keep as is
├── new_pages/                         # Keep as is
├── older_pages/                       # Keep as is
├── older scripts/                     # Keep as is
├── scripts/                           # Keep as is
├── zazi_agents/                       # Keep as is
├── venv/                              # Keep as is
│
├── main.py                            # Keep in root
├── data_loader.py                     # Keep in root
├── database_utils.py                  # Keep in root
├── zz_data_processing.py              # Keep in root
├── zz_data_process_23.py              # Keep in root
├── process_survey_cto_updated.py      # Keep in root
├── process_teampact_data.py           # Keep in root
├── db_api_get_sessions.py             # Keep in root
├── create_letter_tracker.py           # Keep in root
├── letter_tracker_htmls.py            # Keep in root
├── grouping_logic.py                  # Keep in root
├── requirements.txt                   # Keep in root
├── DATA_SOURCES_DOCUMENTATION.md      # Keep in root (main reference)
└── .gitignore                         # Keep in root
```

---

## 🎯 Cleanup Phases

### Phase 1: IMMEDIATE (High Priority) - Safe Deletions
1. ✅ **DELETE** `data_loader copy.py` (duplicate)
2. ✅ Create `/tests_and_utils` folder
3. ✅ Move 5 test/inspect files from root to `/tests_and_utils`

### Phase 2: ORGANIZATION (Medium Priority) - Documentation
1. ✅ Create `/docs` folder
2. ✅ Move 4 markdown files to `/docs` (keep DATA_SOURCES_DOCUMENTATION.md in root)
3. ✅ Update any hardcoded paths if needed

### Phase 3: ARCHIVE (Low Priority) - Old Files
1. ⚠️ Create `/archive` folder
2. ⚠️ Verify `display_23.py` and `display_home.py` usage
3. ⚠️ Move to archive if truly unused
4. ⚠️ Move `merged_data_2025-01-29.csv` to archive
5. ⚠️ Move `structure.txt` to archive

### Phase 4: VERIFICATION (After Cleanup)
1. ✅ Run the app to ensure nothing broke
2. ✅ Test a few pages from each year (2023, 2024, 2025)
3. ✅ Verify agents still work
4. ✅ Check Project Management pages
5. ✅ Update this document with results

---

## ⚠️ Before Deleting Anything

### Safety Checklist
- [ ] Commit current state to git
- [ ] Create backup branch: `git checkout -b cleanup-backup`
- [ ] Document what you're moving/deleting
- [ ] Test after each phase

### Commands to Run Before Cleanup
```bash
# Create backup branch
git checkout -b cleanup-backup
git add -A
git commit -m "Backup before cleanup"

# Return to main branch
git checkout main

# Create new branch for cleanup
git checkout -b cleanup-2025-11-13
```

---

## 📊 Impact Analysis

### Files Affected by Cleanup
- **Moved:** 10 files
- **Deleted:** 1 file (duplicate)
- **Archived:** 2-4 files (pending verification)
- **Total Changes:** 13-15 files

### Risk Level
- **Low Risk:** Test files, inspect files, utility scripts (not imported)
- **Medium Risk:** Documentation moves (no code dependencies)
- **High Risk:** None (we're keeping all actively used files)

### Breaking Changes
- **Expected:** None
- **Reason:** Only moving files that aren't imported by active code

---

## 🔄 Post-Cleanup Tasks

1. Update `.gitignore` if needed
2. Update README if you create one
3. Consider adding `/docs/README.md` to explain documentation structure
4. Archive this CLEANUP_PLAN.md to `/docs/cleanup_history/`

---

## 📝 Notes

- The `/older_pages` and `/older scripts` folders are already well organized
- Consider eventually moving display_23.py and display_home.py to `/older scripts` if confirmed unused
- Keep `ea_sessions_test.py` in new_pages as it's referenced in main.py
- The `/scripts` folder is already good - contains utility scripts
- Most test files are properly organized in module folders (zazi_agents, etc.)

---

**Next Steps:** Review this plan and proceed with Phase 1 (safest changes first)

