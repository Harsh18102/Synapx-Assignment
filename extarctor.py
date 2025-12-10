import re
from dateutil import parser as dateparser
import pdfplumber
from utils import first_nonempty, find_all_lines_with_keywords


def extract_text_from_pdf(path):
    """Extract text from PDF using pdfplumber."""
    text_parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts)


# helper regex patterns
_POLICY_RE = re.compile(r"(Policy\s*Number|Policy #|Policy No\.?|Policy):\s*([A-Z0-9\-\/]+)", re.I)
_NAME_RE = re.compile(r"(Name of Insured|Insured|Policyholder|Name):\s*(.+)", re.I)
_DATE_RE = re.compile(r"(Date of Loss|Date of Accident|Date\s*of\s*Loss):\s*([A-Za-z0-9,\-\/ ]+)", re.I)
_TIME_RE = re.compile(r"(Time of Loss|Time):\s*([0-9]{1,2}:[0-9]{2}\s*(AM|PM|am|pm)?)", re.I)
_LOCATION_RE = re.compile(r"(Location of Loss|Address|Location):\s*(.+)", re.I)
_VIN_RE = re.compile(r"(VIN|Vehicle Identification Number):\s*([A-Z0-9\-]+)", re.I)
_PLATE_RE = re.compile(r"(Plate Number|License Plate|Plate #):\s*([A-Z0-9\-]+)", re.I)
_ESTIMATE_RE = re.compile(r"(Estimate Amount|Estimated Damage|Amount):\s*₹?\s*([0-9,]+(?:\.[0-9]{1,2})?)", re.I)
_PHONE_RE = re.compile(r"(\+?\d{1,3}[-\s]?\d{6,12})")
_EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")


def try_parse_date(s):
    try:
        dt = dateparser.parse(s, fuzzy=True)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return None


def parse_text_to_fields(text):
    if not text:
        text = ""

    lines = [l.strip() for l in text.splitlines() if l.strip()]
    full = "\n".join(lines)

    # Policy number
    m = _POLICY_RE.search(full)
    policy_number = m.group(2).strip() if m else first_nonempty(find_all_lines_with_keywords(lines, ["policy", "policy number", "policy #", "policy no"]), default=None)

    # Policyholder / insured name
    m = _NAME_RE.search(full)
    policyholder = m.group(2).strip() if m else first_nonempty(find_all_lines_with_keywords(lines, ["insured", "name of insured", "policyholder", "name:"]), default=None)

    # Date and Time
    m = _DATE_RE.search(full)
    incident_date = try_parse_date(m.group(2).strip()) if m else None

    m = _TIME_RE.search(full)
    incident_time = m.group(2).strip() if m else None

    # Location
    m = _LOCATION_RE.search(full)
    location = m.group(2).strip() if m else first_nonempty(find_all_lines_with_keywords(lines, ["location", "address", "location of loss"]), default=None)

    # Description: try find lines after "Description" or "Narrative" or "Remarks"
    desc = None
    for keyword in ("Description of Accident", "Description", "Narrative", "Remarks"):
        for i, line in enumerate(lines):
            if keyword.lower() in line.lower():
                # take this line and up to next 3 lines as description if short
                desc_lines = [line.split(":", 1)[-1].strip()] + lines[i + 1:i + 4]
                desc = " ".join([d for d in desc_lines if d])
                break
        if desc:
            break
    if not desc:
        # fallback: find a long line
        long_lines = [l for l in lines if len(l) > 60]
        desc = long_lines[0] if long_lines else ""

    # VIN / Plate / Make-Model
    m = _VIN_RE.search(full)
    vin = m.group(2).strip() if m else None

    m = _PLATE_RE.search(full)
    plate = m.group(2).strip() if m else None

    # Make/Model heuristics
    make, model, year = None, None, None
    mm_line = first_nonempty(find_all_lines_with_keywords(lines, ["make", "model", "year", "vehicle"]), default=None)
    if mm_line:
        # naive split
        parts = mm_line.split()
        if parts:
            make = parts[0]
            if len(parts) > 1:
                model = " ".join(parts[1:])

    # Estimate amount
    m = _ESTIMATE_RE.search(full)
    estimate = None
    if m:
        estimate = float(m.group(2).replace(",", ""))
    else:
        # fallback look for "Estimate" or "Amount" lines
        amt_line = first_nonempty(find_all_lines_with_keywords(lines, ["estimate", "amount", "estimate amount", "estimated damage"]), default=None)
        if amt_line:
            nums = re.findall(r"[0-9,]+(?:\.[0-9]{1,2})?", amt_line)
            if nums:
                estimate = float(nums[0].replace(",", ""))

    claimant = None
    claimant_phone = None
    claimant_email = None
    for kw in ["reported by", "claimant", "reporting party", "name:"]:
        for i, line in enumerate(lines):
            if kw in line.lower():
                # get that line's content
                claimant = line.split(":", 1)[-1].strip() if ":" in line else line
                # look nearby for phone / email
                window = " ".join(lines[max(0, i - 2): i + 3])
                phones = _PHONE_RE.findall(window)
                claimant_phone = phones[0] if phones else None
                emails = _EMAIL_RE.findall(window)
                claimant_email = emails[0] if emails else None
                break
        if claimant:
            break

    third_parties = []
    tp_lines = find_all_lines_with_keywords(lines, ["other party", "other vehicle", "other driver", "witness"])
    for l in tp_lines[:3]:
        ph = _PHONE_RE.search(l)
        em = _EMAIL_RE.search(l)
        third_parties.append({"raw": l, "phone": ph.group(1) if ph else None, "email": em.group(0) if em else None})

    attachments = []
    for l in lines:
        if any(ext in l.lower() for ext in [".jpg", ".png", ".pdf", "photo", "police report"]):
            attachments.append(l)

    fields = {
        "policyNumber": policy_number,
        "policyholderName": policyholder,
        "policyEffectiveFrom": None,
        "policyEffectiveTo": None,
        "incidentDate": incident_date,
        "incidentTime": incident_time,
        "location": {"raw": location} if location else {},
        "description": desc,
        "claimant": {"name": claimant, "phone": claimant_phone, "email": claimant_email},
        "thirdParties": third_parties,
        "asset": {
            "assetType": "Automobile",
            "vin": vin,
            "plateNumber": plate,
            "make": make,
            "model": model,
            "year": year,
        },
        "estimatedDamage": estimate,
        "attachments": attachments,
    }

    return fields
