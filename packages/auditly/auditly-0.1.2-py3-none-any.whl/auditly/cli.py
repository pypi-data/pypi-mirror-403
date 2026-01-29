import argparse
import sys

from auditly.env_scanner import scan_environment
from auditly.file_scanner import scan_requirements
from auditly.subdep_scanner import scan_requirements_transitive
from auditly.reporter import print_report

# NEW FEATURE
from auditly.dep_tree import (
    show_tree_for_package,
    show_tree_for_environment
)


# NEW FEATURE: explain
from auditly.explain import explain_package


def main():
    # ========================
    # NEW: pkg --tree FEATURE
    # ========================
    if len(sys.argv) >= 2 and sys.argv[1] == "pkg":
        if "--tree" not in sys.argv:
            print("[auditly] Usage: auditly pkg [package==version] --tree")
            return

        if len(sys.argv) == 3:
            # auditly pkg --tree
            print("[auditly] Dependency tree (environment)\n")
            show_tree_for_environment()
            return

        if len(sys.argv) >= 4:
            target = sys.argv[2]
            if "==" in target:
                pkg, ver = target.split("==", 1)
                print("[auditly] Dependency tree\n")
                show_tree_for_package(pkg, ver)
                return

            print("[auditly] Usage: auditly pkg <package>==<version> --tree")
            return
        
        
    # ========================
    # NEW: explain FEATURE
    # ========================
    if len(sys.argv) >= 3 and sys.argv[1] == "explain":
        target = sys.argv[2]

        if "==" in target:
            pkg, ver = target.split("==", 1)
        else:
            pkg, ver = target, None

        explain_package(pkg, ver)
        return
    

    # =====================
    # EXISTING SCANNERS
    # =====================
    parser = argparse.ArgumentParser("auditly")

    parser.add_argument("-r", "--requirements")
    parser.add_argument("--transitive", action="store_true")
    parser.add_argument("--json", action="store_true")

    args = parser.parse_args()

    print("[auditly] Starting dependency security audit...")

    if args.requirements:
        if args.transitive:
            findings, total = scan_requirements_transitive(args.requirements)
        else:
            findings, total = scan_requirements(args.requirements)
    else:
        findings, total = scan_environment(transitive=args.transitive)

    print_report(findings, total, json_output=args.json)