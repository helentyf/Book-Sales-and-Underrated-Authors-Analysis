# Book Sales and Underrated Authors Analysis

This project analyzes book ratings and reader behavior by combining Goodreads and Book-Crossing datasets.
The goal is to identify highly rated but under-recognized books and explore patterns across publication years, genres, and user demographics.

# Main Research Questions

Which highly-rated books receive disproportionately fewer ratings?
What patterns exist across publication years, genres, and author profiles?
How do user demographics correlate with rating behavior?

# Tools Used

1. **Python** (pandas, numpy) - Data manipulation, cleaning, and analysis
2. **SQL** (SQLite) - Database creation and complex queries for data joins
3. **Data visualization:** Tableau - Interactive dashboards and visualizations
4. **File formats:** CSV, Excel (openpyxl) - Data storage and export formats

# Project Summary

This project cleans and integrates Goodreads and Book-Crossing data to surface high-potential books and publishers. The analysis focuses on identifying highly rated books with low visibility and translating those findings into a sales-oriented strategy.

Key outputs:
- Cleaned, standardized datasets with reliable identifiers and consistent rating scales.
- A master dataset with engagement and rating gap metrics for opportunity analysis.
- Two interactive Tableau dashboards that move from discovery to action.

# Tableau Dashboards

Tableau Public links:
- **Dashboard 2 – Actionable Sales Strategy**: https://public.tableau.com/views/Dashboard2-SalesStrategy/Dashboard2SalesStrategy?:language=en-GB&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link
- **Dashboard 1 – Hidden Gems Discovery**: https://public.tableau.com/views/Dashboard1-HiddenGemsDiscovery/Dashboard1-HiddenGemsDiscovery?:language=en-GB&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link

Dashboards included:
- **Hidden Gems Discovery**: Define what counts as a hidden gem using sliders, then explore which publishers and books stand out.
- **Actionable Sales Strategy**: Compare engagement and rating gaps, and select priority books to build a focused sales list.

# Data Sources

Two datasets are referenced for comparison in this analysis:

- **Goodreads Books** - approximately 11k books with ratings and metadata (~77MB)
- **Book-Crossing** - user ratings and demographic data

## Download Instructions

### Goodreads Books Dataset

**Dataset Link:** https://www.kaggle.com/datasets/jealousleopard/goodreadsbooks

**Dataset Details:**
- **Size:** ~77MB
- **Records:** 11,000+ books
- **Contents:** Ratings, reviews, publishers, authors, ISBNs, publication dates, page counts, language codes

**Download Methods:**

1. **Via Kaggle Website:**
   - Visit: https://www.kaggle.com/datasets/jealousleopard/goodreadsbooks
   - Sign in to your Kaggle account (create one if needed)
   - Click the "Download" button
   - Extract the ZIP file and locate `books.csv` (~77MB)
   - Place `books.csv` in `data/raw/` directory

2. **Via Kaggle API:**
   ```bash
   pip install kaggle
   # Configure API credentials (place kaggle.json in ~/.kaggle/)
   kaggle datasets download jealousleopard/goodreadsbooks
   unzip goodreadsbooks.zip
   # Move books.csv to data/raw/
   mv books.csv data/raw/
   ```

### Book-Crossing Dataset

**Kaggle Dataset:** Search for "Book-Crossing Dataset" on Kaggle or visit: https://www.kaggle.com/datasets

**Download Methods:**

1. **Via Kaggle Website:**
   - Search for "Book-Crossing Dataset" on Kaggle
   - Download the dataset containing:
     - `BX-Books.csv`
     - `BX-Users.csv`
     - `BX-Book-Ratings.csv`
   - Extract the files

2. **Via Kaggle API:**
   ```bash
   # Find the dataset identifier and download
   kaggle datasets download [dataset-identifier]
   unzip [downloaded-file].zip
   ```

### Place Files in Project

After downloading, place the files in `data/raw/`:

```
data/raw/
  ├── books.csv
  ├── BX-Books.csv
  ├── BX-Users.csv
  └── BX-Book-Ratings.csv
```

# Setup and Installation

Requirements: Python 3.8+ and dependencies listed in requirements.txt
```bash
pip install -r requirements.txt
```

## Running the Analysis

**Option 1: Run all scripts sequentially**
```bash
python run_all.py
```

**Option 2: Run individual scripts (useful for checking intermediate results)**
```bash
python scripts/01_explore_data.py
python scripts/02_clean_goodreads.py
python scripts/03_clean_bookcrossing.py
python scripts/04_create_database.py
python scripts/05_analyze_data.py
python scripts/06_export_for_tableau.py
```

Note: The Book-Crossing cleaning script takes 3-5 minutes to process due to dataset volume and encoding inconsistencies.

# Project Structure

```
data/raw/          # Original downloaded datasets
data/processed/    # Cleaned CSV files and SQLite database
scripts/           # Python scripts for ETL and analysis
output/reports/    # Analysis results and summary statistics
output/tableau/    # Prepared data exports for visualization
```

## Output Files

The pipeline generates:

- Cleaned datasets in `data/processed/`
- Combined SQLite database with normalized schema
- Analysis reports (CSV format) showing underrated books, rating distributions, and user patterns
- Tableau-ready data exports in `output/tableau/`

# Technical Notes

## Data quality challenges encountered:

- Book-Crossing dataset contains significant inconsistencies in ISBN formatting and character encoding
- Cross-dataset book matching required fuzzy logic due to title format variations (different punctuation, subtitle handling)
- SQLite proved more efficient than pandas for complex aggregation queries at this scale

## Design decisions:

- Minimum rating threshold of 10 reviews applied to reduce noise in underrated book identification
- Latin-1 encoding used for Book-Crossing files due to legacy format
- Fuzzy matching with 85% confidence threshold balances accuracy and coverage
