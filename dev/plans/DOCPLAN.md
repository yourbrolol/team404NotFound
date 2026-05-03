# Documentation Plan: ContestKeeper Project

## Overview
Create comprehensive `docplan.md` master plan + mirrored doc structure for ContestKeeper (Django contest platform). Documentation will be lightweight (overview + key functions + examples), with creative architecture diagrams, API reference, quick-start guides, and troubleshooting sections.

## Target Structure

### Main Documentation Organization
```
doc/
├── docplan.md                    # THIS master plan (index + strategy)
├── README_DOCS.md                # Getting started for documentation
├── ARCHITECTURE.md               # System architecture + data flow (ASCII/Mermaid diagrams)
├── API_REFERENCE.md              # All endpoints + request/response examples
├── QUICK_START_DEV.md            # Developer onboarding guide
├── TROUBLESHOOTING.md            # Common issues + solutions
├── models/
│   ├── _overview.md              # Models architecture overview
│   ├── user.md                   # User, Team, Application models
│   ├── contest.md                # Contest, ContestEvaluationPhase, Round models
│   ├── evaluation.md             # Evaluation models (Submission, Score, etc)
│   └── relationships.md          # Foreign key relationships diagram
├── views/
│   ├── _overview.md              # Views organization + routing
│   ├── views_auth.md             # Authentication & session management
│   ├── views_application.md      # Application management views
│   ├── views_contest.md          # Contest CRUD & management
│   ├── views_team.md             # Team operations
│   ├── views_submission.md       # Submission handling
│   ├── views_evaluation.md       # Jury evaluation & scoring
│   ├── views_leaderboard.md      # Leaderboard generation & display
│   ├── views_rounds.md           # Contest rounds management
│   ├── views_announcement.md     # Announcements & notifications
│   ├── views_notification.md     # Real-time notifications
│   ├── views_analytics.md        # Analytics & statistics
│   ├── views_general.md          # Utility views (about, contact, etc)
│   └── views_base.md             # Base mixins & common utilities
├── forms/
│   ├── _overview.md              # Forms architecture
│   └── forms.md                  # Form classes + validation
├── urls/
│   ├── _overview.md              # URL routing strategy
│   ├── contest_urls.md           # Contest-related routes
│   ├── application_urls.md       # Application routes
│   └── urls.md                   # Main URL config
├── services/
│   ├── _overview.md              # Business logic layer
│   └── services.md               # Service functions & utilities
├── utilities/
│   ├── leaderboard.md            # Leaderboard calculation algorithm
│   ├── context_processors.md     # Template context helpers
│   └── models_admin.md           # Admin configuration
├── management/
│   └── commands.md               # Management commands (e.g., send_deadline_reminders)
├── frontend/
│   ├── templates_overview.md     # Template structure
│   ├── css_guide.md              # CSS architecture & theming
│   └── js_guide.md               # JavaScript functionality guide
├── database/
│   └── migrations_guide.md       # Migration strategy & history
├── testing/
│   └── tests_overview.md         # Test organization & running tests
└── CHANGELOG.md                  # Documentation version history
```

## Implementation Steps

### Phase 1: Foundation (Master Plan & Infrastructure)
1. Create `docplan.md` (THIS file) as master index
2. Create `README_DOCS.md` - documentation navigation & usage guide
3. Create high-level docs:
   - `ARCHITECTURE.md` - System design + ASCII/Mermaid diagrams (data flow, user roles, contest lifecycle)
   - `API_REFERENCE.md` - All endpoints organized by feature (auth, contests, teams, submissions, evaluation, leaderboard)
   - `QUICK_START_DEV.md` - Dev environment setup, first contribution workflow, debugging tips
   - `TROUBLESHOOTING.md` - Common errors, migration issues, permission errors, data problems

**Verification:** All 4 files exist with proper structure and are readable

### Phase 2: Models Documentation (Database Layer)
1. Create `models/_overview.md` - ER diagram + relationships diagram (ASCII/Mermaid)
2. Document each model group:
   - `models/user.md` - User, Team, related fields + helper methods
   - `models/contest.md` - Contest, Round, ContestEvaluationPhase models + state transitions
   - `models/evaluation.md` - Submission, Score, ScoringCriterion, scoring logic
   - `models/relationships.md` - FK relationships as visual diagram

**Verification:** All models are documented; diagrams render correctly in markdown preview

### Phase 3: Views Documentation (Controller/View Layer)
1. Create `views/_overview.md` - Views categorization + routing strategy
2. For each view file, create corresponding doc:
   - Document 2-3 key view classes/functions per file
   - Include URL pattern mapping
   - Add usage examples or success/error flows
   - Note any permission requirements or decorators
3. **Parallel docs:** Create 14 view docs (views_auth.md → views_general.md)

**Verification:** Each view file has a matching doc; all key views are listed

### Phase 4: Forms, URLs, Services (Supporting Layers)
1. Create `forms/_overview.md` + `forms/forms.md`
   - List all form classes
   - Key validation logic
2. Create `urls/_overview.md` + URL-specific docs
   - Routing strategy (contest_urls, application_urls, main urls)
