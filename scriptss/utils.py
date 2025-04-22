import glob
import json
import os

import numpy as np
import pandas as pd

from scriptss.config import COLUMNS_TO_SET_NULL


# Chia file tổng hợp thành nhiều file theo retailer_id và lưu vào thư mục con với tên file gốc
def split_csv_by_retailer_id(input_path=None, output_dir=None):
    """
    Chia file tổng hợp thành nhiều file theo retailer_id và lưu vào thư mục con với tên file gốc
    Args:
        input_path: Đường dẫn đến file CSV cần chia
        output_dir: Thư mục để lưu kết quả
    """
    # Sử dụng giá trị mặc định nếu không được cung cấp
    if input_path is None:
        input_path = "assets/Agg_data/*.csv"

    if output_dir is None:
        output_dir = "assets/retailer_data"

    # Tạo thư mục retailer_data nếu chưa tồn tại
    os.makedirs(output_dir, exist_ok=True)

    # Lấy danh sách file CSV dựa trên input_path
    if "*" in input_path:
        # Nếu input_path chứa ký tự đại diện, sử dụng glob
        csv_files = glob.glob(input_path)
    else:
        # Nếu input_path là một file cụ thể
        csv_files = [input_path]

    for file_path in csv_files:
        print(f"Processing: {file_path}")

        # Lấy tên file gốc không có phần mở rộng
        original_filename = os.path.splitext(os.path.basename(file_path))[0]

        # Tạo thư mục con với tên file gốc
        subfolder_path = os.path.join(output_dir, original_filename)
        os.makedirs(subfolder_path, exist_ok=True)

        # Đọc file CSV với encoding được chỉ định
        try:
            # Thử với utf-8 trước
            df = pd.read_csv(file_path, encoding="utf-8")
        except UnicodeDecodeError:
            # Nếu thất bại, thử với các encoding phổ biến khác
            try:
                df = pd.read_csv(file_path, encoding="latin1")
            except Exception as e:
                print(
                    f"Error: Unable to read {file_path} with common encodings. {str(e)}. Skipping."
                )
                continue

        # Kiểm tra xem cột retailer_id có tồn tại không
        if "retailer_id" not in df.columns:
            print(f"Warning: 'retailer_id' column not found in {file_path}. Skipping.")
            continue

        # Lấy các retailer_id duy nhất
        retailer_ids = df["retailer_id"].unique()

        # Với mỗi retailer_id, tạo một file CSV mới
        for retailer_id in retailer_ids:
            # Lọc dữ liệu cho retailer_id hiện tại
            retailer_data = df[df["retailer_id"] == retailer_id]

            # Tạo tên file đầu ra
            output_filename = f"{subfolder_path}/retailer_{retailer_id}.csv"

            # Lưu vào CSV với UTF-8 BOM encoding
            retailer_data.to_csv(output_filename, index=False, encoding="utf-8-sig")
            print(f"Created: {output_filename} with {len(retailer_data)} rows")

    print("CSV splitting completed.")


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
                    df.loc[:, date_col] = pd.to_datetime(df[date_col], errors="coerce")

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


# Lưu danh sách tên cột vào file
def save_column_names(df, output_path="assets/column_definitions/column_name.txt"):
    try:
        # Đảm bảo thư mục tồn tại
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Tạo nội dung với gạch đầu dòng cho mỗi tên cột
        column_names = [f"- {col}" for col in df.columns]
        content = "\n".join(column_names)

        # Ghi vào file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"Đã lưu danh sách {len(df.columns)} tên cột vào {output_path}")
    except Exception as e:
        print(f"Lỗi khi lưu danh sách tên cột: {str(e)}")


# Xử lý dữ liệu CSV và lưu danh sách tên cột
def process_csv_for_model(file_content, encoding="utf-8-sig"):
    try:
        # Đọc nội dung CSV thành DataFrame
        df = read_csv_content(file_content, encoding)

        # Xử lý dữ liệu
        result = preprocess_csv_data(df)

        # Lưu danh sách tên cột vào file
        save_column_names(result["dataframe"])

        return result
    except Exception as e:
        raise Exception(f"Error processing CSV: {str(e)}")


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


# Lọc DataFrame theo các cột được chỉ định
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


def read_column_data(column_file_path):
    """Đọc file chứa thông tin về các cột và trả về nội dung của file."""
    try:
        with open(column_file_path, "r", encoding="utf-8") as file:
            content = file.read().strip()
        return content
    except Exception as e:
        print(f"Lỗi khi đọc file {column_file_path}: {str(e)}")
        return ""


