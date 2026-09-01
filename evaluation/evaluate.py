import pandas as pd
from pathlib import Path

# ============================================================
# NETSAGE AI - FINAL EVALUATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

AI_FILE = BASE_DIR / "data" / "ai_results.csv"
REVIEW_FILE = BASE_DIR / "data" / "human_review.csv"


def main():

    print("=" * 70)
    print("              NETSAGE AI - FINAL EVALUATION")
    print("=" * 70)

    # --------------------------------------------------------
    # Check files
    # --------------------------------------------------------

    if not AI_FILE.exists():
        print(f"\nERROR: AI results file not found:")
        print(AI_FILE)
        return

    if not REVIEW_FILE.exists():
        print(f"\nERROR: Human review file not found:")
        print(REVIEW_FILE)
        return

    # --------------------------------------------------------
    # Load original AI results
    # --------------------------------------------------------

    ai_df = pd.read_csv(
        AI_FILE,
        dtype=str,
        keep_default_na=False
    )

    # --------------------------------------------------------
    # Load separate human review file
    # --------------------------------------------------------

    review_df = pd.read_csv(
        REVIEW_FILE,
        dtype=str,
        keep_default_na=False
    )

    total = len(ai_df)

    # --------------------------------------------------------
    # Validate required columns
    # --------------------------------------------------------

    ai_required = [
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

    review_required = [
        "case_id",
        "human_review_required",
        "review_status",
        "reviewer_decision",
        "reviewer_notes"
    ]

    missing_ai = [
        column for column in ai_required
        if column not in ai_df.columns
    ]

    missing_review = [
        column for column in review_required
        if column not in review_df.columns
    ]

    if missing_ai:
        print("\nERROR: Missing columns in ai_results.csv:")
        for column in missing_ai:
            print(f" - {column}")
        return

    if missing_review:
        print("\nERROR: Missing columns in human_review.csv:")
        for column in missing_review:
            print(f" - {column}")
        return

    # --------------------------------------------------------
    # Normalize case IDs
    # --------------------------------------------------------

    ai_df["case_id"] = (
        ai_df["case_id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    review_df["case_id"] = (
        review_df["case_id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # --------------------------------------------------------
    # Find missing reviews
    # --------------------------------------------------------

    missing_reviews = ai_df[
        ~ai_df["case_id"].isin(review_df["case_id"])
    ]

    completed = len(ai_df[
        ai_df["case_id"].isin(
            review_df[
                review_df["review_status"]
                .str.strip()
                .str.lower()
                .eq("completed")
            ]["case_id"]
        )
    ])

    # --------------------------------------------------------
    # Human review counts
    # --------------------------------------------------------

    accepted = (
        review_df["reviewer_decision"]
        .str.strip()
        .str.lower()
        .eq("accepted")
        .sum()
    )

    edited = (
        review_df["reviewer_decision"]
        .str.strip()
        .str.lower()
        .eq("edited")
        .sum()
    )

    rejected = (
        review_df["reviewer_decision"]
        .str.strip()
        .str.lower()
        .eq("rejected")
        .sum()
    )

    # --------------------------------------------------------
    # AI classification
    # --------------------------------------------------------

    likely_match = (
        ai_df["agreement"]
        .str.strip()
        .str.lower()
        .eq("likely match")
        .sum()
    )

    human_review = (
        ai_df["agreement"]
        .str.strip()
        .str.lower()
        .eq("needs human review")
        .sum()
    )

    # --------------------------------------------------------
    # Overall Summary
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("OVERALL SUMMARY")
    print("-" * 70)

    print(f"Total Cases              : {total}")
    print(f"Reviews Completed        : {completed}/{total}")
    print(f"Accepted                 : {accepted}")
    print(f"Edited                   : {edited}")
    print(f"Rejected                 : {rejected}")

    # --------------------------------------------------------
    # Missing reviews
    # --------------------------------------------------------

    if len(missing_reviews) > 0:

        print("\nMissing Reviews:")

        for case_id in missing_reviews["case_id"]:
            print(f"  - {case_id}")

    else:

        print("\nAll cases have a human review.")

    # --------------------------------------------------------
    # AI Classification
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("AI CLASSIFICATION")
    print("-" * 70)

    print(f"Likely Match             : {likely_match}")
    print(f"Needs Human Review       : {human_review}")

    likely_rate = (
        likely_match / total * 100
        if total else 0
    )

    review_rate = (
        human_review / total * 100
        if total else 0
    )

    print(f"Likely Match Rate        : {likely_rate:.2f}%")
    print(f"Human Review Rate        : {review_rate:.2f}%")

    # --------------------------------------------------------
    # Human Review
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("HUMAN REVIEW")
    print("-" * 70)

    acceptance_rate = (
        accepted / total * 100
        if total else 0
    )

    edit_rate = (
        edited / total * 100
        if total else 0
    )

    rejection_rate = (
        rejected / total * 100
        if total else 0
    )

    print(
        f"Accepted                 : "
        f"{accepted} ({acceptance_rate:.2f}%)"
    )

    print(
        f"Edited                   : "
        f"{edited} ({edit_rate:.2f}%)"
    )

    print(
        f"Rejected                 : "
        f"{rejected} ({rejection_rate:.2f}%)"
    )

    # --------------------------------------------------------
    # Issue Type Distribution
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("ISSUE TYPE DISTRIBUTION")
    print("-" * 70)

    issue_counts = ai_df["issue_type"].value_counts()

    for issue, count in issue_counts.items():
        print(f"{issue:<20} : {count}")

    # --------------------------------------------------------
    # Severity Distribution
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("SEVERITY DISTRIBUTION")
    print("-" * 70)

    severity_counts = ai_df["severity"].value_counts()

    for severity, count in severity_counts.items():
        print(f"{severity:<20} : {count}")

    # --------------------------------------------------------
    # Human Corrections
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("HUMAN CORRECTIONS")
    print("-" * 70)

    corrected = review_df[
        review_df["reviewer_decision"]
        .str.strip()
        .str.lower()
        .eq("edited")
    ]

    print(f"Cases requiring edits  : {len(corrected)}")

    if len(corrected) > 0:

        print("\nEdited Cases:")

        for case_id in corrected["case_id"]:
            print(f"  - {case_id}")

    # --------------------------------------------------------
    # Requirement checks
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("REQUIREMENT CHECKS")
    print("-" * 70)

    cases_pass = total >= 30
    review_pass = completed == total
    correction_pass = edited >= 5

    print(
        f"[{'PASS' if cases_pass else 'FAIL'}] "
        f"At least 30 troubleshooting cases"
    )

    print(
        f"[{'PASS' if review_pass else 'FAIL'}] "
        f"Human review completed for all cases"
    )

    print(
        f"[{'PASS' if correction_pass else 'FAIL'}] "
        f"At least 5 human-corrected AI responses"
    )

    # --------------------------------------------------------
    # Final Status
    # --------------------------------------------------------

    print("\n" + "=" * 70)

    if (
        cases_pass
        and review_pass
        and correction_pass
    ):
        print("FINAL EVALUATION STATUS: COMPLETE")
    else:
        print("FINAL EVALUATION STATUS: INCOMPLETE")

    print("=" * 70)


if __name__ == "__main__":
    main()
