import argparse
import json
import sys

from extractor import extract_text_from_pdf, parse_text_to_fields
from classifier import classify_claim_type
from validator import validate_fields
from router import route_claim

OUTPUT_FILE = "sample_output.json"


def run_from_text(text):
    fields = parse_text_to_fields(text)
    fields["claimType"] = classify_claim_type(fields)
    missing_fields, flags = validate_fields(fields)
    recommended_route, reasoning = route_claim(fields, missing_fields, flags)
    out = {
        "extractedFields": fields,
        "missingFields": missing_fields,
        "flags": flags,
        "recommendedRoute": recommended_route,
        "reasoning": reasoning,
    }
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", help="Path to FNOL PDF")
    parser.add_argument("--text", help="Path to plain text FNOL")
    parser.add_argument("--out", help="Output JSON path", default=OUTPUT_FILE)
    args = parser.parse_args()

    if args.pdf:
        try:
            text = extract_text_from_pdf(args.pdf)
        except Exception as e:
            print("Error extracting PDF:", e)
            sys.exit(1)
    elif args.text:
        with open(args.text, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        with open("sample_input.txt", "r", encoding="utf-8") as f:
            text = f.read()

    result = run_from_text(text)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print("Output written to", args.out)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
