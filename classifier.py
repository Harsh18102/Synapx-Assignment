import re
def classify_claim_type(fields):
    """
    Determine claimType using description and asset info.
    Returns one of: "motor", "property", "injury", "other"
    """
    desc = ""
    if fields.get("description"):
        desc = fields["description"].lower()
    # Keywords for injury
    injury_kw = ["injury", "hospital", "fracture", "medical", "bodily", "leg", "hospitalized"]
    motor_kw = ["vehicle", "automobile", "car", "truck", "accident", "collision", "vin", "plate"]
    property_kw = ["fire", "theft", "burglary", "flood", "property", "building", "house", "damage to property"]

    for kw in injury_kw:
        if kw in desc:
            return "injury"
    for kw in motor_kw:
        if kw in desc:
            return "motor"
    for kw in property_kw:
        if kw in desc:
            return "property"

    # fallback: if asset.vin or plate present -> motor
    asset = fields.get("asset", {})
    if asset.get("vin") or asset.get("plateNumber"):
        return "motor"

    return "other"
