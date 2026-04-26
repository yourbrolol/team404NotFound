import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ContestKeeper.settings")
django.setup()

from app.models import Contest, User, Team, ScoringCriterion, JuryScore, JuryAssignment

# Find a juror and a contest
contest = Contest.objects.first()
jury = contest.jurys.first()
team = contest.teams.first()
criterion = contest.scoring_criteria.first()

if not JuryAssignment.objects.filter(contest=contest, team=team, jury_member=jury).exists():
    JuryAssignment.objects.create(contest=contest, team=team, jury_member=jury)
    
print("Initial score:")
score, created = JuryScore.objects.get_or_create(
    contest=contest, team=team, jury_member=jury, criterion=criterion,
    defaults={'score': 5.00}
)
print(score.score)

# Try to update
JuryScore.objects.update_or_create(
    contest=contest, team=team, jury_member=jury, criterion=criterion,
    defaults={'score': 6.00}
)
score.refresh_from_db()
print("After update:")
print(score.score)
