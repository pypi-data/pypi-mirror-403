from importlib.metadata import (
    distributions,
    version as get_version,
    requires,
    PackageNotFoundError
)
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet


def _installed_packages():
    return {dist.metadata["Name"].lower(): dist for dist in distributions()}


def _print_tree(name, prefix, seen, installed_pkgs):
    lname = name.lower()

    if lname in seen:
        return
    seen.add(lname)

    try:
        installed_ver = get_version(name)
    except PackageNotFoundError:
        print(f"{prefix}{name} (not installed)")
        return

    print(f"{prefix}{name} (installed: {installed_ver})")

    reqs = requires(name) or []
    for i, req_str in enumerate(reqs):
        req = Requirement(req_str)
        child = req.name
        last = i == len(reqs) - 1
        branch = "└── " if last else "├── "
        child_prefix = prefix + ("    " if last else "│   ")

        try:
            child_ver = get_version(child)
            conflict = (
                req.specifier
                and not SpecifierSet(str(req.specifier)).contains(child_ver)
            )
            status = f"{child_ver}"
            if conflict:
                status += " CONFLICT"
        except PackageNotFoundError:
            status = "not installed"

        print(f"{prefix}{branch}{child} ({req.specifier}) → {status}")
        _print_tree(child, child_prefix, seen, installed_pkgs)


def show_tree_for_package(pkg, requested_version=None):
    seen = set()

    try:
        installed_ver = get_version(pkg)
        if requested_version and installed_ver != requested_version:
            print(
                f"{pkg} (requested: {requested_version}, "
                f"installed: {installed_ver}) VERSION MISMATCH"
            )
        else:
            print(f"{pkg} (installed: {installed_ver})")
    except PackageNotFoundError:
        print(f"{pkg} is not installed")
        return

    _print_tree(pkg, "", seen, _installed_packages())


def show_tree_for_environment():
    installed = _installed_packages()
    for name in sorted(installed):
        show_tree_for_package(name)
        print()
