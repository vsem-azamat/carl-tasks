# Carl Notes Project Overview

This repository contains several interview tasks. Each folder is a self-contained project with its own data and code. Below are instructions for each project.

## 0. Install Dependencies
There is common `requirements.txt` file that lists the dependencies for all projects, excepting second one - `2_youtube_summary`.
To install the dependencies, run:
```bash
python3 -m venv .venv
pip install -r requirements.txt
```

---

## 1. Price Predictions (`1_prices_predictions`)

- **Description:** Forecasts Czech CPI sub-indices to 2050 using various time series models.
- **How to run:**
  1. Open `note.ipynb` in Jupyter Notebook or VS Code.
  2. Run all cells sequentially.
  3. Outputs (charts, forecasts) are saved in the `figures/` folder and as `forecasts_2024_2050.csv`.

---

## 2. Youtube Summary (`2_youtube_summary`)

- **Description:** Automated YouTube comments analysis pipeline that downloads comments, performs sentiment analysis, and generates comprehensive reports.
- **How to run:**
  1. Set up environment: `export OPENAI_API_KEY='your-api-key'`
  2. Configure `config.yaml` with video URLs and analysis parameters
  3. Run the complete pipeline: `make run`
  4. Or run individual steps: `make download`, `make analyze`, `make report`
  5. Check status: `make status` and logs: `make logs`
  6. Reports are generated in the project `reports/` directory.

---

## 3. Stories Impressions Analysis (`3_stories`)

- **Description:** Analyzes Instagram Stories impressions, comparing interpolation and smoothing methods.
- **How to run:**
  1. Open `note.ipynb` in Jupyter Notebook or VS Code.
  2. Run all cells sequentially.
  3. Data is loaded from `stories.csv`.
  4. Alternatively, you can run custom scripts in `run.py` (currently empty, add your code as needed).

---

## 4. Facebook Data Processing (`4_facebook`)

- **Description:** Processes and analyzes Facebook posts data.
- **How to run:**
  1. Install dependencies: `pip install -r requirements.txt` (create this file if needed).
  2. Set your Facebook API token as an environment variable:  
     `export FB_CLIENT_TOKEN=<your_token>`
  3. Use scripts like `parser.py` and `check.py` for data processing and API checks.
  4. Data is stored in `apify.json`.

---

## 5. Simpson's Paradox Analysis (`5_simpsons_paradox`)

- **Description:** Demonstrates Simpson's paradox using Arizona University admissions data.
- **How to run:**
  1. Open `note.ipynb` in Jupyter Notebook or VS Code.
  2. Run all cells sequentially.
  3. Data is loaded from `university.csv`.

---

