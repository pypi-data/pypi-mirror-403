from importlib.metadata import distributions


def get_installed_packages():
    packages = set()
    for dist in distributions():
        name = dist.metadata.get("Name")
        if name:
            packages.add(name.lower())
    return sorted(packages)


def parse_requirements_file(path):
    requirements = []

    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if "==" in line:
                name, version = line.split("==", 1)
                requirements.append((name.strip(), version.strip()))
            else:
                requirements.append((line.strip(), None))

    return requirements




def get_package_dependencies(package_name: str):
    deps = set()
    for dist in distributions():
        if dist.metadata.get("Name", "").lower() == package_name.lower():
            for req in dist.requires or []:
                deps.add(req.split()[0].lower())
    return deps
