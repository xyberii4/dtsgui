import csv
from datetime import datetime
import numpy as np
import copy


class ThermaCSVData:
    def __init__(self, depths: np.ndarray, times: list, temperatures: np.ndarray):
        self.depths = depths
        self.times = times
        self.temperatures = temperatures

    @classmethod
    def from_file(cls, path: str) -> 'ThermaCSVData':
        """Parse Therma CSV format and return a ThermaCSVData instance."""
        with open(path, 'r', newline='', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            # Row 1: Header (e.g. 'Depth [m]', 'Temperature [degC]')
            next(reader)
            
            # Row 2: Times (first column empty, then datetime strings)
            time_row = next(reader)
            times = []
            for t_str in time_row[1:]:
                if t_str.strip():
                    times.append(datetime.strptime(t_str.strip(), '%Y-%m-%d %H:%M:%S'))
                    
            # Row 3+: Depths and temperatures
            depths = []
            temperatures = []
            
            for row in reader:
                if not row or not row[0].strip():
                    continue
                depths.append(float(row[0]))
                
                # Extract temperatures for this depth
                temp_row = []
                # We only want as many temperatures as there are times
                for i in range(1, len(times) + 1):
                    if i < len(row) and row[i].strip():
                        temp_row.append(float(row[i]))
                    else:
                        temp_row.append(np.nan)
                temperatures.append(temp_row)
                
        depths_arr = np.array(depths)
        # temperatures is currently (n_depths, n_times). 
        # Transpose to (n_times, n_depths) for consistency with DTS convention
        temp_arr = np.array(temperatures).T
        
        return cls(depths_arr, times, temp_arr)
        
    def auto_clip_depth(self) -> tuple:
        """Auto-detect valid borehole range by finding contiguous valid data from the top."""
        last_valid_idx = 0
        for j in range(len(self.depths)):
            depth_temps = self.temperatures[:, j]
            # If we hit extreme values, we reached the end of the useful cable
            if np.any(depth_temps < -100) or np.any(depth_temps > 100):
                break
            last_valid_idx = j
                
        min_depth = self.depths[0]
        max_depth = self.depths[last_valid_idx]
        
        return float(min_depth), float(max_depth)
        
    def get_clipped(self, depth_min=None, depth_max=None) -> 'ThermaCSVData':
        """Return a new ThermaCSVData clipped to the given depth range."""
        if depth_min is None:
            depth_min = self.depths[0]
        if depth_max is None:
            depth_max = self.depths[-1]
            
        mask = (self.depths >= depth_min) & (self.depths <= depth_max)
        
        new_depths = self.depths[mask]
        # self.temperatures is (n_times, n_depths)
        new_temps = self.temperatures[:, mask]
        
        return ThermaCSVData(new_depths, copy.copy(self.times), new_temps)
