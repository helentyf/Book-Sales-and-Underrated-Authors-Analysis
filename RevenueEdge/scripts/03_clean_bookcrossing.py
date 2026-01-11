"""
Clean Book-Crossing data - aggregate ratings by ISBN, clean user demographics
"""

import pandas as pd
import numpy as np
import re
import os

print("Book-Crossing Data Cleaning")
print("=" * 70)

os.makedirs('data/processed', exist_ok=True)

# Load raw Book-Crossing data
print("\nLoading raw Book-Crossing datasets...")

try:
    bc_books = pd.read_csv('data/raw/BX-Books.csv', 
                           encoding='latin-1', 
                           sep=';', 
                           on_bad_lines='skip',
                           low_memory=False)
    print(f"Books loaded: {len(bc_books):,} rows")
except FileNotFoundError:
    print("Error: data/raw/BX-Books.csv not found")
    print("Please download the Book-Crossing dataset from Kaggle")
    exit(1)
except Exception as e:
    print(f"Error loading books: {e}")
    exit(1)

try:
    bc_ratings = pd.read_csv('data/raw/BX-Book-Ratings.csv', 
                             encoding='latin-1', 
                             sep=';',
                             on_bad_lines='skip',
                             low_memory=False)
    print(f"Ratings loaded: {len(bc_ratings):,} rows")
except FileNotFoundError:
    print("Error: data/raw/BX-Book-Ratings.csv not found")
    exit(1)
except Exception as e:
    print(f"Error loading ratings: {e}")
    exit(1)

try:
    bc_users = pd.read_csv('data/raw/BX-Users.csv', 
                           encoding='latin-1', 
                           sep=';',
                           on_bad_lines='skip',
                           low_memory=False)
    print(f"Users loaded: {len(bc_users):,} rows")
except FileNotFoundError:
    print("Error: data/raw/BX-Users.csv not found")
    exit(1)
except Exception as e:
    print(f"Error loading users: {e}")
    exit(1)

# Clean ISBN in books dataset
print("\nCleaning ISBNs in books dataset...")

def clean_isbn(isbn):
    """Standardize ISBN format"""
    if pd.isna(isbn):
        return None
    isbn_str = str(isbn).strip().upper()
    isbn_clean = re.sub(r'[-\s]', '', isbn_str)
    isbn_clean = re.sub(r'[^A-Z0-9]', '', isbn_clean)
    if len(isbn_clean) in [10, 13]:
        return isbn_clean
    return None

if 'ISBN' in bc_books.columns:
    bc_books['isbn_clean'] = bc_books['ISBN'].apply(clean_isbn)
    bc_books_clean = bc_books[bc_books['isbn_clean'].notna()].copy()
    print(f"Valid ISBNs: {len(bc_books_clean):,}")
    print(f"Removed: {len(bc_books) - len(bc_books_clean):,} rows without valid ISBN")
else:
    print("Error: 'ISBN' column not found in BX-Books.csv")
    exit(1)

# Filter ratings (remove implicit ratings = 0)
print("\nFiltering explicit ratings...")

if 'Book-Rating' in bc_ratings.columns:
    bc_ratings_explicit = bc_ratings[bc_ratings['Book-Rating'] > 0].copy()
    print(f"Explicit ratings (1-10): {len(bc_ratings_explicit):,}")
    print(f"Removed implicit ratings (0): {len(bc_ratings) - len(bc_ratings_explicit):,}")
    print(f"\nRating distribution:")
    print(bc_ratings_explicit['Book-Rating'].value_counts().sort_index())
else:
    print("Error: 'Book-Rating' column not found")
    exit(1)

# Clean ISBNs in ratings
print("\nCleaning ISBNs in ratings dataset...")

if 'ISBN' in bc_ratings_explicit.columns:
    bc_ratings_explicit['isbn_clean'] = bc_ratings_explicit['ISBN'].apply(clean_isbn)
    bc_ratings_clean = bc_ratings_explicit[bc_ratings_explicit['isbn_clean'].notna()].copy()
    print(f"Ratings with valid ISBN: {len(bc_ratings_clean):,}")
else:
    print("Error: 'ISBN' column not found in ratings")
    exit(1)

# Aggregate ratings by ISBN
print("\nAggregating ratings by ISBN...")

bc_aggregated = bc_ratings_clean.groupby('isbn_clean').agg({
    'Book-Rating': ['mean', 'count', 'std', 'median']
}).reset_index()

bc_aggregated.columns = ['isbn', 'bc_rating_avg', 'bc_rating_count', 'bc_rating_stddev', 'bc_rating_median']

