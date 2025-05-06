import json
import os
import re

import pandas as pd


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
        raise Exception(f"Lỗi khi đọc nội dung CSV thành dataframe: {str(e)}")


# # Xử lý dữ liệu CSV
# def preprocess_csv_data(df):
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
        file_path = "assets/column_definition/overview_prod.txt"
    elif screen_type == "customer_overview":
        file_path = "assets/column_definition/overview_cus.txt"
    elif screen_type == "business_overview":
        file_path = "assets/column_definition/overview_bussiness.txt"
    elif screen_type == "customer_segmentation":
        file_path = "assets/column_definition/segment_cus.txt"

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


# Lọc DataFrame theo các cột được chỉ định (columns)
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


# Lọc DataFrame theo thời gian được chọn (rows)
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
    filtered_df = df[
        df["timeframe_type"].str.contains(filter_keyword, case=False)
    ].copy()

    if filtered_df.empty:
        raise Exception(f"Không tìm thấy dữ liệu phù hợp với từ khóa: {filter_keyword}")

    return filtered_df


# Kiểm tra dữ liệu đầu vào:
def validate_data(df):
    """
    Kiểm tra dữ liệu DataFrame:
    1. Dòng Header: thiếu, thừa, sai tên cột, ký tự lạ
    2. Cấu trúc Array không hợp lệ: thiếu [], dấu phẩy, dấu nháy không đúng
    """
    # Kiểm tra DataFrame có rỗng không
    if df is None or df.empty:
        raise Exception("DataFrame trống, vui lòng kiểm tra lại dữ liệu đầu vào.")

    # Kiểm tra header
    if len(df.columns) < 2:
        raise Exception("DataFrame không hợp lệ, cần có ít nhất 2 cột.")

    # Kiểm tra các ký tự đặc biệt trong tên cột
    invalid_chars_pattern = r"[^\w\s\-_]"  # Không cho phép ký tự đặc biệt ngoài chữ, số, khoảng trắng, gạch ngang, gạch dưới
    for col in df.columns:
        col_name = str(col)
        if re.search(invalid_chars_pattern, col_name) and not (
            col_name.startswith('"') and col_name.endswith('"')
        ):
            raise Exception(f"Tên cột '{col_name}' chứa ký tự không hợp lệ.")

    # Kiểm tra header có trùng nhau không
    if len(df.columns) != len(set(df.columns)):
        raise Exception("Có tên cột bị trùng lặp trong DataFrame.")

    # Kiểm tra cấu trúc Array trong các giá trị
    for col in df.columns:
        for idx, val in df[col].items():
            if pd.isna(val):
                continue
            val_str = str(val).strip()
            # Nếu là array (bắt đầu bằng [ và kết thúc bằng ])
            if val_str.startswith("[") and val_str.endswith("]"):
                # Kiểm tra JSON hợp lệ
                try:
                    json.loads(val_str)
                except json.JSONDecodeError as e:
                    raise Exception(
                        f"Lỗi cấu trúc array tại dòng {idx+1}, cột '{col}': {str(e)}"
                    )
                continue
            # Nếu là số đơn giản (int, float), bỏ qua
            try:
                float_val = float(val_str)
                continue
            except Exception:
                pass
            if "," in val_str or ";" in val_str:
                raise Exception(
                    f"Lỗi: Ô dữ liệu tại dòng {idx+1}, cột '{col}' có nhiều giá trị nhưng không phải dạng array (phải nằm trong [ ]). Giá trị: {val_str}"
                )
    return {"valid": True}


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
