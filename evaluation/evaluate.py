import pandas as pd
from pathlib import Path

# ============================================================
# NETSAGE AI - FINAL EVALUATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "ai_results.csv"


def main():

    print("=" * 70)
    print("              NETSAGE AI - FINAL EVALUATION")
    print("=" * 70)

    if not DATA_FILE.exists():
        print(f"\nERROR: File not found:")
        print(DATA_FILE)
        return

    df = pd.read_csv(DATA_FILE, dtype=str).fillna("")

    total = len(df)

    completed = (
        df["review_status"]
        .str.strip()
        .str.lower()
        .eq("completed")
        .sum()
    )

    accepted = (
        df["reviewer_decision"]
        .str.strip()
        .str.lower()
        .eq("accepted")
        .sum()
    )

    edited = (
        df["reviewer_decision"]
        .str.strip()
        .str.lower()
        .eq("edited")
        .sum()
    )

    rejected = (
        df["reviewer_decision"]
        .str.strip()
        .str.lower()
        .eq("rejected")
        .sum()
    )

    likely_match = (
        df["agreement"]
        .str.strip()
        .str.lower()
        .eq("likely match")
        .sum()
    )

    human_review = (
        df["agreement"]
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
    # AI Classification
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("AI CLASSIFICATION")
    print("-" * 70)

    print(f"Likely Match             : {likely_match}")
    print(f"Needs Human Review       : {human_review}")

    likely_rate = (likely_match / total) * 100 if total else 0
    review_rate = (human_review / total) * 100 if total else 0

    print(f"Likely Match Rate        : {likely_rate:.2f}%")
    print(f"Human Review Rate        : {review_rate:.2f}%")

    # --------------------------------------------------------
    # Human Review
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("HUMAN REVIEW")
    print("-" * 70)

    acceptance_rate = (accepted / total) * 100 if total else 0
    edit_rate = (edited / total) * 100 if total else 0
    rejection_rate = (rejected / total) * 100 if total else 0

    print(f"Accepted                 : {accepted} ({acceptance_rate:.2f}%)")
    print(f"Edited                   : {edited} ({edit_rate:.2f}%)")
    print(f"Rejected                 : {rejected} ({rejection_rate:.2f}%)")

    # --------------------------------------------------------
    # Issue Type Distribution
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("ISSUE TYPE DISTRIBUTION")
    print("-" * 70)

    issue_counts = df["issue_type"].value_counts()

    for issue, count in issue_counts.items():
        print(f"{issue:<20} : {count}")

    # --------------------------------------------------------
    # Severity Distribution
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("SEVERITY DISTRIBUTION")
    print("-" * 70)

    severity_counts = df["severity"].value_counts()

    for severity, count in severity_counts.items():
        print(f"{severity:<20} : {count}")

    # --------------------------------------------------------
    # Human Corrections
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("HUMAN CORRECTIONS")
    print("-" * 70)

    corrected = df[
        df["reviewer_decision"]
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
    # Final Status
    # --------------------------------------------------------

    print("\n" + "=" * 70)

    if completed == total:
        print("FINAL EVALUATION STATUS: COMPLETE")
    else:
        print("FINAL EVALUATION STATUS: INCOMPLETE")

    print("=" * 70)


if __name__ == "__main__":
    main()
