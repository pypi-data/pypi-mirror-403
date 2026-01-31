# TOPSIS — Assignment Project ✅

## Overview
A small CLI and web service implementation of the TOPSIS decision-making method. This repository includes:
- A command-line program `topsis.py` to compute TOPSIS scores and ranks.
- A Flask web service (`app.py`) that accepts an input CSV, weights, impacts and sends the result by email.
- A package prepared for PyPI (naming convention: `Topsis-Mehak-102303724`).

---

## Quick Start ✨

### Requirements
- Python 3.8+
- Install required packages: pandas, numpy, flask

Install with:

```bash
pip install -r requirements.txt
```

### CLI Usage

```bash
python topsis.py <InputDataFile> "<Weights>" "<Impacts>" <OutputResultFileName>
```

Example:

```bash
python topsis.py data.csv "1,1,1,2" "+,+,-,+" output-result.csv
```

Notes:
- `Weights` and `Impacts` are comma-separated strings (e.g., `1,1,1,2` and `+,+,-,+`).
- `Impacts` values must be `+` (benefit) or `-` (cost).

---

## Validation & Error Handling ✔️
The program checks and reports errors for:
- Wrong number of parameters (must be 4).
- File not found.
- Input file must have at least **three** columns.
- Columns from 2nd to last must be numeric.
- Number of weights, impacts, and numeric columns must match.
- Impacts must be `+` or `-`.
- Weights and impacts must be comma-separated.

---

## Input / Output Format
- Input: CSV with first column as identifier (name/ID) and remaining columns as numeric criteria.
- Output: CSV with two added columns: `Topsis Score` and `Rank`.

---

## Packaging & PyPI (Part-II) 🔧
Follow these steps to prepare and upload the package:
1. Update `setup.py` and package metadata (use the naming convention `Topsis-FirstName-RollNumber`).
2. Build distributions:
   ```bash
   python -m build
   ```
3. Upload to PyPI using `twine`:
   ```bash
   python -m twine upload dist/*
   ```
4. Verify by installing from PyPI:
   ```bash
   pip install Topsis-FirstName-RollNumber
   topsis --help
   ```

(See official guides on packaging and uploading to PyPI for full details.)

---

## Web Service (Part-III)
- Run the Flask app:

```bash
python app.py
```

- Web form accepts: CSV file, weights, impacts, and recipient email.
- The server validates input, computes results and emails the output CSV to the provided address.
- Email format is validated and weights/impacts rules are enforced as in CLI.

---

## Testing & Examples
- Test the CLI with provided sample CSV files.
- Install the built package locally and run the CLI namespace if available.
- Use the web UI to upload sample CSVs and confirm email delivery.

---

## Assumptions
- First column of CSV is a unique identifier and not used in calculations.
- We assume weights are positive numbers and impacts are `+` or `-`.
- The user will configure valid SMTP credentials in `app.py` before using the email feature.

---

## Contact / License
Include your name and roll number in `setup.py` metadata. Add a suitable LICENSE file before publishing.

> Minimal, clear, and focused — this README follows the assignment requirements for TOPSIS implementation.