def extract_column_definitions(column_content):
    """Trích xuất định nghĩa cột từ nội dung file, bỏ qua phần comment(#)."""
    lines = column_content.split("\n")
    column_definitions = []

    for line in lines:
        # Bỏ qua các dòng comment bắt đầu bằng # hoặc dòng trống
        if line.strip() and not line.strip().startswith("#"):
            column_definitions.append(line)

    return "\n".join(column_definitions)


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


def print_response_time(func_name, start_time, end_time):
    """
    In ra thời gian phản hồi của một hàm.

    Args:
        func_name (str): Tên hàm/quá trình được đo
        start_time (float): Thời gian bắt đầu
        end_time (float): Thời gian kết thúc
    """
    elapsed_time = end_time - start_time
    print(f"{func_name} thực hiện trong: {elapsed_time:.2f} giây")


def validate_data(df):
    # Tạo bản sao để tránh cảnh báo SettingWithCopyWarning
    df = df.copy()

    bool_check = False
    bool_1 = True
    bool_2 = True
    bool_3 = True

    save_i = 0
    save_i_2 = 0
    save_i_3 = 0
    # Phep tru
    col = ["total_revenue", "net_revenue"]
    col_minus = ["total_return_revenue", "total_cost"]
    results = ["net_revenue", "gross_profit"]

    # Phep nhan
    col_2 = [
        "net_revenue",
        "gross_profit",
        "total_revenue",
        "loyal",
        "promising",
        "explore",
        "risk",
        "sleep",
    ]
    col_divide = [
        "total_quantity",
        "total_quantity",
        "num_invoice_return",
        "total_custmer",
        "total_custmer",
        "total_custmer",
        "total_custmer",
        "total_custmer",
    ]
    results_2 = [
        "avg_net_revenue",
        "avg_profit",
        "evg_order_value",
        "loyal_proportion",
        "promising_proportion",
        "explore_proportion",
        "risk_proportion",
        "sleep_proportion",
    ]

    # Phep cong
    col3 = ["old_customer"]
    col_plus = ["revenue_new_customer"]
    col_plus_2 = ["unknown_customer"]
    results_3 = ["total_custmer"]

    for i in range(len(col)):
        if df[col[i]] - df[col_minus[i]] != df[results[i]]:
            bool_1 = False
            save_i = i

    # Thêm dung sai cho phép chia để xử lý làm tròn số
    tolerance = 0.2  # Có thể điều chỉnh dung sai này
    for i in range(len(col_2)):
        calculated = df[col_2[i]] / df[col_divide[i]]
        difference = abs(calculated - df[results_2[i]])
        if difference.max() > tolerance:  # Kiểm tra sai số lớn nhất
            bool_2 = False
            save_i_2 = i

    for i in range(len(col3)):
        if df[col3[i]] + df[col_plus[i]] + df[col_plus_2[i]] != df[results_3[i]]:
            bool_3 = False
            save_i_3 = i

    if not bool_1:
        print(
            "Dữ liệu tính sai ở cột: "
            + df[col[save_i]]
            + " và "
            + df[col_minus[save_i]]
            + " và "
            + df[results[save_i]]
        )
    if not bool_2:
        print(
            "Dữ liệu tính sai ở cột: "
            + df[col_2[save_i_2]]
            + " và "
            + df[col_divide[save_i_2]]
            + " và "
            + df[results_2[save_i_2]]
        )
    if not bool_3:
        print(
            "Dữ liệu tính sai ở cột: "
            + df[col3[save_i_3]]
            + " và "
            + df[col_plus[save_i_3]]
            + " và "
            + df[col_plus_2[save_i_3]]
            + " và "
            + df[results_3[save_i_3]]
        )

    if bool_1 and bool_2 and bool_3:
        bool_check = True

    return bool_check


