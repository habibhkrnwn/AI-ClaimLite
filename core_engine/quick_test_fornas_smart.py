"""
Quick Test FORNAS Smart Service
Test basic functionality tanpa batch processing
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from services.fornas_smart_service import match_drug

def quick_test():
    """Test cepat untuk verify functionality"""
    print("\n🧪 Quick Test - FORNAS Smart Service\n")
    
    test_cases = [
        ("Parasetamol", "Indonesian name (should exact match)"),
        ("paracetamol", "English name (should use AI normalize)"),
        ("Metformin", "Same in both languages"),
    ]
    
    for drug_name, description in test_cases:
        print(f"📌 Test: {drug_name}")
        print(f"   Description: {description}")
        
        try:
            result = match_drug(drug_name, use_ai=True)
            
            if result["found"]:
                print(f"   ✅ Found: {result['drug'].obat_name}")
                print(f"   Strategy: {result['strategy']}")
                print(f"   Confidence: {result['confidence']}%")
                print(f"   Kode: {result['drug'].kode_fornas}")
            else:
                print(f"   ❌ Not found in database")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
    
    print("✅ Quick test completed!\n")

if __name__ == "__main__":
    try:
        quick_test()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
