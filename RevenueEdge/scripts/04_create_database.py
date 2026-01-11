"""
Create SQLite database and join the cleaned datasets
"""

import pandas as pd
import sqlite3
from datetime import datetime
import os

print("Database Creation")
print("=" * 70)

os.makedirs('data/processed', exist_ok=True)

# Connect to SQLite database
db_path = 'data/processed/revenueedge.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print(f"\nConnected to database: {db_path}")

# Load cleaned datasets
print("\nLoading cleaned datasets...")
try:
    goodreads = pd.read_csv('data/processed/goodreads_cleaned.csv')
    print(f"Goodreads: {len(goodreads):,} rows")
except FileNotFoundError:
    print("Error: goodreads_cleaned.csv not found. Run script 02 first.")
    conn.close()
    exit(1)

try:
    bc_ratings = pd.read_csv('data/processed/bc_ratings_aggregated.csv')
    print(f"BC Ratings: {len(bc_ratings):,} rows")
except FileNotFoundError:
    print("Warning: bc_ratings_aggregated.csv not found. Run script 03 first.")
    bc_ratings = pd.DataFrame()

try:
    bc_users = pd.read_csv('data/processed/bc_users_cleaned.csv')
    print(f"BC Users: {len(bc_users):,} rows")
except FileNotFoundError:
    print("Warning: bc_users_cleaned.csv not found.")
    bc_users = pd.DataFrame()

try:
    bc_demographics = pd.read_csv('data/processed/bc_demographic_insights.csv')
    print(f"BC Demographics: {len(bc_demographics):,} rows")
except FileNotFoundError:
    print("Warning: bc_demographic_insights.csv not found.")
    bc_demographics = pd.DataFrame()

# Create tables
print("\nCreating database schema...")

# Table 1: Books
cursor.execute('''
CREATE TABLE IF NOT EXISTS books (
    book_key TEXT PRIMARY KEY,
    isbn TEXT,
    title TEXT NOT NULL,
    authors TEXT,
    goodreads_rating REAL,
    goodreads_review_count INTEGER,
    page_count INTEGER,
    publication_date TEXT,
    publisher TEXT,
    language TEXT,
    is_uk_publisher BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# Table 2: Community Ratings
cursor.execute('''
CREATE TABLE IF NOT EXISTS community_ratings (
    isbn TEXT PRIMARY KEY,
    bc_rating_avg REAL,
    bc_rating_count INTEGER,
    bc_rating_stddev REAL,
    bc_rating_median REAL,
    bc_rating_normalized REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# Table 3: Users
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    age REAL,
    age_group TEXT,
    country TEXT,
    is_uk BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# Table 4: Demographic Insights
cursor.execute('''
CREATE TABLE IF NOT EXISTS demographic_ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    isbn TEXT,
    age_group TEXT,
    rating_avg REAL,
    rating_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

print("Database schema created")

# Insert data into tables
print("\nInserting data into tables...")

goodreads.to_sql('books', conn, if_exists='replace', index=False)
print(f"Inserted {len(goodreads):,} rows into 'books' table")

if len(bc_ratings) > 0:
    bc_ratings.to_sql('community_ratings', conn, if_exists='replace', index=False)
    print(f"Inserted {len(bc_ratings):,} rows into 'community_ratings' table")

if len(bc_users) > 0:
    bc_users.to_sql('users', conn, if_exists='replace', index=False)
    print(f"Inserted {len(bc_users):,} rows into 'users' table")

if len(bc_demographics) > 0:
    bc_demographics.to_sql('demographic_ratings', conn, if_exists='replace', index=False)
    print(f"Inserted {len(bc_demographics):,} rows into 'demographic_ratings' table")

# Create indexes
print("\nCreating indexes...")

cursor.execute('CREATE INDEX IF NOT EXISTS idx_books_isbn ON books(isbn)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_books_publisher ON books(publisher)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_books_uk ON books(is_uk_publisher)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_community_isbn ON community_ratings(isbn)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_demo_isbn ON demographic_ratings(isbn)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_demo_age ON demographic_ratings(age_group)')

print("Indexes created")

# Perform SQL JOIN to create master dataset
print("\nPerforming SQL JOIN to create master dataset...")

sql_query = '''
SELECT 
    b.book_key,
    b.isbn,
    b.title,
    b.authors,
    b.goodreads_rating,
    b.goodreads_review_count,
    b.page_count,
    b.publisher,
    b.is_uk_publisher,
    c.bc_rating_normalized AS bc_rating,
    c.bc_rating_count AS bc_rating_count,
    c.bc_rating_stddev,
    (c.bc_rating_normalized - b.goodreads_rating) AS rating_gap,
    CASE 
        WHEN c.bc_rating_normalized >= 4.0 AND b.goodreads_review_count < 500 
        THEN 'Hidden Gem'
        WHEN c.bc_rating_normalized >= 4.0 AND b.goodreads_review_count >= 500 
        THEN 'Popular Favorite'
        WHEN c.bc_rating_normalized < 3.0 
        THEN 'Underperformer'
        ELSE 'Average'
    END AS book_category,
    (b.goodreads_rating * LOG(b.goodreads_review_count + 1)) AS engagement_score
FROM books b
LEFT JOIN community_ratings c ON b.isbn = c.isbn
WHERE b.is_uk_publisher = 1 OR c.isbn IS NOT NULL
ORDER BY engagement_score DESC
'''

try:
    master_dataset = pd.read_sql_query(sql_query, conn)
    print(f"Master dataset created: {len(master_dataset):,} rows")
    
    output_path = 'data/processed/master_dataset.csv'
    master_dataset.to_csv(output_path, index=False)
    print(f"Saved to: {output_path}")
    
    print("\n" + "=" * 70)
    print("Master Dataset Summary")
    print("=" * 70)
    print(f"Total books: {len(master_dataset):,}")
    print(f"Books with community ratings: {master_dataset['bc_rating'].notna().sum():,}")
    print(f"UK Publisher books: {master_dataset['is_uk_publisher'].sum():,}")
    print(f"\nBook categories:")
    if 'book_category' in master_dataset.columns:
        print(master_dataset['book_category'].value_counts())
    print("\nTop 10 books by engagement score:")
    print(master_dataset[['title', 'authors', 'goodreads_rating', 'bc_rating', 'engagement_score']].head(10))
    
except Exception as e:
    print(f"Warning: Could not create master dataset: {e}")
    print("This may be because community_ratings table is empty.")

# Close connection
conn.commit()
conn.close()

print("\n" + "=" * 70)
print("Database creation complete")
print("=" * 70)
print(f"\nDatabase saved to: {db_path}")
print("=" * 70)
