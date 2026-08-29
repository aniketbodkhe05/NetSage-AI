import pandas as pd
from pathlib import Path


# --------------------------------------------------
# NetSage AI - Dataset Validator
# --------------------------------------------------

DATA_FILE = Path(__file__).parent.parent / "data" / "cases.csv"

REQUIRED_COLUMNS = [
    "case_id",
    "issue_type",
    "symptom",
    "topology_note",
    "show_output",
    "expected_fault",
    "osi_layer",
    "concept",
    "severity",
    "expected_next_command",
    "expected_fix"
]

REQUIRED_ISSUE_TYPES = [
    "VLAN",
    "Gateway",
    "DHCP",
    "DNS",
    "Routing",
    "ACL",
    "NAT",
    "Wireless"
]


def print_header():
    print("=" * 55)
    print("        NetSage AI - Dataset Validation")
    print("=" * 55)


def main():

    print_header()

    # --------------------------------------------------
    # 1. Check whether CSV exists
    # --------------------------------------------------

    if not DATA_FILE.exists():
        print("\nERROR: cases.csv was not found.")
        print(f"Expected location: {DATA_FILE}")
        return

    print(f"\nDataset found: {DATA_FILE}")

    # --------------------------------------------------
    # 2. Load CSV
    # --------------------------------------------------

    try:
        df = pd.read_csv(DATA_FILE)
    except Exception as error:
        print("\nERROR: Could not read cases.csv")
        print(error)
        return

    # --------------------------------------------------
    # 3. Check required columns
    # --------------------------------------------------

    print("\n[1] Checking required columns...")

    missing_columns = [
        column for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        print("FAILED")
        print("Missing columns:")
        for column in missing_columns:
            print(f"  - {column}")
        return

    print("PASSED - All required columns exist.")

    # --------------------------------------------------
    # 4. Check number of cases
    # --------------------------------------------------

    print("\n[2] Checking number of cases...")

    total_cases = len(df)

    print(f"Total cases: {total_cases}")
    print("Minimum required: 30")

    if total_cases < 30:
        print("FAILED - At least 30 cases are required.")
        return

    print("PASSED")

    # --------------------------------------------------
    # 5. Check required issue types
    # --------------------------------------------------

    print("\n[3] Checking issue-type coverage...")

    issue_counts = df["issue_type"].value_counts()

    all_issue_types_found = True

    for issue in REQUIRED_ISSUE_TYPES:

        count = issue_counts.get(issue, 0)

        if count > 0:
            print(f"{issue:<12}: {count:>2} cases  [PASS]")
        else:
            print(f"{issue:<12}: {count:>2} cases  [FAIL]")
            all_issue_types_found = False

    if not all_issue_types_found:
        print("\nFAILED - One or more required issue types are missing.")
        return

    # --------------------------------------------------
    # 6. Check empty fields
    # --------------------------------------------------

    print("\n[4] Checking required fields...")

    fields_to_check = [
        "symptom",
        "topology_note",
        "show_output",
        "expected_fault",
        "osi_layer",
        "concept",
        "severity",
        "expected_next_command",
        "expected_fix"
    ]

    field_errors = []

    for field in fields_to_check:

        empty_count = df[field].isna().sum()

        if empty_count > 0:

            field_errors.append(
                f"{field}: {empty_count} empty values"
            )

            print(
                f"{field:<22}: FAIL ({empty_count} empty)"
            )

        else:
            print(
                f"{field:<22}: PASS"
            )

    if field_errors:
        print("\nFAILED - Some required fields are empty.")
        return

    # --------------------------------------------------
    # 7. Check duplicate case IDs
    # --------------------------------------------------

    print("\n[5] Checking duplicate case IDs...")

    duplicate_ids = df[
        df["case_id"].duplicated(keep=False)
    ]["case_id"].unique()

    if len(duplicate_ids) > 0:

        print("FAILED")
        print("Duplicate case IDs:")

        for case_id in duplicate_ids:
            print(f"  - {case_id}")

        return

    print("PASSED - No duplicate case IDs.")

    # --------------------------------------------------
    # 8. Display severity distribution
    # --------------------------------------------------

    print("\n[6] Severity distribution...")

    severity_counts = df["severity"].value_counts()

    for severity, count in severity_counts.items():
        print(f"{severity:<12}: {count}")

    # --------------------------------------------------
    # 9. Final result
    # --------------------------------------------------

    print("\n" + "=" * 55)
    print("        DATASET VALIDATION PASSED")
    print("=" * 55)

    print("\nNetSage AI dataset is ready for the next phase.")


if __name__ == "__main__":
    main()
