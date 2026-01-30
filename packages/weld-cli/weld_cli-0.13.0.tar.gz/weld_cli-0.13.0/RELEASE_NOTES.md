### Changed
- `weld prompt show --raw` now displays actual prompt templates instead of stubs
- `weld prompt export --raw` exports real templates used by each task type
- Research prompt overhauled with code-first philosophy
  - Core principles: "Read code, not docs", "Identify authoritative files", "Eliminate assumptions"
  - New sections: Authoritative Files, Existing Patterns, Integration Points, Constraints & Risks
  - Output requirements: Short artifact (1-2 pages), file:line references required, [VERIFY] markers for uncertain items
  - Includes Memento warning about fabrication without verified context
- Plan prompt enhanced with "Why Plans Matter" section
  - Emphasizes planning as highest-leverage activity
  - Good plan requirements: exact steps, concrete files, validation after each change, obvious failure modes
  - Warning: "Bad plans produce dozens of bad lines of code. Bad research produces hundreds."

### Fixed
- `weld prompt show --raw` now displays actual full prompt templates instead of stub placeholders
  - Previously showed ~15 line stubs with "(Full template in ...)" references
  - Now shows complete templates (47-158 lines depending on task type)
  - Templates imported from actual source modules for accuracy
