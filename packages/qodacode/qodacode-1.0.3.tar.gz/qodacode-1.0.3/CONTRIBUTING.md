# Contributing to Qodacode

Thank you for your interest in contributing to Qodacode! We welcome contributions from the community.

## Code of Conduct

Please be respectful and professional in all interactions.

## How to Contribute

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature`
3. **Make your changes**
4. **Run tests**: `pytest tests/`
5. **Commit your changes**: `git commit -m "feat: your feature"`
6. **Push to your fork**: `git push origin feature/your-feature`
7. **Open a Pull Request**

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/qodacode.git
cd qodacode

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/
```

## Pull Request Guidelines

- **Write tests** for new features
- **Update documentation** if needed
- **Follow code style**: We use `ruff` for linting
- **Keep commits atomic**: One logical change per commit
- **Write clear commit messages**:
  - `feat: add new rule SEC-010`
  - `fix: correct SQL injection detection`
  - `docs: update CLI documentation`

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=qodacode --cov-report=html

# Run specific test file
pytest tests/test_scanner.py -v
```

## Code Style

We use `ruff` for linting and formatting:

```bash
# Check code style
ruff check qodacode/

# Auto-fix issues
ruff check --fix qodacode/
```

## Contributor License Agreement (CLA)

By submitting a contribution to this project, you agree to the following terms:

### Individual Contributor License Agreement

1. **Grant of Rights**: You grant Nelson Padilla a perpetual, worldwide, non-exclusive, no-charge, royalty-free, irrevocable copyright license to reproduce, prepare derivative works of, publicly display, publicly perform, sublicense, and distribute Your contributions and such derivative works.

2. **Grant of Patent License**: You grant Nelson Padilla a perpetual, worldwide, non-exclusive, no-charge, royalty-free, irrevocable patent license to make, have made, use, offer to sell, sell, import, and otherwise transfer your contribution.

3. **Ownership**: You represent that you are legally entitled to grant the above licenses. If your employer has rights to intellectual property that you create, you represent that you have received permission to make the contributions on behalf of that employer.

4. **Originality**: You represent that your contribution is your original creation and that you have the right to submit it under the AGPL-3.0 license.

5. **Support**: You are not expected to provide support for your contributions, except to the extent you desire to provide support.

6. **No Warranty**: Unless required by applicable law or agreed to in writing, you provide your contributions on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND.

### Why CLA?

The CLA allows us to:
- Relicense code if needed for commercial versions
- Protect the project from legal issues
- Use contributions in both open source and premium versions
- Maintain full control over the project direction

### How to Sign

**For first-time contributors:**

When you open your first Pull Request, add this line to your PR description:

```
I have read and agree to the Contributor License Agreement in CONTRIBUTING.md
```

## Questions?

- **GitHub Issues**: https://github.com/qodacode/qodacode/issues
- **Discussions**: https://github.com/qodacode/qodacode/discussions

## License

By contributing, you agree that your contributions will be licensed under the AGPL-3.0 license.
