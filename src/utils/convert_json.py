import json
import numpy as np
import pandas as pd




#Not Used
def is_json_string(x):
    try:
        json.loads(x)
        return True
    except (TypeError, json.JSONDecodeError):
        return False

#Not Used
def is_array_like(x):
    return isinstance(x, (list, tuple, np.ndarray))


#Not Used
def df_to_clean_json(df: pd.DataFrame, array_detection_threshold: float = 0.5):
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input 'df' must be a pandas DataFrame.")
    if not 0 <= array_detection_threshold <= 1:
        raise ValueError("array_detection_threshold must be in the range [0, 1]")

    df_copy = df.copy()

    json_cols = []
    for col in df_copy.columns:
        if df_copy[col].apply(lambda x: isinstance(x, str) and is_json_string(x)).any():
            json_cols.append(col)

    for col in json_cols:
        df_copy[col] = df_copy[col].apply(
            lambda x: json.loads(x) if isinstance(x, str) else x
        )

    array_cols = []
    potential_array_cols = df_copy.select_dtypes(include=["object"]).columns

    for col in potential_array_cols:
        non_null_values = df_copy[col].dropna()
        if non_null_values.empty:
            continue

        try:
            is_array_flags = non_null_values.apply(is_array_like)
            array_like_count = is_array_flags.sum()
            total_non_null = len(non_null_values)

            if total_non_null > 0:
                array_like_ratio = array_like_count / total_non_null
                if array_like_ratio >= array_detection_threshold:
                    array_cols.append(col)

        except Exception as e:
            print(f"Warning: Could not process column '{col}' for array detection: {e}")
            continue

    if not array_cols:
        return df_copy, None

    df_no_array = df_copy.drop(columns=array_cols)

    df_array_raw = df_copy[array_cols].copy()
    for col in array_cols:
        mask_notna = df_array_raw[col].notna()
        df_array_raw.loc[mask_notna, col] = df_array_raw.loc[mask_notna, col].apply(
            lambda x: ",".join(map(str, x)) if is_array_like(x) else str(x)
        )

    array_json = df_array_raw.to_json(
        orient="records", indent=2, force_ascii=False, default_handler=str
    )

    return df_no_array, array_json
