# Utilities: Leaderboard Calculation

## LeaderboardComputer Class
- **Path**: `app.leaderboard.LeaderboardComputer`

### Overview
A utility class (using class methods) responsible for the core logic of calculating, caching, and exporting the contest leaderboard.

### Key Class Methods

#### `compute_leaderboard(contest, force_complete=False)`
The primary entry point.
1. Builds the leaderboard state by calling `_build_leaderboard`.
2. Saves the results to the database via `save_leaderboard`.
3. Returns the computed payload and evaluation phase status.

#### `_build_leaderboard(contest)`
The core algorithm:
- Aggregates `JuryScore` records for all teams and criteria.
- Applies weights and aggregation types (Average/Sum).
- Identifies missing scores (where a jury member hasn't scored a team).
- Sorts teams by total score and handles tie-breaking.

#### `save_leaderboard(contest, payload)`
Persists the calculation results into `LeaderboardEntry` records and updates the `ContestEvaluationPhase` status.

#### `export_csv(contest)`
Generates a structured list of headers and rows for CSV export.

### Scoring Logic
1. **Per-Criterion Score**: For each team and criterion, all assigned jury scores are aggregated (default is `AVERAGE`).
2. **Weighted Score**: The aggregate is multiplied by the criterion's `weight`.
3. **Total Score**: The sum of all weighted scores.
4. **Ranking**: Teams are ranked by `Total Score` descending. In case of ties, alphabetical order of team names is typically used as a secondary sort.
