"""
Script untuk generate data mapping ICD10/ICD9 yang belum ada
Dijalankan SETELAH data cleaned_mapping_inacbg dan inacbg_tarif sudah diimport

Author: AI-ClaimLite
Date: 2025-11-18
"""

import json
from collections import defaultdict
import re
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

def get_connection():
    """Get raw database connection for executing SQL"""
    engine = create_engine(DATABASE_URL)
    return engine.raw_connection()


def get_icd10_chapter(icd10_code):
    """
    Extract chapter dari ICD10 code
    Contoh: I21.0 → I21 → chapter I (I00-I99)
    """
    if not icd10_code:
        return None, None
    
    # Ambil huruf pertama dan 2 digit pertama
    match = re.match(r'([A-Z])(\d{1,2})', icd10_code.upper())
    if not match:
        return None, None
    
    letter = match.group(1)
    number = int(match.group(2))
    
    # Return chapter start dan end
    return f"{letter}00", f"{letter}99"


def get_icd9_chapter(icd9_code):
    """
    Extract chapter dari ICD9 procedure code
    Contoh: 57.94 → chapter 55-59 (Urinary)
    """
    if not icd9_code:
        return None
    
    # Ambil 2 digit pertama
    match = re.match(r'(\d{1,2})', str(icd9_code))
    if not match:
        return None
    
    chapter_num = int(match.group(1))
    
    # ICD9 procedure chapters (simplified)
    chapters = [
        (0, 5, "00-05", "CNS procedures", "Nervous", False),
        (6, 7, "06-07", "Endocrine procedures", "Endocrine", False),
        (8, 16, "08-16", "Eye procedures", "Eye", False),
        (18, 20, "18-20", "Ear procedures", "Ear", False),
        (21, 29, "21-29", "Nose/Mouth/Pharynx", "ENT", False),
        (30, 34, "30-34", "Respiratory", "Respiratory", True),
        (35, 39, "35-39", "Cardiovascular", "Cardiovascular", True),
        (40, 41, "40-41", "Hemic/Lymphatic", "Blood", False),
        (42, 54, "42-54", "Digestive", "Digestive", True),
        (55, 59, "55-59", "Urinary", "Nephro-urinary", False),
        (60, 64, "60-64", "Male genital", "Male reproductive", False),
        (65, 71, "65-71", "Female genital", "Female reproductive", True),
        (72, 75, "72-75", "Obstetric", "Obstetric", True),
        (76, 84, "76-84", "Musculoskeletal", "Musculoskeletal", True),
        (85, 86, "85-86", "Skin/Breast", "Integumentary", False),
        (87, 99, "87-99", "Diagnostic/Therapeutic", "General", False),
    ]
    
    for start, end, chapter_range, category, body_system, is_major in chapters:
        if start <= chapter_num <= end:
            return {
                "chapter_range": chapter_range,
                "category": category,
                "body_system": body_system,
                "is_major": is_major
            }
    
    return None


