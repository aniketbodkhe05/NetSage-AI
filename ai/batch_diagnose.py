import os
import json
import time
import pandas as pd

from pathlib import Path
from dotenv import load_dotenv
from google import genai


# ============================================================
# NetSage AI - Batch AI Diagnosis Engine
# Processes all cases in cases.csv
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_FILE = PROJECT_ROOT / "data" / "cases.csv"
PROMPT_FILE = PROJECT_ROOT / "prompts" / "diagnose_prompt.md"
RESULT_FILE = PROJECT_ROOT / "data" / "ai_results.csv"


# ============================================================
# 1. Load Gemini API key
# ============================================================

load_dotenv(PROJECT_ROOT / ".env")

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("ERROR: GEMINI_API_KEY was not found.")
    print("Check your .env file.")
    raise SystemExit(1)


# ============================================================
# Create Gemini client
# ============================================================

client = genai.Client(
    api_key=API_KEY,
   http_options={
    "timeout": 120000
}
)


# ============================================================
# 2. Check files
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


prompt_template = PROMPT_FILE.read_text(
    encoding="utf-8"
)


# ============================================================
# 4. Required columns
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
# 5. Load previous results if available
# ============================================================

if RESULT_FILE.exists() and RESULT_FILE.stat().st_size > 0:

    try:

        results_df = pd.read_csv(
            RESULT_FILE,
            dtype=str
        ).fillna("")

    except Exception as error:

        print("WARNING: Could not read existing ai_results.csv")
        print(error)

        results_df = pd.DataFrame()

else:

    results_df = pd.DataFrame()


# ============================================================
# 6. Process every case
# ============================================================

total_cases = len(df)

print("\n" + "=" * 65)
print("              NETSAGE AI - BATCH DIAGNOSIS")
print("=" * 65)

print(f"\nTotal cases: {total_cases}")
print("Starting AI diagnosis...\n")


for index, case in df.iterrows():

    case_id = str(case["case_id"]).strip()

    print("-" * 65)

    print(
        f"Processing case {index + 1}/{total_cases}: {case_id}"
    )

    print(
        f"Issue type: {case['issue_type']}"
    )


    # --------------------------------------------------------
    # Skip already processed cases
    # --------------------------------------------------------

    if not results_df.empty and "case_id" in results_df.columns:

        existing = results_df[
            results_df["case_id"].astype(str).str.strip() == case_id
        ]

        if not existing.empty:

            print("Already processed - SKIPPING")
            continue


    # --------------------------------------------------------
    # Build evidence-only prompt
    # --------------------------------------------------------

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

Do NOT use or assume the expected answer.

Identify the most likely root cause.

Explain which evidence supports the diagnosis.

Recommend the next command that should be run.

Provide safe fix steps.

Return ONLY valid JSON using this structure:

