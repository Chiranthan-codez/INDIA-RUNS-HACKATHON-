from src.ingestion.candidate_model import Candidate
from src.config.settings import Settings
from src.features.profile_features import ProfileFeatures
from src.features.career_features import CareerFeatures
from src.features.skill_features import SkillFeatures
from src.features.signal_features import SignalFeatures


class FeatureExtractor:
    """
    Orchestrates all feature sub-extractors into a single flat feature dict
    per candidate.

    Algorithm:
        Calls ProfileFeatures, CareerFeatures, SkillFeatures, SignalFeatures
        in sequence and merges their outputs into one dictionary.

    Complexity: O(S + C) per candidate where S = skills, C = career entries.
    Memory: O(F) per candidate where F = ~25 features (flat dict).
    """

    def __init__(self, settings: Settings):
        self.profile_extractor = ProfileFeatures(settings.jd)
        self.career_extractor = CareerFeatures(settings.jd)
        self.skill_extractor = SkillFeatures(settings.jd)
        self.signal_extractor = SignalFeatures(
            decay_days=settings.settings.behavioral_multiplier.last_active_decay_days,
            min_response_rate=settings.settings.behavioral_multiplier.min_response_rate,
        )

    def extract(self, candidate: Candidate) -> dict:
        """
        Extracts all features for a single candidate.
        Returns a flat dictionary of feature name -> float value.
        """
        features = {}
        features["candidate_id"] = candidate.candidate_id

        # Sub-extractors
        features.update(self.profile_extractor.extract(candidate))
        features.update(self.career_extractor.extract(candidate))
        features.update(self.skill_extractor.extract(candidate))
        features.update(self.signal_extractor.extract(candidate))

        return features
