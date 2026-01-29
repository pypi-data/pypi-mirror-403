from importlib.metadata import distributions, version, PackageNotFoundError
from auditly.osv_client import check_vulnerabilities
from auditly.risk import calculate_risk_score
from auditly.utils import get_package_dependencies
from tqdm import tqdm
import requests


def scan_environment(transitive=False):
    findings = []
    scanned = set()
    queue = []

    for d in distributions():
        name = d.metadata.get("Name")
        if name:
            queue.append(name)

    total = len(queue)

    with tqdm(total=total, desc="Scanning environment", unit="pkg") as pbar:
        while queue:
            pkg = queue.pop(0)
            if pkg in scanned:
                continue
            scanned.add(pkg)

            try:
                pkg_version = version(pkg)
            except PackageNotFoundError:
                pbar.update(1)
                continue

            vulns = check_vulnerabilities(pkg, pkg_version)

            if vulns:
                findings.append({
                    "package": pkg,
                    "version": pkg_version,
                    "risk_score": calculate_risk_score(vulns),
                    "vulnerabilities": vulns
                })

            if transitive:
                for dep in get_package_dependencies(pkg):
                    if dep not in scanned:
                        queue.append(dep)

            pbar.update(1)

    return findings, len(scanned)
