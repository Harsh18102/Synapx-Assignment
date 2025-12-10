def route_claim(fields, missing_fields, flags):
    # 1. Investigation: fraud indicator
    for f in flags:
        if f.startswith("possible_fraud"):
            return "Investigation", "Fraud indicator in description"

    # 2. Mandatory-field check
    if missing_fields:
        return "Manual Review", "Missing mandatory fields: " + ", ".join(missing_fields)

    # 3. Specialist queue for injury
    if fields.get("claimType") == "injury":
        return "Specialist Queue", "Injury claim detected; specialist required"

    # 4. Fast-track
    est = fields.get("estimatedDamage")
    try:
        est_val = float(est) if est is not None else None
    except Exception:
        est_val = None

    if est_val is not None and est_val < 25000:
        return "Fast-track", "Estimate below threshold and all mandatory fields present"

    # 5. Default
    return "Manual Review", "Does not meet fast-track rules; requires human review"
