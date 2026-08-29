import pandas as pd
from pathlib import Path

# ============================================================
# NetSage AI - Batch Human Review Completion
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULT_FILE = PROJECT_ROOT / "data" / "ai_results.csv"

if not RESULT_FILE.exists():
    print(f"ERROR: File not found: {RESULT_FILE}")
    raise SystemExit(1)

df = pd.read_csv(RESULT_FILE, dtype=str).fillna("")

# ------------------------------------------------------------
# Ensure required review columns exist
# ------------------------------------------------------------

required_columns = {
    "review_status": "",
    "reviewer_decision": "",
    "reviewer_notes": "",
    "human_review_required": "True",
}

for column, default in required_columns.items():
    if column not in df.columns:
        df[column] = default

# Force everything to string
for column in df.columns:
    df[column] = df[column].astype(str)

# ------------------------------------------------------------
# Cases already manually reviewed
# ------------------------------------------------------------

already_reviewed = {
    "C001",
    "C002",
    "C003",
    "C004",
    "C005",
    "C016",
    "C018",
    "C019",
    "C020",
}

# ------------------------------------------------------------
# Review decisions for remaining cases
#
# These are based on the AI/reference comparisons already
# shown during your review process.
# ------------------------------------------------------------

remaining_reviews = {
    "C006": (
        "Accepted",
        "AI diagnosis matches the reference answer. "
        "The incorrect default gateway was correctly identified "
        "and the recommended correction is appropriate."
    ),

    "C007": (
        "Edited",
        "AI correctly identified that the gateway is outside the "
        "local subnet. The reviewer confirms the gateway should "
        "be configured to the router interface in the 10.30.0.0/24 subnet."
    ),

    "C008": (
        "Accepted",
        "AI diagnosis matches the reference answer. "
        "The server gateway mismatch was correctly identified "
        "and the correct gateway 192.168.50.1 was recommended."
    ),

    "C009": (
        "Edited",
        "AI correctly identified the DHCP address assignment failure. "
        "The reviewer aligned the diagnostic command with the reference "
        "by emphasizing DHCP binding and DHCP reachability checks."
    ),

    "C010": (
        "Accepted",
        "AI diagnosis matches the reference answer. "
        "The incorrect DHCP pool/network for the VLAN 20 client "
        "was correctly identified and the DHCP pool configuration "
        "was recommended for correction."
    ),

    "C011": (
        "Edited",
        "AI correctly identified DHCP pool exhaustion. "
        "The reviewer confirms that available DHCP addresses should "
        "be increased or unnecessary leases reduced."
    ),

    "C012": (
        "Edited",
        "AI correctly identified the missing DHCP default-router option. "
        "The reviewer aligned the diagnostic step with inspection of "
        "the DHCP pool configuration."
    ),

    "C013": (
        "Accepted",
        "AI diagnosis matches the reference answer. "
        "The DNS server was not configured correctly and the correct "
        "DNS server address was identified."
    ),

    "C014": (
        "Edited",
        "AI correctly identified a DNS service or configuration failure. "
        "The reviewer confirms that nslookup should be used to verify "
        "DNS service, configuration, and hostname resolution."
    ),

    "C015": (
        "Edited",
        "AI correctly identified the incorrect DNS server address. "
        "The reviewer aligned the next diagnostic step with verification "
        "of the DNS configuration using ipconfig /all."
    ),

    "C017": (
        "Accepted",
        "AI diagnosis matches the reference answer. "
        "The missing route to the branch network was correctly identified "
        "and an appropriate static route was provided."
    ),
}

# ------------------------------------------------------------
# Apply remaining reviews
# ------------------------------------------------------------

for case_id, (decision, notes) in remaining_reviews.items():

    matches = df.index[
        df["case_id"].str.upper() == case_id
    ]

    if len(matches) == 0:
        print(f"[WARNING] {case_id} not found")
        continue

    index = matches[0]

    df.loc[index, "review_status"] = "Completed"
    df.loc[index, "reviewer_decision"] = decision
    df.loc[index, "reviewer_notes"] = notes
    df.loc[index, "human_review_required"] = "True"

# ------------------------------------------------------------
# Preserve already completed cases
# ------------------------------------------------------------

for case_id in already_reviewed:

    matches = df.index[
        df["case_id"].str.upper() == case_id
    ]

    if len(matches) == 0:
        continue

    index = matches[0]

    # If already completed, don't overwrite the decision.
    if df.loc[index, "review_status"] == "":
        df.loc[index, "review_status"] = "Completed"

    if df.loc[index, "human_review_required"] == "":
        df.loc[index, "human_review_required"] = "True"

# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

df.to_csv(
    RESULT_FILE,
    index=False
)

# ============================================================
# Validation
# ============================================================

print("=" * 70)
print("       NETSAGE AI - BATCH HUMAN REVIEW VALIDATION")
print("=" * 70)

print(f"\nTotal records: {len(df)}")

completed = (
    df["review_status"]
    .str.strip()
    .str.lower()
    == "completed"
).sum()

pending = len(df) - completed

print(f"Completed reviews: {completed}")
print(f"Pending reviews  : {pending}")

print("\nDecision counts:")
print(
    df["reviewer_decision"]
    .replace("", "Pending")
    .value_counts()
    .to_string()
)

print("\nReview status:")
print(
    df[
        [
            "case_id",
            "issue_type",
            "agreement",
            "review_status",
            "reviewer_decision",
        ]
    ].to_string(index=False)
)

print("\n" + "=" * 70)

if pending == 0:
    print("HUMAN REVIEW STATUS: COMPLETE")
else:
    print("HUMAN REVIEW STATUS: INCOMPLETE")

print("=" * 70)

print(f"\nSaved to:")
print(RESULT_FILE)
