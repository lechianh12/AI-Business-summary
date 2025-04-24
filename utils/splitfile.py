import os
import shutil
import sys

# Thêm thư mục gốc vào sys.path để import module -> fix lỗi import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scriptss.utils import split_csv_by_retailer_id


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



if __name__ == "__main__":
    split_csv_by_retailer_id_basic()




