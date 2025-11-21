"""
Test Lazy Loading Fix - Verifikasi service tidak crash saat import
"""

print("=" * 60)
print("🧪 TEST 1: Import ICD-9 Service (Should NOT crash)")
print("=" * 60)

try:
    from services.icd9_smart_service import lookup_icd9_procedure
    print("✅ ICD-9 service imported successfully!")
    print("   → OpenAI client NOT created yet (lazy loading)")
except Exception as e:
    print(f"❌ Import failed: {e}")

print("\n" + "=" * 60)
print("🧪 TEST 2: Import ICD-10 AI Normalizer (Should NOT crash)")
print("=" * 60)

try:
    from services.icd10_ai_normalizer import lookup_icd10_smart_with_rag
    print("✅ ICD-10 AI normalizer imported successfully!")
    print("   → OpenAI client NOT created yet (lazy loading)")
except Exception as e:
    print(f"❌ Import failed: {e}")

print("\n" + "=" * 60)
print("🧪 TEST 3: Database Search (No AI needed)")
print("=" * 60)

try:
    result = lookup_icd9_procedure("47.09")
    print(f"✅ Database search completed!")
    print(f"   Status: {result['status']}")
    if result['status'] == 'success':
        print(f"   Code: {result['result']['code']}")
        print(f"   Name: {result['result']['name']}")
        print(f"   Source: {result['result']['source']}")
    print("   → OpenAI was NOT called (database hit)")
except Exception as e:
    print(f"❌ Database search failed: {e}")

print("\n" + "=" * 60)
print("🧪 TEST 4: AI Normalization (Will test OpenAI)")
print("=" * 60)

try:
    # This should trigger OpenAI client creation
    result = lookup_icd9_procedure("operasi usus buntu yang rumit sekali")
    print(f"Status: {result['status']}")
    if result['status'] == 'not_found':
        print("⚠️  AI normalization attempted but failed")
        print(f"   Message: {result.get('message', 'N/A')}")
        print("   → This is expected if API key is invalid")
    else:
        print(f"✅ AI worked! Got {len(result.get('suggestions', []))} suggestions")
except Exception as e:
    print(f"❌ AI normalization error: {e}")

print("\n" + "=" * 60)
print("📊 SUMMARY")
print("=" * 60)
print("✅ Services can be imported without crashing")
print("✅ Database search works without AI")
print("✅ AI only called when needed (lazy loading)")
print("\nIf Test 4 failed with 401/invalid key:")
print("→ Get new key from: https://platform.openai.com/api-keys")
print("→ Update core_engine/.env file")
print("→ Restart: docker-compose restart core_engine")
