# Ticket Board

| Wave | ID | Title | Lane | Stage | Status | Resolution | Verification | Parallel Safe | Overlap Risk | Depends On | Follow-ups |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | SETUP-001 | Bootstrap environment and confirm scaffold readiness | repo-foundation | closeout | done | done | trusted | no | high | - | - |
| 0 | SYSTEM-001 | Create the base Godot project architecture | game-architecture | closeout | done | done | trusted | no | medium | SETUP-001 | - |
| 1 | CORE-001 | Implement the baseline player controller | gameplay-core | closeout | done | done | trusted | no | medium | SETUP-001, SYSTEM-001 | - |
| 1 | CORE-002 | Build the glitch event system with fairness guardrails | gameplay-systems | qa | qa | open | suspect | no | medium | SETUP-001, SYSTEM-001, CORE-001 | REMED-002, REMED-003, REMED-001 |
| 1 | CORE-003 | Create reusable room, hazard, and checkpoint flow | level-systems | planning | todo | open | suspect | yes | low | SETUP-001, SYSTEM-001 | - |
| 2 | UX-001 | Add Android touch controls and HUD readability scaffolding | mobile-ux | planning | todo | open | suspect | yes | low | SETUP-001, CORE-001 | - |
| 2 | CONTENT-001 | Build the Startup Sector vertical slice | content-vertical-slice | planning | todo | open | suspect | no | medium | CORE-001, CORE-002, CORE-003, UX-001 | - |
| 3 | POLISH-001 | Layer core glitch presentation and feedback polish | presentation | planning | todo | open | suspect | yes | low | CONTENT-001 | - |
| 4 | REMED-002 | Godot headless validation fails | remediation | review | review | open | suspect | no | low | - | ANDROID-001, REMED-004 |
| 4 | REMED-003 | Source imports reference missing local modules | remediation | planning | todo | open | suspect | no | low | - | - |
| 5 | REMED-001 | Godot headless validation fails | remediation | planning | todo | open | suspect | no | low | - | - |
| 21 | ANDROID-001 | Create Android export surfaces | android-export | planning | todo | open | suspect | no | medium | - | RELEASE-001 |
| 24 | RELEASE-001 | Build Android debug APK | release-readiness | planning | todo | open | suspect | no | medium | ANDROID-001 | - |
| 10 | REMED-004 | The supplied session transcript shows the agent searching for workflow bypasses or soft dependency overrides instead of following the lifecycle contract | remediation | planning | todo | open | suspect | no | low | - | - |
