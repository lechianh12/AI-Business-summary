import glob
import json
import os

import pandas as pd


# Chia file tổng hợp thành nhiều file theo retailer_id
def split_csv_by_retailer_id(input_path=None, output_dir=None):

    # Sử dụng giá trị mặc định nếu không được cung cấp
    if input_path is None:
        input_path = "assets/Agg_data/*.csv"

    if output_dir is None:
        output_dir = "assets/retailer_data"

    # Create retailer_data directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Get CSV files based on input_path
    if "*" in input_path:
        # If input_path contains wildcard, use glob
        csv_files = glob.glob(input_path)
    else:
        # If input_path is a specific file
        csv_files = [input_path]

    for file_path in csv_files:
        print(f"Processing: {file_path}")

        # Read CSV file with specified encoding
        try:
            # Try with utf-8 first
            df = pd.read_csv(file_path, encoding="utf-8")
        except UnicodeDecodeError:
            # If that fails, try with other common encodings
            try:
                df = pd.read_csv(file_path, encoding="latin1")
            except Exception as e:
                print(
                    f"Error: Unable to read {file_path} with common encodings. {str(e)}. Skipping."
                )
                continue

        # Check if retailer_id column exists
        if "retailer_id" not in df.columns:
            print(f"Warning: 'retailer_id' column not found in {file_path}. Skipping.")
            continue

        # Get unique retailer_ids
        retailer_ids = df["retailer_id"].unique()

        # For each unique retailer_id, create a new CSV file
        for retailer_id in retailer_ids:
            # Filter data for the current retailer_id
            retailer_data = df[df["retailer_id"] == retailer_id]

            # Create output filename
            output_filename = f"{output_dir}/retailer_{retailer_id}.csv"

            # Save to CSV with UTF-8 BOM encoding
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
        }
    else:
        # Trả về dữ liệu gốc nếu không có cột nào hợp lệ
        return processed_data


def read_column_data(column_file_path):
    """Đọc file chứa thông tin về các cột và trả về nội dung của file."""
    try:
        with open(column_file_path, "r", encoding="utf-8") as file:
            content = file.read()
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