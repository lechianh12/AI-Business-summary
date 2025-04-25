import json
import os

import pandas as pd


def read_csv_content(file_content, encoding="utf-8-sig"):
    try:
        if isinstance(file_content, bytes):
            df = pd.read_csv(pd.io.common.BytesIO(file_content), encoding=encoding)
        else:
            df = pd.read_csv(pd.io.common.StringIO(file_content), encoding=encoding)
        return df
    except Exception as e:
        raise Exception(f"Lỗi khi đọc nội dung CSV: {str(e)}")


def preprocess_csv_data(df):
    df = df.copy()
    try:
        numeric_columns = df.select_dtypes(include=["number"]).columns
        for col in numeric_columns:
            df.loc[:, col] = df[col].fillna(0)
        non_numeric_columns = df.select_dtypes(exclude=["number"]).columns
        for col in non_numeric_columns:
            df.loc[:, col] = df[col].fillna("")
        for col in df.columns:
            if df[col].dtype == "object":
                sample = df[col].dropna().iloc[0] if not df[col].dropna().empty else ""
                if (
                    isinstance(sample, str)
                    and sample.startswith("[")
                    and sample.endswith("]")
                ):
                    try:
                        df.loc[:, col] = df[col].apply(
                            lambda x: (
                                json.loads(x) if isinstance(x, str) and x.strip() else x
                            )
                        )
                    except Exception:
                        pass
        csv_text = df.to_csv(index=False)
        stats = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "numeric_columns": list(numeric_columns),
            "sample_rows": df.head(3).to_dict(orient="records"),
        }
        date_columns = [
            col for col in df.columns if "date" in col.lower() or "time" in col.lower()
        ]
        if date_columns:
            for date_col in date_columns:
                try:
                    df.loc[:, date_col] = pd.to_datetime(
                        df[date_col], errors="coerce", format="%m-%d-%Y"
                    )
                    if not df[date_col].isna().all():
                        stats[f"{date_col}_range"] = {
                            "min": df[date_col].min().strftime("%Y-%m-%d"),
                            "max": df[date_col].max().strftime("%Y-%m-%d"),
                        }
                except Exception:
                    pass
        return {"dataframe": df, "csv_text": csv_text, "stats": stats}
    except Exception as e:
        raise Exception(f"Lỗi khi xử lý dữ liệu CSV: {str(e)}")


def get_columns_for_screen(screen_type):
    columns = []
    file_path = None
    if screen_type == "product_overview":
        file_path = "assets/column_data/overview_prod.txt"
    elif screen_type == "customer_overview":
        file_path = "assets/column_data/overview_cus.txt"
    if file_path and os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                lines = file.readlines()
            for line in lines:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "•" in line:
                    parts = line.split(":", 1)
                    col_part = parts[0].strip()
                    col_name = col_part.replace("•", "").strip()
                    columns.append(col_name)
        except Exception as e:
            print(f"Lỗi khi đọc file {file_path}: {str(e)}")
    return columns


def filter_by_timeframe(df, time_period):
    if "timeframe_type" in df.columns:
        return df[df["timeframe_type"] == time_period]
    return df


def process_csv_for_screen(processed_data, column_list):
    df = processed_data["dataframe"]
    filtered_df = df[column_list] if column_list else df
    filtered_csv_text = filtered_df.to_csv(index=False)
    filtered_data = {
        "dataframe": filtered_df,
        "csv_text": filtered_csv_text,
        "stats": processed_data["stats"],
    }
    return filtered_data, filtered_df