def set_null_values_for_previous_periods(df):
    """
    Set giá trị null cho các cột được chỉ định lọc theo timeframe_type
    Args:
        DataFrame đã lọc timeframe_type
    Returns:
        DataFrame đã được xử lý, với giá trị null cho các cột được chỉ định trong dữ liệu kì trước
    """
    # Tạo bản sao để tránh SettingWithCopyWarning
    df = df.copy()

    # Danh sách các cột cần set giá trị là null cho dữ liệu kì trước
    columns_to_set_null = COLUMNS_TO_SET_NULL

    # Lọc ra các hàng thuộc dữ liệu kì trước dựa trên timeframe_type
    previous_period_mask = df["timeframe_type"].str.contains(
        "trước đó", case=False
    ) | df["timeframe_type"].str.contains("tháng trước", case=False)

    # Kiểm tra các cột tồn tại trong DataFrame
    valid_columns = [col for col in columns_to_set_null if col in df.columns]

    if valid_columns:
        # Set giá trị null cho các cột được chỉ định trong dữ liệu kì trước
        for col in valid_columns:
            df.loc[previous_period_mask, col] = None
    else:
        # Nếu không tìm thấy các cột đã chỉ định, thử tìm theo cách khác
        # Ví dụ: tìm các cột có chứa từ khóa cụ thể
        potential_columns = []
        for col in df.columns:
            # Kiểm tra xem cột có chứa bất kỳ từ khóa nào
            if any(
                keyword.lower() in col.lower()
                for keyword in [
                    "product_rev",
                    "product_quantity",
                    "product_profit",
                    "group_quantity",
                    "group_rev",
                    "group_profit",
                ]
            ):
                potential_columns.append(col)

        # Set giá trị null cho các cột được tìm thấy trong dữ liệu kì trước
        for col in potential_columns:
            df.loc[previous_period_mask, col] = None

    return df


def drop_null_top10_row(df):
    pivot = df.pivot(
        index="retailer_id", columns="timeframe_type", values="top_product_quantity"
    )

    # ---- Xử lý 7 ngày ----
    # 1. Cả last và prev null => drop cả hai
    products_drop_both_7 = pivot[
        pivot["7 ngày gần nhất"].isna() & pivot["7 ngày trước đó"].isna()
    ].index

    # 2. last có value, prev null => drop prev_7_days
    products_drop_prev7 = pivot[
        pivot["7 ngày gần nhất"].notna() & pivot["7 ngày trước đó"].isna()
    ].index

    # 3. last null, prev có value => drop cả hai
    products_drop_both_7_2 = pivot[
        pivot["7 ngày gần nhất"].isna() & pivot["7 ngày trước đó"].notna()
    ].index

    # ---- Xử lý 30 ngày ----
    products_drop_both_30 = pivot[
        pivot["30 ngày gần nhất"].isna() & pivot["30 ngày trước đó"].isna()
    ].index

    products_drop_prev30 = pivot[
        pivot["30 ngày gần nhất"].notna() & pivot["30 ngày trước đó"].isna()
    ].index

    products_drop_both_30_2 = pivot[
        pivot["30 ngày gần nhất"].isna() & pivot["30 ngày trước đó"].notna()
    ].index

    # ---- Xử lý tháng này ----
    products_drop_both_month = pivot[
        pivot["tháng này"].isna() & pivot["tháng trước"].isna()
    ].index

    products_drop_prev_month = pivot[
        pivot["tháng này"].notna() & pivot["tháng trước"].isna()
    ].index

    products_drop_both_month_2 = pivot[
        pivot["tháng này"].isna() & pivot["tháng trước"].notna()
    ].index

    # ---- Tạo mask drop ----
    mask_drop = (
        (
            (df["retailer_id"].isin(products_drop_both_7))
            & (df["timeframe_type"].isin(["7 ngày gần nhất", "7 ngày trước đó"]))
        )
        | (
            (df["retailer_id"].isin(products_drop_prev7))
            & (df["timeframe_type"] == "prev_7_days")
        )
        | (
            (df["retailer_id"].isin(products_drop_both_7_2))
            & (df["timeframe_type"].isin(["7 ngày gần nhất", "7 ngày trước đó"]))
        )
        | (
            (df["retailer_id"].isin(products_drop_both_30))
            & (df["timeframe_type"].isin(["30 ngày gần nhất", "7 ngày trước đó"]))
        )
        | (
            (df["retailer_id"].isin(products_drop_prev30))
            & (df["timeframe_type"] == "30 ngày trước đó")
        )
        | (
            (df["retailer_id"].isin(products_drop_both_30_2))
            & (df["timeframe_type"].isin(["30 ngày gần nhất", "7 ngày trước đó"]))
        )
        | (
            (df["retailer_id"].isin(products_drop_both_month))
            & (df["timeframe_type"].isin(["tháng này", "tháng trước"]))
        )
        | (
            (df["retailer_id"].isin(products_drop_prev_month))
            & (df["timeframe_type"] == "tháng trước")
        )
        | (
            (df["retailer_id"].isin(products_drop_both_month_2))
            & (df["timeframe_type"].isin(["tháng này", "tháng trước"]))
        )
    )

    # Kết quả cuối cùng
    df_cleaned = df[~mask_drop].copy()

    return df_cleaned


def is_json_string(x):
    try:
        json.loads(x)
        return True
    except (TypeError, json.JSONDecodeError):
        return False


def is_array_like(x):
    return isinstance(x, (list, tuple, np.ndarray))


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
