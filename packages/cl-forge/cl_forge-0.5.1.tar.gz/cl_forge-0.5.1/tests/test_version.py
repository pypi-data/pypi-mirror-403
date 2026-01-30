import cl_forge


def test_version_accessible():
    assert hasattr(cl_forge, "__version__")
    # In a development environment without the package installed, it might be "unknown"
    # or if installed it should match the Cargo.toml version (0.4.0)
    print(f"Detected version: {cl_forge.__version__}")
    assert cl_forge.__version__ != ""
