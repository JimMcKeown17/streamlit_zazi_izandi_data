# TeamPact API Assessment Data Mapping — 2026

**Last Updated:** March 3, 2026

This document describes how 2026 assessment data flows from the TeamPact API into the `assessments_2026` database table, with particular focus on how **Grade**, **Programme Name (program_name)**, and **Class Name (class_name)** are resolved.

---

## Overview

Assessment data is synced nightly via the Django management command:
```bash
python manage.py sync_assessments_2026
```

Located at: `Zazi_iZandi_Website_2025/api/management/commands/sync_assessments_2026.py`

The sync involves **two API calls** that are combined:

1. **Survey Responses** — `GET /surveys/{survey_id}/responses` — fetches all assessment answers
2. **Group Lookup** — `GET /groups/{group_id}` — resolves class_name and program_name from group_id

---

## Survey IDs

| Survey ID | Language / Type | Description |
|-----------|----------------|-------------|
| **815** | isiXhosa | Baseline Full Assessment - IsiXhosa |
| **816** | Afrikaans | Baseline Full Assessment - Afrikaans 2026 |
| **817** | English | Baseline Full Assessment - English 2026 |
| **805** | ECD | ZZ ECD Baseline 2026 |
| **824** | N/A | Mentor Visits 2026 (separate sync) |

---

## Two Different Mapping Paths

### Path A: NMB Surveys (815, 816, 817) — Requires Group Lookup

NMB survey responses do **NOT** include `class_name` or `program_name` directly. They provide:

| API Response Field | Contains | Example |
|-------------------|----------|---------|
| `participant_id` | Learner ID | `351549` |
| `participant_name` | Learner full name | `"Aqhama Diniso"` |
| `group_id` | JSON string with group/class ID(s) | `"[59979]"` |
| `group_name` | Always null | `null` |
| `user_name` | EA/collector who administered | `"Asemahle Mancayi"` |
| `user_id` | EA user ID | `28764` |

**To get class_name and program_name**, the sync script:

1. Collects all unique `group_id` values from all NMB responses
2. Parses each `group_id` from its JSON string format (e.g., `"[59979]"` → `59979`)
3. Calls `GET /groups/{group_id}` for each unique group ID
4. Builds a lookup cache: `{group_id: {name, program_name}}`

#### Group API Response → Field Mapping

```
GET /groups/59979 response:
{
  "data": {
    "name": "Grade 1 - Canzibe Primary School",    ← becomes class_name
    "program_id": 1522,
    "program": {
      "name": "Canzibe Primary School",             ← becomes program_name
    }
  }
}
```

| Database Column | Source | Example |
|----------------|--------|---------|
| `class_name` | `groups/{id}.data.name` | `"Grade 1 - Canzibe Primary School"` |
| `program_name` | `groups/{id}.data.program.name` | `"Canzibe Primary School"` |
| `class_id` | First parsed value from `group_id` | `59979` |
| `grade` | **Derived** from `class_name` via substring matching | `"Grade 1"` |

#### Grade Derivation Logic

Grade is **NOT** a direct API field for NMB surveys. It is extracted from `class_name` using this logic (in `extract_grade_from_class_name()`):

```python
if 'Grade R' in class_name:   → 'Grade R'
if 'Grade 1' in class_name:   → 'Grade 1'
if 'Grade 2' in class_name:   → 'Grade 2'
# Fallback: check first character
first_char = class_name.strip()[0].upper()
'R' → 'Grade R'
'1' → 'Grade 1'
'2' → 'Grade 2'
# Otherwise → '' (empty string)
```

#### Participant Name Splitting

The API provides `participant_name` as a single string. The sync splits it:
```python
full_name = "Aqhama Diniso"
first_name = "Aqhama"     # first token
last_name  = "Diniso"     # remainder after first space
```

Gender is **not available** from NMB survey responses — stored as empty string.

---

### Path B: ECD Survey (805) — Direct Fields

ECD survey responses **DO** include `class_name` and `program_name` directly in the API response. No group lookup needed.

