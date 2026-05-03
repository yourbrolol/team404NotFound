# 🧪 ContestKeeper Test Documentation

This directory contains detailed documentation for the backend test suites of the ContestKeeper project.

## 📁 Documented Tests

| File | Description |
| :--- | :--- |
| [test_application.md](./test_application.md) | Application approval and validation logic. |
| [test_evaluation.md](./test_evaluation.md) | Scoring criteria, jury scores, and evaluation phases. |
| [test_full_workflow.md](./test_full_workflow.md) | **Golden Path** integration test (End-to-End). |
| [test_integration.md](./test_integration.md) | Detailed user scenarios, access control, and notification pipeline. |
| [test_jury_assignment.md](./test_jury_assignment.md) | Jury load balancing and assignment-based access control. |
| [test_leaderboard.md](./test_leaderboard.md) | Score computation, ranking, ties, and data export. |
| [test_round.md](./test_round.md) | Round lifecycle (Draft -> Active -> Closed) and deadlines. |
| [test_seed.md](./test_seed.md) | Verification of the `seed_data` management command. |
| [test_submission.md](./test_submission.md) | Submission constraints, deadlines, and visibility rules. |
| [test_views.md](./test_views.md) | Home page discovery and role-based Profile views. |
| [tests_integration.md](./tests_integration.md) | Supplementary integration tests (Drafts, Pagination). |

## 🚀 Running Tests

To run all tests:
```bash
python manage.py test app
```

To run a specific test file:
```bash
python manage.py test app.tests.test_filename
```

## 🛠️ Local Development
For local development and testing, refer to the [Local Testing Guide](../../ContestKeeper/app/tests/localdev/README.md).
