# Clinical Consistency Module - Quick Start Guide

## What is this?
The Clinical Consistency Module validates the clinical appropriateness of treatment decisions in medical claims by checking:
- ✅ Diagnosis → Procedures (Are the procedures appropriate for this diagnosis?)
- ✅ Diagnosis → Medications (Are the medications appropriate for this diagnosis?)
- ✅ Procedures → Medications (Are the medications appropriate for these procedures?)

## How to Use

### 1. Standalone Usage

```python
from services.consistency_service import analyze_clinical_consistency

result = analyze_clinical_consistency(
    dx="J18.9",  # ICD-10 code for Pneumonia
    tx_list=["87.44", "93.96", "96.01"],  # ICD-9 procedure codes
    drug_list=["ceftriaxone", "amoxicillin", "salbutamol"]  # Generic drug names
)

print(result["konsistensi"]["tingkat_konsistensi"])  # Output: "Tinggi", "Sedang", or "Rendah"
```

### 2. Integrated with AI-CLAIM Lite

The module is automatically used when calling `analyze_lite_single()`:

```python
from services.lite_service import analyze_lite_single

result = await analyze_lite_single(payload, db_pool)

# Access consistency results
consistency = result["konsistensi"]
print(consistency["tingkat_konsistensi"])  # Overall level
print(consistency["dx_tx"]["status"])       # Diagnosis → Procedures
print(consistency["dx_drug"]["status"])     # Diagnosis → Drugs
print(consistency["tx_drug"]["status"])     # Procedures → Drugs
```

## Output Format

```json
{
  "konsistensi": {
    "dx_tx": {
      "status": "✅ Sesuai",
      "catatan": "Tindakan sesuai dengan protokol diagnosis J18.9"
    },
    "dx_drug": {
      "status": "⚠️ Parsial",
      "catatan": "Sebagian terapi sesuai (2/3)"
    },
    "tx_drug": {
      "status": "✅ Sesuai",
      "catatan": "Obat pendukung sesuai dengan tindakan"
    },
    "tingkat_konsistensi": "Tinggi",
    "_score": 2.5
  }
}
```

## Status Meanings

| Status | Icon | Meaning |
|--------|------|---------|
| Sesuai | ✅ | Fully compliant with clinical guidelines |
| Parsial | ⚠️ | Partially compliant, some items missing or extra |
| Tidak Sesuai | ❌ | Not compliant with clinical guidelines |

## Consistency Levels

| Level | Score Range | Meaning |
|-------|-------------|---------|
| **Tinggi** | ≥ 2.5 | High consistency - treatment follows guidelines |
| **Sedang** | 1.5 - 2.4 | Medium consistency - some deviations noted |
| **Rendah** | < 1.5 | Low consistency - significant deviations from guidelines |

## Testing

### Run Unit Tests
```bash
python test_consistency_module.py
```

### Run Integration Test
```bash
python test_integration_consistency.py
```

### Run Debug Tests
```bash
python test_exact_match.py
python test_score_debug.py
```

## Configuration

### JSON Mapping Files
Located in `rules/` directory:
- `icd10_icd9_map.json` - Diagnosis → Procedures mapping
- `diagnosis_obat_map.json` - Diagnosis → Drugs mapping
- `tindakan_obat_map.json` - Procedures → Drugs mapping

### Example Mapping Entry

**icd10_icd9_map.json:**
```json
{
  "J18.9": [
    "87.44",  // Chest X-ray
    "93.96",  // Inhalation therapy
    "96.01"   // Intubation
  ]
}
```

**diagnosis_obat_map.json:**
```json
{
  "J18.9": [
    "amoxicillin",
    "ceftriaxone",
    "azithromycin"
  ]
}
```

## Troubleshooting

### Issue: All validations return "Tidak Sesuai" for valid data
**Cause**: Mapping files don't contain the ICD code
**Solution**: Add the ICD-10/ICD-9 code to the appropriate JSON file

### Issue: Unicode errors when printing output
**Cause**: Windows console encoding (CP1252) doesn't support emoji
**Solution**: Use `ensure_ascii=False` in json.dumps() or avoid printing emoji directly

### Issue: Score always 0.0
**Cause**: Drug name or code formatting mismatch
**Solution**: Check normalization - codes are uppercase, drugs are lowercase

## API Reference

### analyze_clinical_consistency()

**Parameters:**
- `dx` (str): ICD-10 diagnosis code (e.g., "J18.9")
- `tx_list` (List[str]): List of ICD-9 procedure codes
- `drug_list` (List[str]): List of generic drug names

**Returns:**
- `dict`: Consistency validation results

**Example:**
```python
result = analyze_clinical_consistency(
    dx="J18.9",
    tx_list=["87.44", "93.96"],
    drug_list=["ceftriaxone", "amoxicillin"]
)
```

### validate_dx_tx()
Validates Diagnosis → Procedures relationship

### validate_dx_drug()
Validates Diagnosis → Medications relationship

### validate_tx_drug()
Validates Procedures → Medications relationship

## Performance

- **Execution Time**: < 50ms per validation (all 3 checks)
- **Memory Usage**: Minimal (JSON files cached in memory)
- **Concurrency**: Thread-safe (no global state modification)

## Logging

Enable debug logging to see detailed matching information:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

Output:
```
[DX→TX] Match score: 1.00 (3/3)
[DX→DRUG] Match score: 0.67 (2/3)
[TX→DRUG] Match score: 1.00 (2/2)
```

## Support

For issues or questions:
1. Check `CLINICAL_CONSISTENCY_MODULE.md` for detailed documentation
2. Review test files for usage examples
3. Check console logs for detailed error messages

## License

Part of AI-CLAIM Lite System
© 2024 - Internal Use Only