However, learner identity (name, grade, gender) is in **free-text answers**, not in participant fields:

| Question ID | Maps To | Description |
|------------|---------|-------------|
| 28183 | `first_name` | Learner first name |
| 28184 | `last_name` | Learner last name |
| 28181 | `grade` | Learner grade (free text) |
| 28185 | `gender` | Learner gender |

| Database Column | Source | Notes |
|----------------|--------|-------|
| `class_name` | `response.class_name` | Direct from API |
| `program_name` | `response.program_name` | Direct from API |
| `grade` | Answer to question 28181 | Free-text, may need normalization |
| `first_name` | Answer to question 28183 | Free-text |
| `last_name` | Answer to question 28184 | Free-text |
| `gender` | Answer to question 28185 | Free-text |
| `participant_id` | Not available | Stored as empty string |

---

## Sync Process (3 Phases)

```
Phase 1: Fetch all NMB survey responses
  └─ GET /surveys/815/responses?page=1..N  (all pages)
  └─ GET /surveys/816/responses?page=1..N
  └─ GET /surveys/817/responses?page=1..N

Phase 2: Build group cache
  └─ Collect unique group_ids from all NMB responses
  └─ GET /groups/{id} for each unique group_id
  └─ Cache: {group_id → {class_name, program_name}}

Phase 3: Flatten & save
  └─ For each NMB response:
      └─ Look up class_name + program_name from group cache
      └─ Derive grade from class_name
      └─ Split participant_name → first_name + last_name
      └─ Extract EGRA sub-test scores from answers
      └─ Save to assessments_2026 + assessment_cells_2026
  └─ For ECD (survey 805): fetch, flatten (direct fields), save
```

---

## Database Schema: assessments_2026

| Column | Type | Source (NMB) | Source (ECD) |
|--------|------|-------------|-------------|
| `response_id` | String | `response.response_id` | `response.response_id` |
| `survey_id` | Integer | `response.survey_id` | `response.survey_id` |
| `survey_name` | String | Hardcoded per survey ID | `"ZZ ECD Baseline 2026"` |
| `participant_id` | String | `response.participant_id` | Empty string |
| `first_name` | String | Split from `participant_name` | Answer Q28183 |
| `last_name` | String | Split from `participant_name` | Answer Q28184 |
| `gender` | String | Empty string (not available) | Answer Q28185 |
| `grade` | String | Derived from `class_name` | Answer Q28181 |
| `language` | String | From `SURVEY_LANGUAGE` map | `"ECD"` |
| `program_name` | String | Group API → `program.name` | Direct from response |
| `class_name` | String | Group API → `data.name` | Direct from response |
| `class_id` | Integer | First parsed `group_id` | None |
| `collected_by` | String | `response.user_name` | `response.user_name` |
| `response_date` | DateTime | `response.response_start_at` | `response.response_start_at` |
| `letters_total_correct` | Integer | EGRA answer | EGRA answer |
| `letters_total_incorrect` | Integer | EGRA answer | EGRA answer |
| `letters_total_attempted` | Integer | EGRA answer | EGRA answer |
| `letters_total_not_attempted` | Integer | EGRA `total_incomplete` | EGRA `total_incomplete` |
| `letters_time_taken` | Float | EGRA answer | EGRA answer |
| `nonwords_total_correct` | Integer | EGRA answer | N/A (ECD has letters only) |
| `nonwords_total_incorrect` | Integer | EGRA answer | N/A |
| `nonwords_total_attempted` | Integer | EGRA answer | N/A |
| `nonwords_total_not_attempted` | Integer | EGRA `total_incomplete` | N/A |
| `nonwords_time_taken` | Float | EGRA answer | N/A |
| `words_total_correct` | Integer | EGRA answer | N/A |
| `words_total_incorrect` | Integer | EGRA answer | N/A |
| `words_total_attempted` | Integer | EGRA answer | N/A |
| `words_total_not_attempted` | Integer | EGRA `total_incomplete` | N/A |
| `words_time_taken` | Float | EGRA answer | N/A |
| `assessment_complete` | String | EGRA `assessment_completed` | EGRA `assessment_completed` |
| `stop_rule_reached` | String | EGRA `stop_rule` | EGRA `stop_rule` |
| `timer_elapsed` | String | EGRA `timer_elapsed` | EGRA `timer_elapsed` |
| `assessment_type` | String | CLI arg (default: `"baseline"`) | CLI arg (default: `"baseline"`) |
| `data_refresh_timestamp` | DateTime | Set to `timezone.now()` at sync | Set to `timezone.now()` at sync |

