import pandas as pd
import requests
import json
from datetime import datetime, timedelta
from typing import List,Union,Any,Dict,Optional 
import pyarrow 
import re
from typing import List, Tuple
import numpy as np
import os
import warnings
from dateutil import parser
import time 
import pandas as pd


# --- Helper Functions ---

def read_api_key(file_path):

    try:
        with open(file_path, 'r') as f:
            line = f.readline().strip()

            # Ensure the line is not empty and contains an '='
            if not line or '=' not in line:
                print(f"Error: The file '{file_path}' has an invalid format. Expected 'key=value'.")
                return None

            # Split the line at the first '=' to separate key and value
            key, value = line.split('=', 1)

            # Strip any surrounding whitespace from the value
            # and remove any potential quotes if they exist
            api_key = value.strip().strip('"').strip("'")
            
            # Check if the extracted value is empty
            if not api_key:
                print(f"Error: The API key value in '{file_path}' is empty.")
                return None
            
            return api_key

    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while reading the file: {e}")
        return None

def _load_raw_data(data: Union[str, pd.DataFrame], **kwargs):

    """Universal reader for CSV, Parquet, Excel, etc."""

    if isinstance(data, pd.DataFrame):
        return data.copy()
    
    if not isinstance(data, str):
        raise TypeError("Input must be a file path (str) or a pandas DataFrame.")

    if not os.path.exists(data):
        raise FileNotFoundError(f"File not found at '{data}'")

    file_extension = os.path.splitext(data)[1].lower()
    
    readers = {
        '.csv': pd.read_csv,
        '.tsv': lambda path, **kw: pd.read_csv(path, sep='\t', **kw),
        '.parquet': pd.read_parquet, '.pqt': pd.read_parquet,
        '.xls': pd.read_excel, '.xlsx': pd.read_excel,
        '.json': pd.read_json,
        '.html': lambda path, **kw: pd.read_html(path, **kw)[0]
    }

    if file_extension not in readers:
        
        raise ValueError(f"Unsupported file type: '{file_extension}'")

    try:
        
        df = readers[file_extension](data, **kwargs)
        df.columns = [col.lower() for col in df.columns]
        
        return df
    
    except Exception as e:
    
        raise RuntimeError(f"Error reading file: {e}")

def _validate_datetime_format(df: pd.DataFrame):
    
    """Helper function to handle complex datetime parsing logic."""

    valid_date_formats = [
        '%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%d %H:%M:%S.%f', '%d/%m/%Y %H:%M:%S.%f',
        '%d-%m-%Y %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M',
        '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ', '%d-%m-%Y',
        '%d/%m/%Y', '%d/%m/%Y %H:%M', '%d/%m/%Y %H:%M:%S', '%d-%m-%Y %H:%M:%S',
        '%d-%m-%Y %H:%M'
    ]

    for fmt in valid_date_formats:
    
        try:
    
            df['datetime'] = pd.to_datetime(df['datetime'], format=fmt)
    
            return df
    
        except (ValueError, TypeError):
    
            continue

    raise ValueError("Could not convert 'datetime' column to any supported format.")

# --- Main Functions ---

def ohlc_dataframe(data: Union[str, pd.DataFrame], **kwargs):
    
    df = _load_raw_data(data, **kwargs)
    current_cols = set(df.columns)
    
    required_ohlc = {'open', 'high', 'low', 'close'}
    
    if not required_ohlc.issubset(current_cols):
    
        raise ValueError(f"Missing OHLC columns: {required_ohlc - current_cols}")

    if 'datetime' in current_cols:
    
        return _validate_datetime_format(df)
    
    elif 'step' in current_cols:
    
        return df
    
    raise ValueError("DataFrame must contain 'datetime' or 'step'.")

def univariate_dataframe(data: Union[str, pd.DataFrame], **kwargs):
    
    df = _load_raw_data(data, **kwargs)
    
    current_cols = set(df.columns)
    
    if 'value' not in current_cols:
    
        raise ValueError("Univariate DataFrame must contain a 'value' column.")

    if 'datetime' in current_cols:
    
        return _validate_datetime_format(df)
    
    elif 'step' in current_cols:
    
        return df
    
    raise ValueError("DataFrame must contain 'datetime' or 'step'.")

