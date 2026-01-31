## How to Contribute

1. Review the [python library issues]() for tasks for this implementation.
1. Review the [openproficiency model issues](https://github.com/openproficiency/model/issues) for broader tasks.
1. Fork this repository and make your changes.
   > ❗️**Important:** They must be in alignment with the open [proficiency model](https://github.com/openproficiency/model)
1. Start the project in a Codespace or local development container.
1. Verify all unit tests pass.
1. Create a pull request.

## Run Tests workflow

Before creating a workflow, please run the [Unit Tests](./.github/workflows/unit-tests.yml) workflow locally using Act.

```bash
act --job verify_unit_tests
```

```bash
act -W .github/workflows/unit-tests.yml --job verify_unit_tests
```

## Publish to PyPI

1. Install tooling (run from the repo root).

   ```bash
   python3 -m pip install --upgrade build twine
   ```

2. Clean old artifacts.

   ```bash
   rm -rf dist build *.egg-info
   ```

3. Build the package (creates sdist and wheel in `dist/`).

   ```bash
   python3 -m build
   ```

4. Validate metadata (confirm long description renders).

   ```bash
   twine check dist/*
   ```

5. Upload to PyPI. Twine will prompt for a password. Use your PyPI API token.

   ```bash
   twine upload dist/*
   ```

6. Build and upload.

```bash
rm -rf dist build *.egg-info
python3 -m build
twine check dist/*
twine upload dist/*
```
