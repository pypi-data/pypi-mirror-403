def calculate_risk_score(vulnerabilities):
    """
    Calculate numeric risk score based on vulnerability severity.
    Supports:
    - CVSS v3 scores
    - String severities (LOW/MEDIUM/HIGH/CRITICAL)
    - Mixed formats (OSV reality)
    """
    score = 0

    for vuln in vulnerabilities:
        severity = vuln.get("severity")

        # Case 1: severity is a STRING
        if isinstance(severity, str):
            score += {
                "LOW": 1,
                "MEDIUM": 3,
                "HIGH": 6,
                "CRITICAL": 10
            }.get(severity.upper(), 1)

        # Case 2: severity is a LIST
        elif isinstance(severity, list):
            for sev in severity:

                # CVSS object
                if isinstance(sev, dict) and sev.get("type") == "CVSS_V3":
                    try:
                        score += int(float(sev.get("score", 0)))
                    except:
                        score += 3

                # String inside list
                elif isinstance(sev, str):
                    score += {
                        "LOW": 1,
                        "MEDIUM": 3,
                        "HIGH": 6,
                        "CRITICAL": 10
                    }.get(sev.upper(), 1)

        # Case 3: unknown / missing severity
        else:
            score += 1

    return score
