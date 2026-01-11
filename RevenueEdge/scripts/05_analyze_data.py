"""
Generate analysis reports from the master dataset
"""

import pandas as pd
import numpy as np
import sqlite3
import os
from datetime import datetime

print("Business Insights Analysis")
print("=" * 70)

os.makedirs('output/reports', exist_ok=True)

# Load master dataset
print("\nLoading master dataset...")
try:
    master = pd.read_csv('data/processed/master_dataset.csv')
    print(f"Loaded {len(master):,} rows")
except FileNotFoundError:
    print("Error: master_dataset.csv not found. Run script 04 first.")
    exit(1)

# Connect to database for additional queries
db_path = 'data/processed/revenueedge.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
else:
    conn = None
    print("Warning: Database not found. Some analyses may be limited.")

# Analysis 1: UK Publisher Performance
print("\nAnalyzing UK Publisher Performance...")

uk_publishers = master[master['is_uk_publisher'] == True].copy()

if len(uk_publishers) > 0:
    publisher_performance = uk_publishers.groupby('publisher').agg({
        'goodreads_rating': ['mean', 'count', 'std'],
        'goodreads_review_count': 'mean',
        'bc_rating': 'mean',
        'engagement_score': 'mean'
    }).round(2)
    
    publisher_performance.columns = ['avg_rating', 'book_count', 'rating_std', 
                                     'avg_reviews', 'avg_bc_rating', 'avg_engagement']
    publisher_performance = publisher_performance.sort_values('avg_engagement', ascending=False)
    
    print("\nTop UK Publishers by Engagement Score:")
    print(publisher_performance.head(10))
    
    publisher_performance.to_csv('output/reports/uk_publisher_performance.csv')
    print(f"Saved: output/reports/uk_publisher_performance.csv")
else:
    print("No UK publisher data available")

# Analysis 2: Rating Gap Analysis
print("\nAnalyzing Rating Gaps...")

rating_comparison = master[master['bc_rating'].notna()].copy()

if len(rating_comparison) > 0:
    rating_comparison['rating_difference'] = rating_comparison['bc_rating'] - rating_comparison['goodreads_rating']
    
    community_favorites = rating_comparison[
        rating_comparison['rating_difference'] > 0.5
    ].sort_values('rating_difference', ascending=False)
    
    goodreads_favorites = rating_comparison[
        rating_comparison['rating_difference'] < -0.5
    ].sort_values('rating_difference', ascending=True)
    
    print(f"\nBooks where community rates significantly higher ({len(community_favorites)}):")
    print(community_favorites[['title', 'authors', 'goodreads_rating', 'bc_rating', 'rating_difference']].head(10))
    
    print(f"\nBooks where Goodreads rates significantly higher ({len(goodreads_favorites)}):")
    print(goodreads_favorites[['title', 'authors', 'goodreads_rating', 'bc_rating', 'rating_difference']].head(10))
    
    rating_comparison.to_csv('output/reports/rating_comparison.csv', index=False)
    print(f"Saved: output/reports/rating_comparison.csv")
else:
    print("No rating comparison data available")

# Analysis 3: Hidden Gems Analysis
print("\nIdentifying Hidden Gems...")

hidden_gems = master[
    (master['bc_rating'] >= 4.0) & 
    (master['goodreads_review_count'] < 500) &
    (master['bc_rating_count'] >= 20)
].sort_values('bc_rating', ascending=False)

if len(hidden_gems) > 0:
    print(f"\nFound {len(hidden_gems)} hidden gems (high community rating, low Goodreads reviews):")
    print(hidden_gems[['title', 'authors', 'goodreads_rating', 'bc_rating', 
                      'goodreads_review_count', 'bc_rating_count']].head(15))
    
    hidden_gems.to_csv('output/reports/hidden_gems.csv', index=False)
    print(f"Saved: output/reports/hidden_gems.csv")
else:
    print("No hidden gems found with current criteria")

# Analysis 4: Demographic Insights
print("\nAnalyzing Demographic Preferences...")

if conn:
    try:
        demo_query = '''
        SELECT 
            dr.age_group,
            COUNT(DISTINCT dr.isbn) as book_count,
            AVG(dr.rating_avg) as avg_rating,
            SUM(dr.rating_count) as total_ratings
        FROM demographic_ratings dr
        GROUP BY dr.age_group
        ORDER BY avg_rating DESC
        '''
        demo_insights = pd.read_sql_query(demo_query, conn)
        
        if len(demo_insights) > 0:
            print("\nRating preferences by age group:")
            print(demo_insights)
            demo_insights.to_csv('output/reports/demographic_insights.csv', index=False)
            print(f"Saved: output/reports/demographic_insights.csv")
        else:
            print("No demographic data available")
    except Exception as e:
        print(f"Could not analyze demographics: {e}")

# Analysis 5: Statistical Summary
print("\nGenerating Statistical Summary...")

summary_stats = {
    'metric': [
        'Total Books',
        'Books with Community Ratings',
        'UK Publisher Books',
        'Average Goodreads Rating',
        'Average Community Rating',
        'Books with Rating Gap > 0.5',
        'Hidden Gems Identified'
    ],
    'value': [
        len(master),
        master['bc_rating'].notna().sum(),
        master['is_uk_publisher'].sum(),
        master['goodreads_rating'].mean(),
        master['bc_rating'].mean() if master['bc_rating'].notna().any() else None,
        len(rating_comparison[rating_comparison['rating_difference'] > 0.5]) if len(rating_comparison) > 0 else 0,
        len(hidden_gems)
    ]
}

summary_df = pd.DataFrame(summary_stats)
print("\n" + "=" * 70)
print("Executive Summary")
print("=" * 70)
print(summary_df.to_string(index=False))
summary_df.to_csv('output/reports/executive_summary.csv', index=False)
print(f"\nSaved: output/reports/executive_summary.csv")

# Generate comprehensive report
report_path = 'output/reports/analysis_report.txt'
with open(report_path, 'w') as f:
    f.write("=" * 70 + "\n")
    f.write("ANALYSIS REPORT\n")
    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write("=" * 70 + "\n\n")
    
    f.write("EXECUTIVE SUMMARY\n")
    f.write("-" * 70 + "\n")
    f.write(summary_df.to_string(index=False))
    f.write("\n\n")
    
    if len(uk_publishers) > 0:
        f.write("TOP UK PUBLISHERS\n")
        f.write("-" * 70 + "\n")
        f.write(publisher_performance.head(10).to_string())
        f.write("\n\n")
    
    if len(hidden_gems) > 0:
        f.write("TOP HIDDEN GEMS\n")
        f.write("-" * 70 + "\n")
        f.write(hidden_gems[['title', 'authors', 'bc_rating', 'goodreads_review_count']].head(10).to_string())
        f.write("\n\n")

print(f"\nComprehensive report saved: {report_path}")

if conn:
    conn.close()

print("\n" + "=" * 70)
print("Analysis complete")
print("=" * 70)
print("\nGenerated Reports:")
print("  - Executive Summary")
print("  - UK Publisher Performance")
print("  - Rating Comparison")
print("  - Hidden Gems")
print("  - Demographic Insights (if available)")
print("=" * 70)
