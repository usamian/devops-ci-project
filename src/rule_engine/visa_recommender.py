"""
Atlas AI — Visa Recommender System
Analyzes user profile and recommends the best UK visa options.

This system checks eligibility across all available visa types and
provides a ranked recommendation based on the user's circumstances.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from src.rule_engine.rules_base import ApplicantProfile, EligibilityResult, Verdict
from src.rule_engine.skilled_worker import SkilledWorkerRuleEngine
from src.rule_engine.health_care_worker import HealthCareWorkerRuleEngine
from src.rule_engine.graduate import GraduateRuleEngine
from src.rule_engine.global_talent import GlobalTalentRuleEngine
from src.rule_engine.student_visa import StudentVisaRuleEngine
from src.rule_engine.family_visa import FamilyVisaRuleEngine


@dataclass
class VisaRecommendation:
    """Represents a visa recommendation with score and details."""
    visa_type: str
    visa_name: str
    verdict: str
    summary: str
    score: int
    matched_criteria: List[str]
    missing_criteria: List[str]
    priority: int  # 1 = highest priority


class VisaRecommender:
    """
    Recommends the best UK visa options based on user profile.
    
    The recommender:
    1. Checks eligibility for all available visa types
    2. Calculates a compatibility score for each
    3. Ranks options by score and suitability
    4. Provides detailed explanations for each option
    """
    
    def __init__(self):
        # Initialize all rule engines
        self.engines = {
            "skilled_worker": SkilledWorkerRuleEngine(),
            "health_care_worker": HealthCareWorkerRuleEngine(),
            "graduate": GraduateRuleEngine(),
            "global_talent": GlobalTalentRuleEngine(),
            "student": StudentVisaRuleEngine(),
            "family": FamilyVisaRuleEngine(),
        }
        
        # Visa priority order (generally preferred options first)
        self.visa_priority = {
            "skilled_worker": 1,      # Most common work route
            "health_care_worker": 2,  # Special healthcare route
            "global_talent": 3,       # For exceptional individuals
            "graduate": 4,            # Post-study work
            "student": 5,             # Study route
            "family": 6,              # Family route
        }
    
    def recommend_best_visa(
        self, 
        profile: ApplicantProfile,
        user_location: Optional[str] = None,
        user_intent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze profile and recommend the best visa options.
        
        Args:
            profile: ApplicantProfile with user's details
            user_location: Current location (e.g., "Dubai", "India")
            user_intent: User's stated intent (e.g., "work", "study", "join family")
        
        Returns:
            Dictionary with recommended visas and detailed analysis
        """
        results = []
        
        for visa_type, engine in self.engines.items():
            try:
                result = engine.check_eligibility(profile)
                
                # Calculate compatibility score
                score, matched, missing = self._calculate_compatibility_score(
                    profile, result, visa_type
                )
                
                # Adjust score based on user intent
                if user_intent:
                    score = self._adjust_score_for_intent(score, visa_type, user_intent)
                
                # Adjust score based on location (some visas harder from certain countries)
                if user_location:
                    score = self._adjust_score_for_location(score, visa_type, user_location)
                
                results.append(VisaRecommendation(
                    visa_type=visa_type,
                    visa_name=engine.VISA_NAME,
                    verdict=result.verdict.value,
                    summary=result.summary,
                    score=score,
                    matched_criteria=matched,
                    missing_criteria=missing,
                    priority=self.visa_priority.get(visa_type, 10),
                ))
                
            except Exception as e:
                # Log error but continue with other visas
                print(f"[VisaRecommender] Error checking {visa_type}: {e}")
                continue
        
        # Sort by score (descending), then by priority (ascending)
        results.sort(key=lambda x: (-x.score, x.priority))
        
        return {
            "recommended_visa": results[0] if results else None,
            "all_options": results,
            "eligible_options": [r for r in results if r.verdict == "eligible"],
            "profile_summary": self._summarize_profile(profile),
            "user_location": user_location,
            "user_intent": user_intent,
        }
    
    def _calculate_compatibility_score(
        self,
        profile: ApplicantProfile,
        result: EligibilityResult,
        visa_type: str,
    ) -> Tuple[int, List[str], List[str]]:
        """
        Calculate compatibility score for a visa type.
        
        Returns:
            Tuple of (score, matched_criteria, missing_criteria)
        """
        score = 0
        matched = []
        missing = []
        
        # Base score for eligibility
        if result.verdict == Verdict.ELIGIBLE:
            score += 100
            matched.append("Meets all eligibility requirements")
        elif result.verdict == Verdict.INSUFFICIENT_INFO:
            score += 30
            missing.append("Insufficient information provided")
        else:
            # Check how close to eligible
            passed_rules = len([r for r in result.rule_results if r.passed])
            total_rules = len(result.rule_results)
            if total_rules > 0:
                pass_rate = passed_rules / total_rules
                score += int(pass_rate * 70)
                
                if pass_rate >= 0.8:
                    matched.append("Meets most requirements")
                elif pass_rate >= 0.5:
                    matched.append("Meets some requirements")
                    missing.append("Several requirements not met")
                else:
                    missing.append("Most requirements not met")
        
        # Bonus points for specific profile attributes
        if visa_type == "skilled_worker":
            if profile.salary_annual and profile.salary_annual >= 50000:
                score += 15
                matched.append("High salary (£50k+)")
            if profile.job_title:
                score += 5
                matched.append(f"Professional occupation ({profile.job_title})")
            if profile.has_sponsor:
                score += 20
                matched.append("Has sponsor/Certificate of Sponsorship")
            if profile.english_proficiency in ("test_passed", "native", "exempt"):
                score += 10
                matched.append("English proficiency confirmed")
            if not profile.has_sponsor:
                missing.append("No sponsor yet - need to find UK employer")
        
        elif visa_type == "health_care_worker":
            if profile.job_title:
                job_lower = profile.job_title.lower()
                if any(term in job_lower for term in ["nurse", "doctor", "care", "health", "medical"]):
                    score += 20
                    matched.append("Healthcare profession")
            if profile.has_sponsor:
                score += 15
                matched.append("Has NHS/healthcare sponsor")
        
        elif visa_type == "graduate":
            if profile.qualification:
                qual_lower = profile.qualification.lower()
                if "phd" in qual_lower:
                    score += 15
                    matched.append("PhD from UK institution (3 years granted)")
                elif any(term in qual_lower for term in ["master", "msc", "mba"]):
                    score += 10
                    matched.append("UK Master's degree (2 years granted)")
                elif any(term in qual_lower for term in ["bachelor", "bsc", "ba"]):
                    score += 5
                    matched.append("UK Bachelor's degree (2 years granted)")
            if profile.current_visa_type and "student" in profile.current_visa_type.lower():
                score += 15
                matched.append("Currently on Student visa")
            else:
                missing.append("Must currently hold Student visa")
        
        elif visa_type == "global_talent":
            if profile.qualification:
                qual_lower = profile.qualification.lower()
                if "phd" in qual_lower:
                    score += 15
                    matched.append("Doctoral qualification")
            if profile.job_title:
                job_lower = profile.job_title.lower()
                if any(term in job_lower for term in ["professor", "researcher", "scientist", "academic"]):
                    score += 15
                    matched.append("Academic/research profession")
                elif any(term in job_lower for term in ["software", "developer", "engineer", "ai", "tech"]):
                    score += 10
                    matched.append("Digital technology profession")
                elif any(term in job_lower for term in ["artist", "designer", "writer", "musician"]):
                    score += 10
                    matched.append("Arts and culture profession")
            if hasattr(profile, 'has_endorsement') and profile.has_endorsement:
                score += 20
                matched.append("Has endorsement from competent body")
            else:
                missing.append("Need endorsement from designated body")
        
        elif visa_type == "student":
            if hasattr(profile, 'has_cas') and profile.has_cas:
                score += 25
                matched.append("Has CAS from UK institution")
            if profile.english_proficiency in ("test_passed", "native", "exempt"):
                score += 10
                matched.append("English proficiency confirmed")
            if profile.savings and profile.savings >= 15000:
                score += 10
                matched.append("Sufficient funds for maintenance")
            else:
                missing.append("Need CAS and maintenance funds")
        
        elif visa_type == "family":
            if hasattr(profile, 'relationship_status') and profile.relationship_status:
                score += 15
                matched.append(f"Relationship status: {profile.relationship_status}")
            if hasattr(profile, 'partner_uk_status') and profile.partner_uk_status:
                score += 15
                matched.append("Partner has UK status")
            sponsor_income = getattr(profile, 'sponsor_income', None)
            if sponsor_income and sponsor_income >= 18600:
                score += 15
                matched.append("Meets financial requirement")
            else:
                missing.append("Need to meet £18,600 income requirement")
        
        return score, matched, missing
    
    def _adjust_score_for_intent(
        self, 
        score: int, 
        visa_type: str, 
        user_intent: str
    ) -> int:
        """Adjust score based on user's stated intent."""
        intent_lower = user_intent.lower()
        
        # Intent-based adjustments
        if "work" in intent_lower or "job" in intent_lower:
            if visa_type in ("skilled_worker", "health_care_worker", "global_talent"):
                score += 10
        elif "study" in intent_lower or "education" in intent_lower:
            if visa_type == "student":
                score += 15
            elif visa_type == "graduate":
                score += 5
        elif "family" in intent_lower or "spouse" in intent_lower or "partner" in intent_lower:
            if visa_type == "family":
                score += 15
        elif "post-study" in intent_lower or "after graduation" in intent_lower:
            if visa_type == "graduate":
                score += 20
        
        return score
    
    def _adjust_score_for_location(
        self, 
        score: int, 
        visa_type: str, 
        user_location: str
    ) -> int:
        """Adjust score based on user's current location."""
        location_lower = user_location.lower()
        
        # Some locations may have specific considerations
        # This is a simplified version - in practice, you'd have more nuanced rules
        
        return score
    
    def _summarize_profile(self, profile: ApplicantProfile) -> str:
        """Create a human-readable summary of the user's profile."""
        parts = []
        
        if profile.job_title:
            parts.append(f"Occupation: {profile.job_title}")
        if profile.salary_annual:
            parts.append(f"Salary: £{profile.salary_annual:,}/year")
        if profile.country_of_origin:
            parts.append(f"Nationality: {profile.country_of_origin}")
        if profile.age:
            parts.append(f"Age: {profile.age}")
        if profile.qualification:
            parts.append(f"Education: {profile.qualification}")
        if profile.english_proficiency:
            parts.append(f"English: {profile.english_proficiency}")
        if profile.has_sponsor is not None:
            parts.append(f"Sponsorship: {'Yes' if profile.has_sponsor else 'No'}")
        
        return ", ".join(parts) if parts else "Incomplete profile"
    
    def get_visa_comparison(
        self, 
        profile: ApplicantProfile,
        visa_types: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Compare specific visa types side-by-side.
        
        Args:
            profile: ApplicantProfile
            visa_types: List of visa types to compare (default: all)
        
        Returns:
            Comparison table data
        """
        if visa_types is None:
            visa_types = list(self.engines.keys())
        
        comparison = []
        for visa_type in visa_types:
            if visa_type not in self.engines:
                continue
            
            engine = self.engines[visa_type]
            result = engine.check_eligibility(profile)
            
            comparison.append({
                "visa_type": visa_type,
                "visa_name": engine.VISA_NAME,
                "verdict": result.verdict.value,
                "summary": result.summary,
                "rules_passed": len([r for r in result.rule_results if r.passed]),
                "total_rules": len(result.rule_results),
                "source_url": engine.GOV_UK_URL,
            })
        
        return {
            "comparison": comparison,
            "profile_summary": self._summarize_profile(profile),
        }


# Global instance for easy access
visa_recommender = VisaRecommender()


def get_visa_recommendation(
    profile: ApplicantProfile,
    user_location: Optional[str] = None,
    user_intent: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convenience function to get visa recommendations.
    
    Example usage:
        profile = ApplicantProfile(
            job_title="Software Engineer",
            salary_annual=50000,
            has_sponsor=False,
            country_of_origin="India",
            age=28,
            qualification="BSc Computer Science",
            english_proficiency="test_passed",
        )
        
        recommendation = get_visa_recommendation(
            profile, 
            user_location="Dubai",
            user_intent="work"
        )
    """
    return visa_recommender.recommend_best_visa(profile, user_location, user_intent)