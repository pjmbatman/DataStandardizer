import pickle
import numpy as np
from typing import List, Dict, Any


class CycleRecord:
    def __init__(self,
                 cycle_number: int,
                 *,
                 voltage_v: List[float] = None,
                 current_a: List[float] = None,
                 charge_capacity_ah: List[float] = None,
                 discharge_capacity_ah: List[float] = None,
                 time_s: List[float] = None,
                 temperature_c: List[float] = None,
                 internal_resistance_ohm: float = None,
                 **kwargs):
        self.cycle_number = cycle_number
        self.voltage_v = voltage_v
        self.current_a = current_a
        self.charge_capacity_ah = charge_capacity_ah
        self.discharge_capacity_ah = discharge_capacity_ah
        self.time_s = time_s
        self.temperature_c = temperature_c
        self.internal_resistance_ohm = internal_resistance_ohm

        self.additional_data = {}
        for key, val in kwargs.items():
            self.additional_data[key] = val

    def to_dict(self):
        return {
            'cycle_number': self.cycle_number,
            'voltage_v': self.voltage_v,
            'current_a': self.current_a,
            'charge_capacity_ah': self.charge_capacity_ah,
            'discharge_capacity_ah': self.discharge_capacity_ah,
            'time_s': self.time_s,
            'temperature_c': self.temperature_c,
            'internal_resistance_ohm': self.internal_resistance_ohm,
            **self.additional_data
        }


class CyclingProtocol:
    def __init__(self,
                 c_rate: float = None,
                 current_a: float = None,
                 voltage_v: float = None,
                 power_w: float = None,
                 start_voltage_v: float = None,
                 start_soc: float = None,
                 end_voltage_v: float = None,
                 end_soc: float = None):
        self.c_rate = c_rate
        self.current_a = current_a
        self.voltage_v = voltage_v
        self.power_w = power_w
        self.start_voltage_v = start_voltage_v
        self.start_soc = start_soc
        self.end_voltage_v = end_voltage_v
        self.end_soc = end_soc

    def to_dict(self):
        return {
            'c_rate': self.c_rate,
            'current_a': self.current_a,
            'voltage_v': self.voltage_v,
            'power_w': self.power_w,
            'start_voltage_v': self.start_voltage_v,
            'start_soc': self.start_soc,
            'end_voltage_v': self.end_voltage_v,
            'end_soc': self.end_soc,
        }


