import tomllib
from pathlib import Path

from .utils import REQUIREMENTS_FILES, is_valid_dependency_file


def get_package_name(dep_spec: str) -> str:
    """extract the package name from dependency specification file
    >>> get_package_name("requests>=2.28.0")
    'requests'
    >>> get_package_name("click[shell]")
    'click'
    """
    name = dep_spec.split(";")[0]
    name = name.split("[")[0]
    for op in ["==", ">=", "<=", ">", "<", "~=", "!="]:
        name = name.split(op)[0]
    return name.strip()


def parse_pyproject(path: Path) -> tuple[set[str], set[str]]:
    assert is_valid_dependency_file(path), "invalid dependency specification file"
    with open(path, "rb") as f:
        data = tomllib.load(f)
    dev_packages, prod_packages = set(), set()
    if not data or not isinstance(data, dict):
        return prod_packages, dev_packages
    prod_deps = data.get("project", {}).get("dependencies", {})
    prod_packages = {get_package_name(dep) for dep in prod_deps}
    #  dependency-groups (PEP 735)
    dev_packages = set()
    dep_groups = data.get("dependency-groups", {})
    for group_name, deps in dep_groups.items():
        dev_packages.update([get_package_name(dep) for dep in deps])

    # check tool.hatch.envs.*.dependencies
    hatch_envs = data.get("tool", {}).get("hatch", {}).get("envs", {})
    for env_name, env_config in hatch_envs.items():
        if env_name != "default":  # Skip default env
            env_deps = env_config.get("dependencies", [])
            dev_packages.update([get_package_name(dep) for dep in env_deps])

    poetry_groups = data.get("tool", {}).get("poetry", {})
    main_deps = poetry_groups.get("dependencies", {})
    if "python" in main_deps:
        del main_deps["python"]
    prod_packages.update(main_deps.keys())

    # dev-dependencies
    legacy_other_deps = poetry_groups.get("dev-dependencies", {})
    dev_packages.update(legacy_other_deps.keys())
    # Poetry >=1.2
    groups = poetry_groups.get("group", {})
    for group_name, group_config in groups.items():
        group_deps = group_config.get("dependencies", {})
        if group_name == "dev":
            dev_packages.update(group_deps.keys())
        else:
            dev_packages.update(group_deps.keys())

    return prod_packages, dev_packages


def parse_requirements(path: Path) -> set[str]:
    assert is_valid_dependency_file(path), "invalid dependency specification file"
    packages = set()
    with open(path) as f:
        for line in f:
            line = line.strip()
            # Skip comments, empty lines, and -e/--editable installs
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            pkg = get_package_name(line)
            if pkg:
                packages.add(pkg)
    return packages


def find_and_parse() -> tuple[set[str], set[str]]:
    """parse dependency files in current directory when not given explicit files"""
    pyproject = Path("pyproject.toml")
    requirements = Path("requirements.txt")
    requirements_dev = Path("requirements-dev.txt")

    prod_deps = set()
    other_deps = set()

    if pyproject.exists():
        prod_deps, other_deps = parse_pyproject(pyproject)
    if requirements.exists():
        prod_deps.update(parse_requirements(requirements))
    if requirements_dev.exists():
        other_deps.update(parse_requirements(requirements_dev))

    # some other requirements files
    for pattern in REQUIREMENTS_FILES:
        other_file = Path(pattern)
        if other_file.exists():
            other_deps.update(parse_requirements(other_file))
    if not prod_deps and not other_deps:
        raise FileNotFoundError("I did not find dependency files to parse!")
    other_deps -= prod_deps
    return prod_deps, other_deps
