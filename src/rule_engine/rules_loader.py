"""
Atlas AI — Rules Loader
Centralized loader for visa rules from JSON files.
Ensures all rule engines use consistent, data-driven rules.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Mapping of visa types to their JSON rule files
VISA_RULE_FILES = {
    "skilled_worker": "skilled_worker_rules.json",
    "health_care_worker": "health_care_worker_rules.json",
    "graduate": "graduate_rules.json",
    "global_talent": "global_talent_rules.json",
    "student": "student_visa_rules.json",
    "family": "family_visa_rules.json",
}


class RulesLoader:
    """
    Centralized loader for visa rules from JSON files.
    
    This class provides a single source of truth for all visa rules,
    ensuring consistency across all rule engines.
    """
    
    def __init__(self, rules_dir: Optional[str] = None):
        """
        Initialize the rules loader.
        
        Args:
            rules_dir: Directory containing rule JSON files. 
                      Defaults to data/rules/
        """
        if rules_dir:
            self.rules_dir = Path(rules_dir)
        else:
            # Default to data/rules/ relative to project root
            self.rules_dir = Path(__file__).parent.parent.parent / "data" / "rules"
        
        # Cache for loaded rules
        self._rules_cache: Dict[str, Dict[str, Any]] = {}
    
    def load_rules(self, visa_type: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        Load rules for a specific visa type from JSON file.
        
        Args:
            visa_type: The visa type (e.g., 'skilled_worker', 'graduate')
            use_cache: Whether to use cached rules if available
            
        Returns:
            Dictionary containing rules and metadata, or None if not found
        """
        # Check cache first
        if use_cache and visa_type in self._rules_cache:
            return self._rules_cache[visa_type]
        
        # Get the rule file name
        rule_file = VISA_RULE_FILES.get(visa_type)
        if not rule_file:
            logger.warning(f"No rule file mapping found for visa type: {visa_type}")
            return None
        
        # Construct file path
        rule_path = self.rules_dir / rule_file
        
        # Check if file exists
        if not rule_path.exists():
            logger.warning(f"Rule file not found: {rule_path}")
            return None
        
        # Load and parse JSON
        try:
            with open(rule_path, 'r', encoding='utf-8') as f:
                rules_data = json.load(f)
            
            # Cache the loaded rules
            if use_cache:
                self._rules_cache[visa_type] = rules_data
            
            return rules_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing rule file {rule_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading rule file {rule_path}: {e}")
            return None
    
    def get_rule(self, visa_type: str, rule_key: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific rule for a visa type.
        
        Args:
            visa_type: The visa type
            rule_key: The rule key (e.g., 'sponsorship', 'salary')
            
        Returns:
            The rule dictionary, or None if not found
        """
        rules_data = self.load_rules(visa_type)
        if not rules_data:
            return None
        
        rules = rules_data.get("rules", {})
        return rules.get(rule_key)
    
    def get_all_rules(self, visa_type: str) -> Optional[Dict[str, Dict[str, Any]]]:
        """
        Get all rules for a visa type.
        
        Args:
            visa_type: The visa type
            
        Returns:
            Dictionary of all rules, or None if not found
        """
        rules_data = self.load_rules(visa_type)
        if not rules_data:
            return None
        
        return rules_data.get("rules", {})
    
    def get_metadata(self, visa_type: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a visa type.
        
        Args:
            visa_type: The visa type
            
        Returns:
            Metadata dictionary, or None if not found
        """
        rules_data = self.load_rules(visa_type)
        if not rules_data:
            return None
        
        return rules_data.get("_metadata")
    
    def get_visa_config(self, visa_type: str) -> Optional[Dict[str, Any]]:
        """
        Get the full configuration for a visa type (rules + metadata + extras).
        
        Args:
            visa_type: The visa type
            
        Returns:
            Full configuration dictionary, or None if not found
        """
        return self.load_rules(visa_type)
    
    def list_available_visa_types(self) -> list:
        """
        List all visa types that have rule files available.
        
        Returns:
            List of available visa type strings
        """
        available = []
        for visa_type, rule_file in VISA_RULE_FILES.items():
            rule_path = self.rules_dir / rule_file
            if rule_path.exists():
                available.append(visa_type)
        return available
    
    def refresh_cache(self):
        """Clear the rules cache to force reloading from files."""
        self._rules_cache.clear()


# Global rules loader instance
rules_loader = RulesLoader()