---

## Database Schema: assessment_cells_2026

Individual letter/word/nonword cell results, one row per cell per response.

| Column | Type | Source |
|--------|------|--------|
| `response_id` | String | Links to `assessments_2026.response_id` |
| `question_type` | String | `"letters"`, `"nonwords"`, or `"words"` |
| `cell_id` | String | The letter/word tested (e.g., `"a"`, `"m"`) |
| `cell_index` | Integer | Position in the assessment grid (0-indexed) |
| `status` | String | `"correct"`, `"incorrect"`, or `"incomplete"` |
| `time_taken` | Float | Milliseconds for this cell |

---

## EGRA Sub-Test Detection

NMB surveys (815/816/817) can have up to 3 EGRA sub-tests per response. The sync determines which sub-test an answer belongs to using:

1. **Question label** (if available): `"letter"` → letters, `"non"/"nonsense"` → nonwords, else → words
2. **Cell count fallback**: If no label, 60 cells → letters (first match only)

---

## Known Groups (Sample)

| group_id | class_name | program_name (school) | Grade |
|----------|-----------|----------------------|-------|
| 59979 | Grade 1 - Canzibe Primary School | Canzibe Primary School | Grade 1 |
| 60243 | Grade 1 - Sipho Hashe Combined School | Sipho Hashe Combined School | Grade 1 |
| 60318 | Grade R - Phakamile Primary School | Phakamile Primary School | Grade R |
| 60320 | Grade 2 - Phakamile Primary School | Phakamile Primary School | Grade 2 |
| 60354 | Grade R - J K Zondi Primary School | J K Zondi Primary School | Grade R |
| 60355 | Grade 1 - J K Zondi Primary School | J K Zondi Primary School | Grade 1 |
| 60370 | Grade R - Nomathamsanqa Primary School | Nomathamsanqa Primary School | Grade R |
| 60388 | Grade 2 - James Ntungwana Primary School | James Ntungwana Primary School | Grade 2 |
| 60454 | Grade R - Melisizwe Public Primary School | Melisizwe Public Primary School | Grade R |
| 60603 | Grade 1 - Masinyusane | Masinyusane | Grade 1 |

---

## Troubleshooting

### Grade shows as empty
- The `group_id` on the response may not have been resolved (API error or missing group)
- The `class_name` doesn't contain "Grade R", "Grade 1", or "Grade 2"
- Check the sync log for group cache build errors

### program_name or class_name is empty
- The response's `group_id` field was null or empty
- The group API returned an error for that group_id
- For ECD: the response didn't include `program_name`/`class_name` fields

### Duplicate or missing assessments
- Sync skips responses whose `response_id` already exists in the database
- Use `--full-refresh` to delete and re-sync all records for selected surveys
- Check `data_refresh_timestamp` to see when each record was last synced

### Data not appearing on dashboard
- Streamlit pages cache data for 1 hour (`ttl=3600`). Clear cache or wait.
- Check that the sync ran: `SELECT MAX(data_refresh_timestamp) FROM assessments_2026;`

---

## API Reference Quick Links

- **Base URL:** `https://teampact.co/api/analytics/v1/`
- **Auth:** `Authorization: Bearer {TEAMPACT_API_TOKEN}`
- **Pagination:** `?page=1&per_page=100` — check `meta.last_page`
- **Rate limiting:** 0.5s between pages, 0.3s between group lookups
- **Full API reference:** See `Zazi_iZandi_Website_2025/docs/teampact_api_reference.md`
