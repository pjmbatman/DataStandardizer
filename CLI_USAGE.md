# DDS CLI Usage Guide

## Installation

```bash
pip install -e .
```

## Basic Usage

```bash
dds /path/to/input /path/to/output
```

## Command Syntax

```bash
dds INPUT_FILE OUTPUT_FILE [OPTIONS]
```

## Examples

### 1. Basic Standardization
```bash
dds battery_data.csv standardized_output.pkl
```

### 2. With Custom Cell ID
```bash
dds battery_data.csv output.pkl --cell-id "cell_001"
```

### 3. Custom Similarity Threshold
```bash
dds battery_data.csv output.pkl --threshold 0.5
```

### 4. Generate Report Only (No Data Output)
```bash
dds battery_data.csv dummy.pkl --report-only
```

### 5. Show Mapping Suggestions
```bash
dds battery_data.csv output.pkl --suggestions
```

### 6. Use Custom Field Mapping
```bash
dds battery_data.csv output.pkl --mapping custom_mapping.json
```

### 7. Verbose Output with Report Saving
```bash
dds battery_data.csv output.pkl --verbose --save-report
```

### 8. Force Map All Columns (Ignore Threshold)
```bash
dds battery_data.csv output.pkl --force-all
```

### 9. Quiet Mode (Minimal Output)
```bash
dds battery_data.csv output.pkl --quiet
```

## Options

| Option | Short | Description |
|--------|-------|-------------|
| `--cell-id` | `-c` | Custom cell identifier |
| `--threshold` | `-t` | Similarity threshold (0.0-1.0) |
| `--mapping` | `-m` | JSON file with custom mappings |
| `--report-only` | `-r` | Generate report only |
| `--suggestions` | `-s` | Show mapping suggestions |
| `--quiet` | `-q` | Suppress output |
| `--verbose` | `-v` | Detailed output |
| `--save-report` | | Save mapping report to file |
| `--force-all` | `-f` | Map all columns to best matches (ignore threshold) |

## Custom Mapping File Format

Create a JSON file with your custom mappings:

```json
{
    "V_cell": "voltage_v",
    "I_load": "current_a",
    "Time": "time_s",
    "Temperature": "temperature_c"
}
```

## Output

- **Primary**: Pickle file (.pkl) containing CellRecord object
- **Optional**: Mapping report (text file)

## Supported Input Formats

- CSV (`.csv`)
- Excel (`.xlsx`, `.xls`)
- Pickle (`.pkl`, `.pickle`)
- MATLAB (`.mat`)
- Text/TSV (`.txt`, `.tsv`)

## Example Output

```
🔍 Processing: battery_data.csv
📊 Similarity threshold: 0.3

🔄 Standardizing data...

✅ SUCCESS!
📁 Input:  battery_data.csv
💾 Output: output.pkl
🔬 Cell ID: battery_data
📊 Mapped fields: 8
❓ Unmapped columns: 0
🔄 Cycles: 1
📈 Data points per cycle: 100
```

## Loading Standardized Data

```python
from dds import CellRecord

# Load the standardized data
cell = CellRecord.load('output.pkl')

# Access the data
print(f"Cell ID: {cell.cell_id}")
print(f"Cycles: {len(cell.cycles)}")
print(f"Voltage data: {cell.cycles[0].voltage_v[:5]}")
```