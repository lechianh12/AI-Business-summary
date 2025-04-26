import json
import os
import re

import pandas as pd
from fastapi import HTTPException

# Đọc file csv và encoding UTF-8 BOM
def read_csv_content(file_content, encoding="utf-8-sig"):
    try:
        # Convert content to DataFrame
        if isinstance(file_content, bytes):
            df = pd.read_csv(pd.io.common.BytesIO(file_content), encoding=encoding)
        else:
            df = pd.read_csv(pd.io.common.StringIO(file_content), encoding=encoding)

        return df
    except Exception as e:
        raise Exception(f"Lỗi khi đọc nội dung CSV: {str(e)}")


# Xử lý dữ liệu CSV
def preprocess_csv_data(df):
    """
    Args:df
    Returns: dict chứa df
    """
    # Tạo bản sao để tránh cảnh báo SettingWithCopyWarning
    df = df.copy()

    # Basic data cleaning
    try:
        # Handle missing values for numerical columns
        numeric_columns = df.select_dtypes(include=["number"]).columns
        for col in numeric_columns:
            df.loc[:, col] = df[col].fillna(0)

        # Handle missing values for non-numerical columns
        non_numeric_columns = df.select_dtypes(exclude=["number"]).columns
        for col in non_numeric_columns:
            df.loc[:, col] = df[col].fillna("")

        # Process columns with list-like strings (convert string representations to actual lists)
        for col in df.columns:
            if df[col].dtype == "object":
                # Check if column has list-like strings
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
                    except Exception:  # If conversion fails, keep as is
                        pass

        # Create a clean CSV string representation
        csv_text = df.to_csv(index=False)

        # Add basic statistics for quick reference
        stats = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "numeric_columns": list(numeric_columns),
            "sample_rows": df.head(3).to_dict(orient="records"),
        }

        # If there's a date/time column, add time range info
        date_columns = [
            col for col in df.columns if "date" in col.lower() or "time" in col.lower()
        ]
        # fix lỗi SettingWithCopyWarning
        if date_columns:
            for date_col in date_columns:
                try:
                    # Chỉ định định dạng cụ thể nếu biết
                    df.loc[:, date_col] = pd.to_datetime(
                        df[date_col], errors="coerce", format="%m-%d-%Y"
                    )

                    # Kiểm tra xem chuyển đổi có thành công không trước khi lấy min, max
                    if not df[date_col].isna().all():
                        stats[f"{date_col}_range"] = {
                            "min": df[date_col].min().strftime("%Y-%m-%d"),
                            "max": df[date_col].max().strftime("%Y-%m-%d"),
                        }
                except Exception:
                    pass

        # Return processed data
        return {"dataframe": df, "csv_text": csv_text, "stats": stats}

    except Exception as e:
        raise Exception(f"Lỗi khi xử lý dữ liệu CSV: {str(e)}")

# Lấy danh sách các cột cần thiết dựa trên loại màn hình
def get_columns_for_screen(screen_type):
    """
    Lấy danh sách các cột cần hiển thị dựa trên loại màn hình.
    Args:
        screen_type (str): Loại màn hình.
    Returns:
        list: Danh sách các cột cần hiển thị.
    """
    columns = []
    file_path = None

    # Xác định file để đọc dựa trên loại màn hình
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
                # Bỏ qua dòng trống hoặc dòng comment
                if not line or line.startswith("#"):
                    continue

                # Tách lấy tên cột (phần trước dấu :)
                if "•" in line:
                    parts = line.split(":", 1)
                    col_part = parts[0].strip()
                    # Loại bỏ ký tự bullet (•) và khoảng trắng
                    col_name = col_part.replace("•", "").strip()
                    columns.append(col_name)
        except Exception as e:
            print(f"Lỗi khi đọc file {file_path}: {str(e)}")

    return columns


# Lọc DataFrame theo các cột được chỉ định (hàng dọc)
def process_csv_for_screen(processed_data, column_list):
    """
    Lọc DataFrame để chỉ giữ các cột được chỉ định.
    Args:
        processed_data (dict).
        column_list (list): Danh sách các cột cần giữ lại.
    Returns:
        dict: Dữ liệu mới với chỉ các cột đã chọn.
    """
    df = processed_data["dataframe"]

    # Lọc các cột tồn tại trong DataFrame
    valid_columns = [col for col in column_list if col in df.columns]

    if valid_columns:
        # Sử dụng loc để tạo một bản sao mới của DataFrame với các cột đã chọn
        filtered_df = df.loc[:, valid_columns].copy()

        # Tạo CSV text mới
        filtered_csv_text = filtered_df.to_csv(index=False)

        # Cập nhật thống kê
        filtered_stats = {
            "row_count": len(filtered_df),
            "column_count": len(filtered_df.columns),
            "columns": list(filtered_df.columns),
            "numeric_columns": list(
                filtered_df.select_dtypes(include=["number"]).columns
            ),
            "sample_rows": filtered_df.head(3).to_dict(orient="records"),
        }

        return {
            "dataframe": filtered_df,
            "csv_text": filtered_csv_text,
            "stats": filtered_stats,
        }, filtered_df
    else:
        # Trả về dữ liệu gốc nếu không có cột nào hợp lệ
        return processed_data, df


