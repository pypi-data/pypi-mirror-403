import requests

OSV_API = "https://api.osv.dev/v1/query"

def check_vulnerabilities(package, version):
    payload = {
        "package": {
            "name": package,
            "ecosystem": "PyPI"
        },
        "version": version
    }

    resp = requests.post(OSV_API, json=payload, timeout=15)
    data = resp.json()

    vulns = []

    for v in data.get("vulns", []):
        fix_version = None

        # 🔹 Extract fix versions safely
        for affected in v.get("affected", []):
            for r in affected.get("ranges", []):
                for event in r.get("events", []):
                    if "fixed" in event:
                        fix_version = event["fixed"]

        vulns.append({
            "id": v.get("id"),
            "summary": v.get("summary"),
            "severity": v.get("severity"),
            "references": [r.get("url") for r in v.get("references", [])],
            "fix_version": fix_version
        })

    return vulns
