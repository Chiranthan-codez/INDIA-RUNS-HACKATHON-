from src.ingestion.candidate_model import Candidate


class ReasoningGenerator:
    """
    Generates a 1-2 sentence, candidate-specific reasoning string for the
    submission CSV.

    Design principles (from submission_spec Stage 4 checks):
        - Reference specific facts from the candidate's profile.
        - Connect reasoning to JD requirements.
        - Acknowledge gaps honestly.
        - No hallucination — only use data present in the candidate object.
        - Vary sentence structure across candidates.

    Algorithm:
        1. Identify top 2-3 strengths from features.
        2. Identify top 1 concern if any.
        3. Compose sentence using template variants selected by candidate_id hash
           to ensure variation.

    Complexity: O(S + C) per candidate where S = skills, C = career entries.
    Memory: O(1) per call.
    """

    # Sentence starters for variation (selected by hash of candidate_id)
    OPENERS = [
        "{title} with {exp:.1f} years of experience",
        "{exp:.1f}-year {title}",
        "Experienced {title} ({exp:.1f} yrs)",
        "{title}, {exp:.1f} years in the field",
        "{title} bringing {exp:.1f} years of experience",
    ]

    def generate(self, candidate: Candidate, features: dict, score: float, rank: int) -> str:
        profile = candidate.profile
        skills = candidate.skills

        # Pick opener variant using candidate_id hash for deterministic variation
        opener_idx = hash(candidate.candidate_id) % len(self.OPENERS)
        opener = self.OPENERS[opener_idx].format(
            title=profile.current_title,
            exp=profile.years_of_experience,
        )

        # Strengths
        strengths = []

        # Skill match strength
        bucket_count = features.get("skill_matched_bucket_count", 0)
        if bucket_count >= 4:
            strengths.append(f"strong JD skill alignment ({int(bucket_count)}/8 requirement buckets)")
        elif bucket_count >= 2:
            strengths.append(f"partial JD skill alignment ({int(bucket_count)}/8 buckets)")

        # Career strength
        ai_roles = features.get("total_ai_roles", 0)
        if ai_roles >= 2:
            strengths.append(f"{int(ai_roles)} AI/ML-titled roles in career history")
        elif ai_roles >= 1:
            strengths.append("prior AI/ML-titled role")

        # Product company experience
        if features.get("has_product_exp", 0) > 0 and features.get("services_fraction", 1.0) < 0.5:
            strengths.append("predominantly product-company background")

        # Location match
        if features.get("location_score", 0) > 0.5:
            strengths.append(f"based in {profile.location}")

        # Behavioral strengths
        if features.get("open_to_work", 0) > 0.5:
            strengths.append("actively looking")
        if features.get("github_score", 0) > 0.5:
            strengths.append("strong GitHub activity")

        # Concerns
        concerns = []

        if features.get("notice_score", 1.0) < 0.5:
            np_days = candidate.redrob_signals.notice_period_days
            concerns.append(f"long notice period ({np_days} days)")

        if features.get("days_since_active", 0) > 90:
            days = int(features.get("days_since_active", 0))
            concerns.append(f"inactive for {days} days")

        if features.get("is_disqualified_firm_only", 0) > 0.5:
            concerns.append("only services-company experience")

        if features.get("skill_trust_multiplier", 1.0) < 0.8:
            concerns.append("possible skill inflation")

        exp = profile.years_of_experience
        if exp < 5:
            concerns.append(f"below experience threshold ({exp:.1f} yrs)")
        elif exp > 12:
            concerns.append(f"significantly over experience band ({exp:.1f} yrs)")

        # Compose
        parts = [opener]

        if strengths:
            parts.append("; ".join(strengths[:3]))

        if concerns and rank > 30:
            # Only mention concerns for lower-ranked candidates
            parts.append("concern: " + concerns[0])
        elif concerns and len(concerns) > 0 and rank > 60:
            parts.append("concerns: " + "; ".join(concerns[:2]))

        reasoning = "; ".join(parts) + "."

        # Truncate if too long (submission column should be concise)
        if len(reasoning) > 300:
            reasoning = reasoning[:297] + "..."

        return reasoning
