import re
from src.ingestion.candidate_model import Candidate
from src.config.settings import JDRequirements

class CareerFeatures:
    """
    Analyzes candidate career history and tenure pattern features.
    """
    def __init__(self, jd: JDRequirements):
        self.jd = jd
        self.ai_regex = re.compile(
            r"\b(ai|ml|machine learning|deep learning|nlp|natural language|computer vision|data scientist|search|retrieval|ranking|embeddings|recommend|founding engineer)\b",
            re.IGNORECASE
        )
        self.disqualified_firms = [name.lower() for name in jd.disqualifiers.services_companies]

    def extract(self, candidate: Candidate) -> dict:
        history = candidate.career_history
        if not history:
            return {
                "avg_tenure_months": 0.0,
                "services_fraction": 0.0,
                "product_months": 0.0,
                "has_product_exp": 0.0,
                "total_ai_roles": 0.0,
                "is_disqualified_firm_only": 1.0  # Empty history is heavily penalized
            }
            
        total_months = 0
        services_months = 0
        product_months = 0
        ai_roles_count = 0
        disqualified_roles_count = 0
        
        for entry in history:
            dur = entry.duration_months
            total_months += dur
            
            # Check if company is on the disqualified list or has "IT Services" industry
            comp_name = entry.company.lower()
            is_service = False
            
            # Check explicit list match
            for firm in self.disqualified_firms:
                if firm in comp_name:
                    is_service = True
                    break
                    
            # Check industry match
            if entry.industry.lower() == "it services" or entry.industry.lower() == "consulting":
                is_service = True
                
            if is_service:
                services_months += dur
                disqualified_roles_count += 1
            else:
                product_months += dur
                
            # Check if title has AI keywords
            if self.ai_regex.search(entry.title):
                ai_roles_count += 1
                
        # Calculations
        num_roles = len(history)
        avg_tenure = total_months / num_roles if num_roles > 0 else 0.0
        services_fraction = services_months / total_months if total_months > 0 else 0.0
        
        # Flag if they have ONLY worked at disqualified services companies
        is_disqualified_only = 1.0 if disqualified_roles_count == num_roles else 0.0
        
        return {
            "avg_tenure_months": avg_tenure,
            "services_fraction": services_fraction,
            "product_months": product_months,
            "has_product_exp": 1.0 if product_months > 0 else 0.0,
            "total_ai_roles": float(ai_roles_count),
            "is_disqualified_firm_only": is_disqualified_only
        }
