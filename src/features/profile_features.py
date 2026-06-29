import re
from src.ingestion.candidate_model import Candidate
from src.config.settings import JDRequirements

class ProfileFeatures:
    """
    Extracts features from the static candidate profile.
    """
    def __init__(self, jd: JDRequirements):
        self.jd = jd
        # Regex to capture core AI/ML terms
        self.ai_regex = re.compile(
            r"\b(ai|ml|machine learning|deep learning|nlp|natural language|computer vision|data scientist|search|retrieval|ranking|embeddings|recommend|founding engineer)\b",
            re.IGNORECASE
        )

    def extract(self, candidate: Candidate) -> dict:
        profile = candidate.profile
        
        # 1. Experience Years
        exp_years = profile.years_of_experience
        
        # 2. Target Location Match
        # Check if candidate location matches target cities
        loc_score = 0.0
        candidate_loc = profile.location.lower()
        for target in self.jd.target_locations:
            if target.lower() in candidate_loc:
                loc_score = 1.0
                break
                
        # 3. Current Title Relevance
        current_title = profile.current_title
        title_relevance = 0.0
        
        # Check if current title matches target title
        if self.jd.role.title.lower() in current_title.lower():
            title_relevance = 1.0
        elif self.ai_regex.search(current_title):
            title_relevance = 0.8
        elif "software" in current_title.lower() or "developer" in current_title.lower() or "engineer" in current_title.lower():
            title_relevance = 0.4
            
        # 4. Company Size Feature
        # Enum: ["1-10", "11-50", "51-200", "201-500", "501-1000", "1001-5000", "5001-10000", "10001+"]
        # Small and medium product companies are preferred for a founding engineer
        size_scores = {
            "1-10": 0.9,
            "11-50": 1.0,
            "51-200": 0.9,
            "201-500": 0.8,
            "501-1000": 0.7,
            "1001-5000": 0.5,
            "5001-10000": 0.4,
            "10001+": 0.3
        }
        company_size_score = size_scores.get(profile.current_company_size, 0.5)
        
        return {
            "exp_years": exp_years,
            "location_score": loc_score,
            "current_title_relevance": title_relevance,
            "company_size_score": company_size_score,
        }
