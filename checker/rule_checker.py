import re
from pathlib import Path


# ============================================================
# NetSage AI - Deterministic Network Rule Checker
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ============================================================
# Utility functions
# ============================================================

def print_result(check_name, passed, details):
    status = "PASS" if passed else "FAIL"

    print(f"\n[{status}] {check_name}")
    print(f"      {details}")


# ============================================================
# 1. Duplicate IP Address Check
# ============================================================

def check_duplicate_ips(ip_addresses):
    seen = set()
    duplicates = set()

    for ip in ip_addresses:
        if ip in seen:
            duplicates.add(ip)
        else:
            seen.add(ip)

    passed = len(duplicates) == 0

    if passed:
        details = "No duplicate IP addresses detected."
    else:
        details = (
            "Duplicate IP addresses found: "
            + ", ".join(sorted(duplicates))
        )

    print_result(
        "Duplicate IP Check",
        passed,
        details
    )

    return passed


# ============================================================
# 2. Subnet Mask Check
# ============================================================

def check_subnet_mask(ip_address, subnet_mask, expected_mask):
    passed = subnet_mask == expected_mask

    if passed:
        details = (
            f"{ip_address} uses the correct subnet mask "
            f"{subnet_mask}."
        )
    else:
        details = (
            f"{ip_address} uses {subnet_mask}; "
            f"expected {expected_mask}."
        )

    print_result(
        "Subnet Mask Check",
        passed,
        details
    )

    return passed


# ============================================================
# 3. Default Gateway Check
# ============================================================

def check_gateway(ip_address, gateway, network_gateway):
    passed = gateway == network_gateway

    if passed:
        details = (
            f"Gateway {gateway} matches the expected "
            f"network gateway."
        )
    else:
        details = (
            f"Configured gateway {gateway} does not match "
            f"expected gateway {network_gateway}."
        )

    print_result(
        "Default Gateway Check",
        passed,
        details
    )

    return passed


# ============================================================
# 4. Interface Status Check
# ============================================================

def check_interface_status(interface_name, status):
    normalized_status = status.lower().strip()

    passed = normalized_status in [
        "up",
        "up/up",
        "connected"
    ]

    if passed:
        details = (
            f"{interface_name} is operational "
            f"({status})."
        )
    else:
        details = (
            f"{interface_name} is not operational "
            f"({status})."
        )

    print_result(
        "Interface Status Check",
        passed,
        details
    )

    return passed


# ============================================================
# 5. VLAN Existence Check
# ============================================================

def check_vlan(vlan_id, existing_vlans):
    vlan_id = str(vlan_id)

    normalized_vlans = [
        str(vlan).strip()
        for vlan in existing_vlans
    ]

    passed = vlan_id in normalized_vlans

    if passed:
        details = (
            f"VLAN {vlan_id} exists in the VLAN database."
        )
    else:
        details = (
            f"VLAN {vlan_id} is missing from the VLAN database."
        )

    print_result(
        "VLAN Existence Check",
        passed,
        details
    )

    return passed


# ============================================================
# 6. Routing Table Check
# ============================================================

def check_route(destination_network, routing_table):
    destination_network = destination_network.strip()

    normalized_routes = [
        str(route).strip()
        for route in routing_table
    ]

    passed = destination_network in normalized_routes

    if passed:
        details = (
            f"Route to {destination_network} exists."
        )
    else:
        details = (
            f"No route to {destination_network} "
            f"was found in the routing table."
        )

    print_result(
        "Routing Table Check",
        passed,
        details
    )

    return passed


# ============================================================
# Demonstration / Sample Network Case
# ============================================================

def run_demo():
    print("=" * 60)
    print("          NETSAGE AI - RULE CHECKER")
    print("=" * 60)

    print("\nRunning deterministic network checks...")

    # --------------------------------------------------------
    # Test 1: Duplicate IP
    # --------------------------------------------------------

    ip_addresses = [
        "192.168.10.10",
        "192.168.10.11",
        "192.168.10.12",
        "192.168.10.10"
    ]

    check_duplicate_ips(ip_addresses)

    # --------------------------------------------------------
    # Test 2: Subnet mask
    # --------------------------------------------------------

    check_subnet_mask(
        "192.168.10.10",
        "255.255.255.0",
        "255.255.255.0"
    )

    # --------------------------------------------------------
    # Test 3: Gateway
    # --------------------------------------------------------

    check_gateway(
        "192.168.10.10",
        "192.168.10.1",
        "192.168.10.1"
    )

    # --------------------------------------------------------
    # Test 4: Interface
    # --------------------------------------------------------

    check_interface_status(
        "GigabitEthernet0/1",
        "up/up"
    )

    # --------------------------------------------------------
    # Test 5: VLAN
    # --------------------------------------------------------

    check_vlan(
        30,
        [10, 20, 30, 40]
    )

    # --------------------------------------------------------
    # Test 6: Route
    # --------------------------------------------------------

    check_route(
        "192.168.20.0/24",
        [
            "192.168.10.0/24",
            "192.168.20.0/24"
        ]
    )

    print("\n" + "=" * 60)
    print("RULE CHECKER DEMONSTRATION COMPLETE")
    print("=" * 60)


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    run_demo()