# Convert 1-10 scale to 1-5 scale (to match Goodreads)
bc_aggregated['bc_rating_normalized'] = bc_aggregated['bc_rating_avg'] / 2

# Filter out books with fewer than 10 ratings
bc_aggregated_filtered = bc_aggregated[bc_aggregated['bc_rating_count'] >= 10].copy()

print(f"Unique books with ratings: {len(bc_aggregated):,}")
print(f"Books with >=10 ratings: {len(bc_aggregated_filtered):,}")
print(f"\nAggregated statistics:")
print(bc_aggregated_filtered.describe())

# User demographics cleaning
print("\nCleaning user demographics...")

bc_users_clean = bc_users.copy()

# Clean age field
if 'Age' in bc_users_clean.columns:
    bc_users_clean['Age'] = pd.to_numeric(bc_users_clean['Age'], errors='coerce')
    
    # Remove unrealistic ages
    bc_users_clean.loc[(bc_users_clean['Age'] < 10) | (bc_users_clean['Age'] > 100), 'Age'] = np.nan
    
    # Create age groups
    def categorize_age(age):
        if pd.isna(age):
            return 'Unknown'
        elif age < 26:
            return '18-25'
        elif age < 36:
            return '26-35'
        elif age < 51:
            return '36-50'
        elif age < 66:
            return '51-65'
        else:
            return '66+'
    
    bc_users_clean['age_group'] = bc_users_clean['Age'].apply(categorize_age)
else:
    bc_users_clean['Age'] = np.nan
    bc_users_clean['age_group'] = 'Unknown'

# Extract country from location
if 'Location' in bc_users_clean.columns:
    bc_users_clean['country'] = bc_users_clean['Location'].apply(
        lambda x: str(x).split(',')[-1].strip().upper() if pd.notna(x) else 'Unknown'
    )
    
    bc_users_clean['is_uk'] = bc_users_clean['country'].isin(['UK', 'UNITED KINGDOM', 'ENGLAND', 'SCOTLAND', 'WALES'])
else:
    bc_users_clean['country'] = 'Unknown'
    bc_users_clean['is_uk'] = False

print(f"Users cleaned: {len(bc_users_clean):,}")
print(f"UK users: {bc_users_clean['is_uk'].sum():,}")
print(f"\nAge group distribution:")
print(bc_users_clean['age_group'].value_counts())

# Join ratings with users to get demographics
print("\nCreating demographic-enriched ratings...")

if 'User-ID' in bc_ratings_clean.columns and 'User-ID' in bc_users_clean.columns:
    ratings_with_users = bc_ratings_clean.merge(
        bc_users_clean[['User-ID', 'age_group', 'country', 'is_uk']], 
        on='User-ID', 
        how='left'
    )
    
    # Aggregate by ISBN and demographics
    demographic_insights = ratings_with_users.groupby(['isbn_clean', 'age_group']).agg({
        'Book-Rating': ['mean', 'count']
    }).reset_index()
    
    demographic_insights.columns = ['isbn', 'age_group', 'rating_avg', 'rating_count']
    demographic_insights = demographic_insights[demographic_insights['rating_count'] >= 5]
else:
    print("Warning: Cannot create demographic insights (missing User-ID column)")
    demographic_insights = pd.DataFrame(columns=['isbn', 'age_group', 'rating_avg', 'rating_count'])
    ratings_with_users = bc_ratings_clean.copy()

# Export cleaned datasets
print("\n" + "=" * 70)
print("Exporting cleaned datasets")
print("=" * 70)

bc_aggregated_filtered.to_csv('data/processed/bc_ratings_aggregated.csv', index=False)
print(f"Saved: data/processed/bc_ratings_aggregated.csv ({len(bc_aggregated_filtered):,} rows)")

bc_users_clean.to_csv('data/processed/bc_users_cleaned.csv', index=False)
print(f"Saved: data/processed/bc_users_cleaned.csv ({len(bc_users_clean):,} rows)")

demographic_insights.to_csv('data/processed/bc_demographic_insights.csv', index=False)
print(f"Saved: data/processed/bc_demographic_insights.csv ({len(demographic_insights):,} rows)")

ratings_with_users.to_csv('data/processed/bc_ratings_with_demographics.csv', index=False)
print(f"Saved: data/processed/bc_ratings_with_demographics.csv ({len(ratings_with_users):,} rows)")

print("\n" + "=" * 70)
print("Book-Crossing cleaning complete")
print("=" * 70)
