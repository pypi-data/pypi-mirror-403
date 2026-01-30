# norm-findings
A lean CLI tool for normalizing security scanner findings based on DefectDojo parsers.

This project provides a standalone Python package and a minimal Docker image to convert findings from O(100) security scanners into a normalized format.

## Open Source Attribution
This project is based on the excellent work of the [DefectDojo](https://github.com/DefectDojo/django-DefectDojo) community. We leverage their parser logic while providing a lean, dependency-minimized execution environment. See the [NOTICE](NOTICE) file for more details.

## Installation

The default installation includes the core CLI and **all parser dependencies**, providing full functionality out-of-the-box.

### Standard (Core + Parsers)
```bash
pip install .
```

### Optional: Server Support
If you need the REST API server, install the server extra:
```bash
pip install ".[server]"
```

### Optional: Development
For running tests or contributing:
```bash
pip install ".[dev]"
```

## Running Tests

### Unit Tests
Verify the core installation and stubs:
```bash
pytest tests/test_cli.py
```

### E2E Parser Verification (Development only)
To verify all 200+ parsers against real DefectDojo sample data:
1. Ensure the development dependencies are installed (`pip install ".[dev]"`).
2. Run the updater to fetch sample data:
   ```bash
   python -m norm_findings.updater
   ```
3. Run the E2E tests:
   ```bash
   pytest tests/test_e2e.py
   ```

## Usage
### CLI
```bash
norm-findings convert --parser TrivyParser --input-file trivy.json --output-file findings.json
```

### Docker
```bash
docker run -v $(pwd):/dojo -it ghcr.io/scribe-security/norm-findings:latest convert --parser TrivyParser --input-file /dojo/trivy.json --output-file /dojo/findings.json
```

### Using as a Library
You can use `norm-findings` in your own Python projects to parse security reports programmatically:

```python
from norm_findings.parsers.trivy.parser import TrivyParser
import json

parser = TrivyParser()
with open("trivy.json", "r") as f:
    findings = parser.get_findings(f, "test-identification")

for finding in findings:
    print(f"Found: {finding.title} ({finding.severity})")
```

## Legacy Version
The original monkey-patched version of this tool is preserved in the `legacy-monkeypatch` branch and tagged as `v1.x-legacy`. 

To use the legacy version:
```bash
git checkout v1.x-legacy
```

## Automatic Updates
`norm-findings` includes a built-in updater that fetches the latest parsers and tests from DefectDojo:
```bash
python -m norm_findings.updater
```

## Development

### Workflow
1.  **Branching**: Create a new branch for your feature or bugfix from `main`.
2.  **Syncing Parsers**: Run the updater to ensure you have the latest DefectDojo parsers:
    ```bash
    python -m norm_findings.updater
    ```
3.  **Testing**: Always run the test suite before pushing:
    ```bash
    pytest tests/test_cli.py
    pytest tests/test_e2e.py --ignore norm_findings/stubs/models.py
    ```
4.  **Pushing**: Push your branch to GitHub and open a Pull Request.

### Versioning
`norm-findings` uses [setuptools-scm](https://github.com/pypa/setuptools-scm) for automatic versioning. 
- The version is automatically derived from the most recent Git tag.
- When working on local uncommitted changes, the version will include a `.dev` suffix and the current timestamp.
- The version is written to `norm_findings/_version.py` during the build process.

### Releasing
Releases are automated via GitHub Actions and are triggered by pushing a version tag:

1.  **Create a tag**: Create a semantic version tag starting with `v` (e.g., `v1.1.0`):
    ```bash
    git tag -a v1.1.0 -m "Release version 1.1.0"
    ```
2.  **Push the tag**:
    ```bash
    git push origin v1.1.0
    ```
3.  **Automated Pipeline**: The [build workflow](.github/workflows/build.yml) will automatically:
    - Run all tests.
    - Build the Python wheel and source distribution.
    - Publish to **PyPI**.
    - Build and push the Docker image to **GHCR** (tagged with the version and `latest`).

### Automatic Parser Updates
A daily [GitHub Action](.github/workflows/check-updates.yml) runs the `updater.py` logic. If new parsers or updates are detected in DefectDojo:
1.  A new branch `auto-update-parsers` is created.
2.  A Pull Request is opened with a summary of the changes.
3.  Maintainers can review and merge the PR to keep `norm-findings` up-to-date.
