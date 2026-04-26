# Models: Evaluation & Submissions

## ScoringCriterion Class
- **Path**: `app.models.ScoringCriterion`

### Overview
Defines a metric for judging a team's submission.

### Key Attributes
- `contest`: `ForeignKey` to `Contest`.
- `name`: `CharField` (max 100).
- `max_score`: `PositiveIntegerField` (default 100).
- `weight`: `DecimalField` (multiplier for total score).
- `aggregation_type`: `SUM` or `AVERAGE`.

---

## Submission Class
- **Path**: `app.models.Submission`

### Overview
Work submitted by a team for a specific round.

### Key Attributes
- `round`: `ForeignKey` to `Round`.
- `team`: `ForeignKey` to `Team`.
- `github_url`: `URLField`.
- `video_url`: `URLField`.
- `description`: `TextField`.

### Key Properties
- `is_editable`: `True` if the round is still open.

---

## JuryScore Class
- **Path**: `app.models.JuryScore`

### Overview
A score given by a jury member to a team on a specific criterion.

### Key Attributes
- `jury_member`: `ForeignKey` to `User`.
- `team`: `ForeignKey` to `Team`.
- `criterion`: `ForeignKey` to `ScoringCriterion`.
- `score`: `DecimalField`.

---

## LeaderboardEntry Class
- **Path**: `app.models.LeaderboardEntry`

### Overview
Cached rank and score data for a team in a contest.

### Key Attributes
- `contest`: `ForeignKey` to `Contest`.
- `team`: `ForeignKey` to `Team`.
- `rank`: `PositiveIntegerField`.
- `total_score`: `DecimalField`.
- `category_scores`: `JSONField` (breakdown by criterion).
- `jury_breakdown`: `JSONField` (breakdown by jury).
