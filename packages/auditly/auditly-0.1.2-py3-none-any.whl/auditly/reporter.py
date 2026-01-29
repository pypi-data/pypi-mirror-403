import json

def print_report(
    findings,
    total_scanned_packages=0,
    json_output=False,
    show_references=False,
    show_all=False
):
    total_vulns = sum(len(f["vulnerabilities"]) for f in findings)

    if json_output:
        print(json.dumps({
            "summary": {
                "total_packages_scanned": total_scanned_packages,
                "total_vulnerabilities_found": total_vulns
            },
            "results": findings
        }, indent=4))
        return

    print("\n[auditly] Vulnerability Scan Summary")
    print(f"Total Packages Scanned      : {total_scanned_packages}")
    print(f"Total Vulnerabilities Found : {total_vulns}\n")

    if not findings:
        print("[auditly] No known vulnerabilities found\n")
        return

    for item in findings:
        print(f"Package     : {item['package']}=={item['version']}")
        print(f"Risk Score  : {item['risk_score']}")

        if not item["vulnerabilities"] and not show_all:
            continue

        for v in item["vulnerabilities"]:
            print(f"  - {v['id']}: {v.get('summary')}")

            # FIX SUGGESTION
            if v.get("fix_version"):
                print(
                    f"    → Suggested fix: pip install "
                    f"{item['package']}=={v['fix_version']}"
                )
            else:
                print(
                    "    → No fix available. "
                    "Monitor upstream or contact maintainers."
                )

            if show_references and v.get("references"):
                print("    References:")
                for ref in v["references"]:
                    print(f"      • {ref}")

        print("-" * 60)
