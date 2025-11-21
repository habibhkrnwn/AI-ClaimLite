"""
Script untuk import data cleaned_mapping_cbg dari Excel ke database
Mudah dipakai, tinggal jalankan!

Author: AI-ClaimLite
Date: 2025-11-18
"""

import pandas as pd
import psycopg2
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database_connection import get_connection


def import_cleaned_mapping(excel_file_path):
    """
    Import data dari Excel ke tabel cleaned_mapping_cbg
    
    Args:
        excel_file_path: Path ke file Excel cleaned_mapping_cbg.xlsx
    """
    
    print("="*80)
    print("IMPORT CLEANED MAPPING CBG FROM EXCEL")
    print("="*80)
    
    # Check file exists
    if not os.path.exists(excel_file_path):
        print(f"✗ ERROR: File not found: {excel_file_path}")
        return False
    
    print(f"✓ File found: {excel_file_path}")
    
    # Read Excel
    print("\nReading Excel file...")
    try:
        df = pd.read_excel(excel_file_path)
        print(f"✓ Loaded {len(df)} rows from Excel")
    except Exception as e:
        print(f"✗ ERROR reading Excel: {str(e)}")
        return False
    
    # Show columns
    print(f"\nColumns found: {list(df.columns)}")
    
    # Required columns
    required_columns = [
        'layanan', 'icd10_primary', 'icd10_secondary', 'icd10_all',
        'icd9_list', 'icd9_signature', 'kelas_raw', 'inacbg_code',
        'diagnosis_raw', 'proclist_raw'
    ]
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"⚠ WARNING: Missing columns: {missing_columns}")
        print("Continuing with available columns...")
    
    # Connect to database
    print("\nConnecting to database...")
    try:
        conn = get_connection()
        cursor = conn.cursor()
        print("✓ Connected to database")
    except Exception as e:
        print(f"✗ ERROR connecting to database: {str(e)}")
        return False
    
    # Check if table exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'cleaned_mapping_cbg'
        );
    """)
    
    if not cursor.fetchone()[0]:
        print("\n✗ ERROR: Table 'cleaned_mapping_cbg' does not exist!")
        print("Please run 'create_inacbg_tables.sql' first.")
        return False
    
    # Ask for confirmation
    print(f"\n⚠ This will insert {len(df)} rows into 'cleaned_mapping_cbg' table.")
    response = input("Continue? (y/n): ")
    if response.lower() != 'y':
        print("Import cancelled.")
        return False
    
    # Clear existing data (optional)
    response = input("\nClear existing data first? (y/n): ")
    if response.lower() == 'y':
        cursor.execute("DELETE FROM cleaned_mapping_cbg")
        print(f"✓ Cleared existing data")
    
    # Insert data
    print("\nInserting data...")
    success_count = 0
    error_count = 0
    
    for idx, row in df.iterrows():
        try:
            # Prepare values
            layanan = row.get('layanan')
            icd10_primary = row.get('icd10_primary')
            icd10_secondary = row.get('icd10_secondary') if pd.notna(row.get('icd10_secondary')) else None
            icd10_all = row.get('icd10_all') if pd.notna(row.get('icd10_all')) else None
            icd9_list = row.get('icd9_list') if pd.notna(row.get('icd9_list')) else None
            icd9_signature = row.get('icd9_signature') if pd.notna(row.get('icd9_signature')) else None
            kelas_raw = row.get('kelas_raw')
            inacbg_code = row.get('inacbg_code')
            diagnosis_raw = row.get('diagnosis_raw') if pd.notna(row.get('diagnosis_raw')) else None
            proclist_raw = row.get('proclist_raw') if pd.notna(row.get('proclist_raw')) else None
            
            # Convert numeric to string if needed
            if pd.notna(icd9_list) and isinstance(icd9_list, (int, float)):
                icd9_list = str(icd9_list)
            if pd.notna(icd9_signature) and isinstance(icd9_signature, (int, float)):
                icd9_signature = str(icd9_signature)
            if pd.notna(proclist_raw) and isinstance(proclist_raw, (int, float)):
                proclist_raw = str(proclist_raw)
            
            # Insert
            cursor.execute("""
                INSERT INTO cleaned_mapping_cbg 
                (layanan, icd10_primary, icd10_secondary, icd10_all, 
                 icd9_list, icd9_signature, kelas_raw, inacbg_code, 
                 diagnosis_raw, proclist_raw, frequency)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
            """, (
                layanan,
                icd10_primary,
                icd10_secondary,
                icd10_all,
                icd9_list,
                icd9_signature,
                kelas_raw,
                inacbg_code,
                diagnosis_raw,
                proclist_raw
            ))
            
            success_count += 1
            
            # Progress indicator
            if (idx + 1) % 100 == 0:
                print(f"  Progress: {idx + 1}/{len(df)} rows...")
                
        except Exception as e:
            error_count += 1
            print(f"\n⚠ Error at row {idx + 1}: {str(e)}")
            print(f"  Data: {row.to_dict()}")
            
            # Ask to continue
            if error_count > 10:
                response = input(f"\nToo many errors ({error_count}). Continue? (y/n): ")
                if response.lower() != 'y':
                    conn.rollback()
                    return False
    
    # Commit
    try:
        conn.commit()
        print(f"\n✓ Successfully imported {success_count} rows")
        if error_count > 0:
            print(f"⚠ {error_count} rows failed")
    except Exception as e:
        print(f"\n✗ ERROR committing transaction: {str(e)}")
        conn.rollback()
        return False
    
    # Verify
    print("\nVerifying data...")
    cursor.execute("SELECT COUNT(*) FROM cleaned_mapping_cbg")
    total_count = cursor.fetchone()[0]
    print(f"✓ Total rows in database: {total_count}")
    
    # Statistics
    cursor.execute("""
        SELECT 
            layanan,
            COUNT(*) as total,
            COUNT(DISTINCT icd10_primary) as unique_icd10,
            COUNT(DISTINCT inacbg_code) as unique_cbg
        FROM cleaned_mapping_cbg
        GROUP BY layanan
    """)
    
    print("\nStatistics by layanan:")
    print(f"{'Layanan':<10} {'Total':<10} {'Unique ICD10':<15} {'Unique CBG':<15}")
    print("-" * 50)
    for row in cursor.fetchall():
        print(f"{row[0]:<10} {row[1]:<10} {row[2]:<15} {row[3]:<15}")
    
    # Sample data
    print("\nSample data (first 5 rows):")
    cursor.execute("""
        SELECT icd10_primary, icd9_signature, layanan, inacbg_code 
        FROM cleaned_mapping_cbg 
        LIMIT 5
    """)
    
    for row in cursor.fetchall():
        print(f"  {row[0]} + {row[1]} ({row[2]}) → {row[3]}")
    
    conn.close()
    
    print("\n" + "="*80)
    print("✓ IMPORT COMPLETED SUCCESSFULLY")
    print("="*80)
    
    return True


def main():
    """
    Main execution
    """
    print("\n🚀 CLEANED MAPPING CBG IMPORTER\n")
    
    # Get file path from user or argument
    if len(sys.argv) > 1:
        excel_file = sys.argv[1]
    else:
        print("Please provide the path to cleaned_mapping_cbg.xlsx")
        print("\nUsage:")
        print("  python import_cleaned_mapping.py path/to/cleaned_mapping_cbg.xlsx")
        print("\nOr drag & drop the Excel file here and press Enter:")
        excel_file = input("> ").strip().strip('"').strip("'")
    
    if not excel_file:
        print("No file specified. Exiting.")
        return 1
    
    # Import
    success = import_cleaned_mapping(excel_file)
    
    if success:
        print("\n✓ Next step: Run generate_mapping_data.py")
        return 0
    else:
        print("\n✗ Import failed. Please check errors above.")
        return 1


if __name__ == "__main__":
    exit(main())