#Lọc DataFrame theo thời gian được chọn (hàng ngang)
def filter_by_timeframe(df, time_period):
    """
    Lọc dữ liệu dựa vào timeframe_type
    Args:
        df : raw
        time_period (str)
    Returns:
        DataFrame đã lọc chỉ chứa dữ liệu liên quan đến time_period
    """
    if "timeframe_type" not in df.columns:
        raise Exception("DataFrame không có cột timeframe_type để lọc theo thời gian")

    # Xác định từ khóa tìm kiếm dựa trên time_period
    filter_keyword = ""
    if time_period == "month_current":
        filter_keyword = "tháng"
    elif time_period == "days_7":
        filter_keyword = "7 ngày"
    elif time_period == "days_30":
        filter_keyword = "30 ngày"
    else:
        raise Exception(f"Loại thời gian không được hỗ trợ: {time_period}")

    # Lọc dữ liệu chỉ giữ các hàng có timeframe_type chứa từ khóa phù hợp, và tạo bản sao
    # fix lỗi SettingWithCopyWarning
    filtered_df = df[
        df["timeframe_type"].str.contains(filter_keyword, case=False)
    ].copy()

    if filtered_df.empty:
        raise Exception(f"Không tìm thấy dữ liệu phù hợp với từ khóa: {filter_keyword}")

    return filtered_df


#Kiểm tra dữ liệu đầu vào:
def validate_data(raw_csv_content, expected_columns=None, log_func=print):
    """
    Kiểm tra dữ liệu đầu vào:
    1. Không đồng nhất về dấu phân cách: Chỉ cho phép , hoặc ;
    2. Dòng Header bị lỗi: thiếu, thừa, sai tên cột, ký tự lạ
    3. Cấu trúc Array không hợp lệ: thiếu [], dấu phẩy, dấu nháy không đúng
    Nếu có lỗi sẽ log bug qua log_func.
    """

    bugs = []
    # 1. Kiểm tra dấu phân cách
    lines = raw_csv_content.splitlines()
    sep_candidates = [",", ";"]
    sep_count = {sep: 0 for sep in sep_candidates}
    for line in lines[:10]:
        for sep in sep_candidates:
            sep_count[sep] += line.count(sep)
    main_sep = max(sep_count, key=sep_count.get)
    for line in lines[:10]:
        if "," in line and ";" in line:
            raise Exception("Không đồng nhất về dấu phân cách trên dòng: " + line)

    # 2. Kiểm tra header
    import csv
    import io

    sniffer = csv.Sniffer()
    try:
        dialect = sniffer.sniff(raw_csv_content, delimiters=",;")
        reader = csv.reader(io.StringIO(raw_csv_content), dialect)
        header = next(reader)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Lỗi đọc header: {e}")
        header = []
    if expected_columns:
        if len(header) != len(expected_columns):
            bugs.append(
                f"Header bị thiếu/thừa cột. Header: {header}, Định nghĩa: {expected_columns}"
            )
        for h, e in zip(header, expected_columns):
            if h.strip() != e.strip():
                bugs.append(f"Sai tên cột: {h} (mong đợi: {e})")
        for h in header:
            if re.search(r"[^\w\d_ ]", h):
                bugs.append(f"Header có ký tự không mong muốn: {h}")

    # 3. Kiểm tra array
    array_pattern = re.compile(r"\[.*?\]")
    for i, line in enumerate(lines[1:]):
        arrays = re.findall(array_pattern, line)
        for arr in arrays:
            if not arr.startswith("[") or not arr.endswith("]"):
                bugs.append(f"Array không có ngoặc vuông đúng ở dòng {i+2}: {arr}")
            if "," not in arr and ";" not in arr:
                bugs.append(f"Array thiếu dấu phân cách phần tử ở dòng {i+2}: {arr}")
            if (
                re.search(r'"[^"]*"', arr) is None
                and re.search(r"'[^']*'", arr) is None
            ):
                bugs.append(f"Array thiếu dấu nháy bao quanh chuỗi ở dòng {i+2}: {arr}")
    # Log bug
    for bug in bugs:
        log_func("[BUG] " + bug)
    return bugs


# utils cho systemprompt
def read_column_data(column_file_path):
    """Đọc file chứa thông tin về các cột và trả về nội dung của file."""
    try:
        with open(column_file_path, "r", encoding="utf-8") as file:
            content = file.read().strip()
        return content
    except Exception as e:
        print(f"Lỗi khi đọc file {column_file_path}: {str(e)}")
        return ""
