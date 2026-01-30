from numpy import number
from .nsys_event import NsysEvent, ESD, RecordCol
import os.path
from sqlalchemy import text
import json
from fractions import Fraction
import pandas as pd
from typing import Any
from collections import defaultdict

event_type_nvtx_base = 9600
event_type_nvtx_nesmik = 81000
event_type_nvtx_nccl = 9500

class NVTXPushPopSimpleSemantic(NsysEvent):

    domains_dfs = []
    event_semantic_def_dict_per_domain: list[ESD] = []
    default_domain_type_map = {"Default": event_type_nvtx_base, "neSmiK": event_type_nvtx_nesmik, "NCCL": event_type_nvtx_nccl}
    default_category_type_map = {"default": 0}
    combined_record_columns: list[list[tuple[number | str, str]]] | list[tuple[number | str, str]] = []

    def __init__(self, report) -> None:
        super().__init__(report)
    
    def Setup(self):
        with open(os.path.join(os.path.dirname(__file__), '../scripts/nvtx_pushpop_simple.sql'), 'r') as query:
            self.query = text(query.read())

    def _preprocess(self):
        #self._df["domain"] = self._df["Name"].str.split(":").str[0]
        self._df = self._df.rename(columns={"PID":"Pid", "TID":"Tid"})
        return super()._preprocess()
    
    def get_event_semantic_definition_dictionary(self) -> list[ESD]:
        self._df.loc[self._df["domain"].isna(), "domain"] = "Default"
        self._df["domain_id"] = self._df["domain"].map(self.default_domain_type_map)
        # Assign rest of IDs
        self._df.loc[self._df["domain_id"].isna(), "domain_id"] = ((self._df[self._df["domain_id"].isna()].groupby("domain").ngroup() + 1) * 100 ) + event_type_nvtx_base
        self._df["domain_id"] = self._df["domain_id"].astype(int)
        domain_names = self._df[["domain_id", "domain"]].drop_duplicates().reset_index(drop=True)
        
        # Event and type information difers between domains. We should treat each domain DF as a different semantic really
        # We create lists to maintain separated dictionaries of semantic per domain
        domains_dfs = []
        combined_record_columns = []
        categories_names_per_domain = []
        payload_types_dictionaries_per_domain = []

        for dn in domain_names.itertuples():
            aux_d = self._df[self._df["domain"] == dn.domain]
            aux_d, aux_cn = self._get_categories_types(aux_d)
            aux_d, aux_rn = self._get_range_types(aux_d)

            # Now merge domain definition with categories to get the event semantic defintion dictionary
            aux_esdd: list[ESD] = []
            for i, r in aux_cn.iterrows():
                aux_esdd.append({
                    "name": f"NVTX {dn.domain} domain {r['category']} category",
                    "type": dn.domain_id + r['category_id'],
                    "names": aux_rn
                })

            if dn.domain == "NCCL":
                aux_d, pl_dict, pl_cols = self._extract_NCCL_payload(aux_d)
            else:
                aux_d, pl_dict, pl_cols = self._extract_generic_payload(aux_d, dn.domain, dn.domain_id + len(aux_esdd))

            aux_esdd += (pl_dict)

            aux_d.loc[:, "event_type"] = aux_d["domain_id"] + aux_d["category_id"]
            categories_names_per_domain.append(aux_esdd)
            combined_record_columns.append([("event_type", "event_value")]+pl_cols)
            domains_dfs.append(aux_d)
        self.domains_dfs = domains_dfs
        self.event_semantic_def_dict_per_domain = categories_names_per_domain
        self.combined_record_columns = combined_record_columns
        self.domain_names = domain_names

        return [x for xs in categories_names_per_domain for x in xs]
        

    def _parse_payload_with_strategy(self, cell, strategy='round', scale_factor=1000):
        """
        Parses the JSON payload and applies a specific integer transformation strategy.
        
        Strategies:
        - 'round': Rounds float to nearest int.
        - 'scale': Multiplies by scale_factor and casts to int.
        - 'string': Casts value to string.
        - 'fraction': Splits value into numerator and denominator columns.
        """
        # 1. Basic JSON Extraction
        if pd.isna(cell):
            return {}
        
        try:
            payload = json.loads(cell) if isinstance(cell, str) else cell
            data_list = payload.get('data')
        except (json.JSONDecodeError, TypeError, AttributeError):
            return {}

        if not isinstance(data_list, list) or len(data_list) == 0:
            return {}

        flat_payload = {}
        key_counters = defaultdict(int)

        def extract_values(key, value) -> None:
            """Recursively drills down lists to find the value wrapper dict."""
            if isinstance(value, list):
                for item in value:
                    extract_values(key, item)
            elif isinstance(value, dict):
                # leaf wrapper 
                if len(value) > 0:
                    
                    # Generate Name: key_0, key_1, etc.
                    idx = key_counters[key]
                    col_name = f"{key}_{idx}"
                    key_counters[key] += 1
                    
                    flat_payload[col_name] = value

        # Iterate over the main data list
        for item in data_list:
            if isinstance(item, dict):
                for key, value in item.items():
                    extract_values(key, value)

        parsed_row = {}
        
        # 2. Iterate and Transform
        for column_name, value_dict in flat_payload.items():
            if isinstance(value_dict, dict) and len(value_dict) > 0:
                # Extract raw value (e.g. 12.345)
                raw_value = list(value_dict.values())[0]
                struct_dtype = list(value_dict.keys())[0]
                
                try:
                    if struct_dtype in ["int32", "int64", "int16", "uint16", "uint32", "uint64"]:
                        parsed_row[column_name] = int(raw_value)
                    elif struct_dtype in ["float64", "float32", "float16"]:
                        # --- STRATEGY IMPLEMENTATIONS FOR FLOAT NUMBERS ---
                        if strategy == 'round':
                            # Option 1: Direct Rounding
                            parsed_row[column_name] = int(round(float(raw_value)))
                            
                        elif strategy == 'scale':
                            # Option 2: Scale and Truncate (Fixed Point)
                            # Example: 12.345 * 1000 -> 12345
                            scaled_val = float(raw_value) * scale_factor
                            parsed_row[column_name] = int(scaled_val)
                            
                        elif strategy == 'string':
                            # Option 3: Cast to String (for later Enum indexing)
                            parsed_row[column_name] = str(raw_value)
                            
                        elif strategy == 'fraction':
                            # Option 4: Fraction Expansion (Numerator/Denominator)
                            # Uses Python's Fraction library to find best integer approximation
                            f = Fraction(float(raw_value)).limit_denominator(1_000_000)
                            parsed_row[f"{column_name}_num"] = int(f.numerator)
                            parsed_row[f"{column_name}_denom"] = int(f.denominator)
                    else: # For other object-like string values
                        parsed_row[column_name] = raw_value
                        
                except (ValueError, TypeError):
                    # Handle cases where conversion fails
                    continue

        return parsed_row

    def _extract_generic_payload(self, df: pd.DataFrame, dn: str, next_available_et: int) -> tuple[pd.DataFrame, list[ESD], list[Any]]:
        df_aux = df.copy()

        json_expanded = df_aux['jsonText'].apply(lambda x: self._parse_payload_with_strategy(x, strategy='scale', scale_factor=1_000_000)).apply(pd.Series)
        df_aux = pd.concat([df_aux, json_expanded], axis=1)

        nccl_payload_event_dict: list[ESD] = [ESD(name=f"{col} in domain {dn}", type=(next_available_et + i), names=None) for i, col in enumerate(json_expanded.columns)]

        retrieval_cols = []
        for i, ev in enumerate(nccl_payload_event_dict):
            col = json_expanded.columns[i]
            if json_expanded.dtypes[col] == "object":
                df_aux[f"{col}_value"] = df_aux.groupby(col, dropna=True).ngroup() + 1
                df_aux[f"{col}_value"] = df_aux[f"{col}_value"].fillna(0).apply(int)
                unique_values = df_aux[[col, f"{col}_value"]].dropna().drop_duplicates()
                nccl_payload_event_dict[i]["names"] = pd.DataFrame({
                    f"Name": unique_values[col].tolist(),
                    f"event_value": unique_values[f"{col}_value"].tolist()
                })
                df_aux[col] = df_aux[f"{col}_value"]
            retrieval_cols.append(tuple([ev["type"], col]))
        return df_aux, nccl_payload_event_dict, retrieval_cols
    
    def _extract_NCCL_payload(self, df) -> tuple[pd.DataFrame, list[ESD], list[Any]]:
        df_aux = df.copy()
        df_aux["jsonText"] = df_aux["jsonText"].apply(lambda s: json.loads(s) if(pd.notna(s)) else '')
        json_expanded = pd.json_normalize(df_aux["jsonText"]).set_index(df_aux.index)
        json_expanded['payload_valid'] = json_expanded.notna().any(axis='columns')
        df_aux = pd.concat([df_aux.drop(columns=['jsonText']), json_expanded], axis=1)

        nccl_payload_event_dict: list[ESD] = [ESD(name=col, type=(event_type_nvtx_nccl + 1 + i), names=None) for i, col in enumerate(json_expanded.columns)]

        # Now complete with semantic, non-numeric types
        retrieval_cols = []
        for i, ev in enumerate(nccl_payload_event_dict):
            col = ev["name"]
            if json_expanded.dtypes[col] == "object":
                df_aux[f"{col}_value"] = df_aux.groupby(col, dropna=True).ngroup() + 1
                df_aux[f"{col}_value"] = df_aux[f"{col}_value"].fillna(0).apply(int)
                unique_values = df_aux[[col, f"{col}_value"]].dropna().drop_duplicates()
                nccl_payload_event_dict[i]["names"] = pd.DataFrame({
                    f"Name": unique_values[col].tolist(),
                    f"event_value": unique_values[f"{col}_value"].tolist()
                })
                df_aux[col] = df_aux[f"{col}_value"]
            retrieval_cols.append(tuple([ev["type"], col]))

        return (df_aux, nccl_payload_event_dict, retrieval_cols)
    
    def _get_categories_types(self, df):
        df.loc[df["category"].isna(), "category"] = "default"
        df.loc[:, "category_id"] = df["category"].map(self.default_category_type_map)
        df.loc[df["category_id"].isna(), "category_id"] = (df[df["category_id"].isna()].groupby("category").ngroup() + 1)
        df["category_id"] = df["category_id"].astype(int)
        categories_names = df[["category_id", "category"]].drop_duplicates()
        return (df, categories_names.reset_index(drop=True))

    def _get_range_types(self, df):
        df.loc[:, "event_value"] = df.groupby(["Name"]).ngroup() + 1
        ranges_names = df[['event_value', 'Name']].drop_duplicates()
        ranges_names.sort_values("event_value", inplace=True)
        return (df, ranges_names.reset_index(drop=True))
    
    def get_record_columns(self) -> list[list[RecordCol]] | list[RecordCol]:
        return self.combined_record_columns
    
    def get_df(self) -> pd.DataFrame | list[pd.DataFrame]:
        if len(self.domains_dfs) > 0:
            return [d for d in self.domains_dfs]
        else:
            return self._df.copy()
        
    def get_df_for_domain(self, dn: str) -> pd.DataFrame:
        idx = self.domain_names[self.domain_names["domain"] == dn].index
        if idx.empty:
            raise Exception("Domain does not exist in this NVTX data")
        else:
            return self.domains_dfs[idx.values[0]]
        
    def get_esdd_for_domain(self, dn: str) -> ESD:
        idx = self.domain_names[self.domain_names["domain"] == dn].index
        if idx.empty:
            raise Exception("Domain does not exist in this NVTX data")
        else:
            return self.event_semantic_def_dict_per_domain[idx.values[0]]

    def get_record_columns_for_domain(self, dn: str) -> list[RecordCol]:
        idx = self.domain_names[self.domain_names["domain"] == dn].index
        if idx.empty:
            raise Exception("Domain does not exist in this NVTX data")
        else:
            return self.combined_record_columns[idx.values[0]]