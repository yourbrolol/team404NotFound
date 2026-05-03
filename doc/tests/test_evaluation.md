# ⚖️ Test Documentation: `test_evaluation.py`

## Purpose
This test suite validates the evaluation and scoring system, ensuring that jury scores adhere to contest rules, criteria limits, and participant constraints.

## Test Class: `EvaluationModelsTest`
Tests the `ScoringCriterion`, `JuryScore`, and `ContestEvaluationPhase` models.

### Setup
- Creates an **Organizer**, two **Jury members**, two **Captains**, and a **Team member**.
- Initializes two **Teams** and one **Contest**.
- Defines two **Scoring Criteria**:
  - "Backend" (Max: 100, Weight: 1.0, Type: Average)
  - "Design" (Max: 50, Weight: 2.0, Type: Sum)

### Test Cases
1. **`test_create_scoring_models`**
   - **Scenario**: A jury member is assigned to a team and submits a score.
   - **Action**: Create a `JuryAssignment` and a `JuryScore`.
   - **Verification**: 
     - The score value is correctly saved.
     - The default evaluation phase status is `NOT_STARTED`.
     - The string representation of criteria is correct.

2. **`test_score_validation_rejects_score_above_maximum`**
   - **Scenario**: A jury member attempts to submit a score higher than the criterion's `max_score`.
   - **Action**: Attempt to create a `JuryScore` of 51 for the "Design" criterion (Max: 50).
   - **Verification**: Raises a `ValidationError`.

3. **`test_score_validation_rejects_team_outside_contest`**
   - **Scenario**: A jury member attempts to score a team that is not participating in the selected contest.
   - **Action**: Create a team "Gamma" (not in "EvalCup") and attempt to save a score for it.
   - **Verification**: Raises a `ValidationError`.
