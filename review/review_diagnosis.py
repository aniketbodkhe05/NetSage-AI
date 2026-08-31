import pandas as pd
from pathlib import Path


# ============================================================
# NetSage AI - Human Review System
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

AI_RESULT_FILE = PROJECT_ROOT / "data" / "ai_results.csv"
HUMAN_REVIEW_FILE = PROJECT_ROOT / "data" / "human_review.csv"


# ============================================================
# 1. Check AI results
# ============================================================

if not AI_RESULT_FILE.exists():
    print("ERROR: ai_results.csv was not found.")
    print(f"Expected location: {AI_RESULT_FILE}")
    raise SystemExit(1)


# ============================================================
# 2. Load original AI results
# ============================================================

try:
    df = pd.read_csv(
        AI_RESULT_FILE,
        dtype=str,
        keep_default_na=False
    )

except Exception as error:
    print("ERROR: Could not read ai_results.csv")
    print(error)
    raise SystemExit(1)


if df.empty:
    print("ERROR: ai_results.csv is empty.")
    raise SystemExit(1)


# ============================================================
# 3. Required AI columns
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
    column for column in required_columns
    if column not in df.columns
]

if missing_columns:
    print("\nERROR: Required columns are missing:")

    for column in missing_columns:
        print(f" - {column}")

    raise SystemExit(1)


# ============================================================
# 4. Load existing human review log
# ============================================================

review_columns = [
    "case_id",
    "human_review_required",
    "review_status",
    "reviewer_decision",
    "reviewer_notes"
]


if HUMAN_REVIEW_FILE.exists():

    review_df = pd.read_csv(
        HUMAN_REVIEW_FILE,
        dtype=str,
        keep_default_na=False
    )

else:

    review_df = pd.DataFrame(
        columns=review_columns
    )


# Ensure required review columns exist

for column in review_columns:

    if column not in review_df.columns:
        review_df[column] = ""

    review_df[column] = (
        review_df[column]
        .fillna("")
        .astype(str)
    )


# ============================================================
# 5. Display available cases
# ============================================================

print("=" * 60)
print("             NETSAGE AI - HUMAN REVIEW")
print("=" * 60)

print("\nAvailable AI diagnoses:\n")

for index, row in df.iterrows():

    existing_review = review_df[
        review_df["case_id"].astype(str).str.upper()
        == str(row["case_id"]).upper()
    ]

    if existing_review.empty:
        status = "Pending"
    else:
        status = existing_review.iloc[0]["reviewer_decision"]

        if status == "":
            status = "Pending"

    print(
        f"{index + 1}. "
        f"{row['case_id']} | "
        f"{row['issue_type']} | "
        f"AI Agreement: {row['agreement']} | "
        f"Review: {status}"
    )


# ============================================================
# 6. Select case
# ============================================================

case_id = input(
    "\nEnter case ID to review (example: C016): "
).strip().upper()


matches = df[
    df["case_id"].astype(str).str.upper()
    == case_id
]


if matches.empty:

    print(f"\nERROR: Case {case_id} was not found.")
    raise SystemExit(1)


case = matches.iloc[0]


# ============================================================
# 7. Display ORIGINAL AI diagnosis
# ============================================================

print("\n" + "=" * 60)
print("ORIGINAL AI DIAGNOSIS")
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
# 8. Display reference answer
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
# 9. Human decision
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
    raise SystemExit(1)


decision = decision_map[choice]


# ============================================================
# 10. Reviewer notes
# ============================================================

notes = input(
    "\nEnter reviewer notes: "
).strip()


# ============================================================
# 11. Update HUMAN REVIEW only
# ============================================================

new_review = {
    "case_id": case_id,
    "human_review_required": "True",
    "review_status": "Completed",
    "reviewer_decision": decision,
    "reviewer_notes": notes
}


existing_index = review_df[
    review_df["case_id"].astype(str).str.upper()
    == case_id
].index


if len(existing_index) > 0:

    index = existing_index[0]

    for column in review_columns:
        review_df.loc[index, column] = new_review[column]

else:

    review_df = pd.concat(
        [
            review_df,
            pd.DataFrame([new_review])
        ],
        ignore_index=True
    )


# ============================================================
# 12. Save separate human review log
# ============================================================

try:

    review_df.to_csv(
        HUMAN_REVIEW_FILE,
        index=False
    )

except Exception as error:

    print("\nERROR: Could not save human review.")
    print(error)
    raise SystemExit(1)


# ============================================================
# 13. Verify separation
# ============================================================

print("\n" + "=" * 60)
print("HUMAN REVIEW SAVED")
print("=" * 60)

print(f"\nCase       : {case_id}")
print(f"Decision   : {decision}")
print(f"Status     : Completed")
print(f"Notes      : {notes}")

print("\nOriginal AI results:")
print(f"  {AI_RESULT_FILE}")

print("\nHuman review log:")
print(f"  {HUMAN_REVIEW_FILE}")

print("\nOriginal AI diagnosis was NOT modified.")

print("=" * 60)
