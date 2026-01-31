# Contributing to datawhisk

Thank you found using `datawhisk`! We welcome contributions to make this library better for everyone.

## Development Setup

1. **Fork and Clone**
   Fork the repo on GitHub, then clone your fork:
   ```bash
   git clone https://github.com/Ramku3639/datawhisk.git
   cd datawhisk
   ```

2. **Create Environment**
   It's recommended to work in a virtual environment.
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   ```

3. **Install Dependencies**
   Install the package in editable mode with dev extras:
   ```bash
   pip install -e ".[dev]"
   ```

## Running Tests

We use `pytest` for testing. Ensure you run the test suite before submitting a PR.

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=datawhisk
```

## Code Quality Standards

We enforce high code quality standards using strict linting configurations.

1. **Formatting** (Black):
   ```bash
   black datawhisk tests
   ```

2. **Linting** (Flake8):
   ```bash
   flake8 datawhisk tests
   ```

3. **Type Checking** (MyPy):
   ```bash
   mypy datawhisk
   ```

**Note:** Your code must pass all three checks to be merged.

## Contributing Workflow

1. Create a new branch for your feature or fix:
   ```bash
   git checkout -b feature/my-new-feature
   ```

2. Write your code and **add tests** for it.
3. Run the quality checks (tests, format, lint, type-check).
4. Update documentation if necessary.
5. Commit your changes:
   ```bash
   git commit -m "Add feature X"
   ```
6. Push to your fork and submit a Pull Request.

## Reporting Issues

If you find a bug or have a feature request, please open an issue on GitHub.
- Provide a minimal reproducible example.
- Include your OS and Python version.