class CellRecord:
    def __init__(self,
                 cell_id: str,
                 *,
                 cycles: List[CycleRecord] = None,
                 form_factor: str = None,
                 anode_material: str = None,
                 cathode_material: str = None,
                 electrolyte_material: str = None,
                 nominal_capacity_ah: float = None,
                 depth_of_charge: float = 1.0,
                 depth_of_discharge: float = 1.0,
                 initial_cycles: int = 0,
                 charge_protocol: List[CyclingProtocol] = None,
                 discharge_protocol: List[CyclingProtocol] = None,
                 max_voltage_limit_v: float = None,
                 min_voltage_limit_v: float = None,
                 max_current_limit_a: float = None,
                 min_current_limit_a: float = None,
                 reference: str = None,
                 description: str = None,
                 **kwargs):
        self.cell_id = cell_id
        self.cycles = cycles or []
        self.form_factor = form_factor
        self.anode_material = anode_material
        self.cathode_material = cathode_material
        self.electrolyte_material = electrolyte_material
        self.nominal_capacity_ah = nominal_capacity_ah
        self.depth_of_charge = depth_of_charge
        self.depth_of_discharge = depth_of_discharge
        self.initial_cycles = initial_cycles
        self.max_voltage_limit_v = max_voltage_limit_v
        self.min_voltage_limit_v = min_voltage_limit_v
        self.max_current_limit_a = max_current_limit_a
        self.min_current_limit_a = min_current_limit_a
        self.reference = reference
        self.description = description

        if isinstance(charge_protocol, CyclingProtocol):
            charge_protocol = [charge_protocol]
        self.charge_protocol = charge_protocol or []
        if isinstance(discharge_protocol, CyclingProtocol):
            discharge_protocol = [discharge_protocol]
        self.discharge_protocol = discharge_protocol or []

        for key, val in kwargs.items():
            setattr(self, key, val)

    def to_dict(self):
        result = {}
        for key, val in self.__dict__.items():
            if not callable(val) and not key.startswith('_'):
                if key == 'cycles' or 'protocol' in key:
                    result[key] = [item.to_dict() for item in val] if val else []
                elif hasattr(val, 'to_dict'):
                    result[key] = val.to_dict()
                else:
                    result[key] = val
        return result

    def dump(self, path):
        with open(path, 'wb') as fout:
            pickle.dump(self.to_dict(), fout)

    def feature_extractor(self, feature_types: List[str] = None) -> Dict[str, Any]:
        if feature_types is None:
            feature_types = ['capacity_fade', 'voltage_curves', 'temperature_stats']
        
        features = {}
        
        if 'capacity_fade' in feature_types:
            discharge_capacities = [cycle.discharge_capacity_ah[-1] if cycle.discharge_capacity_ah else 0 
                                  for cycle in self.cycles if cycle.discharge_capacity_ah]
            if discharge_capacities:
                features['initial_capacity'] = discharge_capacities[0]
                features['final_capacity'] = discharge_capacities[-1]
                features['capacity_fade_rate'] = (discharge_capacities[0] - discharge_capacities[-1]) / len(discharge_capacities)
                features['discharge_capacities'] = discharge_capacities
        
        if 'voltage_curves' in feature_types:
            voltage_features = []
            for cycle in self.cycles[:10]:  # First 10 cycles
                if cycle.voltage_v:
                    voltage_features.extend([
                        np.mean(cycle.voltage_v),
                        np.std(cycle.voltage_v),
                        np.max(cycle.voltage_v),
                        np.min(cycle.voltage_v)
                    ])
            features['voltage_curve_features'] = voltage_features
        
        if 'temperature_stats' in feature_types:
            temp_data = [temp for cycle in self.cycles for temp in (cycle.temperature_c or []) if temp is not None]
            if temp_data:
                features['avg_temperature'] = np.mean(temp_data)
                features['max_temperature'] = np.max(temp_data)
                features['min_temperature'] = np.min(temp_data)
        
        return features

    def print_description(self):
        print(f'**************Description of battery cell {self.cell_id}**************')
        for key, val in self.__dict__.items():
            if key == 'cycles':
                print(f'cycle count: {len(val)}')
                
                # Calculate total data points across all cycles
                total_data_points = 0
                if val:
                    for cycle in val:
                        if cycle.voltage_v:  # Use voltage as the reference since it's most common
                            total_data_points += len(cycle.voltage_v)
                        elif cycle.current_a:  # Fallback to current if no voltage
                            total_data_points += len(cycle.current_a)
                        elif cycle.time_s:  # Fallback to time if no current
                            total_data_points += len(cycle.time_s)
                
                print(f'total data points: {total_data_points:,}')
                
                # Show detailed information for first, middle, and last cycles
                if val and len(val) > 0:
                    print('\n--- Sample Cycle Details (first, middle, last cycles) ---')

                    # Select 3 cycles: first, middle, last
                    sample_cycles = []
                    if len(val) == 1:
                        sample_cycles = [val[0]]
                    elif len(val) == 2:
                        sample_cycles = [val[0], val[1]]
                    else:
                        middle_idx = len(val) // 2
                        sample_cycles = [val[0], val[middle_idx], val[-1]]
                    
                    def get_sample_points(data_list):
                        """Get 5 sample points: first 2, middle, last 2"""
                        if len(data_list) <= 5:
                            return data_list
                        middle_idx = len(data_list) // 2
                        return [data_list[0], data_list[1], data_list[middle_idx], 
                                data_list[-2], data_list[-1]]
                    
                    for i, cycle in enumerate(sample_cycles):
                        cycle_desc = 'first' if i == 0 else ('middle' if i == 1 and len(sample_cycles) == 3 else 'last')
                        
                        # Count data points in this cycle
                        data_point_counts = []
                        if cycle.voltage_v:
                            data_point_counts.append(len(cycle.voltage_v))
                        if cycle.current_a:
                            data_point_counts.append(len(cycle.current_a))
                        if cycle.charge_capacity_ah:
                            data_point_counts.append(len(cycle.charge_capacity_ah))
                        if cycle.discharge_capacity_ah:
                            data_point_counts.append(len(cycle.discharge_capacity_ah))
                        if cycle.time_s:
                            data_point_counts.append(len(cycle.time_s))
                        if cycle.temperature_c:
                            data_point_counts.append(len(cycle.temperature_c))
                        
                        # Get the most common count (should be consistent)
                        if data_point_counts:
                            from collections import Counter
                            count_freq = Counter(data_point_counts)
                            most_common_count = count_freq.most_common(1)[0][0]
                            data_point_info = f" - {most_common_count} data points"
                            if len(set(data_point_counts)) > 1:
                                data_point_info += f" (inconsistent: {dict(count_freq)})"
                        else:
                            data_point_info = " - no data points"
                        
                        print(f'\nCycle {cycle.cycle_number} ({cycle_desc}){data_point_info}:')
                        print('--- Sample Data Point Details (first, second, middle, second last, last) ---\n')
                        
                        # Show voltage values (5 sample points)
                        if cycle.voltage_v:
                            voltage_sample = get_sample_points(cycle.voltage_v)
                            print(f'  voltage_v ({len(cycle.voltage_v)} points): {voltage_sample}')
                        
                        # Show current values (5 sample points)
                        if cycle.current_a:
                            current_sample = get_sample_points(cycle.current_a)
                            print(f'  current_a ({len(cycle.current_a)} points): {current_sample}')
                        
                        # Show capacity values (5 sample points)
                        if cycle.charge_capacity_ah:
                            charge_sample = get_sample_points(cycle.charge_capacity_ah)
                            print(f'  charge_capacity_ah ({len(cycle.charge_capacity_ah)} points): {charge_sample}')
                            
                        if cycle.discharge_capacity_ah:
                            discharge_sample = get_sample_points(cycle.discharge_capacity_ah)
                            print(f'  discharge_capacity_ah ({len(cycle.discharge_capacity_ah)} points): {discharge_sample}')
                        
                        # Show time values (5 sample points)
                        if cycle.time_s:
                            time_sample = get_sample_points(cycle.time_s)
                            print(f'  time_s ({len(cycle.time_s)} points): {time_sample}')
                        
                        # Show temperature values (5 sample points)
                        if cycle.temperature_c:
                            temp_sample = get_sample_points(cycle.temperature_c)
                            print(f'  temperature_c ({len(cycle.temperature_c)} points): {temp_sample}')
                        
                        # Show single-value features
                        if cycle.internal_resistance_ohm is not None:
                            print(f'  internal_resistance_ohm: {cycle.internal_resistance_ohm}')
                    
                    if len(val) > 3:
                        print(f'\n... and {len(val) - len(sample_cycles)} cycles not shown')
                    
                    print('--- End Cycle Details ---\n')
                        
            elif val is not None and val != []:
                print(f'{key}: {val}')

    @staticmethod
    def load(path):
        with open(path, 'rb') as fin:
            obj = pickle.load(fin)
        
        if obj.get('charge_protocol'):
            obj['charge_protocol'] = [
                CyclingProtocol(**protocol)
                for protocol in obj['charge_protocol']
            ]
        if obj.get('discharge_protocol'):
            obj['discharge_protocol'] = [
                CyclingProtocol(**protocol)
                for protocol in obj['discharge_protocol']
            ]
        if obj.get('cycles'):
            obj['cycles'] = [CycleRecord(**data) for data in obj['cycles']]
        
        return CellRecord(**obj)