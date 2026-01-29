from importlib.metadata import version as get_version, PackageNotFoundError
from auditly.osv_client import check_vulnerabilities
from auditly.risk import calculate_risk_score
from auditly.utils import parse_requirements_file
from tqdm import tqdm

def scan_requirements(requirements_file):
    """
    Scan only packages listed in requirements.txt
    """
    findings = []
    packages = parse_requirements_file(requirements_file)
    scanned = 0

    with tqdm(total=len(packages), desc="Scanning requirements", unit="pkg") as pbar:
        for pkg, pinned_version in packages:
            scanned += 1
            pbar.update(1)

            try:
                installed_version = pinned_version or get_version(pkg)
            except PackageNotFoundError:
                continue

            vulns = check_vulnerabilities(pkg, installed_version)

            if vulns:
                findings.append({
                    "package": pkg,
                    "version": installed_version,
                    "risk_score": calculate_risk_score(vulns),
                    "vulnerabilities": vulns
                })

    return findings, scanned
