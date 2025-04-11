import os
import sys

# Thêm thư mục gốc vào sys.path để import module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.utils import split_csv_by_retailer_id


def test_split_csv_by_retailer_id():
    # Chỉ định rõ đường dẫn file đầu vào và thư mục đầu ra
    input_path = "assets/merchant_data/full_product_and_customer_bs.csv"
    output_dir = "assets/retailer_data"

    # Gọi hàm với tham số rõ ràng
    split_csv_by_retailer_id(input_path=input_path, output_dir=output_dir)


if __name__ == "__main__":
    test_split_csv_by_retailer_id()
