from datetime import datetime
from src.ingestion.candidate_model import Candidate

class HoneypotDetector:
    """
    Identifies 'honeypots' and impossible profiles within the candidate pool
    using a set of strict chronological and data-consistency rules.
    """
    def __init__(self, thresholds=None):
        # We can pass thresholds from program settings
        self.min_expert_zero_count = 3
        self.max_duration_mismatch_months = 3
        self.max_career_pre_edu_years = 6

    def check(self, candidate: Candidate) -> bool:
        """
        Runs all consistency checks on a candidate.
        Returns True if the candidate is flagged as a honeypot, False otherwise.
        """
        if self._check_expert_skills_inflation(candidate):
            return True
        if self._check_career_duration_mismatch(candidate):
            return True
        if self._check_education_vs_career_mismatch(candidate):
            return True
        if self._check_experience_profile_mismatch(candidate):
            return True
        return False

    def _check_expert_skills_inflation(self, candidate: Candidate) -> bool:
        """
        Checks if the candidate claims to be an expert in many skills
        with exactly 0 months of usage.
        """
        expert_zero_count = 0
        for skill in candidate.skills:
            if skill.proficiency == "expert" and skill.duration_months == 0:
                expert_zero_count += 1
        return expert_zero_count >= self.min_expert_zero_count

    def _check_career_duration_mismatch(self, candidate: Candidate) -> bool:
        """
        Checks if the listed duration_months of any job role is completely
        inconsistent with the start and end dates.
        """
        current_year = 2026
        current_month = 6
        
        for entry in candidate.career_history:
            start_str = entry.start_date
            end_str = entry.end_date
            listed_dur = entry.duration_months
            
            try:
                start_dt = datetime.strptime(start_str, "%Y-%m-%d")
                if end_str:
                    end_dt = datetime.strptime(end_str, "%Y-%m-%d")
                else:
                    end_dt = datetime(current_year, current_month, 29)
                    
                calc_dur = (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month)
                
                # Check for negative duration or significant mismatch
                if calc_dur < 0 or abs(calc_dur - listed_dur) > self.max_duration_mismatch_months:
                    return True
            except ValueError:
                # If date format is corrupt
                return True
        return False

    def _check_education_vs_career_mismatch(self, candidate: Candidate) -> bool:
        """
        Checks if the candidate started working full-time long before
        starting their earliest higher education degree.
        """
        career_years = []
        for entry in candidate.career_history:
            try:
                year = int(entry.start_date.split("-")[0])
                career_years.append(year)
            except ValueError:
                pass
                
        edu_years = [edu.start_year for edu in candidate.education if edu.start_year]
        
        if career_years and edu_years:
            earliest_career = min(career_years)
            earliest_edu = min(edu_years)
            if earliest_edu - earliest_career > self.max_career_pre_edu_years:
                return True
        return False

    def _check_experience_profile_mismatch(self, candidate: Candidate) -> bool:
        """
        Checks if the static overall years_of_experience listed in the profile
        is completely mismatched with the sum of durations of their roles.
        """
        exp_years = candidate.profile.years_of_experience
        total_dur_years = sum(entry.duration_months for entry in candidate.career_history) / 12.0
        
        # If experience is stated as > 2 years but total roles duration is double or less than 30% of it
        if exp_years > 2:
            if total_dur_years > exp_years * 2.0 or total_dur_years < exp_years * 0.3:
                return True
        return False
