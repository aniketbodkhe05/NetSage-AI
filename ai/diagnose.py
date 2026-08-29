import os
import json
import pandas as pd

from pathlib import Path
from dotenv import load_dotenv
from google import genai


# ============================================================
# NetSage AI - Gemini AI Diagnosis Engine
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_FILE = PROJECT_ROOT / "data" / "cases.csv"
PROMPT_FILE = PROJECT_ROOT / "prompts" / "diagnose_prompt.md"
RESULT_FILE = PROJECT_ROOT / "data" / "ai_results.csv"


# ============================================================
# 1. Load environment variables
# ============================================================

load_dotenv(PROJECT_ROOT / ".env")

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("ERROR: GEMINI_API_KEY was not found.")
    print("Please check your .env file.")
    raise SystemExit(1)

client = genai.Client(api_key=API_KEY)


# ============================================================
# 2. Check required files
# ============================================================

if not DATA_FILE.exists():
    print(f"ERROR: Dataset not found: {DATA_FILE}")
    raise SystemExit(1)

if not PROMPT_FILE.exists():
    print(f"ERROR: Prompt file not found: {PROMPT_FILE}")
    raise SystemExit(1)


# ============================================================
# 3. Load dataset and prompt
# ============================================================

try:
    df = pd.read_csv(DATA_FILE)
except Exception as error:
    print("ERROR: Could not read cases.csv")
    print(error)
    raise SystemExit(1)

prompt_template = PROMPT_FILE.read_text(encoding="utf-8")


# ============================================================
# 4. Check required dataset columns
# ============================================================

required_columns = [
    "case_id",
    "issue_type",
    "symptom",
    "topology_note",
    "show_output",
    "expected_fault",
    "expected_next_command",
    "expected_fix",
]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:
    print("ERROR: Missing columns:")

    for column in missing_columns:
        print(f" - {column}")

    raise SystemExit(1)


# ============================================================
# 5. Ask user for case ID
# ============================================================

case_id = input(
    "\nEnter case ID (example: C016): "
).strip().upper()


case_rows = df[
    df["case_id"]
    .astype(str)
    .str.upper()
    == case_id
]


if case_rows.empty:

    print(f"\nERROR: Case {case_id} was not found.")

    print("\nAvailable cases:")

    print(
        ", ".join(
            df["case_id"]
            .astype(str)
            .tolist()
        )
    )

    raise SystemExit(1)


case = case_rows.iloc[0]


# ============================================================
# 6. Build diagnostic input
#
# IMPORTANT:
# Expected answer is NOT sent to Gemini.
# This prevents the AI from simply copying the answer.
# ============================================================

case_prompt = f"""
CASE ID:
{case["case_id"]}

ISSUE TYPE:
{case["issue_type"]}

SYMPTOM:
{case["symptom"]}

TOPOLOGY NOTE:
{case["topology_note"]}

SHOW COMMAND OUTPUT:
{case["show_output"]}

Analyze this Cisco-style networking troubleshooting case.

Use ONLY the symptom, topology information, and
show-command evidence provided above.

Do not assume that the expected answer is known.

Identify the most likely root cause.

Explain which evidence supports your diagnosis.

Recommend the next command that should be run.

Provide safe fix steps.

Return ONLY valid JSON.

The JSON must contain a "diagnosis" object with these fields:

root_cause
confidence
osi_layer
concept
severity
evidence
next_command
fix_steps
alternative_causes
"""


# ============================================================
# 7. Display case information
# ============================================================

print("\n" + "=" * 60)
print("              NETSAGE AI")
print("=" * 60)

print("\nCase:", case_id)
print("Issue:", case["issue_type"])

print("\nSending evidence to Gemini AI...")
print("Please wait...\n")


# ============================================================
# 8. Send case to Gemini
# ============================================================

try:

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt_template + "\n\n" + case_prompt,
        config={
            "response_mime_type": "application/json"
        }
    )

    raw_output = response.text.strip()

except Exception as error:

    print("\nERROR while calling Gemini API:")
    print(error)

    raise SystemExit(1)


# ============================================================
# 9. Display AI response
# ============================================================

print("=" * 60)
print("AI RESPONSE")
print("=" * 60)

print(raw_output)


# ============================================================
# 10. Parse JSON
# ============================================================

try:

    diagnosis = json.loads(raw_output)

except json.JSONDecodeError:

    print("\nERROR: Gemini response was not valid JSON.")

    print("\nRaw response:")
    print(raw_output)

    raise SystemExit(1)


