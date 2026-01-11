#!/usr/bin/env python3
"""
To run all data processing scripts in sequence
"""

import subprocess
import sys
import os
from datetime import datetime

def run_script(script_name, description):
    """Run a Python script and handle errors"""
    print("\n" + "=" * 70)
    print(f"Running: {description}")
    print("=" * 70)
    
    script_path = os.path.join('scripts', script_name)
    
    if not os.path.exists(script_path):
        print(f"Error: {script_path} not found")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            check=True,
            capture_output=False
        )
        print(f"{description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_name}: {e}")
        return False
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
        return False

def main():
    """Main execution function"""
    print("=" * 70)
    print("Complete Data Pipeline")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    if not os.path.exists('scripts'):
        print("Error: Please run this script from the RevenueEdge directory")
        print("   Current directory:", os.getcwd())
        sys.exit(1)
    
    scripts = [
        ('01_explore_data.py', 'Data Exploration'),
        ('02_clean_goodreads.py', 'Goodreads Data Cleaning'),
        ('03_clean_bookcrossing.py', 'Book-Crossing Data Cleaning'),
        ('04_create_database.py', 'Database Creation & SQL Joins'),
        ('05_analyze_data.py', 'Business Insights Analysis'),
        ('06_export_for_tableau.py', 'Tableau Export')
    ]
    
    success_count = 0
    for script_name, description in scripts:
        if run_script(script_name, description):
            success_count += 1
        else:
            print(f"\nStopping pipeline due to error in {script_name}")
            print("   You may need to download datasets or fix errors before continuing")
            break
    
    print("\n" + "=" * 70)
    print("Pipeline Execution Summary")
    print("=" * 70)
    print(f"Completed: {success_count}/{len(scripts)} steps")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if success_count == len(scripts):
        print("\nAll steps completed successfully!")
        print("\nNext Steps:")
        print("  1. Review reports in output/reports/")
        print("  2. Open Tableau and connect to output/tableau/revenueedge_master_data.csv")
    else:
        print("\nPipeline incomplete. Please review errors above.")
    
    print("=" * 70)

if __name__ == '__main__':
    main()
