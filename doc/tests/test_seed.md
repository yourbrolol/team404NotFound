# 🌱 Test Documentation: `test_seed.py`

## Purpose
This test ensures that the custom management command `seed_data` correctly populates the database with demo data. This is critical for development environments and for providing a consistent starting point for manual testing.

## Test Class: `SeedDataTest`
Tests the execution and output of the `seed_data` management command.

### Test Cases
1. **`test_seed_data_command`**
   - **Action**: Calls `python manage.py seed_data --clear`.
   - **Verifications**:
     - **Users**: Confirms the creation of the default organizer, juries, and team captains.
     - **Contest**: Verifies that the "AI Innovation Hackathon 2026" contest exists and is owned by the organizer.
     - **Teams**: Checks that 3 teams (e.g., "Alpha Force 1") are created and linked to the contest.
     - **Rounds**: Confirms the "Prototype Development" round is created.
     - **Submissions**: Ensures each team has an initial submission.
     - **Scoring**: Validates the creation of 3 scoring criteria.
     - **Assignments & Scores**: Confirms the creation of 6 jury assignments and 18 individual jury scores (simulating a fully evaluated contest).
