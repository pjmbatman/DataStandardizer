# Dynamic Data Standardizer

A Python tool that automatically maps raw time-series data to predefined battery data structures using NLP-based similarity matching.

## Features

- **Multi-format Support**: Reads CSV, Excel (xlsx/xls), Pickle, MATLAB (.mat), and text files
- **Intelligent Mapping**: Uses NLP similarity algorithms to match column names to predefined fields
- **Battery Data Focus**: Specifically designed for battery/cell testing data standardization
- **Flexible Integration**: Works with existing CellRecord and CycleRecord data structures
- **Customizable Mapping**: Allows manual override of automatic mappings

## Supported File Formats

- `.csv` - Comma-separated values
- `.xlsx/.xls` - Excel files
- `.pkl/.pickle` - Python pickle files
- `.mat` - MATLAB data files
- `.txt/.tsv` - Text/tab-separated files

## Target Data Structure

The standardizer maps to these predefined fields:

### CycleRecord Fields
- `cycle_number`: Cycle index/number
- `voltage_v`: Voltage measurements in volts
- `current_a`: Current measurements in amperes
- `charge_capacity_ah`: Charge capacity in amp-hours
- `discharge_capacity_ah`: Discharge capacity in amp-hours
- `time_s`: Time measurements in seconds
- `temperature_c`: Temperature in Celsius
- `internal_resistance_ohm`: Internal resistance in ohms

### CellRecord Fields
- `cell_id`: Cell identifier
- `form_factor`: Physical form factor
- `anode_material`: Anode material composition
- `cathode_material`: Cathode material composition
- `electrolyte_material`: Electrolyte composition
- `nominal_capacity_ah`: Rated capacity
- `depth_of_charge/discharge`: DOC/DOD values
- `voltage/current_limits`: Operating limits
- `reference`: Data source reference
- `description`: Additional description

## Usage

### Basic Usage

```python
from data_standardizer import DataStandardizer

# Initialize the standardizer
standardizer = DataStandardizer()

# Standardize data from a file
result = standardizer.standardize_data('battery_data.csv')

# Create a CellRecord object
cell_record = standardizer.create_cell_record(result, cell_id='cell_001')

# Print mapping report
standardizer.print_mapping_report('battery_data.csv')
```

### Custom Mapping

```python
# Define custom column mappings
custom_mapping = {
    'Voltage (V)': 'voltage_v',
    'Current [A]': 'current_a',
    'Time_Seconds': 'time_s'
}

# Use custom mapping
result = standardizer.standardize_data('data.csv', custom_mapping)
```

### Getting Mapping Suggestions

```python
# Get top 3 suggestions for each column
df, columns = standardizer.read_data('data.csv')
suggestions = standardizer.suggest_mappings(columns)

for col, sug in suggestions.items():
    print(f"{col}: {sug}")
```

## Similarity Algorithm

The tool uses a multi-method similarity calculation:

1. **Sequence Matching**: Character-level similarity using difflib
2. **Token-based Matching**: Word-level overlap comparison
3. **Semantic Matching**: Domain-specific term recognition

### Key Term Recognition

The algorithm recognizes variations of key terms:
- **Voltage**: volt, v, voltage
- **Current**: current, amp, ampere, a, i
- **Capacity**: capacity, cap, ah, mah
- **Temperature**: temperature, temp, celsius, c
- **Time**: time, timestamp, seconds, s
- **Cycle**: cycle, index, number, count
- **Resistance**: resistance, ohm, impedance, r

## Example

```python
#!/usr/bin/env python3
from data_standardizer import DataStandardizer

# Create sample data with various naming conventions
import pandas as pd
import numpy as np

data = {
    'Voltage (V)': np.random.uniform(3.0, 4.2, 100),
    'Current [A]': np.random.uniform(-2.0, 2.0, 100),
    'Charge_Capacity_Ah': np.cumsum(np.random.uniform(0, 0.01, 100)),
    'Time_Seconds': np.arange(100) * 10,
    'Temp_Celsius': np.random.uniform(20, 35, 100),
}

df = pd.DataFrame(data)
df.to_csv('example.csv', index=False)

# Standardize the data
standardizer = DataStandardizer()
result = standardizer.standardize_data('example.csv')

# Create CellRecord
cell = standardizer.create_cell_record(result, 'example_cell')
print(f"Created cell with {len(cell.cycles)} cycles")
```

## Requirements

- Python 3.7+
- pandas
- numpy
- scipy (for MATLAB files)
- openpyxl (for Excel files)

## Installation

```bash
pip install pandas numpy scipy openpyxl
```

## Output Structure

The `standardize_data()` method returns:

```python
{
    'mapping_used': {...},           # Column mappings applied
    'unmapped_columns': [...],       # Columns that couldn't be mapped
    'raw_data_shape': (rows, cols),  # Original data dimensions
    'standardized_data': {...},      # Mapped data
    'unmapped_data': {...}           # Unmapped column data
}
```

## Customization

You can adjust the similarity threshold:

```python
standardizer = DataStandardizer()
standardizer.similarity_threshold = 0.5  # Default is 0.3
```

Lower thresholds are more permissive, higher thresholds are more strict.