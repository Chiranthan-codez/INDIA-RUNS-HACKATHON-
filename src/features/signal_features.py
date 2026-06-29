import math
from datetime import datetime
from src.ingestion.candidate_model import Candidate


class SignalFeatures:
    """
    Extracts features from the 23 Redrob behavioral signals.

    These signals measure candidate *availability* and *engagement* on the
    platform. The JD explicitly says to down-weight inactive candidates.

    Algorithm:
        - Activity decay: exponential decay based on days since last active.
        - Response quality: linear transform of recruiter_response_rate.
        - Availability composite: open_to_work, notice period, work mode.
        - Verification signals: email, phone, LinkedIn connected.
        - GitHub activity score pass-through.

    Complexity: O(1) per candidate — fixed number of signal lookups.
    Memory: O(1) per candidate — returns a flat dict.
    """

    # Reference date for computing recency (approx mid-2026)
    REFERENCE_DATE = datetime(2026, 6, 29)

    def __init__(self, decay_days: float = 180.0, min_response_rate: float = 0.05):
        self.decay_days = decay_days
        self.min_response_rate = min_response_rate

    def extract(self, candidate: Candidate) -> dict:
        signals = candidate.redrob_signals

        # 1. Activity multiplier: exp(-days_since_active / decay_days)
        try:
            last_active = datetime.strptime(signals.last_active_date, "%Y-%m-%d")
            days_since = (self.REFERENCE_DATE - last_active).days
            days_since = max(0, days_since)
        except (ValueError, TypeError):
            days_since = 365  # Assume very stale if unparseable

        activity_multiplier = math.exp(-days_since / self.decay_days)

        # 2. Response multiplier: 0.5 + 0.5 * response_rate
        #    Floor at min_response_rate to avoid total zeroing
        rr = max(signals.recruiter_response_rate, self.min_response_rate)
        response_multiplier = 0.5 + 0.5 * rr

        # 3. Open-to-work bonus
        open_to_work = 1.0 if signals.open_to_work_flag else 0.0

        # 4. Notice period penalty (0-1 scale, penalize > 90 days)
        np_days = signals.notice_period_days
        if np_days <= 30:
            notice_score = 1.0
        elif np_days <= 60:
            notice_score = 0.9
        elif np_days <= 90:
            notice_score = 0.7
        elif np_days <= 120:
            notice_score = 0.4
        else:
            notice_score = 0.2

        # 5. Work mode compatibility (JD prefers hybrid/flexible)
        work_mode_scores = {
            "hybrid": 1.0,
            "flexible": 0.9,
            "onsite": 0.8,
            "remote": 0.6,
        }
        work_mode_score = work_mode_scores.get(signals.preferred_work_mode, 0.5)

        # 6. Willingness to relocate
        relocate_score = 1.0 if signals.willing_to_relocate else 0.5

        # 7. GitHub activity (-1 means no GitHub linked)
        github_score = 0.0
        if signals.github_activity_score >= 0:
            github_score = signals.github_activity_score / 100.0

        # 8. Verification signals
        verified_count = sum([
            signals.verified_email,
            signals.verified_phone,
            signals.linkedin_connected,
        ])
        verification_score = verified_count / 3.0

        # 9. Interview completion rate
        interview_score = signals.interview_completion_rate

        # 10. Profile completeness (0-100 -> 0-1)
        completeness = signals.profile_completeness_score / 100.0

        # 11. Composite behavioral multiplier
        behavioral_multiplier = (
            activity_multiplier
            * response_multiplier
            * notice_score
        )

        return {
            "activity_multiplier": activity_multiplier,
            "response_multiplier": response_multiplier,
            "open_to_work": open_to_work,
            "notice_score": notice_score,
            "work_mode_score": work_mode_score,
            "relocate_score": relocate_score,
            "github_score": github_score,
            "verification_score": verification_score,
            "interview_score": interview_score,
            "profile_completeness": completeness,
            "behavioral_multiplier": behavioral_multiplier,
            "days_since_active": float(days_since),
        }
