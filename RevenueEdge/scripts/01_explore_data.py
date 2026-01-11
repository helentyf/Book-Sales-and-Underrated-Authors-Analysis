"""
Initial data exploration - for checking what's in the datasets
"""

import pandas as pd
import numpy as np
import os

pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_rows', 50)

print("Data Exploration Report")
print("=" * 70)

data_dir = 'data/raw'
if not os.path.exists(data_dir):
    print(f"\nWarning: {data_dir} directory not found.")
    print("Please download datasets and place them in data/raw/")
    print("\nRequired files:")
    print("  - books.csv (Goodreads)")
    print("  - BX-Books.csv")
    print("  - BX-Users.csv")
    print("  - BX-Book-Ratings.csv")
    exit(1)

# Load Goodreads data
print("\n1. GOODREADS DATASET")
print("-" * 70)
try:
    goodreads_path = os.path.join(data_dir, 'books.csv')
    if os.path.exists(goodreads_path):
        goodreads = pd.read_csv(goodreads_path, on_bad_lines='skip', low_memory=False)
        print(f"Loaded: {len(goodreads):,} rows")
        print(f"Columns ({len(goodreads.columns)}): {list(goodreads.columns)}")
        print(f"Memory usage: {goodreads.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
        print("\nFirst 3 rows:")
        print(goodreads.head(3))
        print("\nData types:")
        print(goodreads.dtypes)
        print("\nMissing values:")
        missing = goodreads.isnull().sum()
        print(missing[missing > 0])
        print("\nBasic statistics:")
        print(goodreads.describe())
    else:
        print(f"File not found: {goodreads_path}")
except Exception as e:
    print(f"Error loading Goodreads: {e}")

# Load Book-Crossing Books
print("\n\n2. BOOK-CROSSING BOOKS DATASET")
print("-" * 70)
try:
    bc_books_path = os.path.join(data_dir, 'BX-Books.csv')
    if os.path.exists(bc_books_path):
        bc_books = pd.read_csv(bc_books_path, 
                               encoding='latin-1', 
                               sep=';', 
                               on_bad_lines='skip',
                               low_memory=False)
        print(f"Loaded: {len(bc_books):,} rows")
        print(f"Columns ({len(bc_books.columns)}): {list(bc_books.columns)}")
        print("\nFirst 3 rows:")
        print(bc_books.head(3))
        print("\nMissing values:")
        missing = bc_books.isnull().sum()
        print(missing[missing > 0])
    else:
        print(f"File not found: {bc_books_path}")
except Exception as e:
    print(f"Error loading BC Books: {e}")

# Load Book-Crossing Ratings
print("\n\n3. BOOK-CROSSING RATINGS DATASET")
print("-" * 70)
try:
    bc_ratings_path = os.path.join(data_dir, 'BX-Book-Ratings.csv')
    if os.path.exists(bc_ratings_path):
        bc_ratings = pd.read_csv(bc_ratings_path, 
                                 encoding='latin-1', 
                                 sep=';',
                                 on_bad_lines='skip',
                                 low_memory=False)
        print(f"Loaded: {len(bc_ratings):,} rows")
        print(f"Columns ({len(bc_ratings.columns)}): {list(bc_ratings.columns)}")
        print(f"\nRating distribution:")
        if 'Book-Rating' in bc_ratings.columns:
            print(bc_ratings['Book-Rating'].value_counts().sort_index())
            print(f"\nNon-zero ratings: {len(bc_ratings[bc_ratings['Book-Rating'] > 0]):,}")
            print(f"Zero ratings (implicit): {len(bc_ratings[bc_ratings['Book-Rating'] == 0]):,}")
    else:
        print(f"File not found: {bc_ratings_path}")
except Exception as e:
    print(f"Error loading BC Ratings: {e}")

# Load Book-Crossing Users
print("\n\n4. BOOK-CROSSING USERS DATASET")
print("-" * 70)
try:
    bc_users_path = os.path.join(data_dir, 'BX-Users.csv')
    if os.path.exists(bc_users_path):
        bc_users = pd.read_csv(bc_users_path, 
                              encoding='latin-1', 
                              sep=';',
                              on_bad_lines='skip',
                              low_memory=False)
        print(f"Loaded: {len(bc_users):,} rows")
        print(f"Columns ({len(bc_users.columns)}): {list(bc_users.columns)}")
        if 'Age' in bc_users.columns:
            print("\nAge distribution:")
            print(bc_users['Age'].describe())
            print(f"\nMissing ages: {bc_users['Age'].isna().sum():,}")
    else:
        print(f"File not found: {bc_users_path}")
except Exception as e:
    print(f"Error loading BC Users: {e}")

print("\n" + "=" * 70)
print("Exploration complete")
print("=" * 70)
