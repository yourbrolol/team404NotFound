# 🏆 Test Documentation: `test_full_workflow.py`

## Purpose
This is a comprehensive end-to-end integration test that simulates the "Golden Path" of a contest lifecycle. It ensures that all major components (Contests, Teams, Rounds, Applications, Jury, and Leaderboard) work together seamlessly through view-based actions.

## Test Class: `FullWorkflowIntegrationTest`
An end-to-end test following TASK-33 requirements.

### Setup
- Initializes four users: **Organizer**, **Jury Member**, **Participant 1 (Captain)**, and **Participant 2 (Member)**.
- Creates unique `django.test.Client` instances for each user and logs them in.

### The "Golden Path" Workflow
1.  **Contest Creation**: Organizer creates a contest with specific registration and start/end dates.
2.  **Criteria Setup**: Organizer adds a "Innovation" scoring criterion.
3.  **Round Creation**: Organizer creates an "Alpha Round" with technical requirements and must-have items.
4.  **Team Formation**: Participant 1 creates a team "Coders United".
5.  **Team Approval**: Organizer approves the team application.
6.  **Team Expansion**: Participant 2 joins the team; Captain (Participant 1) approves the join request.
7.  **Round Activation**: Organizer activates the round.
8.  **Solution Submission**: Team Captain submits a solution (GitHub link, video URL, description).
9.  **Closing Submissions**: Organizer closes the submission window for the round.
10. **Jury Assignment**: Organizer assigns the Jury member to evaluate the team.
11. **Evaluation**: Jury member submits scores for the team.
12. **Leaderboard Update**: Organizer recalculates the leaderboard and finishes the evaluation phase.
13. **Final Verification**: The system verifies that the leaderboard is publicly visible and correctly reflects the team's score.
