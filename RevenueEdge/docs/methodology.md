# Methodology Documentation

Notes on how the data cleaning and analysis was done.

## Data Sources

- **Goodreads Books**: Kaggle dataset with ~10,000 books
- **Book-Crossing Dataset**: Kaggle dataset with ~270,000 ratings from ~278,000 users

## Data Cleaning Steps

### ISBN Standardization

ISBNs came in different formats (with/without hyphens, ISBN-10 vs ISBN-13). I standardized them by:
1. Removing all hyphens, spaces, and special characters
2. Converting to uppercase
3. Validating length (must be 10 or 13 characters)
4. Using ISBN-13 when available, falling back to ISBN-10

### Composite Key Creation

Some books didn't have valid ISBNs, so I created composite keys from title + author:
- Format: `COMP_{title_clean}_{author_clean}`
- Removed special characters and limited length for consistency

### Missing Value Handling

- **ISBNs**: Created composite keys for missing ISBNs
- **Ratings**: Removed invalid ratings (outside 0-5 range)
- **Pages**: Removed unrealistic values (< 10 or > 2000 pages)
- **Ages**: Removed unrealistic ages (< 10 or > 100 years)

### Publisher Standardization

Same publisher appeared with variations (e.g., "Penguin", "Penguin Books", "Penguin UK"). I standardized to canonical names using keyword matching to improve grouping.

### Rating Aggregation

Aggregated Book-Crossing ratings by ISBN:
- Calculated mean, count, standard deviation, median
- Filtered for statistical significance (≥10 ratings)
- Normalized 1-10 scale to 1-5 scale for comparison with Goodreads

## SQL Database Design

### Schema

**books** (Primary table)
- Primary Key: `book_key`
- Indexes: `isbn`, `publisher`, `is_uk_publisher`

**community_ratings** (Ratings aggregations)
- Primary Key: `isbn`
- Index: `isbn`

**users** (User demographics)
- Primary Key: `user_id`

**demographic_ratings** (Age-group preferences)
- Primary Key: `id` (auto-increment)
- Indexes: `isbn`, `age_group`

### Key SQL Query

Master dataset join:
```sql
SELECT 
    b.*,
    c.bc_rating_normalized,
    (c.bc_rating_normalized - b.goodreads_rating) AS rating_gap,
    CASE 
        WHEN c.bc_rating_normalized >= 4.0 AND b.goodreads_review_count < 500 
        THEN 'Hidden Gem'
        ...
    END AS book_category
FROM books b
LEFT JOIN community_ratings c ON b.isbn = c.isbn
```

## Analytical Methods

### Engagement Score

Formula: `rating * LOG(review_count + 1)`

This balances rating quality with review volume. The logarithmic scaling prevents high-review-count bias.

### Book Categorization

- **Hidden Gem**: High community rating (≥4.0), low Goodreads reviews (<500)
- **Popular Favorite**: High rating (≥4.0), high reviews (≥500)
- **Underperformer**: Low community rating (<3.0)
- **Average**: All others

### Rating Gap Analysis

Metric: `Community Rating - Goodreads Rating`

- Positive gap: Community rates higher
- Negative gap: Goodreads rates higher
- Large gaps (>0.5): Significant difference worth investigating

## Data Quality Checks

1. ISBN format validation
2. Rating range validation (0-5)
3. Age range validation (10-100)
4. Page count validation (10-2000)
5. Duplicate removal based on `book_key`
6. Minimum 10 ratings for aggregated metrics
7. Minimum 5 ratings per demographic segment

## Limitations

1. Not all books have both Goodreads and community ratings
2. Book-Crossing (1-10) normalized to Goodreads (1-5) scale
3. UK publisher detection based on keyword matching
4. Datasets may be from different time periods
