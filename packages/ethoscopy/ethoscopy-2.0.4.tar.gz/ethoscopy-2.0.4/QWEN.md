# Ethoscopy Project Context

## Project Overview

Ethoscopy is a Python data-analysis toolbox designed for curating, cleaning, analyzing, and visualizing behavioral time series data, particularly from the Ethoscope hardware system (a Drosophila monitoring system). It extends Pandas DataFrames to include linked metadata, facilitating complex behavioral analyses.

Key features include:
- Loading data from Ethoscope `.db` files (local or remote FTP).
- Data curation and cleaning functions (e.g., removing dead specimens, interpolating missing values).
- Sleep calculation from movement data.
- Circadian rhythm analysis tools (e.g., periodograms).
- Hidden Markov Model (HMM) implementation for latent behavioral state analysis, utilizing `hmmlearn`.
- Visualization capabilities using either Seaborn (static) or Plotly (interactive).
- A factory function `behavpy()` to create specialized DataFrame objects with chosen visualization backends.

The core architecture is built around the `behavpy_core` class (in `src/ethoscopy/behavpy_core.py`), which is extended by `behavpy_plotly` and `behavpy_seaborn` (in `src/ethoscopy/behavpy_plotly.py` and `src/ethoscopy/behavpy_seaborn.py` respectively). The main factory function `behavpy()` (in `src/ethoscopy/behavpy.py`) instantiates the appropriate backend-specific class.

Version 2.0 introduced significant refactoring for compatibility with newer Pandas/NumPy versions, unified analysis classes under `behavpy()`, and allowed backend selection for plotting.

## Key Technologies and Dependencies

- **Core:** Python (3.10+), Pandas (2.2.2+), NumPy (2.0.0+)
- **Visualization:** Plotly (5.22.0+), Seaborn (0.13.2+)
- **Analysis:** hmmlearn (0.3.2+), pywavelets, astropy, scipy
- **Utilities:** tabulate, colour
- **Testing:** pytest, pytest-cov, pytest-mock, pytest-xdist
- **Development:** black, ruff, isort, pre-commit
- **Build:** hatchling

## Building, Running, and Testing

### Installation

```bash
# Recommended: Install in a virtual environment
pip install ethoscopy
# Or for development
pip install -e ".[dev]"
```

### Using Ethoscopy

Ethoscopy is intended for use in Jupyter Notebooks or Python scripts.
```python
import ethoscopy as etho

# Create a behavpy object
data = pandas_dataframe # Your experimental data
metadata = pandas_dataframe # Your experimental metadata
df = etho.behavpy(data, metadata, check=True, canvas='plotly', palette='Set2')

# Filter data
filtered_df = df.xmv('experimental_column', 'group_2') # Example method
```

### Running Tests

Ethoscopy uses `pytest` for its comprehensive test suite.

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=ethoscopy --cov-report=term-missing

# Run specific categories (see TESTING.md)
pytest -m unit          # Fast unit tests
pytest -m integration   # Integration tests
pytest -m "not slow"    # Skip slow tests

# Convenience script (run_tests.py)
python run_tests.py                    # Run all tests with coverage
python run_tests.py --type unit        # Run unit tests
python run_tests.py --type integration # Run integration tests
python run_tests.py --no-coverage      # Run without coverage
```

See [TESTING.md](TESTING.md) for detailed testing guidelines, test structure, categories, and writing tests.

## Development Conventions

- **Code Style:** Formatted with Black, linted with Ruff.
- **Imports:** Managed with isort.
- **Testing:** Comprehensive test suite with pytest, aiming for >70% coverage. Tests are categorized (unit, integration, slow).
- **Pre-commit Hooks:** Used for formatting, linting, and running fast tests locally before commits/pushes.
- **Dependencies:** Managed via `pyproject.toml`.
- **Packaging:** Uses `hatchling` as the build backend.