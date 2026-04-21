# Meta-Skill-Engineering Extra Plan Intake

This document is an active issue-intake note for [13-meta-skill-engineering-repo-hardening](../README.md).

It is not the canonical implementation plan. The canonical plan lives in the numbered folder above. This note exists to preserve the specific Meta Skill Studio issues that triggered the extra planning work.

## Intake Focus

The separate Meta-Skill-Engineering repo needs more than generic “skill system evolution” guidance. It needs:

- a fully functional CLI so an AI agent can drive all major suite features without relying on TUI/GUI
- stronger evaluation methodology, especially where the `plugin-eval` work already demonstrates useful patterns
- a repo-specific hardening plan for the studio shell, evaluation workflow, packaging, and automation path

## Captured UI / Studio Issues

1. `🔴 Bug` Improve crashes if no goal entered because a parameter pipe separator is missing.
2. `🔴 Bug` Dashboard library tier counts show `0/0/0` on first load.
3. `🔴 Bug` Settings documentation links show “Available” but have no open button.
4. `🔴 Bug` Status-bar runtime indicator stays green regardless of real status.
5. `🔴 Bug` Library tier selector buttons show numbers only, not tier names.
6. `🔴 Bug` Library search box is not visible in the standard layout.
7. `🟡 UX` Raw enum names appear in every target-tier ComboBox.
8. `🟡 UX` Library category names have no gap before count values.
9. `🟡 UX` Skill-detail buttons float even when no skill is selected.
10. `🟡 UX` Inputs and dropdowns lack placeholder or hint text.
11. `🟡 UX` Import has no folder browse button for local-folder import.
12. `🟡 UX` GitHub and local-folder import sections are visually identical.
13. `🟡 UX` ManagePage depends on selection from Library and cannot stand alone.
14. `🟡 UX` ManagePromote uses primary styling even when nothing is selected.
15. `🟡 UX` Automation stop button lacks clear disabled state.
16. `🟡 UX` Automation surfaces lack active progress indication.
17. `🟡 UX` Provider/model settings appear empty despite runtime readiness.
18. `🟡 UX` Analytics snapshot table duplicates the stat cards.
19. `🟡 UX` Analytics stat card colors are inconsistent.
20. `🟡 UX` Create/Improve/Test/Automation pages waste large lower-screen areas.
21. `🟡 Code` Improve uses `List<T>` instead of `ObservableCollection<T>` for run history.
22. `🟡 Code` All pages remain mounted in the visual tree instead of using a content host.
23. `🟡 Code` Automation cancellation is flag-only and does not flow a `CancellationToken`.
24. `🟡 Code` Assistant chat bubbles ignore the shared styles in `App.xaml`.
25. `🟡 Design` Automation sliders use native WPF theme styling instead of app styling.
26. `🟡 Design` Analytics “Refresh analytics” is visually buried.
27. `🟡 Design` Raw YAML frontmatter and Markdown are rendered as plain monospace text.
28. `🟡 Design` Analytics run history would expose raw JSON filenames.
29. `🟢 Polish` Nav rail is icon-only with no labels.
30. `🟢 Polish` Nav rail shows plain text `MSS` instead of a stronger mark.
31. `🟢 Polish` Library lacks a zero-results empty state.
32. `🟢 Polish` Log activity text is green without semantic meaning.
33. `🟢 Polish` No keyboard shortcuts are surfaced.
34. `🟢 Polish` Assistant input lacks Enter-to-send.
35. `🟢 Polish` Top-bar refresh always refreshes Library regardless of current page.
36. `🟢 Polish` Improve button naming is inconsistent.
37. `🟢 Polish` Dashboard and Manage tier counts are redundant.
38. `🟢 Polish` Create output card duplicates dashboard activity log.

## Planning Consequence

The numbered plan must treat these as inputs, not as the full scope. It also has to cover:

- CLI parity for the suite
- Linux/headless AI-operator usage for the suite where relevant
- plugin-eval techniques worth lifting into repo-wide evaluation
- packaging, documentation, and automation alignment
