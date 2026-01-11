"""
Clean Goodreads data - standardize ISBNs, handle missing values
"""

import pandas as pd
import numpy as np
import re
import os

print("Goodreads Data Cleaning")
print("=" * 70)

os.makedirs('data/processed', exist_ok=True)

# Load raw data
print("\nLoading raw data...")
try:
    goodreads = pd.read_csv('data/raw/books.csv', on_bad_lines='skip', low_memory=False)
    print(f"Loaded {len(goodreads):,} rows")
except FileNotFoundError:
    print("Error: data/raw/books.csv not found")
    print("Please download the Goodreads dataset from Kaggle and place it in data/raw/")
    exit(1)
except Exception as e:
    print(f"Error loading data: {e}")
    exit(1)

initial_rows = len(goodreads)

# Clean ISBN field
print("\nCleaning ISBN field...")

def clean_isbn(isbn):
    """Standardize ISBN format - remove hyphens, validate length"""
    if pd.isna(isbn):
        return None
    
    isbn_str = str(isbn).strip().upper()
    isbn_clean = re.sub(r'[-\s]', '', isbn_str)
    isbn_clean = re.sub(r'[^A-Z0-9]', '', isbn_clean)
    
    if len(isbn_clean) in [10, 13]:
        return isbn_clean
    else:
        return None

# Apply cleaning function
if 'isbn' in goodreads.columns:
    goodreads['isbn_clean'] = goodreads['isbn'].apply(clean_isbn)
else:
    goodreads['isbn_clean'] = None

if 'isbn13' in goodreads.columns:
    goodreads['isbn13_clean'] = goodreads['isbn13'].apply(clean_isbn)
else:
    goodreads['isbn13_clean'] = None

# Use isbn13 if available, otherwise isbn
goodreads['ISBN'] = goodreads['isbn13_clean'].fillna(goodreads['isbn_clean'])

print(f"Valid ISBNs: {goodreads['ISBN'].notna().sum():,}")
print(f"Missing ISBNs: {goodreads['ISBN'].isna().sum():,}")

# Create composite key for books without ISBN
print("\nCreating composite keys for books without ISBN...")

def create_composite_key(row):
    """Create unique identifier from title + author for books without ISBN"""
    if pd.notna(row['ISBN']):
        return row['ISBN']
    
    title = str(row.get('title', '')).strip().upper() if pd.notna(row.get('title')) else ''
    author = str(row.get('authors', '')).strip().upper() if pd.notna(row.get('authors')) else ''
    
    if title and author:
        title_clean = re.sub(r'[^A-Z0-9]', '', title)
        author_clean = re.sub(r'[^A-Z0-9]', '', author.split(',')[0])
        return f"COMP_{title_clean[:30]}_{author_clean[:20]}"
    
    return None

goodreads['book_key'] = goodreads.apply(create_composite_key, axis=1)

print(f"Total valid keys: {goodreads['book_key'].notna().sum():,}")

# Handle missing and invalid values
print("\nHandling missing values...")

goodreads_clean = goodreads[goodreads['book_key'].notna()].copy()
print(f"Removed {len(goodreads) - len(goodreads_clean):,} rows without valid identifiers")

# Clean ratings (should be 0-5 for Goodreads)
if 'average_rating' in goodreads_clean.columns:
    goodreads_clean['average_rating'] = pd.to_numeric(
        goodreads_clean['average_rating'], 
        errors='coerce'
    )
    goodreads_clean = goodreads_clean[
        (goodreads_clean['average_rating'] >= 0) & 
        (goodreads_clean['average_rating'] <= 5)
    ]

# Clean rating count
if 'ratings_count' in goodreads_clean.columns:
    goodreads_clean['ratings_count'] = pd.to_numeric(
        goodreads_clean['ratings_count'], 
        errors='coerce'
    ).fillna(0).astype(int)

# Clean page numbers
if 'num_pages' in goodreads_clean.columns:
    goodreads_clean['num_pages'] = pd.to_numeric(
        goodreads_clean['num_pages'], 
        errors='coerce'
    )
    goodreads_clean.loc[
        (goodreads_clean['num_pages'] < 10) | 
        (goodreads_clean['num_pages'] > 2000), 
        'num_pages'
    ] = np.nan

print("Invalid values cleaned")

