# Albania Validation Checks

This module provides comprehensive validation checks for Albanian administrative regions and energy data integrity within the WB-OEMC project.

## Features

### 1. Administrative Regions Validation
- Validates all 37 Albanian administrative regions/districts
- Ensures proper region ID mapping (1-37)
- Checks for missing or duplicate region entries
- Based on the official Albanian administrative division map

### 2. OST Data Validation
- Validates energy demand data from OST (Albanian TSO)
- Checks data completeness and quality
- Validates temporal consistency (hourly intervals)
- Identifies data anomalies (negative values, missing data)
- Ensures reasonable date ranges

## Supported Albanian Regions

The system validates all 37 Albanian administrative regions:

1. Beratit, 2. Kuçovës, 3. Skraparit, 4. Bulqizës, 5. Dibrës, 6. Matit, 7. Durrësit, 8. Krujës, 9. Elbasanit, 10. Gramshit, 11. Librazhdit, 12. Peqinit, 13. Fierit, 14. Lushnjës, 15. Mallakastrës, 16. Gjirokastrës, 17. Përmetit, 18. Tepelenës, 19. Devollit, 20. Kolonjës, 21. Korçës, 22. Pogradecit, 23. Has, 24. Kukësit, 25. Tropojës, 26. Kurbinit, 27. Lezhës, 28. Mirditës, 29. Shkodrës, 30. Malësi e Madhe, 31. Pukës, 32. Shkodrës, 33. Kavajës, 34. Tiranës, 35. Delvinës, 36. Sarandës, 37. Vlorës

## Usage

### Command Line
```bash
# Run Albania checks standalone
python albania_checks.py

# Run with specific OST data file
python albania_checks.py --ost-data /path/to/ost_data.csv

# Skip data validation (regions only)
python albania_checks.py --skip-data
```

### Integrated with Energy Scrapers
```bash
# Run Albania checks as part of energy scraper workflow
python -m energy_scrapers.main --target albania_checks

# Run all energy scrapers including Albania checks
python -m energy_scrapers.main --target all
```

### Programmatic Usage
```python
from energy_scrapers import albania_checks

# Run all checks
results = albania_checks.run_albania_checks("/path/to/ost_data.csv")

# Print formatted results
albania_checks.print_check_results(results)

# Check specific components
is_valid, errors = albania_checks.validate_albania_regions()
```

## Output

The checks provide detailed status reports:

```
============================================================
            ALBANIA VALIDATION CHECKS
============================================================
Timestamp: 2025-09-11 22:25:37.859050
Overall Status: PASS

📍 Administrative Regions Check:
   Status: ✅ PASS
   Total Regions: 37

📊 OST Data Check:
   Status: ✅ PASS
   Data Path: /path/to/ost_demand.csv

============================================================
```

## Exit Codes

- `0`: All checks passed
- `1`: One or more checks failed

## Integration

The Albania checks are integrated into the main energy scrapers workflow and can be run as part of the overall data validation pipeline for Western Balkan energy modeling.