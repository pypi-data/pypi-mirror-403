from importlib.metadata import version, PackageNotFoundError, metadata
from auditly.osv_client import check_vulnerabilities
from auditly.dep_tree import show_tree_for_package


def _severity_label(score):
    if score >= 9:
        return "CRITICAL"
    if score >= 7:
        return "HIGH"
    if score >= 4:
        return "MEDIUM"
    return "LOW"


def explain_package(pkg, requested_version=None):
    print("[auditly] Package Explanation\n")

    # -----------------------
    # Installed version
    # -----------------------
    try:
        installed_version = version(pkg)
        installed = True
    except PackageNotFoundError:
        installed_version = None
        installed = False

    target_version = requested_version or installed_version

    print(f"Package        : {pkg}")
    print(f"Requested Ver  : {requested_version or 'Not specified'}")
    print(f"Installed Ver  : {installed_version or 'Not installed'}")
    print()

    # -----------------------
    # Metadata
    # -----------------------
    try:
        meta = metadata(pkg)
        summary = meta.get("Summary", "No description available.")
        homepage = meta.get("Home-page", "N/A")
    except Exception:
        summary = "No description available."
        homepage = "N/A"

    print("Description:")
    print(summary)
    print(f"Homepage: {homepage}\n")

    # -----------------------
    # Vulnerabilities
    # -----------------------
    if not target_version:
        print("Security Status:")
        print("Package is not installed and no version specified\n")
    else:
        vulns = check_vulnerabilities(pkg, target_version)

        print("Security Status:")
        if not vulns:
            print("No known vulnerabilities found\n")
        else:
            print(f"{len(vulns)} vulnerabilities found\n")

            for v in vulns:
                score = v.get("cvss_score", 0)
                severity = _severity_label(score)

                print(f"- {v['id']} ({severity})")
                print(f"  Affected : {v.get('affected_versions', 'Unknown')}")
                print(f"  Fix      : {v.get('fix', 'Upgrade to a secure version')}")
                print()

    # -----------------------
    # Dependencies
    # -----------------------
    print("Dependencies:")
    try:
        deps = show_tree_for_package(pkg, target_version)
        if not deps:
            print("- None")
        else:
            for d in deps:
                print(f"- {d}")
    except Exception:
        print("- Unable to resolve dependencies")

    print("\nRecommendation:")
    if installed:
        print("Keep dependencies updated and monitor security advisories.")
    else:
        print("Install only if required and prefer the latest stable version.")

    print("\n" + "-" * 60)
