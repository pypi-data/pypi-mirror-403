Contributing
============

We welcome contributions to ML-EcoLyzer! Please see the
`CONTRIBUTING.md <https://github.com/JomaMinoza/ml-ecolyzer/blob/main/CONTRIBUTING.md>`_
file in the repository root for detailed guidelines.

Quick Start for Contributors
----------------------------

1. Fork the repository
2. Clone your fork::

    git clone https://github.com/YOUR_USERNAME/ml-ecolyzer.git
    cd ml-ecolyzer

3. Install in development mode::

    pip install -e ".[dev,docs]"

4. Create a branch for your changes::

    git checkout -b feature/your-feature-name

5. Make your changes and run tests::

    pytest tests/

6. Submit a pull request

Code Style
----------

- Use **Black** for formatting (line length: 88)
- Use **isort** for import sorting
- Follow Google-style docstrings
- Include type hints for function signatures

Running Tests
-------------

.. code-block:: bash

    # Run all tests
    pytest

    # Run with coverage
    pytest --cov=mlecolyzer

    # Skip slow tests
    pytest -m "not slow"

Building Documentation
----------------------

.. code-block:: bash

    cd docs
    make html

The documentation will be built in ``docs/_build/html/``.
