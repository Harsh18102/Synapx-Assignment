import re
from dateutil import parser as dateparser

FRAUD_KEYWORDS = ["fraud", "staged", "inconsistent", "multiple claims", "fake", "fabricated"]

def is_date_parseable(s):
    if not s:
        return False
    try:
        dateparser.parse(s, fuzzy=True)
        return True
    except Exception:
        return False

def validate_fields(fields):
    """
    Return (missing_fields_list, flags_list)
    missing_fields: list of string keys
    flags: list of strings (e.g., 'possible_fraud', 'incidentDate_format_invalid')
    """
    missing = []
    flags = []

    # Required checks
    if not fields.get("policyNumber"):
        missing.append("policyNumber")
    if not fields.get("policyholderName"):
        missing.append("policyholderName")
    if not fields.get("incidentDate"):
        missing.append("incidentDate")
    else:
        # check parseability
        if not is_date_parseable(fields.get("incidentDate")):
            flags.append("incidentDate_format_invalid")

    # For motor claims, require vin or plate
    if fields.get("claimType") == "motor":
        asset = fields.get("asset", {})
        if not asset.get("vin") and not asset.get("plateNumber"):
            missing.append("asset.vin_or_plate")

    # estimatedDamage numeric check
    est = fields.get("estimatedDamage")
    if est is None:
        missing.append("estimatedDamage")
    else:
        try:
            float(est)
        except Exception:
            flags.append("estimatedDamage_not_numeric")

    # Fraud keyword scan in description
    desc = (fields.get("description") or "").lower()
    for kw in FRAUD_KEYWORDS:
        if kw in desc:
            flags.append("possible_fraud:" + kw)
            break

    # Simple attachments check: optional but helpful
    if fields.get("attachments") is None:
        # not critical, but note
        flags.append("attachments_missing_flag")

    return missing, flags