def generate_icd10_cmg_mapping(conn):
    """
    Generate ICD10 → CMG mapping dari data yang ada
    """
    print("\n" + "="*80)
    print("GENERATING ICD10 → CMG MAPPING")
    print("="*80)
    
    # CMG mapping berdasarkan Permenkes
    cmg_rules = {
        'A': {'chapters': ['A', 'B'], 'description': 'Infectious & parasitic diseases'},
        'C': {'chapters': ['C'], 'description': 'Myeloproliferative & neoplasms'},
        'D': {'chapters': ['D'], 'description': 'Haemopoietic & immune system'},
        'E': {'chapters': ['E'], 'description': 'Endocrine, nutrition & metabolism'},
        'F': {'chapters': ['F'], 'description': 'Mental health & behavioral'},
        'G': {'chapters': ['G'], 'description': 'Central nervous system'},
        'H': {'chapters': ['H'], 'description': 'Eye and adnexa / Ear, nose, throat'},  # H00-H59 = Eye, H60-H95 = ENT
        'U': {'chapters': ['H'], 'description': 'Ear, nose, mouth & throat'},  # Special handling
        'I': {'chapters': ['I'], 'description': 'Cardiovascular system'},
        'J': {'chapters': ['J'], 'description': 'Respiratory system'},
        'K': {'chapters': ['K'], 'description': 'Digestive system'},
        'B': {'chapters': ['K'], 'description': 'Hepatobiliary & pancreatic'},  # K70-K87
        'L': {'chapters': ['L'], 'description': 'Skin, subcutaneous & breast'},
        'M': {'chapters': ['M'], 'description': 'Musculoskeletal & connective tissue'},
        'N': {'chapters': ['N'], 'description': 'Nephro-urinary system'},
        'V': {'chapters': ['N'], 'description': 'Male reproductive system'},  # N40-N53
        'W': {'chapters': ['N'], 'description': 'Female reproductive system'},  # N60-N99
        'O': {'chapters': ['O'], 'description': 'Deliveries'},
        'P': {'chapters': ['P'], 'description': 'Newborns & neonates'},
        'Q': {'chapters': ['Q'], 'description': 'Congenital anomalies'},
        'S': {'chapters': ['S', 'T', 'V', 'W', 'X', 'Y'], 'description': 'Injuries & poisonings'},
        'Z': {'chapters': ['Z'], 'description': 'Health status & contacts'},
    }
    
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute("DELETE FROM icd10_cmg_mapping")
    
    # Generate mapping untuk setiap CMG
    insert_count = 0
    
    for cmg, rule in cmg_rules.items():
        for chapter_letter in rule['chapters']:
            # Insert range mapping
            cursor.execute("""
                INSERT INTO icd10_cmg_mapping 
                (icd10_code, icd10_chapter_start, icd10_chapter_end, cmg, cmg_description, priority)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                None,  # icd10_code (NULL untuk range mapping)
                f"{chapter_letter}00",
                f"{chapter_letter}99",
                cmg,
                rule['description'],
                1
            ))
            insert_count += 1
    
    # Special handling untuk subdivisi
    special_mappings = [
        ('H00', 'H59', 'H', 'Eye and adnexa', 2),
        ('H60', 'H95', 'U', 'Ear, nose, mouth & throat', 2),
        ('K70', 'K77', 'B', 'Hepatobiliary & pancreatic', 2),
        ('K80', 'K87', 'B', 'Hepatobiliary & pancreatic', 2),
        ('N40', 'N53', 'V', 'Male reproductive system', 2),
        ('N60', 'N99', 'W', 'Female reproductive system', 2),
    ]
    
    for start, end, cmg, desc, priority in special_mappings:
        cursor.execute("""
            INSERT INTO icd10_cmg_mapping 
            (icd10_code, icd10_chapter_start, icd10_chapter_end, cmg, cmg_description, priority)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (None, start, end, cmg, desc, priority))
        insert_count += 1
    
    conn.commit()
    print(f"✓ Inserted {insert_count} ICD10 → CMG mappings")
    
    # Show sample
    cursor.execute("SELECT * FROM icd10_cmg_mapping LIMIT 10")
    print("\nSample data:")
    for row in cursor.fetchall():
        print(f"  {row}")


