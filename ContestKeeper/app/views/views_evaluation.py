from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.db import transaction

from app.forms import JuryEvaluationForm
from app.models import Contest, Team, ScoringCriterion, JuryScore, Submission, ContestEvaluationPhase
from app.views.views_base import JuryRequiredMixin

class JuryEvaluationView(JuryRequiredMixin, View):
    template_name = "app/juries/jury_evaluation.html"

    def get_context_data(self, **kwargs):
        contest = self.contest
        team = get_object_or_404(Team, pk=self.kwargs["team_pk"])
        round_id = self.kwargs.get("round_id")
        
        # Get latest submission for reference
        submission = Submission.objects.filter(team=team, round_id=round_id).first()
        if not submission:
            # Fallback to any submission from this team in this contest
            submission = Submission.objects.filter(team=team, round__contest=contest).order_by('-submitted_at').first()

        criteria = contest.scoring_criteria.all().order_by('order')
        
        # Get existing scores
        existing_scores = JuryScore.objects.filter(
            contest=contest, 
            team=team, 
            jury_member=self.request.user
        )
        initial_scores = {s.criterion_id: s.score for s in existing_scores}
        
        form = JuryEvaluationForm(criteria=criteria, initial_scores=initial_scores)
        
        # Check if evaluation is finished
        phase = ContestEvaluationPhase.objects.filter(contest=contest).first()
        is_readonly = phase and phase.status == ContestEvaluationPhase.Status.COMPLETED

        return {
            "contest": contest,
            "team": team,
            "submission": submission,
            "form": form,
            "criteria": criteria,
            "is_readonly": is_readonly,
        }

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        contest = self.contest
        team = get_object_or_404(Team, pk=self.kwargs["team_pk"])
        criteria = contest.scoring_criteria.all()
        
        # Block edits if evaluation is finished
        phase = ContestEvaluationPhase.objects.filter(contest=contest).first()
        if phase and phase.status == ContestEvaluationPhase.Status.COMPLETED:
            messages.error(request, "Evaluation is already finalized and cannot be edited.")
            return redirect("round_submissions", pk=contest.pk, round_id=self.kwargs.get("round_id"))

        form = JuryEvaluationForm(request.POST, criteria=criteria)
        if form.is_valid():
            with transaction.atomic():
                for criterion in criteria:
                    score_value = form.cleaned_data.get(f'criterion_{criterion.id}')
                    JuryScore.objects.update_or_create(
                        contest=contest,
                        team=team,
                        jury_member=request.user,
                        criterion=criterion,
                        defaults={'score': score_value}
                    )
            messages.success(request, f"Scores for {team.name} have been saved.")
            
            # Redirect to submission list of the same round
            round_id = request.POST.get("round_id") or request.GET.get("round_id")
            if round_id:
                return redirect("round_submissions", pk=contest.pk, round_id=round_id)
            return redirect("contest_detail", pk=contest.pk)
            
        context = self.get_context_data()
        context["form"] = form
        return render(request, self.template_name, context)
