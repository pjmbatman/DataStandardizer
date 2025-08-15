import os
import pandas as pd
import pickle
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import scipy.io
from difflib import SequenceMatcher
import re


class DataStandardizer:
    def __init__(self, cell_record_path: str = None):
        self.target_fields = self._extract_target_fields()
        self.similarity_threshold = 0.3
        self.force_best_match = False
        
    def _extract_target_fields(self) -> Dict[str, List[str]]:
        """Extract target field names from CycleRecord and CellRecord classes"""
        cycle_fields = [
            'cycle_number', 'voltage_v', 'current_a', 'charge_capacity_ah',
            'discharge_capacity_ah', 'time_s', 'temperature_c', 'internal_resistance_ohm'
        ]
        
        cell_fields = [
            'cell_id', 'form_factor', 'anode_material', 'cathode_material',
            'electrolyte_material', 'nominal_capacity_ah', 'depth_of_charge',
            'depth_of_discharge', 'initial_cycles', 'max_voltage_limit_v',
            'min_voltage_limit_v', 'max_current_limit_a', 'min_current_limit_a',
            'reference', 'description'
        ]
        
        return {
            'cycle_fields': cycle_fields,
            'cell_fields': cell_fields,
            'all_fields': cycle_fields + cell_fields
        }

    def detect_file_format(self, file_path: str) -> str:
        """Detect file format based on extension"""
        file_path = Path(file_path)
        extension = file_path.suffix.lower()
        
        format_map = {
            '.csv': 'csv',
            '.xlsx': 'excel',
            '.xls': 'excel', 
            '.pkl': 'pickle',
            '.pickle': 'pickle',
            '.mat': 'matlab',
            '.txt': 'text',
            '.tsv': 'tsv'
        }
        
        return format_map.get(extension, 'unknown')

    def read_data(self, file_path: str) -> Tuple[pd.DataFrame, List[str]]:
        """Read data from various file formats and return DataFrame with column names"""
        file_format = self.detect_file_format(file_path)
        
        try:
            if file_format == 'csv':
                df = pd.read_csv(file_path)
                
            elif file_format == 'excel':
                df = pd.read_excel(file_path)
                
            elif file_format == 'pickle':
                with open(file_path, 'rb') as f:
                    data = pickle.load(f)
                if isinstance(data, dict):
                    df = pd.DataFrame(data)
                elif isinstance(data, pd.DataFrame):
                    df = data
                else:
                    df = pd.DataFrame({'data': [data]})
                    
            elif file_format == 'matlab':
                mat_data = scipy.io.loadmat(file_path)
                # Remove metadata keys
                data_keys = [k for k in mat_data.keys() if not k.startswith('__')]
                if len(data_keys) == 1:
                    df = pd.DataFrame(mat_data[data_keys[0]])
                else:
                    df = pd.DataFrame({k: mat_data[k].flatten() if mat_data[k].ndim > 1 else mat_data[k] 
                                     for k in data_keys})
                    
            elif file_format == 'text' or file_format == 'tsv':
                # Try different delimiters
                delimiters = ['\t', ' ', ',', ';']
                df = None
                for delimiter in delimiters:
                    try:
                        df = pd.read_csv(file_path, delimiter=delimiter)
                        if len(df.columns) > 1:
                            break
                    except:
                        continue
                if df is None:
                    df = pd.read_csv(file_path, delimiter='\t')
                    
            else:
                raise ValueError(f"Unsupported file format: {file_format}")
                
            return df, list(df.columns)
            
        except Exception as e:
            raise Exception(f"Error reading file {file_path}: {str(e)}")

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two strings using multiple methods"""
        text1_clean = self._clean_text(text1)
        text2_clean = self._clean_text(text2)
        
        # Method 1: SequenceMatcher
        seq_similarity = SequenceMatcher(None, text1_clean, text2_clean).ratio()
        
        # Method 2: Token-based similarity
        tokens1 = set(re.findall(r'\w+', text1_clean))
        tokens2 = set(re.findall(r'\w+', text2_clean))
        
        if tokens1 and tokens2:
            token_similarity = len(tokens1 & tokens2) / len(tokens1 | tokens2)
        else:
            token_similarity = 0
            
        # Method 3: Substring similarity
        substring_similarity = self._substring_similarity(text1_clean, text2_clean)
        
        # Combine similarities with weights
        combined_similarity = (seq_similarity * 0.4 + 
                             token_similarity * 0.4 + 
                             substring_similarity * 0.2)
        
        return combined_similarity

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for comparison"""
        text = text.lower()
        # Remove special characters but keep underscores
        text = re.sub(r'[^a-z0-9_\s]', '', text)
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _substring_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity based on common substrings"""
        # Check if one is contained in the other
        if text1 in text2 or text2 in text1:
            return 0.8
        
        # Check for common key terms and their variations
        key_terms_map = {
            'voltage': ['volt', 'v', 'voltage'],
            'current': ['current', 'amp', 'ampere', 'a', 'i'],
            'capacity': ['capacity', 'cap', 'ah', 'mah'],
            'temperature': ['temperature', 'temp', 'celsius', 'c', 'kelvin', 'fahrenheit'],
            'time': ['time', 'timestamp', 'seconds', 's', 'minutes', 'hours'],
            'cycle': ['cycle', 'index', 'number', 'count'],
            'resistance': ['resistance', 'ohm', 'impedance', 'r'],
            'charge': ['charge', 'charging'],
            'discharge': ['discharge', 'discharging'],
            'power': ['power', 'w', 'watt'],
            'energy': ['energy', 'wh', 'joule']
        }
        
        # Find matching key terms
        text1_terms = set()
        text2_terms = set()
        
        for key_term, variations in key_terms_map.items():
            for variation in variations:
                # Use both substring and word boundary matching
                if (variation in text1 or 
                    re.search(r'\b' + re.escape(variation) + r'\b', text1)):
                    text1_terms.add(key_term)
                if (variation in text2 or 
                    re.search(r'\b' + re.escape(variation) + r'\b', text2)):
                    text2_terms.add(key_term)
        
        if text1_terms and text2_terms:
            common_terms = text1_terms & text2_terms
            return len(common_terms) / max(len(text1_terms), len(text2_terms))
        
        return 0

    def map_features(self, raw_columns: List[str], force_best_match: bool = False) -> Dict[str, str]:
        """Map raw column names to target field names using similarity"""
        mapping = {}
        used_targets = set()
        
        # Sort raw columns by length (longer names often more descriptive)
        sorted_columns = sorted(raw_columns, key=len, reverse=True)
        
        for raw_col in sorted_columns:
            best_match = None
            best_score = 0
            
            for target_field in self.target_fields['all_fields']:
                if target_field in used_targets:
                    continue
                    
                similarity = self.calculate_similarity(raw_col, target_field)
                
                if similarity > best_score:
                    best_score = similarity
                    best_match = target_field
            
            # Map if above threshold OR if force_best_match is True and we found a match
            if best_match and (best_score >= self.similarity_threshold or force_best_match):
                mapping[raw_col] = best_match
                used_targets.add(best_match)
        
        return mapping

    def suggest_mappings(self, raw_columns: List[str]) -> Dict[str, List[Tuple[str, float]]]:
        """Suggest top 3 mappings for each raw column with similarity scores"""
        suggestions = {}
        
        for raw_col in raw_columns:
            scores = []
            for target_field in self.target_fields['all_fields']:
                similarity = self.calculate_similarity(raw_col, target_field)
                scores.append((target_field, similarity))
            
            # Sort by similarity score and take top 3
            scores.sort(key=lambda x: x[1], reverse=True)
            suggestions[raw_col] = scores[:3]
        
        return suggestions

    def standardize_data(self, file_path: str, custom_mapping: Dict[str, str] = None) -> Dict[str, Any]:
        """Main method to standardize data from raw file"""
        # Read data
        df, raw_columns = self.read_data(file_path)
        
        # Get mapping (use custom if provided, otherwise auto-map)
        if custom_mapping:
            # Start with custom mapping, then auto-map remaining columns
            mapping = custom_mapping.copy()
            
            # Find unmapped columns
            unmapped_columns = [col for col in raw_columns if col not in mapping]
            
            # Auto-map the remaining columns
            if unmapped_columns:
                auto_mapping = self.map_features(unmapped_columns, self.force_best_match)
                # Merge auto-mapping, avoiding conflicts with custom mapping
                used_targets = set(mapping.values())
                for raw_col, target_field in auto_mapping.items():
                    if target_field not in used_targets:
                        mapping[raw_col] = target_field
                        used_targets.add(target_field)
        else:
            mapping = self.map_features(raw_columns, self.force_best_match)
        
        # Create standardized data structure
        standardized_data = {
            'mapping_used': mapping,
            'unmapped_columns': [col for col in raw_columns if col not in mapping],
            'raw_data_shape': df.shape,
            'standardized_data': {}
        }
        
        # Map the data
        for raw_col, target_field in mapping.items():
            if raw_col in df.columns:
                data = df[raw_col].dropna().tolist()
                standardized_data['standardized_data'][target_field] = data
        
        # Store unmapped data
        unmapped_data = {}
        for col in standardized_data['unmapped_columns']:
            unmapped_data[col] = df[col].dropna().tolist()
        
        standardized_data['unmapped_data'] = unmapped_data
        
        return standardized_data

    def create_cell_record(self, standardized_data: Dict[str, Any], cell_id: str = None) -> 'CellRecord':
        """Create a CellRecord object from standardized data"""
        from .cell_record import CellRecord, CycleRecord
        
        data = standardized_data['standardized_data']
        
        # Determine if this is cycle data or cell metadata
        cycle_data_fields = [f for f in self.target_fields['cycle_fields'] if f in data and f != 'cycle_number']
        
        if cycle_data_fields:
            # This appears to be cycle data
            cycle_records = []
            
            # Determine number of data points
            data_length = max(len(data[field]) for field in cycle_data_fields if field in data)
            
            # Create a single cycle record for now (can be enhanced to detect multiple cycles)
            cycle_kwargs = {}
            for field in self.target_fields['cycle_fields']:
                if field in data:
                    if field == 'cycle_number':
                        cycle_kwargs[field] = data[field][0] if data[field] else 1
                    else:
                        cycle_kwargs[field] = data[field]
            
            if 'cycle_number' not in cycle_kwargs:
                cycle_kwargs['cycle_number'] = 1
                
            cycle_record = CycleRecord(**cycle_kwargs)
            cycle_records.append(cycle_record)
            
            # Create cell record
            cell_kwargs = {'cell_id': cell_id or 'unknown_cell', 'cycles': cycle_records}
            
            # Add any cell-level metadata
            for field in self.target_fields['cell_fields']:
                if field in data and field != 'cell_id':
                    cell_kwargs[field] = data[field][0] if isinstance(data[field], list) else data[field]
            
            return CellRecord(**cell_kwargs)
        
        else:
            # This appears to be cell metadata only
            cell_kwargs = {'cell_id': cell_id or 'unknown_cell'}
            
            for field in self.target_fields['cell_fields']:
                if field in data and field != 'cell_id':
                    cell_kwargs[field] = data[field][0] if isinstance(data[field], list) else data[field]
            
            return CellRecord(**cell_kwargs)

    def print_mapping_report(self, file_path: str, mapping: Dict[str, str] = None):
        """Print a detailed report of the mapping process"""
        df, raw_columns = self.read_data(file_path)
        
        if mapping is None:
            mapping = self.map_features(raw_columns)
        
        suggestions = self.suggest_mappings(raw_columns)
        
        print(f"=== Data Standardization Report for {file_path} ===")
        print(f"File format: {self.detect_file_format(file_path)}")
        print(f"Data shape: {df.shape}")
        print(f"Raw columns: {len(raw_columns)}")
        print(f"Mapped columns: {len(mapping)}")
        print(f"Unmapped columns: {len(raw_columns) - len(mapping)}")
        
        print("\n=== Column Mapping Results ===")
        for raw_col in raw_columns:
            if raw_col in mapping:
                target = mapping[raw_col]
                similarity = self.calculate_similarity(raw_col, target)
                print(f"✓ '{raw_col}' → '{target}' (similarity: {similarity:.3f})")
            else:
                print(f"✗ '{raw_col}' → [UNMAPPED]")
                print(f"    Top suggestions: {suggestions[raw_col][:3]}")
        
        print(f"\n=== Unmapped Columns ({len(raw_columns) - len(mapping)}) ===")
        for col in raw_columns:
            if col not in mapping:
                print(f"- {col}")