# Contributing to FMUS-VOX

Thank you for your interest in contributing to FMUS-VOX! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you are expected to uphold our Code of Conduct. Please report unacceptable behavior to [maintainer@email.com].

## How Can I Contribute?

### Reporting Bugs

This section guides you through submitting a bug report. Following these guidelines helps maintainers understand your report, reproduce the behavior, and find related reports.

**Before Submitting A Bug Report:**
* Check the [issues](https://github.com/mexyusef/fmus-vox/issues) to see if the problem has already been reported.
* Perform a quick search to see if the problem has been reported already.

**How Do I Submit A Good Bug Report?**
* Use a clear and descriptive title
* Describe the exact steps which reproduce the problem
* Provide specific examples to demonstrate the steps
* Describe the behavior you observed after following the steps
* Explain which behavior you expected to see instead and why
* Include screenshots or animated GIFs if possible
* Include details about your configuration and environment

### Suggesting Enhancements

This section guides you through submitting an enhancement suggestion, including completely new features and minor improvements to existing functionality.

**Before Submitting An Enhancement Suggestion:**
* Check if the enhancement has already been suggested
* Check if it's already available in the latest version

**How Do I Submit A Good Enhancement Suggestion?**
* Use a clear and descriptive title
* Provide a step-by-step description of the suggested enhancement
* Provide specific examples to demonstrate the steps
* Describe the current behavior and how your enhancement would change it
* Explain why this enhancement would be useful to most users

### Pull Requests

* Fill in the required template
* Follow the Python style guide (PEP 8)
* Include appropriate test cases
* End all files with a newline
* Document new code based on our documentation standards
* Update the README.md with details of changes to the interface

## Styleguides

### Git Commit Messages

* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
* Limit the first line to 72 characters or less
* Reference issues and pull requests liberally after the first line

### Python Styleguide

* Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
* Use [Black](https://black.readthedocs.io/) code formatter
* Use [isort](https://pycqa.github.io/isort/) for import sorting
* Add type hints where possible
* Write docstrings in the Google style

### Documentation Styleguide

* Use [Markdown](https://daringfireball.net/projects/markdown/) for documentation
* Use [Google-style docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) for Python code

## Development Environment Setup

1. Fork and clone the repository.
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
4. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Running Tests

```bash
pytest
```

To run tests with coverage:

```bash
pytest --cov=fmus_vox
```

## Additional Resources

* [PEP 8 -- Style Guide for Python Code](https://www.python.org/dev/peps/pep-0008/)
* [The Python Tutorial](https://docs.python.org/3/tutorial/)
* [Python Documentation](https://docs.python.org/3/)

Thanks for your contributions!
