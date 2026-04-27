# generation/drc/rules.py

from typing import Dict, Any, List
from config.settings import settings
from utils.logger import get_module_logger


logger = get_module_logger(__name__)


# --------------------------------------------------
# RULE SEVERITY
# --------------------------------------------------
SEVERITY = {
    "ERROR": "ERROR",
    "WARNING": "WARNING",
    "INFO": "INFO"
}


# --------------------------------------------------
# DEFAULT RULES (BASELINE)
# --------------------------------------------------
DEFAULT_RULES = {
    "min_trace_width": {
        "value": settings.MIN_TRACE_WIDTH,
        "severity": SEVERITY["ERROR"]
    },
    "min_clearance": {
        "value": settings.MIN_CLEARANCE,
        "severity": SEVERITY["ERROR"]
    },
    "component_overlap": {
        "enabled": True,
        "severity": SEVERITY["ERROR"]
    },
    "route_clearance": {
        "enabled": True,
        "severity": SEVERITY["ERROR"]
    },
    "route_component_clearance": {
        "enabled": True,
        "severity": SEVERITY["ERROR"]
    },
    "boundary_check": {
        "enabled": True,
        "severity": SEVERITY["ERROR"]
    },
    "unconnected_nets": {
        "enabled": True,
        "severity": SEVERITY["WARNING"]
    }
}


# --------------------------------------------------
# RULE MANAGER CLASS
# --------------------------------------------------
class RuleEngine:

    def __init__(self, custom_rules: Dict[str, Any] = None):
        self.rules = DEFAULT_RULES.copy()

        if custom_rules:
            self.rules.update(custom_rules)

        logger.info("DRC Rule Engine initialized")

    # --------------------------------------------------
    # GET RULE VALUE
    # --------------------------------------------------
    def get(self, rule_name: str, default=None):
        return self.rules.get(rule_name, default)

    # --------------------------------------------------
    # CHECK IF RULE ENABLED
    # --------------------------------------------------
    def is_enabled(self, rule_name: str) -> bool:
        rule = self.rules.get(rule_name, {})
        return rule.get("enabled", True)

    # --------------------------------------------------
    # GET RULE VALUE (NUMERIC)
    # --------------------------------------------------
    def get_value(self, rule_name: str):
        rule = self.rules.get(rule_name, {})
        return rule.get("value")

    # --------------------------------------------------
    # GET SEVERITY
    # --------------------------------------------------
    def get_severity(self, rule_name: str):
        rule = self.rules.get(rule_name, {})
        return rule.get("severity", SEVERITY["ERROR"])

    # --------------------------------------------------
    # ADD OR UPDATE RULE
    # --------------------------------------------------
    def update_rule(self, rule_name: str, config: Dict[str, Any]):
        self.rules[rule_name] = config
        logger.debug(f"Rule updated: {rule_name}")

    # --------------------------------------------------
    # VALIDATE RULE SET
    # --------------------------------------------------
    def validate_rules(self):
        for name, rule in self.rules.items():
            if not isinstance(rule, dict):
                raise ValueError(f"Invalid rule format: {name}")

        logger.info("All rules validated successfully")

    # --------------------------------------------------
    # EXPORT RULES
    # --------------------------------------------------
    def export(self) -> Dict[str, Any]:
        return self.rules


# --------------------------------------------------
# RULE-BASED ERROR FORMATTER
# --------------------------------------------------
def format_error(rule_engine: RuleEngine, rule_name: str, message: str, extra: Dict = None):
    return {
        "type": rule_name,
        "message": message,
        "severity": rule_engine.get_severity(rule_name),
        "details": extra or {}
    }


# --------------------------------------------------
# APPLY RULES TO ERRORS
# --------------------------------------------------
def apply_rule_metadata(rule_engine: RuleEngine, errors: List[Dict]) -> List[Dict]:
    """
    Attach severity + metadata to errors
    """

    enriched = []

    for err in errors:
        rule_name = err.get("type", "UNKNOWN")

        enriched.append({
            **err,
            "severity": rule_engine.get_severity(rule_name)
        })

    return enriched


# --------------------------------------------------
# FILTER ERRORS BY SEVERITY
# --------------------------------------------------
def filter_errors(errors: List[Dict], level: str = "ERROR") -> List[Dict]:
    """
    Filter errors by severity level
    """
    return [e for e in errors if e.get("severity") == level]


# --------------------------------------------------
# SUMMARY
# --------------------------------------------------
def summarize_errors(errors: List[Dict]) -> Dict[str, int]:
    summary = {
        "ERROR": 0,
        "WARNING": 0,
        "INFO": 0
    }

    for err in errors:
        sev = err.get("severity", "ERROR")
        summary[sev] = summary.get(sev, 0) + 1

    return summary


# --------------------------------------------------
# DEBUG TEST
# --------------------------------------------------
if __name__ == "__main__":
    engine = RuleEngine()

    sample_errors = [
        {"type": "min_trace_width", "message": "Too thin"},
        {"type": "unconnected_nets", "message": "Missing connection"},
    ]

    enriched = apply_rule_metadata(engine, sample_errors)

    print("Enriched:", enriched)
    print("Summary:", summarize_errors(enriched))
  
