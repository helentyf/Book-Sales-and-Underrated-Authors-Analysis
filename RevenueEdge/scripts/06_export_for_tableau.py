"""
Export data in Tableau-ready format
"""

import pandas as pd
import os
from datetime import datetime

print("Tableau Export")
print("=" * 70)

os.makedirs('output/tableau', exist_ok=True)

# Load master dataset
print("\nLoading master dataset...")
try:
    master = pd.read_csv('data/processed/master_dataset.csv')
    print(f"Loaded {len(master):,} rows")
except FileNotFoundError:
    print("Error: master_dataset.csv not found. Run previous scripts first.")
    exit(1)

# Prepare Tableau-ready dataset
print("\nPreparing Tableau-ready dataset...")

column_mapping = {
    'book_key': 'Book Key',
    'isbn': 'ISBN',
    'title': 'Title',
    'authors': 'Authors',
    'goodreads_rating': 'Goodreads Rating',
    'goodreads_review_count': 'Goodreads Review Count',
    'bc_rating': 'Community Rating',
    'bc_rating_count': 'Community Rating Count',
    'bc_rating_stddev': 'Rating Std Dev',
    'rating_gap': 'Rating Gap',
    'book_category': 'Book Category',
    'engagement_score': 'Engagement Score',
    'publisher': 'Publisher',
    'is_uk_publisher': 'Is UK Publisher',
    'page_count': 'Page Count',
    'language': 'Language'
}

available_columns = {k: v for k, v in column_mapping.items() if k in master.columns}
tableau_data = master[list(available_columns.keys())].copy()

tableau_data.columns = [available_columns[col] for col in tableau_data.columns]

# Fill missing values
tableau_data['Community Rating'] = tableau_data['Community Rating'].fillna(0)
tableau_data['Community Rating Count'] = tableau_data['Community Rating Count'].fillna(0)
tableau_data['Rating Gap'] = tableau_data['Rating Gap'].fillna(0)
tableau_data['Book Category'] = tableau_data['Book Category'].fillna('No Category')

if 'Is UK Publisher' in tableau_data.columns:
    tableau_data['Is UK Publisher'] = tableau_data['Is UK Publisher'].fillna(0)
    tableau_data['Is UK Publisher'] = tableau_data['Is UK Publisher'].apply(
        lambda x: 'True' if x == 1 or x == True or str(x).lower() == 'true' else 'False'
    )

if 'Community Rating' in tableau_data.columns:
    tableau_data['Has Community Rating'] = tableau_data['Community Rating'] > 0
if 'Rating Gap' in tableau_data.columns:
    tableau_data['Rating Difference Abs'] = abs(tableau_data['Rating Gap'])

# Export to CSV
csv_path = 'output/tableau/revenueedge_master_data.csv'
tableau_data.to_csv(csv_path, index=False)
print(f"Saved CSV: {csv_path}")

# Export to Excel
print("\nExporting to Excel...")
excel_path = 'output/tableau/revenueedge_master_data.xlsx'

with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
    tableau_data.to_excel(writer, sheet_name='Master Data', index=False)
    
    summary = pd.DataFrame({
        'Metric': [
            'Total Books',
            'Books with Community Ratings',
            'UK Publisher Books',
            'Average Goodreads Rating',
            'Average Community Rating',
            'Hidden Gems',
            'Popular Favorites'
        ],
        'Value': [
            len(tableau_data),
            tableau_data['Has Community Rating'].sum(),
            tableau_data['Is UK Publisher'].sum(),
            tableau_data['Goodreads Rating'].mean(),
            tableau_data[tableau_data['Community Rating'] > 0]['Community Rating'].mean(),
            len(tableau_data[tableau_data['Book Category'] == 'Hidden Gem']),
            len(tableau_data[tableau_data['Book Category'] == 'Popular Favorite'])
        ]
    })
    summary.to_excel(writer, sheet_name='Summary', index=False)
    
    if 'Publisher' in tableau_data.columns:
        publisher_stats = tableau_data.groupby('Publisher').agg({
            'Goodreads Rating': 'mean',
            'Goodreads Review Count': 'mean',
            'Engagement Score': 'mean',
            'Title': 'count'
        }).round(2)
        publisher_stats.columns = ['Avg Rating', 'Avg Reviews', 'Avg Engagement', 'Book Count']
        publisher_stats = publisher_stats.sort_values('Avg Engagement', ascending=False)
        publisher_stats.to_excel(writer, sheet_name='Publisher Performance', index=True)

print(f"Saved Excel: {excel_path}")

# Create Tableau documentation
print("\nCreating Tableau documentation...")

doc_path = 'output/tableau/TABLEAU_SETUP_GUIDE.md'
with open(doc_path, 'w') as f:
    f.write("# Tableau Setup Guide\n\n")
    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    f.write("## Data Source\n\n")
    f.write("1. Open Tableau Public\n")
    f.write("2. Connect to Text File\n")
    f.write(f"3. Select: `output/tableau/revenueedge_master_data.csv`\n\n")
    f.write("## Recommended Visualizations\n\n")
    f.write("### 1. Publisher Performance Dashboard\n")
    f.write("- Bar chart of Publisher vs Average Engagement Score\n")
    f.write("- Filter: Is UK Publisher = True\n")
    f.write("- Color: By Book Category\n\n")
    f.write("### 2. Rating Comparison Scatter Plot\n")
    f.write("- X-axis: Goodreads Rating\n")
    f.write("- Y-axis: Community Rating\n")
    f.write("- Size: Goodreads Review Count\n")
    f.write("- Color: Book Category\n\n")
    f.write("### 3. Hidden Gems Table\n")
    f.write("- Filter: Book Category = 'Hidden Gem'\n")
    f.write("- Sort: By Community Rating (Descending)\n")
    f.write("- Columns: Title, Authors, Community Rating, Goodreads Review Count\n\n")
    f.write("## Key Metrics\n\n")
    f.write("- **Engagement Score**: Combines rating and review count\n")
    f.write("- **Rating Gap**: Difference between community and Goodreads ratings\n")
    f.write("- **Book Category**: Hidden Gem, Popular Favorite, Underperformer, Average\n\n")

print(f"Saved documentation: {doc_path}")

print("\n" + "=" * 70)
print("Tableau export complete")
print("=" * 70)
print(f"\nFiles ready for Tableau:")
print(f"  - CSV: {csv_path}")
print(f"  - Excel: {excel_path}")
print(f"  - Guide: {doc_path}")
print("=" * 70)