{{
  "case_id": "string",
  "diagnosis": {{
    "root_cause": "string",
    "confidence": "High/Medium/Low",
    "osi_layer": "string",
    "concept": "string",
    "severity": "High/Medium/Low",
    "evidence": ["string"],
    "next_command": "string",
    "fix_steps": ["string"],
    "alternative_causes": ["string"]
  }}
}}
"""


    # --------------------------------------------------------
    # Call Gemini with retry protection
    # --------------------------------------------------------

    raw_output = None

    MAX_RETRIES = 2
    for attempt in range(1, MAX_RETRIES + 1):

        try:

            print(
                f"Calling Gemini for {case_id} "
                f"(attempt {attempt}/{MAX_RETRIES})..."
            )

            response = client.interactions.create(
                model="gemini-3.6-flash",
                input=(
                    prompt_template
                    + "\n\n"
                    + case_prompt
                )
            )

            raw_output = response.output_text.strip()

            print(
                f"Gemini response received for {case_id}"
            )

            break


        except KeyboardInterrupt:

            print("\nProcess interrupted by user.")
            print(
                "Previously saved results are safe."
            )

            raise


        except Exception as error:

            print(
                f"Gemini error for {case_id}:"
            )

            print(error)

            if attempt < MAX_RETRIES:

                wait_time = attempt * 3

                print(
                    f"Retrying in {wait_time} seconds..."
                )

                time.sleep(wait_time)

            else:

                print(
                    f"Failed to process {case_id} "
                    f"after {MAX_RETRIES} attempts."
                )

                print(
                    "Skipping this case and continuing..."
                )


    # If all attempts failed
    if raw_output is None:
        continue


    # --------------------------------------------------------
    # Parse JSON
    # --------------------------------------------------------

    try:

        diagnosis = json.loads(raw_output)

    except json.JSONDecodeError:

        print(
            f"ERROR: Gemini returned invalid JSON for {case_id}."
        )

        print("Skipping this case...")
        continue


    # --------------------------------------------------------
    # Validate diagnosis structure
    # --------------------------------------------------------

    if "diagnosis" not in diagnosis:

        print(
            f"ERROR: Missing diagnosis object for {case_id}."
        )

        print("Skipping this case...")
        continue


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


    missing_fields = [
        field
        for field in required_ai_fields
        if field not in diagnosis_data
    ]


    if missing_fields:

        print("ERROR: Missing AI fields:")

        for field in missing_fields:
            print(f" - {field}")

        print("Skipping this case...")
        continue


    # --------------------------------------------------------
    # Human review requirement
    # --------------------------------------------------------

    human_review_required = True
    review_status = "Pending"
    reviewer_decision = "Pending"
    reviewer_notes = ""


    # --------------------------------------------------------
    # Evidence formatting
    # --------------------------------------------------------

    evidence = diagnosis_data["evidence"]

    if isinstance(evidence, list):

        evidence_text = " | ".join(
            str(item)
            for item in evidence
        )

    else:

        evidence_text = str(evidence)


    # --------------------------------------------------------
    # Fix formatting
    # --------------------------------------------------------

    fix_steps = diagnosis_data["fix_steps"]

    if isinstance(fix_steps, list):

        fix_text = " | ".join(
            str(item)
            for item in fix_steps
        )

    else:

        fix_text = str(fix_steps)


    # --------------------------------------------------------
    # Alternative causes
    # --------------------------------------------------------

    alternatives = diagnosis_data["alternative_causes"]

    if isinstance(alternatives, list):

        alternative_text = " | ".join(
            str(item)
            for item in alternatives
        )

    else:

        alternative_text = str(alternatives)


    # --------------------------------------------------------
    # Compare AI diagnosis with expected answer
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # Prepare result
    # --------------------------------------------------------

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
            human_review_required,

        "review_status":
            review_status,

        "reviewer_decision":
            reviewer_decision,

        "reviewer_notes":
            reviewer_notes

    }


    # --------------------------------------------------------
    # Add result to dataframe
    # --------------------------------------------------------

    new_result_df = pd.DataFrame(
        [result]
    )


    if results_df.empty:

        results_df = new_result_df

    else:

        results_df = pd.concat(
            [
                results_df,
                new_result_df
            ],
            ignore_index=True
        )


    # --------------------------------------------------------
    # Save after EVERY case
    # --------------------------------------------------------

    results_df.to_csv(
        RESULT_FILE,
        index=False
    )


    print(
        f"AI diagnosis completed: {agreement}"
    )

    print(
        f"Saved progress: "
        f"{len(results_df)}/{total_cases}"
    )


    # Small delay to avoid API limits
    time.sleep(3)


# ============================================================
# 7. Final summary
# ============================================================

print("\n" + "=" * 65)
print("              BATCH DIAGNOSIS COMPLETE")
print("=" * 65)

print("\nResults saved to:")
print(RESULT_FILE)


if not results_df.empty:

    print(
        f"\nCases successfully processed: "
        f"{len(results_df)}/{total_cases}"
    )

    if "agreement" in results_df.columns:

        print("\nAgreement summary:")

        print(
            results_df["agreement"]
            .value_counts()
            .to_string()
        )


print("\nHuman review is REQUIRED for all cases.")

print("=" * 65)
