# Blocker Register — Scafforge Recovery

Generated: 2026-04-10
Status: Active

---

## Active Blockers

| ID | Description | Severity | Root Cause | Status |
|----|-------------|----------|------------|--------|
| BLK-001 | stage-gate-enforcer lacks managed_blocked check | HIGH | RC-001 | OPEN |
| BLK-002 | deterministic-refresh is non-catalog stage name | MEDIUM | RC-002 | OPEN |
| BLK-003 | asserted_completed_stages not re-validated | MEDIUM | RC-003 | OPEN |
| BLK-004 | WFLOW031 predictive repair trap in team-leader | MEDIUM | RC-005 | OPEN |
| BLK-005 | Python-only validation gap for Godot repos | HIGH | RC-008 | OPEN - partial fix needed |

## Resolved Blockers

| ID | Description | Resolution |
|----|-------------|------------|
| BLK-R01 | Transition guidance ignores verdict | ALREADY FIXED in current code (ticket_lookup.ts lines 282-393) |
| BLK-R02 | SKILL001 stage-linked blocker | WORKING AS DESIGNED |
| BLK-R03 | Blender system dependencies | FIXED — installed libsm6, libxext6, libxrender-dev |

## Downstream Repo Blockers (Not Scafforge bugs)

| Repo | Active Ticket | Stage | Blocking? | Notes |
|------|--------------|-------|-----------|-------|
| GPTTalker | EDGE-004 | closeout (done) | NO | repair_follow_on: source_follow_up |
| Spinner | RELEASE-001 | review | NO | repair_follow_on: source_follow_up |
| Glitch | RELEASE-001 | qa | NO | repair_follow_on: clean |
