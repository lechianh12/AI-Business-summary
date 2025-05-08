import glob
import os
import sys

import pandas as pd

# Thêm thư mục gốc vào sys.path để import module -> fix lỗi import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def check_retailer_data_exists():
    """
    Kiểm tra xem dữ liệu retailer đã tồn tại hay chưa.
    Returns:
        bool: True nếu dữ liệu đã tồn tại, False nếu chưa
    """
    output_dir = "assets/retailer_data"

    # Kiểm tra nếu thư mục retailer_data không tồn tại
    if not os.path.exists(output_dir):
        return False

    # Kiểm tra xem có thư mục retailer_* nào không
    retailer_folders = [
        d
        for d in os.listdir(output_dir)
        if os.path.isdir(os.path.join(output_dir, d)) and d.startswith("retailer_")
    ]

    # Nếu có ít nhất một thư mục retailer_ và mỗi thư mục có ít nhất một file CSV
    if retailer_folders:
        for folder in retailer_folders:
            folder_path = os.path.join(output_dir, folder)
            csv_files = [f for f in os.listdir(folder_path) if f.endswith(".csv")]
            if not csv_files:
                return False  # Nếu tìm thấy một thư mục không có file CSV nào, coi như dữ liệu chưa đầy đủ
        return True  # Tất cả các thư mục đều có ít nhất một file CSV

    return False  # Không có thư mục retailer_ nào


# Chia file tổng hợp thành nhiều file theo retailer_id và lưu vào thư mục retailer_<retailer_id>
def split_csv_by_retailer_id(input_path=None, output_dir=None):
    """
    Chia file tổng hợp thành nhiều file theo retailer_id và lưu vào thư mục retailer_<retailer_id>
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

    # Tạo từ điển để lưu dữ liệu tạm thời cho mỗi retailer_id
    retailer_data_dict = {}
    file_count = 0

    for file_path in csv_files:
        print(f"Processing: {file_path}")
        file_count += 1

        # Lấy tên file gốc không có phần mở rộng
        original_filename = os.path.splitext(os.path.basename(file_path))[0]

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

        # Với mỗi retailer_id, thêm dữ liệu vào từ điển tạm thời
        for retailer_id in retailer_ids:
            # Lọc dữ liệu cho retailer_id hiện tại
            current_retailer_data = df[df["retailer_id"] == retailer_id]

            retailer_folder = f"retailer_{retailer_id}"
            retailer_folder_path = os.path.join(output_dir, retailer_folder)

            # Tạo thư mục retailer nếu chưa tồn tại
            os.makedirs(retailer_folder_path, exist_ok=True)

            # Tạo khóa duy nhất cho mỗi cặp retailer_id và tên file gốc
            key = (retailer_id, original_filename)

            # Nếu khóa này chưa tồn tại trong từ điển, khởi tạo với dataframe hiện tại
            if key not in retailer_data_dict:
                retailer_data_dict[key] = current_retailer_data
            # Nếu đã tồn tại, nối dữ liệu mới vào
            else:
                retailer_data_dict[key] = pd.concat(
                    [retailer_data_dict[key], current_retailer_data], ignore_index=True
                )

    # Sau khi xử lý tất cả các file, lưu dữ liệu từ từ điển vào các file
    for (retailer_id, original_filename), data in retailer_data_dict.items():
        retailer_folder = f"retailer_{retailer_id}"
        retailer_folder_path = os.path.join(output_dir, retailer_folder)

        # Tạo tên file đầu ra
        output_filename = f"{retailer_folder_path}/{original_filename}.csv"

        # Lưu vào CSV với UTF-8 BOM encoding
        data.to_csv(output_filename, index=False, encoding="utf-8-sig")
        print(f"Created: {output_filename} with {len(data)} rows")

    print(f"Processed {file_count} files. CSV splitting completed.")
