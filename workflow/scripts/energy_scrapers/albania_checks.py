#!/usr/bin/env python3
"""
Albania validation checks for WB-OEMC

This module provides validation checks for Albanian administrative regions
and energy data integrity based on the 37 administrative divisions.
"""

import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Albanian administrative regions based on the map provided in issue #15
ALBANIA_REGIONS = {
    1: "Beratit",
    2: "Kuçovës", 
    3: "Skraparit",
    4: "Bulqizës",
    5: "Dibrës",
    6: "Matit",
    7: "Durrësit",
    8: "Krujës",
    9: "Elbasanit",
    10: "Gramshit",
    11: "Librazhdit",
    12: "Peqinit",
    13: "Fierit",
    14: "Lushnjës",
    15: "Mallakastrës",
    16: "Gjirokastrës",
    17: "Përmetit",
    18: "Tepelenës",
    19: "Devollit",
    20: "Kolonjës",
    21: "Korçës",
    22: "Pogradecit",
    23: "Has",
    24: "Kukësit",
    25: "Tropojës",
    26: "Kurbinit",
    27: "Lezhës",
    28: "Mirditës",
    29: "Shkodrës",
    30: "Malësi e Madhe",
    31: "Pukës",
    32: "Shkodrës",  # Note: Appears twice in the original map
    33: "Kavajës",
    34: "Tiranës",
    35: "Delvinës",
    36: "Sarandës",
    37: "Vlorës"
}

def validate_albania_regions() -> Tuple[bool, List[str]]:
    """
    Validate the Albanian administrative regions mapping.
    
    Returns:
        Tuple of (is_valid, errors_list)
    """
    errors = []
    
    # Check if all regions are defined
    if len(ALBANIA_REGIONS) != 37:
        errors.append(f"Expected 37 regions, found {len(ALBANIA_REGIONS)}")
    
    # Check for sequential numbering
    expected_ids = set(range(1, 38))
    actual_ids = set(ALBANIA_REGIONS.keys())
    
    missing_ids = expected_ids - actual_ids
    if missing_ids:
        errors.append(f"Missing region IDs: {sorted(missing_ids)}")
    
    extra_ids = actual_ids - expected_ids
    if extra_ids:
        errors.append(f"Unexpected region IDs: {sorted(extra_ids)}")
    
    # Check for duplicate region names (note: Shkodrës appears twice, which might be correct)
    region_names = list(ALBANIA_REGIONS.values())
    duplicate_names = [name for name in set(region_names) if region_names.count(name) > 1]
    if duplicate_names:
        logger.warning(f"Duplicate region names found: {duplicate_names}")
    
    # Check for empty region names
    empty_regions = [k for k, v in ALBANIA_REGIONS.items() if not v or not v.strip()]
    if empty_regions:
        errors.append(f"Empty region names for IDs: {empty_regions}")
    
    is_valid = len(errors) == 0
    return is_valid, errors


def validate_ost_data(csv_path: str) -> Tuple[bool, List[str]]:
    """
    Validate OST (Albanian TSO) energy demand data.
    
    Args:
        csv_path: Path to the OST demand CSV file
        
    Returns:
        Tuple of (is_valid, errors_list)
    """
    errors = []
    
    try:
        # Load the data
        df = pd.read_csv(csv_path)
        
        # Check required columns
        required_columns = ['datetime', 'demand']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            errors.append(f"Missing required columns: {missing_columns}")
            return False, errors
        
        # Check data types
        try:
            df['datetime'] = pd.to_datetime(df['datetime'])
        except Exception as e:
            errors.append(f"Invalid datetime format: {e}")
        
        # Check for data completeness
        total_rows = len(df)
        missing_demand = df['demand'].isna().sum()
        
        if missing_demand > 0:
            missing_percentage = (missing_demand / total_rows) * 100
            logger.warning(f"Missing demand data: {missing_demand}/{total_rows} rows ({missing_percentage:.1f}%)")
            
            # If more than 50% missing, consider it an error
            if missing_percentage > 50:
                errors.append(f"Too much missing demand data: {missing_percentage:.1f}%")
        
        # Check for negative demand values
        if 'demand' in df.columns:
            negative_demand = (df['demand'] < 0).sum()
            if negative_demand > 0:
                errors.append(f"Found {negative_demand} negative demand values")
        
        # Check temporal consistency (should be hourly data)
        if len(df) > 1:
            df_sorted = df.sort_values('datetime')
            time_diffs = df_sorted['datetime'].diff().dropna()
            expected_diff = pd.Timedelta(hours=1)
            
            non_hourly = time_diffs[time_diffs != expected_diff]
            if len(non_hourly) > 0:
                logger.warning(f"Found {len(non_hourly)} non-hourly time intervals")
        
        # Check date range (should be reasonable)
        if len(df) > 0:
            min_date = df['datetime'].min()
            max_date = df['datetime'].max()
            
            # Check if dates are in reasonable range (not future, not too old)
            current_year = pd.Timestamp.now().year
            if min_date.year < 2020:
                logger.warning(f"Data starts from {min_date.year}, which seems quite old")
            if max_date.year > current_year + 1:
                errors.append(f"Data extends to {max_date.year}, which is in the future")
        
    except FileNotFoundError:
        errors.append(f"OST data file not found: {csv_path}")
    except Exception as e:
        errors.append(f"Error reading OST data: {e}")
    
    is_valid = len(errors) == 0
    return is_valid, errors


