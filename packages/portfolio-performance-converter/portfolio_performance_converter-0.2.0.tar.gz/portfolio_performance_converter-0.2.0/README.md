# Broker to Portfolio Performance Converter

Tool to convert exports from various brokers to a CSV format compatible with [Portfolio Performance](https://www.portfolio-performance.info/). The system automatically detects the broker format from the input files.

[![CI](https://github.com/marmol-dev/portfolio-performance-converter/actions/workflows/ci.yml/badge.svg)](https://github.com/marmol-dev/portfolio-performance-converter/actions/workflows/ci.yml)
[![Docker](https://github.com/marmol-dev/portfolio-performance-converter/actions/workflows/docker.yml/badge.svg)](https://github.com/marmol-dev/portfolio-performance-converter/actions/workflows/docker.yml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Motivation

**TL;DR:** This tool automates the transformation of bank and broker exports (often chaotic and heterogeneous) into a standardized CSV format that Portfolio Performance can import without errors.

### The Problem
[Portfolio Performance](https://www.portfolio-performance.info/) is an exceptional platform for monitoring financial assets, calculating returns, and managing investment portfolios. However, manually inputting every purchase, sale, or dividend is a tedious and error-prone task.

Although Portfolio Performance supports bulk importing via CSV files, the current financial ecosystem presents several challenges:
- **Heterogeneous Formats:** Every financial institution exports data in a different format (XLS, CSV, JSON, XML).
- **Data Inconsistency:** Column names, date formats, and decimal separators vary between brokers.
- **Incomplete Information:** Key identifiers like ISIN or Ticker Symbols are often missing, preventing Portfolio Performance from correctly identifying the asset.

### The Solution
This tool acts as an intelligent bridge. It automatically detects the source of your files, cleans the data, searches for missing identifiers (like Tickers), and unifies all information into a single CSV file perfectly compatible with Portfolio Performance.

## Installation

<details open>
<summary>🚀 <b>Docker (Recommended)</b></summary>

The easiest way to run the tool without installing Python or dependencies.

**Launch Web Interface:**
```bash
docker run --rm -p 7860:7860 ghcr.io/marmol-dev/portfolio-performance-converter:latest
```

**Run CLI:**
```bash
docker run --rm -v $(pwd):/data ghcr.io/marmol-dev/portfolio-performance-converter:latest -i /data/input.csv -o /data/output.csv
```
</details>

<details>
<summary><b>Using uvx</b></summary>

Use **uvx** (part of the [uv](https://github.com/astral-sh/uv) toolchain) to run it without manual installation.

**Launch Web Interface:**
```bash
uvx --from portfolio-performance-converter pp-converter web
```

**Run CLI:**
```bash
uvx --from portfolio-performance-converter pp-converter -i input.csv -o output.csv
```
</details>

<details>
<summary><b>Using pip</b></summary>

Install the package from PyPI:
```bash
pip install portfolio-performance-converter
```

Then run it:
```bash
# Web Interface
pp-converter web

# CLI
pp-converter -i input.csv -o output.csv
```
</details>

<details>
<summary><b>Run from Source</b></summary>

If you want to run the latest version from git without cloning:
```bash
uvx --from git+https://github.com/marmol-dev/portfolio-performance-converter portfolio-performance-converter web
```

Or if you have cloned the repository:
```bash
uv run pp-converter web
```
</details>

## Usage

### 🌐 Web Interface (Recommended)
The easiest way for most users. Just upload your files and download the result.

1. Launch the web app (see [Installation](#installation)).
2. Upload your broker export files.
3. Download the `converted.csv`.

![Web Interface Demo](docs/images/web-demo.gif)

### 💻 Command Line Interface (CLI)
Ideal for advanced users or automation.

```bash
# Basic usage
pp-converter --input <path_to_file> --output <output_file.csv>

# Multiple files
pp-converter --input file1.csv file2.xlsx --output "converted.csv"
```

### 📥 Importing into Portfolio Performance
Once you have your `converted.csv`:

1. Open Portfolio Performance.
2. Go to **File > Import > CSV Files...**
3. Select your `converted.csv` and follow the matching wizard.

![Portfolio Performance Import Demo](docs/images/pp-import-demo.gif)

## Supported Brokers

| Broker | Input Format | Detection Status | Export instructions | Example |
| :--- | :--- | :--- | :--- | :--- |
| **Binance** | CSV | ✅ Automatic | [Instructions](docs/broker/binance.md) | [Sample](tests/data/binance_sample.csv) |
| **Coinbase** | CSV | ✅ Automatic | [Instructions](docs/broker/coinbase.md) | [Sample](tests/data/coinbase_sample.csv) |
| **Inversis** | Excel / HTML | ✅ Automatic | [Instructions](docs/broker/inversis.md) | [Sample](tests/data/inversis_investments.xls) |
| **MyInvestor** | CSV | ✅ Automatic | [Instructions](docs/broker/myinvestor.md) | [Sample](tests/data/myinvestor_orders.csv) |
| **XTB** | Excel | ✅ Automatic | [Instructions](docs/broker/xtb.md) | [Sample](tests/data/xtb_account.xlsx) |

## Development

If you want to contribute or work with the source code:

### 1. Clone the repository

```bash
git clone <repository_url>
cd portfolio-performance-converter
```

### 2. Install dependencies (with uv)

We recommend using [uv](https://github.com/astral-sh/uv) for development.

```bash
uv sync
```

### 3. Running Tests

```bash
uv run pytest
```

## Project Structure

- `src/`: Main source code.
  - `converters/`: Conversion modules for each broker.
  - `utils.py`: Shared utility functions.
  - `market_data.py`: Interaction with Yahoo Finance.
  - `main.py`: Unified CLI entry point.
  - `app.py`: Web graphical interface (Gradio).
- `config.yaml`: Configuration of overrides for ISINs/Symbols.
