"""
Atlas AI — Visa Advisor
Intelligent visa recommendation system using Groq AI.
Provides personalized visa recommendations based on user profiles and complete rule analysis.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple

from groq_config import GROQ_API_KEY, GROQ_API_URL, GROQ_MODEL, GROQ_SYSTEM_PROMPT
from src.rule_engine.rules_base import ApplicantProfile, EligibilityResult, Verdict
from src.rule_engine.visa_recommender import VisaRecommender, get_visa_recommendation
from src.rule_engine.rules_loader import rules_loader

logger = logging.getLogger(__name__)


class VisaAdvisor:
    """
    Intelligent visa advisor that combines rule-based analysis with AI-powered recommendations.
    
    This class:
    1. Analyzes user profile against all visa rules
    2. Uses Groq AI to provide personalized recommendations
    3. Explains why certain visas are better suited
    4. Provides actionable next steps
    """
    
    def __init__(self):
        self.api_key = GROQ_API_KEY
        self.api_url = GROQ_API_URL
        self.model = GROQ_MODEL
        self.system_prompt = GROQ_SYSTEM_PROMPT
        self.recommender = VisaRecommender()
        
        # Check if API key is configured
        self.available = bool(self.api_key) and self.api_key != ""
        
        if not self.available:
            logger.warning("Groq API key not configured. Set GROQ_API_KEY in groq_config.py")
    
    def analyze_and_recommend(
        self,
        profile: ApplicantProfile,
        user_location: Optional[str] = None,
        user_intent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Perform comprehensive visa analysis and provide AI-powered recommendations.
        
        Args:
            profile: ApplicantProfile with user's details
            user_location: Current location (e.g., "Dubai", "India")
            user_intent: User's stated intent (e.g., "work", "study", "join family")
            
        Returns:
            Comprehensive recommendation with AI-generated explanations
        """
        # Step 1: Get rule-based recommendations
        recommendation = get_visa_recommendation(
            profile, 
            user_location=user_location,
            user_intent=user_intent,
        )
        
        # Step 2: Build detailed analysis context
        analysis_context = self._build_analysis_context(profile, recommendation)
        
        # Step 3: Generate AI-powered recommendations (if Groq is available)
        if self.available:
            ai_recommendation = self._generate_ai_recommendation(
                profile, recommendation, analysis_context
            )
            if ai_recommendation:
                recommendation["ai_analysis"] = ai_recommendation
        
        # Step 4: Add detailed rule-based explanations
        recommendation["detailed_analysis"] = self._build_detailed_analysis(
            profile, recommendation
        )
        
        return recommendation
    
    def _build_analysis_context(
        self, 
        profile: ApplicantProfile, 
        recommendation: Dict[str, Any]
    ) -> str:
        """Build context string for AI analysis."""
        context_parts = []
        
        # Profile summary
        context_parts.append("=== User Profile ===")
        if profile.job_title:
            context_parts.append(f"Occupation: {profile.job_title}")
        if profile.salary_annual:
            context_parts.append(f"Annual Salary: £{profile.salary_annual:,}")
        if profile.country_of_origin:
            context_parts.append(f"Nationality: {profile.country_of_origin}")
        if profile.age:
            context_parts.append(f"Age: {profile.age}")
        if profile.qualification:
            context_parts.append(f"Education: {profile.qualification}")
        if profile.english_proficiency:
            context_parts.append(f"English Level: {profile.english_proficiency}")
        if profile.has_sponsor is not None:
            context_parts.append(f"Has Sponsor: {'Yes' if profile.has_sponsor else 'No'}")
        if profile.current_visa_type:
            context_parts.append(f"Current Visa: {profile.current_visa_type}")
        
        # Visa options summary
        context_parts.append("\n=== Visa Options Analysis ===")
        all_options = recommendation.get("all_options", [])
        for option in all_options[:3]:  # Top 3 options
            context_parts.append(
                f"- {option.visa_name}: {option.verdict.upper()} "
                f"(Score: {option.score}, Priority: {option.priority})"
            )
            if option.matched_criteria:
                context_parts.append(f"  Matched: {', '.join(option.matched_criteria[:3])}")
            if option.missing_criteria:
                context_parts.append(f"  Missing: {', '.join(option.missing_criteria[:3])}")
        
        return "\n".join(context_parts)
    
    def _generate_ai_recommendation(
        self,
        profile: ApplicantProfile,
        recommendation: Dict[str, Any],
        context: str,
    ) -> Optional[str]:
        """Generate AI-powered recommendation using Groq."""
        try:
            import requests
            
            # Build the prompt
            user_prompt = f"""Based on the following UK visa analysis, provide a comprehensive, personalized recommendation:

{context}

Please provide:
1. **Best Visa Option**: Clearly state which visa is the best fit and why
2. **Alternative Options**: Mention 1-2 backup options if the primary doesn't work
3. **Key Requirements**: Highlight the most critical requirements the user must meet
4. **Action Steps**: Provide specific, actionable next steps
5. **Potential Challenges**: Mention any challenges or red flags in their profile
6. **Timeline**: Give a rough timeline for the application process

Be encouraging but realistic. Focus on facts from the analysis above. Always recommend verifying information on GOV.UK."""

            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 1500,
                    "top_p": 0.95,
                },
                timeout=30,
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                return ai_response
            else:
                logger.warning(f"Groq API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating AI recommendation: {e}")
            return None
    
    def _build_detailed_analysis(
        self,
        profile: ApplicantProfile,
        recommendation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build detailed rule-based analysis."""
        detailed = {
            "eligible_visa_types": [],
            "ineligible_visa_types": [],
            "insufficient_info_types": [],
            "recommendations": [],
        }
        
        all_options = recommendation.get("all_options", [])
        
        for option in all_options:
            visa_info = {
                "visa_type": option.visa_type,
                "visa_name": option.visa_name,
                "verdict": option.verdict,
                "score": option.score,
                "priority": option.priority,
                "summary": option.summary,
                "matched_criteria": option.matched_criteria,
                "missing_criteria": option.missing_criteria,
            }
            
            if option.verdict == "eligible":
                detailed["eligible_visa_types"].append(visa_info)
            elif option.verdict == "not_eligible":
                detailed["ineligible_visa_types"].append(visa_info)
            else:
                detailed["insufficient_info_types"].append(visa_info)
        
        # Generate specific recommendations
        if detailed["eligible_visa_types"]:
            best_option = detailed["eligible_visa_types"][0]
            detailed["recommendations"].append({
                "type": "primary",
                "message": f"Based on your profile, the **{best_option['visa_name']}** appears to be your best option.",
                "visa_type": best_option["visa_type"],
            })
        
        if detailed["insufficient_info_types"]:
            detailed["recommendations"].append({
                "type": "info_needed",
                "message": "Some visa options require additional information. Providing more details may open up more options.",
            })
        
        if detailed["ineligible_visa_types"]:
            # Check if any can be made eligible with changes
            for visa in detailed["ineligible_visa_types"]:
                if visa["missing_criteria"]:
                    detailed["recommendations"].append({
                        "type": "improvement",
                        "message": f"For the **{visa['visa_name']}**, you would need to address: {', '.join(visa['missing_criteria'][:2])}.",
                        "visa_type": visa["visa_type"],
                    })
        
        return detailed
    
    def get_visa_comparison_report(
        self,
        profile: ApplicantProfile,
    ) -> str:
        """
        Generate a comprehensive comparison report for all visa types.
        
        Returns:
            Formatted string report comparing all visa options
        """
        report_parts = []
        report_parts.append("# UK Visa Options Comparison Report\n")
        report_parts.append(f"Generated for: {profile.job_title or 'Applicant'}\n")
        report_parts.append("=" * 50 + "\n\n")
        
        # Get recommendation
        recommendation = get_visa_recommendation(profile)
        
        # Add profile summary
        report_parts.append("## Your Profile Summary\n")
        if profile.job_title:
            report_parts.append(f"- **Occupation**: {profile.job_title}")
        if profile.salary_annual:
            report_parts.append(f"- **Salary**: £{profile.salary_annual:,}/year")
        if profile.qualification:
            report_parts.append(f"- **Education**: {profile.qualification}")
        if profile.country_of_origin:
            report_parts.append(f"- **Nationality**: {profile.country_of_origin}")
        report_parts.append("\n")
        
        # Add visa comparison
        report_parts.append("## Visa Options Ranked by Suitability\n\n")
        
        all_options = recommendation.get("all_options", [])
        for i, option in enumerate(all_options, 1):
            status_emoji = "✅" if option.verdict == "eligible" else "❌" if option.verdict == "not_eligible" else "⚠️"
            report_parts.append(f"### {i}. {option.visa_name} {status_emoji}\n")
            report_parts.append(f"**Status**: {option.verdict.upper()}\n")
            report_parts.append(f"**Suitability Score**: {option.score}/100\n\n")
            report_parts.append(f"**Summary**: {option.summary}\n\n")
            
            if option.matched_criteria:
                report_parts.append("**Your Strengths for this visa:**\n")
                for criterion in option.matched_criteria:
                    report_parts.append(f"- ✓ {criterion}")
                report_parts.append("\n")
            
            if option.missing_criteria:
                report_parts.append("**Areas to Address:**\n")
                for criterion in option.missing_criteria:
                    report_parts.append(f"- ✗ {criterion}")
                report_parts.append("\n")
            
            report_parts.append("---\n\n")
        
        # Add disclaimer
        report_parts.append("## Important Disclaimer\n\n")
        report_parts.append(
            "This report is for informational purposes only and does not constitute "
            "legal advice. Immigration rules change frequently. Always verify information "
            "on the official [GOV.UK website](https://www.gov.uk) or consult with a "
            "qualified immigration advisor before making any decisions.\n"
        )
        
        return "\n".join(report_parts)
    
    def is_configured(self) -> bool:
        """Check if Groq API is properly configured."""
        return self.available


# Global visa advisor instance
visa_advisor = VisaAdvisor()