# ============================================================
# 11. Validate AI response
# ============================================================

if "diagnosis" not in diagnosis:

    print(
        "\nERROR: AI response does not contain "
        "'diagnosis'."
    )

    raise SystemExit(1)


diagnosis_data = diagnosis["diagnosis"]


required_ai_fields = [
    "root_cause",
    "confidence",
    "osi_layer",
    "concept",
    "severity",
    "evidence",
    "next_command",
    "fix_steps",
    "alternative_causes",
]


missing_ai_fields = [
    field
    for field in required_ai_fields
    if field not in diagnosis_data
]


if missing_ai_fields:

    print("\nERROR: Missing AI fields:")

    for field in missing_ai_fields:
        print(f" - {field}")

    raise SystemExit(1)


# ============================================================
# 12. Force human review
# ============================================================

diagnosis["human_review"] = {
    "required": True,
    "status": "Pending",
    "reviewer_decision": "Pending",
    "reviewer_notes": ""
}


# ============================================================
# 13. Display structured diagnosis
# ============================================================

print("\n" + "=" * 60)
print("STRUCTURED DIAGNOSIS")
print("=" * 60)

print(
    json.dumps(
        diagnosis,
        indent=2,
        ensure_ascii=False
    )
)


# ============================================================
# 14. Compare AI diagnosis with expected answer
# ============================================================

expected_fault = str(
    case["expected_fault"]
).strip().lower()

ai_root_cause = str(
    diagnosis_data["root_cause"]
).strip().lower()


if (
    expected_fault in ai_root_cause
    or ai_root_cause in expected_fault
):

    agreement = "Likely Match"

else:

    agreement = "Needs Human Review"


# ============================================================
# 15. Convert evidence to text
# ============================================================

evidence = diagnosis_data["evidence"]

if isinstance(evidence, list):

    evidence_text = " | ".join(
        str(item)
        for item in evidence
    )

else:

    evidence_text = str(evidence)


# ============================================================
# 16. Convert fix steps to text
# ============================================================

fix_steps = diagnosis_data["fix_steps"]

if isinstance(fix_steps, list):

    fix_text = " | ".join(
        str(item)
        for item in fix_steps
    )

else:

    fix_text = str(fix_steps)


# ============================================================
# 17. Convert alternative causes to text
# ============================================================

alternative_causes = diagnosis_data["alternative_causes"]

if isinstance(alternative_causes, list):

    alternative_text = " | ".join(
        str(item)
        for item in alternative_causes
    )

else:

    alternative_text = str(alternative_causes)


# ============================================================
# 18. Prepare result
# ============================================================

result = {

    "case_id":
        case["case_id"],

    "issue_type":
        case["issue_type"],

    "ai_root_cause":
        diagnosis_data["root_cause"],

    "confidence":
        diagnosis_data["confidence"],

    "osi_layer":
        diagnosis_data["osi_layer"],

    "concept":
        diagnosis_data["concept"],

    "severity":
        diagnosis_data["severity"],

    "evidence":
        evidence_text,

    "next_command":
        diagnosis_data["next_command"],

    "fix_steps":
        fix_text,

    "alternative_causes":
        alternative_text,

    "expected_fault":
        case["expected_fault"],

    "expected_next_command":
        case["expected_next_command"],

    "expected_fix":
        case["expected_fix"],

    "agreement":
        agreement,

    "human_review_required":
        True,

    "review_status":
        "Pending",

    "reviewer_decision":
        "Pending",

    "reviewer_notes":
        ""
}


# ============================================================
# 19. Save AI result
# ============================================================

result_df = pd.DataFrame([result])


if RESULT_FILE.exists():

    existing_df = pd.read_csv(
        RESULT_FILE
    )

    # Remove previous result for this case
    existing_df = existing_df[
        existing_df["case_id"].astype(str)
        != str(case["case_id"])
    ]

    final_df = pd.concat(
        [existing_df, result_df],
        ignore_index=True
    )

else:

    final_df = result_df


final_df.to_csv(
    RESULT_FILE,
    index=False
)


# ============================================================
# 20. Final message
# ============================================================

print("\n" + "=" * 60)

print("AI diagnosis saved successfully.")

print(
    f"\nResult file:\n{RESULT_FILE}"
)

print(
    "\nAgreement check:",
    agreement
)

print(
    "\nHuman review:",
    "REQUIRED"
)

print(
    "\nStatus:",
    "PENDING"
)

print("=" * 60)
