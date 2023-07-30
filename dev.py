# noqa: INP001
import os
from subprocess import check_call


def hooks() -> None:
    check_call(["pre-commit", "run", "--all-files"])


def format() -> None:
    check_call(["ruff", "check", "--fix", "."])
    check_call(["black", "."])
    check_call(["isort", "."])
    check_call(
        [
            "autoflake",
            "--in-place",
            "--recursive",
            "--remove-all-unused-imports",
            "--remove-unused-variables",
            "--ignore-init-module-imports",
            ".",
        ]
    )


def lint() -> None:
    check_call(["ruff", "check", "."])
    check_call(["flake8", "."])
    check_call(["pylint", "service-customers/src", "service-customers/tests"])
    check_call(["pylint", "service-orders/src", "service-orders/tests"])
    check_call(["mypy", "service-customers/src", "service-customers/tests"])
    check_call(["mypy", "service-orders/src", "service-orders/tests"])
    check_call(["bandit", "-r", "service-customers/src"])
    check_call(["bandit", "-r", "service-orders/src"])


def test() -> None:
    check_call(
        ["pytest", "service-customers"],
        env={"TOMODACHI_TESTCONTAINER_DOCKERFILE_PATH": "service-customers", **os.environ.copy()},
    )
    check_call(
        ["pytest", "service-orders"],
        env={"TOMODACHI_TESTCONTAINER_DOCKERFILE_PATH": "service-orders", **os.environ.copy()},
    )


def test_ci() -> None:
    check_call(
        [
            "pytest",
            "-v",
            "--cov=service-customers/src",
            "--cov-branch",
            "--cov-report=xml:build/service-customers/coverage.xml",
            "--cov-report=html:build/service-customers/htmlcov",
            "--junitxml=build/service-customers/tests.xml",
            "service-customers",
        ],
        env={"TOMODACHI_TESTCONTAINER_DOCKERFILE_PATH": "service-customers", **os.environ.copy()},
    )
    check_call(
        [
            "pytest",
            "-v",
            "--cov=service-orders/src",
            "--cov-branch",
            "--cov-report=xml:build/service-orders/coverage.xml",
            "--cov-report=html:build/service-orders/htmlcov",
            "--junitxml=build/service-orders/tests.xml",
            "service-orders",
        ],
        env={"TOMODACHI_TESTCONTAINER_DOCKERFILE_PATH": "service-orders", **os.environ.copy()},
    )
