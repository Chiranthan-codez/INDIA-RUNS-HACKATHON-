from src.config.settings import ScoringWeights, BehavioralMultiplier


class Scorer:
    """
    Computes a composite ranking score from extracted features.

    Formula:
        score_raw = (
            w_title   * title_score
          + w_skill   * skill_score
          + w_career  * career_score
          + w_exp     * experience_band_score
          + w_loc     * location_score
          + w_edu     * education_score
        )
        score_final = score_raw * behavioral_multiplier * trust_multiplier

    Complexity: O(1) per candidate — fixed arithmetic.
    Memory: O(1).
    """

    def __init__(self, weights: ScoringWeights, behavioral: BehavioralMultiplier):
        self.w = weights
        self.bm = behavioral

    def score(self, features: dict, is_honeypot: bool = False) -> float:
        """
        Computes the final composite score for one candidate.
        Returns 0.0 if the candidate is flagged as a honeypot.
        """
        if is_honeypot:
            return 0.0

        # --- Sub-scores (each normalized to 0-1) ---

        # Title relevance (from profile_features)
        title_score = features.get("current_title_relevance", 0.0)

        # Skill alignment (from skill_features)
        # Combine bucket coverage and weighted score
        bucket_coverage = features.get("skill_bucket_coverage", 0.0)
        # Normalize the raw weighted score with a soft cap
        raw_weighted = features.get("skill_weighted_score", 0.0)
        weighted_norm = min(1.0, raw_weighted / 50.0)  # Cap at 50 for normalization
        skill_score = 0.6 * bucket_coverage + 0.4 * weighted_norm

        # Career fit (from career_features)
        has_product = features.get("has_product_exp", 0.0)
        services_frac = features.get("services_fraction", 0.0)
        ai_roles = min(1.0, features.get("total_ai_roles", 0.0) / 3.0)
        disqualified_only = features.get("is_disqualified_firm_only", 0.0)

        career_score = (
            0.3 * has_product
            + 0.3 * (1.0 - services_frac)
            + 0.3 * ai_roles
            + 0.1 * (1.0 - disqualified_only)
        )

        # Experience band score (sweet spot: 5-9 years, peak at 6-8)
        exp = features.get("exp_years", 0.0)
        exp_score = self._experience_band(exp)

        # Location score
        loc_score = features.get("location_score", 0.0)

        # Education score (placeholder — not heavily weighted per JD)
        # The JD doesn't emphasize education, so we give a flat 0.5 baseline
        edu_score = 0.5

        # --- Raw composite ---
        score_raw = (
            self.w.title_match * title_score
            + self.w.skill_alignment * skill_score
            + self.w.career_fit * career_score
            + self.w.experience_band * exp_score
            + self.w.location * loc_score
            + self.w.education * edu_score
        )

        # --- Multiplicative modifiers ---
        behavioral = features.get("behavioral_multiplier", 1.0)
        trust = features.get("skill_trust_multiplier", 1.0)

        # Open-to-work bonus
        if features.get("open_to_work", 0.0) > 0.5:
            behavioral *= self.bm.open_to_work_bonus

        # GitHub bonus (additive, small)
        github = features.get("github_score", 0.0)
        score_raw += 0.02 * github  # Small bonus, won't dominate

        score_final = score_raw * behavioral * trust

        return round(max(0.0, min(1.0, score_final)), 6)

    @staticmethod
    def _experience_band(years: float) -> float:
        """
        Piecewise scoring for experience years.
        Sweet spot: 6-8 years → 1.0
        Acceptable: 5-9 years → 0.6-1.0
        Outside: decays toward 0.
        """
        if years < 2:
            return 0.0
        elif years < 5:
            return 0.1 + 0.1 * (years - 2)  # 0.1 → 0.4
        elif years < 6:
            return 0.4 + 0.6 * (years - 5)  # 0.4 → 1.0
        elif years <= 8:
            return 1.0
        elif years <= 9:
            return 1.0 - 0.2 * (years - 8)  # 1.0 → 0.8
        elif years <= 12:
            return 0.8 - 0.15 * (years - 9)  # 0.8 → 0.35
        else:
            return max(0.1, 0.35 - 0.02 * (years - 12))
