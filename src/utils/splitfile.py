import os
import shutil
import sys
import glob
import pandas as pd

# Thêm thư mục gốc vào sys.path để import module -> fix lỗi import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))



def split_csv_by_retailer_id_basic():
    """
    Chia file theo retailer_id và lưu trong thư mục con có tên giống tên file đầu vào.
    """
    # Chỉ định rõ đường dẫn file đầu vào và thư mục đầu ra
    input_path = "assets/Agg_data/full_data_for_bs_v3_p3.csv"
    output_dir = "assets/retailer_data"

    # Xác định thư mục con dự kiến
    expected_subfolder = os.path.join(output_dir, "full_data_for_bs_v3_p3")

    # Xóa thư mục con nếu đã tồn tại từ các lần chạy trước đó
    if os.path.exists(expected_subfolder):
        try:
            shutil.rmtree(expected_subfolder)
            print(f"Đã xóa thư mục cũ: {expected_subfolder}")
        except Exception as e:
            print(f"Không thể xóa thư mục {expected_subfolder}: {e}")

    # Gọi hàm với tham số rõ ràng
    split_csv_by_retailer_id(input_path=input_path, output_dir=output_dir)

    # Kiểm tra xem thư mục con có được tạo không
    if os.path.exists(expected_subfolder) and os.path.isdir(expected_subfolder):
        print(f"Đã tạo thành công thư mục con: {expected_subfolder}")

        # Kiểm tra số lượng file đã tạo ra
        split_files = [f for f in os.listdir(expected_subfolder) if f.endswith(".csv")]
        print(f"Đã tạo {len(split_files)} file CSV trong thư mục con: {split_files}")
    else:
        print(f"Không tìm thấy thư mục con dự kiến: {expected_subfolder}")


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





