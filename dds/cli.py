#!/usr/bin/env python3
"""
Command Line Interface for Dynamic Data Standardizer (DDS)

Usage: dds /path/to/input /path/to/output [options]
"""

import argparse
import os
import sys
from pathlib import Path
import json

from .data_standardizer import DataStandardizer
from .cell_record import CellRecord


def validate_input_file(file_path):
    """Validate input file exists and has supported format"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    supported_extensions = {'.csv', '.xlsx', '.xls', '.pkl', '.pickle', '.mat', '.txt', '.tsv'}
    file_ext = Path(file_path).suffix.lower()
    
    if file_ext not in supported_extensions:
        raise ValueError(f"Unsupported file format: {file_ext}. "
                        f"Supported formats: {', '.join(supported_extensions)}")
    
    return True


def validate_output_path(output_path):
    """Validate output directory exists or can be created"""
    output_dir = Path(output_path).parent
    if not output_dir.exists():
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise PermissionError(f"Cannot create output directory {output_dir}: {e}")
    
    return True


def load_custom_mapping(mapping_file):
    """Load custom mapping from JSON file"""
    try:
        with open(mapping_file, 'r') as f:
            mapping = json.load(f)
        return mapping
    except Exception as e:
        raise ValueError(f"Error loading mapping file {mapping_file}: {e}")


def save_mapping_report(standardizer, input_file, output_dir, mapping=None):
    """Save mapping report to file"""
    report_file = output_dir / "mapping_report.txt"
    
    # Capture print output
    import io
    import contextlib
    
    old_stdout = sys.stdout
    sys.stdout = captured_output = io.StringIO()
    
    try:
        standardizer.print_mapping_report(input_file, mapping)
        report_content = captured_output.getvalue()
    finally:
        sys.stdout = old_stdout
    
    with open(report_file, 'w') as f:
        f.write(report_content)
    
    return report_file


def main():
    parser = argparse.ArgumentParser(
        description="Dynamic Data Standardizer - Automatically map raw data to battery data structures",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  dds data.csv output.pkl                           # Basic usage
  dds data.xlsx output.pkl --cell-id "cell_001"    # With custom cell ID
  dds data.csv output.pkl --threshold 0.5          # Custom similarity threshold
  dds data.csv output.pkl --mapping mapping.json   # Custom field mapping
  dds data.csv output.pkl --report-only            # Generate report only
  dds data.csv output.pkl --suggestions            # Show mapping suggestions
  dds data.csv output.pkl --force-all              # Map all columns to best matches

Supported input formats: CSV, Excel (.xlsx/.xls), Pickle (.pkl), MATLAB (.mat), Text (.txt/.tsv)
Output format: Pickle (.pkl) containing CellRecord object
        """
    )
    
    # Positional arguments
    parser.add_argument("input_file", help="Path to input data file")
    parser.add_argument("output_file", help="Path to output pickle file (.pkl)")
    
    # Optional arguments
    parser.add_argument("--cell-id", "-c", 
                       help="Cell identifier (default: auto-generated from filename)")
    
    parser.add_argument("--threshold", "-t", type=float, default=0.3,
                       help="Similarity threshold for automatic mapping (default: 0.3)")
    
    parser.add_argument("--mapping", "-m",
                       help="JSON file containing custom field mappings")
    
    parser.add_argument("--report-only", "-r", action="store_true",
                       help="Generate mapping report only, don't save data")
    
    parser.add_argument("--suggestions", "-s", action="store_true",
                       help="Show top 3 mapping suggestions for each column")
    
    parser.add_argument("--quiet", "-q", action="store_true",
                       help="Suppress output messages")
    
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")
    
    parser.add_argument("--save-report", action="store_true",
                       help="Save mapping report to file")
    
    parser.add_argument("--force-all", "-f", action="store_true",
                       help="Force mapping all columns to best matches (ignore threshold)")
    
    args = parser.parse_args()
    
    try:
        # Validate inputs
        validate_input_file(args.input_file)
        if not args.report_only:
            validate_output_path(args.output_file)
        
        # Initialize standardizer
        standardizer = DataStandardizer()
        standardizer.similarity_threshold = args.threshold
        standardizer.force_best_match = args.force_all
        
        if not args.quiet:
            print(f"🔍 Processing: {args.input_file}")
            print(f"📊 Similarity threshold: {args.threshold}")
        
        # Load custom mapping if provided
        custom_mapping = None
        if args.mapping:
            custom_mapping = load_custom_mapping(args.mapping)
            if not args.quiet:
                print(f"📋 Using custom mapping from: {args.mapping}")
        
        # Generate cell ID
        cell_id = args.cell_id or Path(args.input_file).stem
        
        # Print mapping report
        if args.verbose or args.report_only:
            print("\n" + "="*60)
            standardizer.print_mapping_report(args.input_file, custom_mapping)
            print("="*60)
        
        # Show mapping suggestions
        if args.suggestions:
            print("\n📋 MAPPING SUGGESTIONS")
            print("-" * 40)
            df, columns = standardizer.read_data(args.input_file)
            suggestions = standardizer.suggest_mappings(columns)
            
            for column, top_matches in suggestions.items():
                print(f"\n'{column}':")
                for i, (target, score) in enumerate(top_matches[:3], 1):
                    confidence = "HIGH" if score > 0.7 else "MED" if score > 0.4 else "LOW"
                    print(f"  {i}. {target:<25} (score: {score:.3f}, {confidence})")
        
        # Exit if report-only mode
        if args.report_only:
            if not args.quiet:
                print("\n✅ Report generated (report-only mode)")
            return
        
        # Standardize data
        if not args.quiet:
            print(f"\n🔄 Standardizing data...")
        
        result = standardizer.standardize_data(args.input_file, custom_mapping)
        
        # Create CellRecord
        cell_record = standardizer.create_cell_record(result, cell_id)
        
        # Save output
        output_path = Path(args.output_file)
        cell_record.dump(str(output_path))
        
        # Save mapping report if requested
        if args.save_report:
            report_file = save_mapping_report(standardizer, args.input_file, 
                                            output_path.parent, custom_mapping)
            if not args.quiet:
                print(f"📄 Mapping report saved: {report_file}")
        
        # Summary
        if not args.quiet:
            print(f"\n✅ SUCCESS!")
            print(f"📁 Input:  {args.input_file}")
            print(f"💾 Output: {args.output_file}")
            print(f"🔬 Cell ID: {cell_id}")
            print(f"📊 Mapped fields: {len(result['standardized_data'])}")
            print(f"❓ Unmapped columns: {len(result['unmapped_columns'])}")
            
            if result['unmapped_columns']:
                print(f"   Unmapped: {', '.join(result['unmapped_columns'])}")
            
            print(f"🔄 Cycles: {len(cell_record.cycles)}")
            
            if cell_record.cycles:
                cycle = cell_record.cycles[0]
                data_points = 0
                if cycle.voltage_v:
                    data_points = len(cycle.voltage_v)
                elif cycle.current_a:
                    data_points = len(cycle.current_a)
                print(f"📈 Data points per cycle: {data_points:,}")
    
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()