def rmsf_dataframe(data: Union[str, pd.DataFrame], **kwargs):
    
    df = _load_raw_data(data, **kwargs)
    
    current_cols = set(df.columns)
    
    if 'rmsf' not in current_cols:
        raise ValueError("RMSF DataFrame must contain an 'rmsf' column.")

    if 'step' in current_cols:
        return df
        
    raise ValueError("RMSF DataFrame must contain 'step'.")


def dict_to_dataframe(response_dict: dict, datetime_col: str) -> pd.DataFrame:

    if not isinstance(response_dict, dict):
        raise ValueError("There was an issue with the API response. This often happens if your account hasn't been approved after signing up. Reach out to us at team@sumtyme.ai for assistance.")


    datetimes = []
    chains = []

    if not response_dict:
        return pd.DataFrame({datetime_col: [], 'chain_detected': []})

    for timestamp_str, data in response_dict.items():
        if not isinstance(data, dict) or 'chain_detected' not in data:
            raise KeyError(
                f"Invalid structure for timestamp '{timestamp_str}'. "
                "Expected a dictionary with 'chain_detected' key."
            )
        datetimes.append(timestamp_str)
        chains.append(data['chain_detected'])

    df = pd.DataFrame({
        datetime_col: datetimes,
        'chain_detected': chains
    })

    return df

def write_dict_entry_to_csv(data_dict: Dict[str, Any], filepath: str, separator: str = ','):
    
    HARDCODED_HEADERS = ['datetime', 'chain_detected']
    header_line = separator.join(HARDCODED_HEADERS)
    
    file_exists = os.path.exists(filepath)
    file_is_empty = file_exists and os.path.getsize(filepath) == 0
    file_is_new_or_empty = not file_exists or file_is_empty

    try:
        if file_is_new_or_empty:
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(header_line + '\n')
            
   
        if not data_dict:
            print("Warning: Input dictionary is empty. Skipping file write.")
            return

        try:
            datetime_str, chain_val = next(iter(data_dict.items()))
        except StopIteration:

            print("Warning: Could not extract key/value pair. Skipping file write.")
            return

        data_row_line = separator.join([str(datetime_str), str(chain_val)])


        with open(filepath, 'a', encoding='utf-8') as file:
            file.write(data_row_line + '\n')

    except Exception as e:
        print(f"An error occurred while writing the file: {e}")


