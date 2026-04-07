import csv
import io
import logging
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.utils import timezone

from .models import ContestEvaluationPhase, JuryScore, LeaderboardEntry, ScoringCriterion


logger = logging.getLogger(__name__)
TWOPLACES = Decimal("0.01")


def _quantize(value):
    return Decimal(value).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


class LeaderboardComputer:
    @classmethod
    def _build_leaderboard(cls, contest):
        jury_members = list(contest.jurys.order_by("id"))
        teams = list(contest.teams.order_by("name", "id"))
        criteria = list(contest.scoring_criteria.order_by("order", "id"))
        raw_scores = JuryScore.objects.filter(contest=contest).select_related("team", "jury_member", "criterion")

        grouped_scores = defaultdict(list)
        score_map = {}
        for jury_score in raw_scores:
            grouped_scores[(jury_score.team_id, jury_score.criterion_id)].append(jury_score.score)
            score_map[(jury_score.team_id, jury_score.criterion_id, jury_score.jury_member_id)] = jury_score

        entries = []
        overall_missing = []

        for team in teams:
            category_scores = {}
            jury_breakdown = {}
            team_missing = []
            total_score = Decimal("0.00")

            for criterion in criteria:
                criterion_scores = grouped_scores[(team.id, criterion.id)]
                breakdown_rows = []

                for jury in jury_members:
                    jury_score = score_map.get((team.id, criterion.id, jury.id))
                    if jury_score is None:
                        missing_row = {
                            "jury_id": jury.id,
                            "jury_username": jury.username,
                            "team_id": team.id,
                            "team_name": team.name,
                            "criterion_id": criterion.id,
                            "criterion_name": criterion.name,
                        }
                        team_missing.append(missing_row)
                        breakdown_rows.append(
                            {"jury_id": jury.id, "jury_username": jury.username, "score": None}
                        )
                    else:
                        breakdown_rows.append(
                            {
                                "jury_id": jury.id,
                                "jury_username": jury.username,
                                "score": float(jury_score.score),
                            }
                        )

                if criterion_scores:
                    aggregate = sum(criterion_scores)
                    if criterion.aggregation_type == ScoringCriterion.AggregationType.AVERAGE:
                        aggregate = aggregate / Decimal(len(criterion_scores))
                    weighted_value = _quantize(aggregate * criterion.weight)
                else:
                    weighted_value = Decimal("0.00")

                category_scores[criterion.name] = float(weighted_value)
                jury_breakdown[criterion.name] = breakdown_rows
                total_score += weighted_value

            overall_missing.extend(team_missing)
            entries.append(
                {
                    "team": team,
                    "category_scores": category_scores,
                    "jury_breakdown": jury_breakdown,
                    "missing_scores": team_missing,
                    "computation_complete": len(team_missing) == 0 and bool(criteria) and bool(jury_members),
                    "total_score": _quantize(total_score),
                }
            )

        entries.sort(key=lambda item: (-item["total_score"], item["team"].name.lower(), item["team"].id))

        last_score = None
        rank = 0
        for index, item in enumerate(entries, start=1):
            if last_score is None or item["total_score"] != last_score:
                rank = index
            item["rank"] = rank
            last_score = item["total_score"]

        score_groups = defaultdict(list)
        for item in entries:
            score_groups[item["total_score"]].append(item)
        for group in score_groups.values():
            tied = len(group) > 1
            for item in group:
                item["is_tied"] = tied

        return {
            "criteria": criteria,
            "entries": entries,
            "all_scores_complete": len(overall_missing) == 0 and bool(entries) and bool(criteria) and bool(jury_members),
            "overall_missing": overall_missing,
            "teams_count": len(teams),
        }

    @classmethod
    def save_leaderboard(cls, contest, payload, force_complete=False, trigger_type=None, preserve_completed_at=False):
        phase, _ = ContestEvaluationPhase.objects.get_or_create(
            contest=contest,
            defaults={
                "status": ContestEvaluationPhase.Status.NOT_STARTED,
                "trigger_type": ContestEvaluationPhase.TriggerType.AUTO,
            },
        )

        if trigger_type is not None:
            phase.trigger_type = trigger_type

        if not preserve_completed_at:
            phase.completed_at = None

        phase.all_scores_complete = payload["all_scores_complete"]

        if force_complete or payload["all_scores_complete"]:
            phase.status = ContestEvaluationPhase.Status.COMPLETED
            if phase.completed_at is None:
                phase.completed_at = timezone.now()
        elif JuryScore.objects.filter(contest=contest).exists():
            phase.status = ContestEvaluationPhase.Status.IN_PROGRESS
        else:
            phase.status = ContestEvaluationPhase.Status.NOT_STARTED

        with transaction.atomic():
            phase.save()
            existing_entries = []
            for item in payload["entries"]:
                entry, _ = LeaderboardEntry.objects.update_or_create(
                    contest=contest,
                    team=item["team"],
                    defaults={
                        "rank": item["rank"],
                        "total_score": item["total_score"],
                        "is_tied": item["is_tied"],
                        "category_scores": item["category_scores"],
                        "jury_breakdown": item["jury_breakdown"],
                        "missing_scores": item["missing_scores"],
                        "computation_complete": item["computation_complete"],
                    },
                )
                existing_entries.append(entry.id)

            LeaderboardEntry.objects.filter(contest=contest).exclude(id__in=existing_entries).delete()

        logger.info(
            "Leaderboard activation: trigger=%s, timestamp=%s, all_scores_complete=%s, teams_count=%s",
            phase.trigger_type,
            phase.completed_at,
            phase.all_scores_complete,
            payload["teams_count"],
        )

        return phase

    @classmethod
    def compute_leaderboard(cls, contest, force_complete=False, trigger_type=None, preserve_completed_at=False):
        payload = cls._build_leaderboard(contest)
        phase = cls.save_leaderboard(
            contest,
            payload,
            force_complete=force_complete,
            trigger_type=trigger_type,
            preserve_completed_at=preserve_completed_at,
        )
        return {"phase": phase, **payload}

    @classmethod
    def is_ready_for_auto_activation(cls, contest):
        criteria = list(contest.scoring_criteria.all())
        jurys = list(contest.jurys.all())
        teams = list(contest.teams.all())
        if not criteria or not jurys or not teams:
            return False
        expected = len(criteria) * len(jurys) * len(teams)
        actual = JuryScore.objects.filter(contest=contest).count()
        return expected == actual

    @classmethod
    def get_missing_scores(cls, contest):
        phase = ContestEvaluationPhase.objects.filter(contest=contest).first()
        if phase and phase.status == ContestEvaluationPhase.Status.COMPLETED and phase.all_scores_complete:
            return []
        payload = cls._build_leaderboard(contest)
        return payload["overall_missing"]

    @classmethod
    def export_data(cls, contest, user_is_admin=False):
        entries = LeaderboardEntry.objects.filter(contest=contest).select_related("team").order_by("rank", "team__name")
        if not entries.exists():
            payload = cls._build_leaderboard(contest)
            cls.save_leaderboard(contest, payload, preserve_completed_at=True)
            entries = LeaderboardEntry.objects.filter(contest=contest).select_related("team").order_by("rank", "team__name")
        data = []
        for entry in entries:
            item = {
                "rank": entry.rank,
                "team": entry.team.name,
                "total_score": float(entry.total_score),
                "category_scores": entry.category_scores,
                "computation_complete": entry.computation_complete,
            }
            if user_is_admin:
                item["jury_breakdown"] = entry.jury_breakdown
                item["missing_scores"] = entry.missing_scores
                item["is_tied"] = entry.is_tied
            data.append(item)
        return data

    @classmethod
    def export_csv(cls, contest):
        criteria = list(contest.scoring_criteria.order_by("order", "id"))
        entries = LeaderboardEntry.objects.filter(contest=contest).select_related("team").order_by("rank", "team__name")
        if not entries.exists():
            payload = cls._build_leaderboard(contest)
            cls.save_leaderboard(contest, payload, preserve_completed_at=True)
            entries = LeaderboardEntry.objects.filter(contest=contest).select_related("team").order_by("rank", "team__name")
        header = ["rank", "team", "total_score"] + [criterion.name for criterion in criteria] + ["computation_complete"]
        rows = []
        for entry in entries:
            row = [entry.rank, entry.team.name, float(entry.total_score)]
            for criterion in criteria:
                row.append(entry.category_scores.get(criterion.name, ""))
            row.append(entry.computation_complete)
            rows.append(row)
        return header, rows


def _missing_scores_as_dict(contest):
    missing = {}
    for row in LeaderboardComputer.get_missing_scores(contest):
        missing.setdefault(row["team_name"], {}).setdefault(row["criterion_name"], []).append(row["jury_username"])
    return missing


def get_missing_scores(contest):
    return _missing_scores_as_dict(contest)


def save_leaderboard(contest):
    payload = LeaderboardComputer._build_leaderboard(contest)
    LeaderboardComputer.save_leaderboard(contest, payload)
    return list(LeaderboardEntry.objects.filter(contest=contest).select_related("team").order_by("rank", "team__name"))


def compute_leaderboard(contest, persist=False):
    if persist:
        save_leaderboard(contest)
    return LeaderboardComputer._build_leaderboard(contest)["entries"]


def is_ready_for_auto_activation(contest):
    return LeaderboardComputer.is_ready_for_auto_activation(contest)


def export_data(contest):
    return LeaderboardComputer.export_data(contest, user_is_admin=True)


def export_csv(contest):
    header, rows = LeaderboardComputer.export_csv(contest)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(header)
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue()
