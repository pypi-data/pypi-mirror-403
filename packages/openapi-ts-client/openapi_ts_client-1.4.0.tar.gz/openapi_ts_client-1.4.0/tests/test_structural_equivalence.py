"""Structural equivalence tests for generated TypeScript clients.

Compares the functional structure of generated code against fixtures,
ignoring whitespace, ordering, and formatting differences.
"""

from pathlib import Path

import pytest

from openapi_ts_client import ClientFormat, generate_typescript_client
from tests.conftest import FIXTURES_DIR, load_spec
from tests.ts_structure import extract_ts_structure


@pytest.mark.parametrize("fixture_name", ["petstore", "space_zoo", "tictactoe"])
def test_fetch_structural_equivalence(fixture_name: str, tmp_path: Path, ts_parser) -> None:
    """Test that Fetch generation produces structurally equivalent output."""
    fixture_dir = FIXTURES_DIR / fixture_name / "fetch"
    spec = load_spec(fixture_name)

    # Generate client to temp dir
    generate_typescript_client(spec, ClientFormat.FETCH, tmp_path)

    # Extract structure from both
    expected = extract_ts_structure(fixture_dir, ts_parser)
    actual = extract_ts_structure(tmp_path, ts_parser)

    # Compare file sets (excluding .openapi-generator metadata and docs)
    expected_files = {
        k
        for k in expected.keys()
        if not k.startswith(".openapi-generator") and not k.startswith("docs/")
    }
    actual_files = set(actual.keys())

    missing = expected_files - actual_files
    extra = actual_files - expected_files

    if missing:
        pytest.fail(f"Missing files: {sorted(missing)}")
    if extra:
        pytest.fail(f"Extra files: {sorted(extra)}")

    # Compare structure of each file
    differences = []
    for rel_path in sorted(expected_files):
        exp_struct = expected[rel_path]
        act_struct = actual[rel_path]

        for key in ["interfaces", "functions", "type_aliases", "enums", "classes", "exports"]:
            if exp_struct[key] != act_struct[key]:
                differences.append(
                    f"{rel_path} - {key}:\n"
                    f"  Expected: {exp_struct[key]}\n"
                    f"  Actual:   {act_struct[key]}"
                )

    if differences:
        pytest.fail("\n\n".join(differences))


@pytest.mark.parametrize("fixture_name", ["petstore", "space_zoo", "tictactoe"])
def test_angular_structural_equivalence(fixture_name: str, tmp_path: Path, ts_parser) -> None:
    """Test that Angular generation produces structurally equivalent output."""
    fixture_dir = FIXTURES_DIR / fixture_name / "angular"
    spec = load_spec(fixture_name)

    # Generate client to temp dir
    generate_typescript_client(spec, ClientFormat.ANGULAR, tmp_path)

    # Extract structure from both
    expected = extract_ts_structure(fixture_dir, ts_parser)
    actual = extract_ts_structure(tmp_path, ts_parser)

    # Compare file sets (excluding .openapi-generator metadata)
    expected_files = {k for k in expected.keys() if not k.startswith(".openapi-generator")}
    actual_files = set(actual.keys())

    missing = expected_files - actual_files
    extra = actual_files - expected_files

    if missing:
        pytest.fail(f"Missing files: {sorted(missing)}")
    if extra:
        pytest.fail(f"Extra files: {sorted(extra)}")

    # Compare structure of each file
    differences = []
    for rel_path in sorted(expected_files):
        exp_struct = expected[rel_path]
        act_struct = actual[rel_path]

        for key in ["interfaces", "functions", "type_aliases", "enums", "classes", "exports"]:
            if exp_struct[key] != act_struct[key]:
                differences.append(
                    f"{rel_path} - {key}:\n"
                    f"  Expected: {exp_struct[key]}\n"
                    f"  Actual:   {act_struct[key]}"
                )

    if differences:
        pytest.fail("\n\n".join(differences))


@pytest.mark.parametrize("fixture_name", ["petstore", "space_zoo", "tictactoe"])
def test_axios_structural_equivalence(fixture_name: str, tmp_path: Path, ts_parser) -> None:
    """Test that Axios generation produces structurally equivalent output."""
    fixture_dir = FIXTURES_DIR / fixture_name / "axios"
    spec = load_spec(fixture_name)

    # Generate client to temp dir
    generate_typescript_client(spec, ClientFormat.AXIOS, tmp_path)

    # Extract structure from both
    expected = extract_ts_structure(fixture_dir, ts_parser)
    actual = extract_ts_structure(tmp_path, ts_parser)

    # Compare file sets (excluding .openapi-generator metadata and docs)
    expected_files = {
        k
        for k in expected.keys()
        if not k.startswith(".openapi-generator") and not k.startswith("docs/")
    }
    actual_files = {k for k in actual.keys() if not k.startswith("docs/")}

    missing = expected_files - actual_files
    extra = actual_files - expected_files

    if missing:
        pytest.fail(f"Missing files: {sorted(missing)}")
    if extra:
        pytest.fail(f"Extra files: {sorted(extra)}")

    # Compare structure of each file
    differences = []
    for rel_path in sorted(expected_files):
        exp_struct = expected[rel_path]
        act_struct = actual[rel_path]

        for key in ["interfaces", "functions", "type_aliases", "enums", "classes", "exports"]:
            if exp_struct[key] != act_struct[key]:
                differences.append(
                    f"{rel_path} - {key}:\n"
                    f"  Expected: {exp_struct[key]}\n"
                    f"  Actual:   {act_struct[key]}"
                )

    if differences:
        pytest.fail("\n\n".join(differences))
