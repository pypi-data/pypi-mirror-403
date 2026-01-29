from importlib.metadata import version
from auditly.osv_client import check_vulnerabilities
from auditly.risk import calculate_risk_score
from auditly.utils import parse_requirements_file, get_package_dependencies
from tqdm import tqdm

def scan_requirements_transitive(path):
    roots = parse_requirements_file(path)
    queue = list(roots)
    scanned = set()
    findings = []

    with tqdm(desc="Scanning packages", unit="pkg") as pbar:
        while queue:
            pkg = queue.pop(0)
            if pkg in scanned:
                continue
            scanned.add(pkg)
            pbar.update(1)

            try:
                v = version(pkg)
            except:
                continue

            vulns = check_vulnerabilities(pkg, v)
            if vulns:
                findings.append({
                    "package": pkg,
                    "version": v,
                    "risk_score": calculate_risk_score(vulns),
                    "vulnerabilities": vulns,
                    "deprecated": False
                })

            for d in get_package_dependencies(pkg):
                if d not in scanned:
                    queue.append(d)

    return findings, len(scanned)
