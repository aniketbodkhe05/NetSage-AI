
import pandas as pd
from pathlib import Path


# ============================================================
# NetSage AI - Human Review System
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RESULT_FILE = PROJECT_ROOT / "data" / "ai_results.csv"


# ============================================================
# 1. Check result file
# ============================================================

if not RESULT_FILE.exists():
    print("ERROR: ai_results.csv was not found.")
    print(f"Expected location: {RESULT_FILE}")
    raise SystemExit(1)


# ============================================================
# 2. Load AI results safely
# ============================================================

try:
    # IMPORTANT:
    # Load every column as string so review updates
    # do not cause pandas dtype errors.
    df = pd.read_csv(
        RESULT_FILE,
        dtype=str,
        keep_default_na=False
    )

except Exception as error:
    print("ERROR: Could not read ai_results.csv")
    print(error)
    raise SystemExit(1)


# ============================================================
# 3. Check if dataset is empty
# ============================================================

if df.empty:
    print("ERROR: ai_results.csv is empty.")
    print("Run the AI diagnosis engine first.")
    raise SystemExit(1)


# ============================================================
# 4. Ensure required review columns exist
# ============================================================

review_columns = [
    "human_review_required",
    "review_status",
    "reviewer_decision",
    "reviewer_notes"
]

for column in review_columns:

    if column not in df.columns:
        df[column] = ""

    # Force the column to text
    df[column] = df[column].fillna("").astype(str)


# ============================================================
# 5. Check important diagnosis columns
# ============================================================

required_columns = [
    "case_id",
    "issue_type",
    "agreement",
    "ai_root_cause",
    "confidence",
    "osi_layer",
    "concept",
    "severity",
    "evidence",
    "next_command",
    "fix_steps",
    "expected_fault",
    "expected_next_command",
    "expected_fix"
]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:

    print("\nERROR: Required columns are missing:")

    for column in missing_columns:
        print(f" - {column}")

    raise SystemExit(1)


# ============================================================
# 6. Display available cases
# ============================================================

print("=" * 60)
print("             NETSAGE AI - HUMAN REVIEW")
print("=" * 60)

print("\nAvailable AI diagnoses:\n")

for index, row in df.iterrows():

    print(
        f"{index + 1}. "
        f"{row['case_id']} | "
        f"{row['issue_type']} | "
        f"{row['agreement']}"
    )


# ============================================================
# 7. Select case
# ============================================================

case_id = input(
    "\nEnter case ID to review (example: C016): "
).strip().upper()


matches = df[
    df["case_id"]
    .astype(str)
    .str.upper()
    == case_id
]


if matches.empty:

    print(f"\nERROR: Case {case_id} was not found.")

    print("\nAvailable case IDs:")

    print(
        ", ".join(
            df["case_id"].astype(str).tolist()
        )
    )

    raise SystemExit(1)


index = matches.index[0]

case = df.loc[index]


# ============================================================
# 8. Display AI diagnosis
# ============================================================

print("\n" + "=" * 60)
print("AI DIAGNOSIS")
print("=" * 60)

print(f"\nCase ID       : {case['case_id']}")
print(f"Issue Type    : {case['issue_type']}")
print(f"Root Cause    : {case['ai_root_cause']}")
print(f"Confidence    : {case['confidence']}")
print(f"OSI Layer     : {case['osi_layer']}")
print(f"Concept       : {case['concept']}")
print(f"Severity      : {case['severity']}")


print("\nEvidence:")
print(case["evidence"])


print("\nNext Command:")
print(case["next_command"])


print("\nFix Steps:")
print(case["fix_steps"])


# ============================================================
# 9. Show reference answer
# ============================================================

print("\n" + "=" * 60)
print("REFERENCE ANSWER")
print("=" * 60)

print("\nExpected Fault:")
print(case["expected_fault"])

print("\nExpected Next Command:")
print(case["expected_next_command"])

print("\nExpected Fix:")
print(case["expected_fix"])


# ============================================================
# 10. Human review decision
# ============================================================

print("\n" + "=" * 60)
print("HUMAN REVIEW DECISION")
print("=" * 60)

print("\n1. Accepted")
print("2. Edited")
print("3. Rejected")


choice = input(
    "\nEnter your decision (1/2/3): "
).strip()


decision_map = {
    "1": "Accepted",
    "2": "Edited",
    "3": "Rejected"
}


if choice not in decision_map:

    print("\nERROR: Invalid decision.")

    print("Please run the program again and select 1, 2, or 3.")

    raise SystemExit(1)


decision = decision_map[choice]


# ============================================================
# 11. Reviewer notes
# ============================================================

notes = input(
    "\nEnter reviewer notes: "
).strip()


# ============================================================
# 12. Save human review
# ============================================================

# Everything is stored as STRING intentionally.
df.loc[index, "human_review_required"] = "True"

df.loc[index, "review_status"] = "Completed"

df.loc[index, "reviewer_decision"] = decision

df.loc[index, "reviewer_notes"] = notes


# ============================================================
# 13. Save CSV
# ============================================================

try:

    df.to_csv(
        RESULT_FILE,
        index=False
    )

except Exception as error:

    print("\nERROR: Could not save human review.")
    print(error)

    raise SystemExit(1)


# ============================================================
# 14. Verify saved data
# ============================================================

try:

    verification_df = pd.read_csv(
        RESULT_FILE,
        dtype=str,
        keep_default_na=False
    )

    saved_row = verification_df[
        verification_df["case_id"].astype(str).str.upper()
        == case_id
    ]

    if saved_row.empty:

        print("\nWARNING: Review was saved but verification failed.")

    else:

        saved = saved_row.iloc[0]

        print("\n" + "=" * 60)
        print("HUMAN REVIEW SAVED")
        print("=" * 60)

        print(f"\nCase       : {case_id}")
        print(f"Decision   : {saved['reviewer_decision']}")
        print(f"Status     : {saved['review_status']}")
        print(f"Notes      : {saved['reviewer_notes']}")

        print(
            "\nHuman review requirement: SATISFIED"
        )

        print("\nSaved to:")
        print(RESULT_FILE)

        print("=" * 60)

except Exception as error:

    print("\nWARNING: Review was saved, but verification failed.")
    print(error)