def run_albania_checks(ost_data_path: Optional[str] = None) -> Dict[str, any]:
    """
    Run comprehensive Albania validation checks.
    
    Args:
        ost_data_path: Optional path to OST data CSV file
        
    Returns:
        Dictionary with check results
    """
    results = {
        'timestamp': pd.Timestamp.now(),
        'regions_check': {},
        'data_check': {},
        'overall_status': 'UNKNOWN'
    }
    
    logger.info("Running Albania validation checks...")
    
    # Check 1: Administrative regions validation
    logger.info("Validating Albanian administrative regions...")
    regions_valid, regions_errors = validate_albania_regions()
    results['regions_check'] = {
        'valid': regions_valid,
        'errors': regions_errors,
        'total_regions': len(ALBANIA_REGIONS),
        'region_mapping': ALBANIA_REGIONS
    }
    
    # Check 2: OST data validation (if path provided)
    if ost_data_path:
        logger.info(f"Validating OST data from {ost_data_path}...")
        data_valid, data_errors = validate_ost_data(ost_data_path)
        results['data_check'] = {
            'valid': data_valid,
            'errors': data_errors,
            'data_path': ost_data_path
        }
    else:
        logger.info("No OST data path provided, skipping data validation")
        results['data_check'] = {
            'valid': None,
            'errors': ['No data path provided'],
            'data_path': None
        }
    
    # Determine overall status
    all_checks_valid = regions_valid and (results['data_check']['valid'] is not False)
    results['overall_status'] = 'PASS' if all_checks_valid else 'FAIL'
    
    return results


def print_check_results(results: Dict[str, any]) -> None:
    """Print formatted check results."""
    print("\n" + "="*60)
    print("            ALBANIA VALIDATION CHECKS")
    print("="*60)
    print(f"Timestamp: {results['timestamp']}")
    print(f"Overall Status: {results['overall_status']}")
    print()
    
    # Regional checks
    print("📍 Administrative Regions Check:")
    regions_check = results['regions_check']
    status = "✅ PASS" if regions_check['valid'] else "❌ FAIL"
    print(f"   Status: {status}")
    print(f"   Total Regions: {regions_check['total_regions']}")
    
    if regions_check['errors']:
        print("   Errors:")
        for error in regions_check['errors']:
            print(f"     • {error}")
    print()
    
    # Data checks
    print("📊 OST Data Check:")
    data_check = results['data_check']
    if data_check['valid'] is None:
        print("   Status: ⏸️ SKIPPED")
    else:
        status = "✅ PASS" if data_check['valid'] else "❌ FAIL"
        print(f"   Status: {status}")
    
    if data_check.get('data_path'):
        print(f"   Data Path: {data_check['data_path']}")
    
    if data_check['errors'] and data_check['errors'] != ['No data path provided']:
        print("   Errors:")
        for error in data_check['errors']:
            print(f"     • {error}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description="Albania validation checks for WB-OEMC")
    parser.add_argument(
        "--ost-data", 
        type=str, 
        help="Path to OST demand CSV file",
        default="../../data/energy_scrapers/ost_demand.csv"
    )
    parser.add_argument(
        "--skip-data", 
        action="store_true", 
        help="Skip data validation checks"
    )
    
    args = parser.parse_args()
    
    # Determine data path
    ost_data_path = None
    if not args.skip_data:
        if os.path.exists(args.ost_data):
            ost_data_path = args.ost_data
        else:
            logger.warning(f"OST data file not found: {args.ost_data}")
    
    # Run checks
    results = run_albania_checks(ost_data_path)
    print_check_results(results)
    
    # Exit with appropriate code
    exit_code = 0 if results['overall_status'] == 'PASS' else 1
    exit(exit_code)