class client:


    CAUSAL_OHLC = "/causal-chain/ohlc"
    CAUSAL_V2_OHLC = "/causal-chain/v2/ohlc"

    CAUSAL_UNIV = "/causal-chain/univariate"
    CAUSAL_V2_UNIV = "/causal-chain/v2/univariate"

    CAUSAL_V2_RMSF = "/causal-chain/v2/rmsf"

    def __init__(self, apikey: str = None):
           
        self.base_url = f"https://www.sumtyme.com"

        if apikey is None: # Check if apikey is None
            warnings.warn(
                "To obtain an API key, sign up for an account at www.sumtyme.ai/signup",
                UserWarning
            )

        else:
            self.api_key = apikey

            if not self.api_key:
                raise ValueError(
                    "To obtain an API key, sign up for an account at www.sumtyme.ai/signup"
                )

            print("Client initialised and API key loaded.")

    def send_post_request(self, path: str, payload: dict):
    
        full_url = f"{self.base_url}{path}"

        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }
        
        try:
            response = requests.post(full_url, json=payload, headers=headers)
           
            response.raise_for_status()
            response_data = response.json()

            return response_data
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err} - Response: {response.text}")
            raise
        except requests.exceptions.ConnectionError as conn_err:
            print(f"Connection error occurred: {conn_err}")
            raise
        except requests.exceptions.Timeout as timeout_err:
            print(f"Timeout error occurred: {timeout_err}")
            raise
        except json.JSONDecodeError as json_err:
            print(f"Failed to decode JSON response: {json_err} - Response text: {response.text}")
            raise
        except requests.exceptions.RequestException as req_err:
            print(f"An unexpected request error occurred: {req_err}")
            raise
        except Exception as e:
            print(f"An unexpected error occurred in send_post_request: {e}")
            raise

    @staticmethod
    def _ohlc_series_dict(df: pd.DataFrame, interval: int, interval_unit: str, reasoning_mode: str):
       
        # Validate input DataFrame type
        if not isinstance(df, pd.DataFrame):
            raise TypeError("Input 'df' must be a pandas DataFrame.")

        # Check for required columns
        required_columns = ['datetime', 'open', 'high', 'low', 'close']
        if not all(col in df.columns for col in required_columns):
            missing_cols = [col for col in required_columns if col not in df.columns]
            raise KeyError(f"DataFrame is missing required columns: {missing_cols}")
        
        # Return the formatted dictionary payload
        return {
            "datetime": df['datetime'].astype(str).tolist(),
            "open": df['open'].tolist(),
            "high": df['high'].tolist(),
            "low": df['low'].tolist(),
            "close": df['close'].tolist(),
            "interval": interval,
            "interval_unit": interval_unit,
            "reasoning_mode": reasoning_mode
        }

    @staticmethod
    def _ohlc_series_v2_dict(df: pd.DataFrame, reasoning_mode: str):
       
        # Validate input DataFrame type
        if not isinstance(df, pd.DataFrame):
            raise TypeError("Input 'df' must be a pandas DataFrame.")

        # Check for required columns
        required_columns = ['step', 'open', 'high', 'low', 'close']
        if not all(col in df.columns for col in required_columns):
            missing_cols = [col for col in required_columns if col not in df.columns]
            raise KeyError(f"DataFrame is missing required columns: {missing_cols}")
        
        # Return the formatted dictionary payload
        return {
            "step": df['step'].tolist(),
            "open": df['open'].tolist(),
            "high": df['high'].tolist(),
            "low": df['low'].tolist(),
            "close": df['close'].tolist(),
            "reasoning_mode": reasoning_mode
        }


    @staticmethod
    def _univariate_dict(df: pd.DataFrame, interval: int, interval_unit: str, reasoning_mode: str):
       
        # Validate input DataFrame type
        if not isinstance(df, pd.DataFrame):
            raise TypeError("Input 'df' must be a pandas DataFrame.")

        # Check for required columns
        required_columns = ['datetime', 'value']
        if not all(col in df.columns for col in required_columns):
            missing_cols = [col for col in required_columns if col not in df.columns]
            raise KeyError(f"DataFrame is missing required columns: {missing_cols}")
        
        # Return the formatted dictionary payload
        return {
            "datetime": df['datetime'].astype(str).tolist(),
            "value": df['value'].tolist(),
            "interval": interval,
            "interval_unit": interval_unit,
            "reasoning_mode": reasoning_mode
        }

    @staticmethod
    def _univariate_v2_dict(df: pd.DataFrame, reasoning_mode: str):
       
        # Validate input DataFrame type
        if not isinstance(df, pd.DataFrame):
            raise TypeError("Input 'df' must be a pandas DataFrame.")

        # Check for required columns
        required_columns = ['step', 'value']
        if not all(col in df.columns for col in required_columns):
            missing_cols = [col for col in required_columns if col not in df.columns]
            raise KeyError(f"DataFrame is missing required columns: {missing_cols}")
        
        # Return the formatted dictionary payload
        return {
            "step": df['step'].tolist(),
            "value": df['value'].tolist(),
            "reasoning_mode": reasoning_mode
        }

    @staticmethod
    def _rmsf_series_v2_dict(df: pd.DataFrame, reasoning_mode: str):
       
        # Validate input DataFrame type
        if not isinstance(df, pd.DataFrame):
            raise TypeError("Input 'df' must be a pandas DataFrame.")

        # Check for required columns
        required_columns = ['step', 'rmsf']
        if not all(col in df.columns for col in required_columns):
            missing_cols = [col for col in required_columns if col not in df.columns]
            raise KeyError(f"DataFrame is missing required columns: {missing_cols}")
        
        # Return the formatted dictionary payload
        return {
            "step": df['step'].tolist(),
            "rmsf": df['rmsf'].tolist(),     
            "reasoning_mode": reasoning_mode
        }


    def forecast_path(
        self,
        data_input: Union[str, pd.DataFrame],
        reasoning_mode: str = 'reactive',
        timeframe_dependent: bool = False,
        time_series_type: str = None,  
        rolling_path: bool = False,
        rolling_path_window_size: int = 5001,
        interval: Optional[int] = None,
        interval_unit: Optional[str] = None,
        rmsf_stability: Optional[int] = None,
        rolling_path_file_ouput: Optional[str] = None):

        if timeframe_dependent:
            if interval is None or interval_unit is None:
                raise ValueError("When 'timeframe_dependent' is True, both 'interval' and 'interval_unit' must be provided.")

        if time_series_type == 'ohlc':

            data = ohlc_dataframe(data_input)

            if timeframe_dependent == False:
                url = self.CAUSAL_V2_OHLC
                payload = self._ohlc_series_v2_dict(data,reasoning_mode)
            else:
                url = self.CAUSAL_OHLC
                payload = self._ohlc_series_dict(data,interval,interval_unit,reasoning_mode)
       
            
        elif time_series_type == 'univariate':

            data = univariate_dataframe(data_input)

            if timeframe_dependent == False:
                url = self.CAUSAL_V2_UNIV
                payload = self._univariate_v2_dict(data,reasoning_mode)
            else:
                url = self.CAUSAL_UNIV
                payload = self._univariate_dict(data,interval,interval_unit,reasoning_mode)

        elif time_series_type == 'rmsf':
            data = rmsf_dataframe(data_input)

            url = self.CAUSAL_V2_RMSF
            payload = self._rmsf_series_v2_dict(data,reasoning_mode)

        else:
            return ValueError('Time series type is invalid.')

        data_length = len(data)        

        if rolling_path == False:
            
            if not (5001 <= data_length <= 10000):
                raise ValueError(f"Number of data periods must be between 5001 and 10000. Got: {data_length}")
            
            response_dict = self.send_post_request(url, payload)

            return response_dict

        else: 

            if rolling_path_file_ouput == None:
                custom_stamp = datetime.now().date()

            else:
                custom_stamp = rolling_path_file_ouput
    
            for i in range(0, len(data) - rolling_path_window_size + 1, 1):
            
                try:
                            
                    if time_series_type == 'ohlc':

                        data = ohlc_dataframe(data_input)
                        window_df = data.iloc[i:i + rolling_path_window_size]

                        if timeframe_dependent == False:
                            url = self.CAUSAL_V2_OHLC
                            payload = self._ohlc_v2_series_dict(window_df,reasoning_mode)
                        else:
                            url = self.CAUSAL_OHLC
                            payload = self._ohlc_series_dict(window_df,interval,interval_unit,reasoning_mode)
                        
                    elif time_series_type == 'univariate':

                        data = univariate_dataframe(data_input)
                        window_df = data.iloc[i:i + rolling_path_window_size]

                        if timeframe_dependent == False:
                            url = self.CAUSAL_V2_UNIV
                            payload = self._univariate_v2_dict(window_df,reasoning_mode)
                        else:
                            url = self.CAUSAL_UNIV
                            payload = self._univariate_dict(window_df,interval,interval_unit,reasoning_mode)

                    elif time_series_type == 'rmsf':
                        data = rmsf_dataframe(data_input)
                        window_df = data.iloc[i:i + rolling_path_window_size]

                        url = self.CAUSAL_V2_RMSF
                        payload = self._rmsf_series_v2_dict(window_df,reasoning_mode)
            
                    response_dict = self.send_post_request(url, payload)

                    write_dict_entry_to_csv(response_dict, f'{custom_stamp}.csv', separator=',')

                except Exception as e:
                    print(f"Error processing rolling window for row {data.iloc[-1, 0]}: {e}")

    @staticmethod
    def timeframe_to_seconds(timeframe: str):
        """
        Converts a timeframe string to seconds, supporting resolutions
        from Planck time (pt) up to weeks (w).
        """
        if not isinstance(timeframe, str):
            return None

        # Matches: (Numeric value including scientific notation) + (Unit suffix)
        match = re.match(r'([\d.e+-]+)(pt|ys|zs|as|fs|ps|ns|us|ms|s|m|h|d|w)', timeframe)
        if not match:
            return None

        value_str, unit = match.group(1), match.group(2)

        try:
            value = float(value_str)
        except ValueError:
            return None

        # Conversion table relative to 1 second
        conversions = {
            'pt': 5.391247e-44, # planck time
            'ys': 1e-24,        # yoctosecond
            'zs': 1e-21,        # zeptosecond
            'as': 1e-18,        # attosecond
            'fs': 1e-15,        # femtosecond
            'ps': 1e-12,        # picosecond
            'ns': 1e-9,         # nanosecond
            'us': 1e-6,         # microsecond
            'ms': 1e-3,         # millisecond
            's':  1.0,          # second
            'm':  60.0,         # minute
            'h':  3600.0,       # hour
            'd':  86400.0,      # day
            'w':  604800.0      # week
        }

        return value * conversions.get(unit, 0.0)

    @staticmethod
    def track_causal_paths(combined_df: pd.DataFrame, sorted_timeframes: List[str]):

        highest_freq_tf = sorted_timeframes[0]
        hf_col = f'chain_detected_{highest_freq_tf}'

        # Identify every non-zero highest timeframe as a chain start
        hf_signals = combined_df[combined_df[hf_col].isin([1, -1])].copy()
        initial_indicators = []

        last_dir = None
        
        for i, row in hf_signals.iterrows():
            
            direction = int(row[hf_col])

            # Start new chain only on direction flips (1 -> -1 or -1 -> 1)
            if direction != last_dir:
                initial_indicators.append({
                    'propagation_id': f'Chain_{len(initial_indicators)+1}',
                    'datetime_start': row['datetime'],
                    'direction_type': direction,
                    'propagation_count': 0,
                    'status': 'Started'
                })
                last_dir = direction

        if initial_indicators == []: return pd.DataFrame(), pd.DataFrame()
        initial_df = pd.DataFrame(initial_indicators).set_index('propagation_id')
        propagations_list = []

        for chain_id, chain in initial_df.iterrows():
            current_dt = chain['datetime_start']
            direction = chain['direction_type']

            for j in range(1, len(sorted_timeframes)):
                target_tf = sorted_timeframes[j]
                target_col = f'chain_detected_{target_tf}'

                # Find the FIRST NON-ZERO signal in the target timeframe
                future = combined_df[(combined_df['datetime'] > current_dt) &
                                    (combined_df[target_col].isin([1, -1]))]

                if future.empty:
                    initial_df.loc[chain_id, 'status'] = f'Ended - No 1/-1 signals in {target_tf}'
                    break

                first_non_zero = future.iloc[0]

                # Check if that non-zero signal matches our direction
                if first_non_zero[target_col] == direction:
                    propagations_list.append({
                        'propagation_id': chain_id,
                        'level': j,
                        'datetime': first_non_zero['datetime'],
                        'direction': direction,
                        'timeframe': target_tf
                    })
                    current_dt = first_non_zero['datetime']
                    initial_df.loc[chain_id, 'propagation_count'] = j
                    if j == len(sorted_timeframes) - 1:
                        initial_df.loc[chain_id, 'status'] = 'Full Propagation'
                else:
                    initial_df.loc[chain_id, 'status'] = f'Did not propagate to {target_tf}'
                    break

        return initial_df.reset_index(), pd.DataFrame(propagations_list)


    def map_causal_chains(self,api_outputs):
    
        all_dfs = []

        for filename, tf in api_outputs:
            
            try:
            
                df = pd.read_csv(filename)[['datetime', 'chain_detected']]
                df['datetime'] = pd.to_datetime(df['datetime'])
                df['timeframe'] = tf
                all_dfs.append(df)
            
            except FileNotFoundError:
                print(f"File {filename} not found, skipping.")

        if not all_dfs: return

        # Combine data onto a single timeline
        all_dt = pd.concat([df['datetime'] for df in all_dfs]).unique()
        combined = pd.DataFrame({'datetime': all_dt}).sort_values('datetime')
        for df in all_dfs:
            tf = df['timeframe'].iloc[0]
            combined = pd.merge(combined,
                                df.rename(columns={'chain_detected': f'chain_detected_{tf}'}).drop(columns='timeframe'),
                                on='datetime', how='outer')

        # Fill NaNs with 0 and determine sorting order
        tfs = [f[1] for f in api_outputs if f[1] in [df['timeframe'].iloc[0] for df in all_dfs]]
        combined[[f'chain_detected_{tf}' for tf in tfs]] = combined[[f'chain_detected_{tf}' for tf in tfs]].fillna(0).astype(int)
        sorted_tfs = sorted(tfs, key=self.timeframe_to_seconds)

        # Run Analysis
        initial_df, details_df = self.track_causal_paths(combined, sorted_tfs)

        return(initial_df,details_df)