def generate_icd9_procedure_info(conn):
    """
    Generate ICD9 procedure info dari cleaned_mapping_inacbg
    """
    print("\n" + "="*80)
    print("GENERATING ICD9 PROCEDURE INFO")
    print("="*80)
    
    cursor = conn.cursor()
    
    # Get unique ICD9 codes dari cleaned_mapping_inacbg
    cursor.execute("""
        SELECT DISTINCT 
            UNNEST(string_to_array(icd9_list, ';')) as icd9_code,
            COUNT(*) as frequency
        FROM cleaned_mapping_inacbg
        WHERE icd9_list IS NOT NULL AND icd9_list != ''
        GROUP BY icd9_code
        ORDER BY frequency DESC
    """)
    
    icd9_codes = cursor.fetchall()
    print(f"Found {len(icd9_codes)} unique ICD9 codes from mapping data")
    
    # Clear existing data
    cursor.execute("DELETE FROM icd9_procedure_info")
    
    # Process each ICD9
    insert_count = 0
    for icd9_code, frequency in icd9_codes:
        icd9_code = icd9_code.strip()
        if not icd9_code:
            continue
        
        # Get chapter info
        chapter_info = get_icd9_chapter(icd9_code)
        if not chapter_info:
            print(f"⚠ Skipping {icd9_code} - unknown chapter")
            continue
        
        # Find similar codes (same chapter range)
        cursor.execute("""
            SELECT DISTINCT UNNEST(string_to_array(icd9_list, ';')) as similar_code
            FROM cleaned_mapping_inacbg
            WHERE icd9_list LIKE %s
            LIMIT 10
        """, (f"%{icd9_code[:2]}%",))
        
        similar_codes = [row[0].strip() for row in cursor.fetchall() if row[0].strip() != icd9_code]
        
        # Insert
        cursor.execute("""
            INSERT INTO icd9_procedure_info 
            (icd9_code, description, chapter_range, category, body_system, 
             is_major_procedure, procedure_type, similar_codes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (icd9_code) DO NOTHING
        """, (
            icd9_code,
            f"Procedure {icd9_code}",  # Placeholder description
            chapter_info['chapter_range'],
            chapter_info['category'],
            chapter_info['body_system'],
            chapter_info['is_major'],
            'surgical' if chapter_info['is_major'] else 'diagnostic',
            json.dumps(similar_codes[:5])  # Top 5 similar codes
        ))
        insert_count += 1
    
    conn.commit()
    print(f"✓ Inserted {insert_count} ICD9 procedure info records")
    
    # Show statistics
    cursor.execute("""
        SELECT 
            chapter_range,
            category,
            COUNT(*) as total_codes,
            SUM(CASE WHEN is_major_procedure THEN 1 ELSE 0 END) as major_count,
            SUM(CASE WHEN NOT is_major_procedure THEN 1 ELSE 0 END) as minor_count
        FROM icd9_procedure_info
        GROUP BY chapter_range, category
        ORDER BY chapter_range
    """)
    
    print("\nICD9 Distribution by Chapter:")
    print(f"{'Chapter':<12} {'Category':<30} {'Total':<8} {'Major':<8} {'Minor':<8}")
    print("-" * 70)
    for row in cursor.fetchall():
        print(f"{row[0]:<12} {row[1]:<30} {row[2]:<8} {row[3]:<8} {row[4]:<8}")


def verify_data(conn):
    """
    Verify generated data
    """
    print("\n" + "="*80)
    print("DATA VERIFICATION")
    print("="*80)
    
    cursor = conn.cursor()
    
    # Check icd10_cmg_mapping
    cursor.execute("SELECT COUNT(*) FROM icd10_cmg_mapping")
    cmg_count = cursor.fetchone()[0]
    print(f"✓ icd10_cmg_mapping: {cmg_count} records")
    
    # Check icd9_procedure_info
    cursor.execute("SELECT COUNT(*) FROM icd9_procedure_info")
    icd9_count = cursor.fetchone()[0]
    print(f"✓ icd9_procedure_info: {icd9_count} records")
    
    # Check cleaned_mapping_inacbg (should already exist)
    cursor.execute("SELECT COUNT(*) FROM cleaned_mapping_inacbg")
    mapping_count = cursor.fetchone()[0]
    print(f"✓ cleaned_mapping_inacbg: {mapping_count} records")
    
    # Check inacbg_tarif (should already exist)
    cursor.execute("SELECT COUNT(*) FROM inacbg_tarif")
    tarif_count = cursor.fetchone()[0]
    print(f"✓ inacbg_tarif: {tarif_count} records")
    
    if mapping_count == 0 or tarif_count == 0:
        print("\n⚠ WARNING: cleaned_mapping_inacbg atau inacbg_tarif masih kosong!")
        print("  Pastikan sudah import data Excel terlebih dahulu.")


def main():
    """
    Main execution
    """
    print("="*80)
    print("INA-CBG MAPPING DATA GENERATOR")
    print("AI-ClaimLite Core Engine")
    print("="*80)
    
    try:
        # Connect to database
        conn = get_connection()
        print("✓ Connected to database")
        
        # Generate mappings
        generate_icd10_cmg_mapping(conn)
        generate_icd9_procedure_info(conn)
        
        # Verify
        verify_data(conn)
        
        print("\n" + "="*80)
        print("✓ DATA GENERATION COMPLETED SUCCESSFULLY")
        print("="*80)
        
        conn.close()
        
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