3. Create `services/_overview.md` + `services/services.md`
   - Business logic functions + when to use them
4. Create utility docs:
   - `utilities/leaderboard.md` - Scoring algorithm + ranking calculation
   - `utilities/context_processors.md` - Template context helpers
   - `utilities/models_admin.md` - Admin interface customizations

**Verification:** All non-view backend components documented; cross-references to views/models work

### Phase 5: Frontend & Infrastructure Documentation
1. Create `frontend/templates_overview.md` - Template hierarchy + key partials
2. Create `frontend/css_guide.md` - CSS structure, dark theme variables, responsive design notes
3. Create `frontend/js_guide.md` - JavaScript modules, event handlers, dynamic features
4. Create database & testing docs:
   - `database/migrations_guide.md` - Why migrations exist, how to run them, rollback procedures
   - `testing/tests_overview.md` - Test organization (unit vs integration), how to run, adding new tests
5. Create `management/commands.md` - Scheduled commands + usage

**Verification:** Frontend structure clear; database and test procedures documented

### Phase 6: Polish & Integration
1. Create `CHANGELOG.md` - Document version history of docs themselves
2. Update `doc/docplaceholder.md` to reflect the new structure
3. Add cross-references between related docs (hyperlinks)
4. Ensure all docs follow consistent formatting:
   - Header: filename being documented, last update date, related files
   - Sections: Overview, Key Classes/Functions, Usage Examples, Common Patterns/Gotchas
   - Footer: References to source files and related docs

**Verification:** All docs follow template; no broken links; coherent navigation

## Relevant Files to Document (Core App)
- [models.py](../ContestKeeper/app/models.py) — User, Team, Contest, Application, scoring models
- [views/](../ContestKeeper/app/views/) — 14 view modules (auth, contests, teams, evaluation, leaderboard, etc.)
- [forms.py](../ContestKeeper/app/forms.py) — Form classes with validation
- [services.py](../ContestKeeper/app/services.py) — Business logic layer
- [leaderboard.py](../ContestKeeper/app/leaderboard.py) — Scoring & ranking algorithm
- [urls/](../ContestKeeper/app/urls/) — URL routing configuration
- [templates/](../ContestKeeper/app/templates/) — HTML templates and structure
- [static/css/](../ContestKeeper/app/static/css/) — CSS styling
- [static/js/](../ContestKeeper/app/static/js/) — JavaScript interactions
- [migrations/](../ContestKeeper/app/migrations/) — Database schema changes
- [management/commands/](../ContestKeeper/app/management/commands/) — Custom management commands
- [tests/](../ContestKeeper/app/tests/) — Test suite organization

## Documentation Template (for each file doc)
```markdown
## [Filename]
- Documenting: [source file path]
- Last updated: [d/m/y], commit: [hash]

### Overview
[1-2 sentences about the module's purpose]

### Key Components
- **Class/Function 1**: [Brief description]
- **Class/Function 2**: [Brief description]

### Usage Example
[Code snippet or workflow]

### Common Patterns / Gotchas
[Known issues or best practices]

### Related Files
- [Related file 1](related_file.md)
```

## Verification Checklist
1. ✅ All 40+ doc files created and follow template
2. ✅ Directory structure mirrors app structure
3. ✅ Architecture diagrams (at least 2: data flow + entity relationships)
4. ✅ API reference lists all endpoints with method/status codes
5. ✅ Quick-start guide includes local setup + first feature walkthrough
6. ✅ Troubleshooting covers top 5 common issues with solutions
7. ✅ No broken markdown links; all cross-references valid
8. ✅ README_DOCS.md provides navigation/entry points

## Decisions & Scope
- **Lightweight approach:** Overview + key functions only (not every private method)
- **Mirrored structure:** Docs/ follows app/ structure for easy correlation
- **Creative elements:** ASCII/Mermaid diagrams + quick-start + API reference as primary value-adds
- **Target audience:** New developers joining the project
- **Excluded:** Inline code comments in source (docs replace that); detailed implementation of every function; deployment/DevOps docs

## Timeline Estimate
- Phase 1 (Foundation): 1-2 hours
- Phase 2 (Models): 1.5 hours
- Phase 3 (Views): 3-4 hours (longest phase, 14 files)
- Phase 4 (Services/URLs/Forms): 1.5 hours
- Phase 5 (Frontend + Infra): 2 hours
- Phase 6 (Polish): 1 hour
- **Total: 10-11.5 hours** (can parallelize phases 3-5 if needed)

## Further Considerations
1. **Should we auto-generate some docs from code?** (e.g., API endpoints from Django URL conf)
   - *Recommendation:* Start with manual docs for clarity; consider tooling (drf-spectacular, etc.) for Phase 2
2. **Include deployment/infrastructure docs?** (server setup, environment variables, Docker)
   - *Recommendation:* Excluded for now (focus on code understanding); separate DevOps wiki if needed
3. **Versioning strategy for docs?** (track with code commits, separate changelog)
   - *Recommendation:* Use CHANGELOG.md + git commit tags for doc versions aligned with code releases