# Publisher standardization
print("\nStandardizing publisher names...")

def standardize_publisher(publisher):
    """Standardize publisher names to improve grouping"""
    if pd.isna(publisher):
        return 'Unknown'
    
    pub = str(publisher).strip().upper()
    
    uk_publishers = {
        'PENGUIN': ['PENGUIN', 'PENGUIN BOOKS', 'PENGUIN UK', 'PENGUIN RANDOM HOUSE'],
        'BLOOMSBURY': ['BLOOMSBURY', 'BLOOMSBURY PUBLISHING'],
        'HARPERCOLLINS': ['HARPERCOLLINS', 'HARPER COLLINS', 'HARPER'],
        'MACMILLAN': ['MACMILLAN', 'PAN MACMILLAN', 'MACMILLAN UK'],
        'ORION': ['ORION', 'ORION PUBLISHING'],
        'FABER': ['FABER', 'FABER & FABER', 'FABER AND FABER'],
        'RANDOM HOUSE': ['RANDOM HOUSE', 'RANDOMHOUSE']
    }
    
    for standard_name, variations in uk_publishers.items():
        if any(var in pub for var in variations):
            return standard_name
    
    return publisher.strip()

if 'publisher' in goodreads_clean.columns:
    goodreads_clean['publisher_clean'] = goodreads_clean['publisher'].apply(standardize_publisher)
    print(f"Unique publishers: {goodreads_clean['publisher_clean'].nunique():,}")
else:
    goodreads_clean['publisher_clean'] = 'Unknown'

# UK Publisher flag
print("\nIdentifying UK publishers...")

uk_publisher_keywords = [
    'PENGUIN', 'BLOOMSBURY', 'HARPERCOLLINS', 'MACMILLAN', 
    'ORION', 'FABER', 'CANONGATE', 'HACHETTE UK'
]

goodreads_clean['is_uk_publisher'] = goodreads_clean['publisher_clean'].apply(
    lambda x: any(keyword in str(x).upper() for keyword in uk_publisher_keywords)
)

print(f"UK publishers identified: {goodreads_clean['is_uk_publisher'].sum():,} books")

# Remove duplicates
print("\nRemoving duplicates...")

initial_clean = len(goodreads_clean)
goodreads_clean = goodreads_clean.drop_duplicates(subset=['book_key'], keep='first')
print(f"Removed {initial_clean - len(goodreads_clean):,} duplicate entries")

# Select and rename columns
columns_to_keep = {
    'book_key': 'book_key',
    'ISBN': 'isbn',
    'title': 'title',
    'authors': 'authors',
    'average_rating': 'goodreads_rating',
    'ratings_count': 'goodreads_review_count',
    'num_pages': 'page_count',
    'publication_date': 'publication_date',
    'publisher_clean': 'publisher',
    'language_code': 'language',
    'is_uk_publisher': 'is_uk_publisher'
}

available_columns = {k: v for k, v in columns_to_keep.items() if k in goodreads_clean.columns}
goodreads_final = goodreads_clean[list(available_columns.keys())].rename(columns=available_columns)

for col in columns_to_keep.values():
    if col not in goodreads_final.columns:
        goodreads_final[col] = None

column_order = ['book_key', 'isbn', 'title', 'authors', 'goodreads_rating', 
                'goodreads_review_count', 'page_count', 'publication_date', 
                'publisher', 'language', 'is_uk_publisher']
goodreads_final = goodreads_final[[col for col in column_order if col in goodreads_final.columns]]

# Export cleaned data
output_path = 'data/processed/goodreads_cleaned.csv'
goodreads_final.to_csv(output_path, index=False)

print("\n" + "=" * 70)
print("Cleaning Summary")
print("=" * 70)
print(f"Initial rows:        {initial_rows:,}")
print(f"Final rows:          {len(goodreads_final):,}")
print(f"Rows removed:        {initial_rows - len(goodreads_final):,} ({(initial_rows - len(goodreads_final))/initial_rows*100:.1f}%)")
print(f"Valid ISBNs:         {goodreads_final['isbn'].notna().sum():,}")
print(f"UK Publishers:       {goodreads_final['is_uk_publisher'].sum():,}")
print(f"\nCleaned data saved to: {output_path}")
print("=" * 70)
