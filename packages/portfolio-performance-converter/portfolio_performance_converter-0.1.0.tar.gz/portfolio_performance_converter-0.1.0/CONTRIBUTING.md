# Contributing to `portfolio-performance-converter`

Thank you for your interest in contributing to this project! We welcome contributions from the community.

## Reporting Issues

If you find a bug or have a suggestion for a new feature, please open an issue in the GitHub repository.

1.  Check if the issue already exists.
2.  If not, open a new issue.
3.  Provide a clear title and description.
4.  For bugs, include steps to reproduce, expected behavior, and actual behavior.

## Development Setup

1.  Clone the repository.
2.  Install [uv](https://github.com/astral-sh/uv).
3.  Install dependencies:
    ```bash
    uv sync
    ```

## Running Tests

We use `pytest` for testing. Please ensure all tests pass before submitting your changes.

To run the tests, execute:

```bash
uv run pytest
```

If you are adding new features, please add corresponding tests in the `tests/` directory.

## Coding Style

*   Follow standard Python coding practices (PEP 8).
*   Ensure your code is clean and readable.
*   Document your code where necessary.

## Submitting Pull Requests

1.  Fork the repository and create a new branch for your feature or fix.
2.  Make your changes.
3.  Run tests to ensure nothing is broken.
4.  Submit a Pull Request (PR) with a clear description of your changes.
