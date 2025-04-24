import csv
import ast

def validate_business_csv(file_path):
    def is_number(val):
        try:
            float(val)
            return True
        except:
            return False

    def is_date(val):
        # Đơn giản, bạn có thể dùng datetime.strptime để kiểm tra kỹ hơn
        return '-' in val or '/' in val

    with open(file_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row_idx, row in enumerate(reader, 2):
            # Kiểm tra các trường bắt buộc
            for col in ['timeframe_type', 'timeframe_start', 'timeframe_end', 'retailer_id', 'branch_id']:
                if not row.get(col):
                    print(f"[Bug] Row {row_idx}: Thiếu dữ liệu ở cột {col}")
            if row.get('timeframe_start') and not is_date(row['timeframe_start']):
                print(f"[Bug] Row {row_idx}: Sai định dạng ngày ở timeframe_start")
            if row.get('timeframe_end') and not is_date(row['timeframe_end']):
                print(f"[Bug] Row {row_idx}: Sai định dạng ngày ở timeframe_end")
            for col in ['retailer_id', 'branch_id']:
                if row.get(col) and not is_number(row[col]):
                    print(f"[Bug] Row {row_idx}: Sai kiểu số ở {col}")

            # Kiểm tra các chỉ số số học không âm
            num_cols = [
                'num_invoice_sell', 'num_invoice_sell_per_day', 'total_revenue', 'revenue_per_day',
                'total_return_revenue', 'total_return_revenue_per_day', 'net_revenue', 'net_revenue_per_day',
                'total_cost', 'total_cost_per_day', 'gross_profit', 'gross_profit_per_day'
            ]
            for col in num_cols:
                if col in row and row[col]:
                    try:
                        val = float(row[col])
                        if val < 0:
                            print(f"[Bug] Row {row_idx}: Giá trị âm không hợp lệ ở {col}")
                    except:
                        print(f"[Bug] Row {row_idx}: Sai kiểu số ở {col}")

            # Kiểm tra các trường dạng array
            array_cols = [
                'bs_category_rev_name_rev', 'bs_group_revenue', 'bs_group_revenue_per_inv',
                'bs_product_rev_name', 'bs_product_revenue', 'bs_product_revenue_per_inv',
                # ... thêm các trường array khác theo định nghĩa ...
            ]
            for col in array_cols:
                if col in row and row[col]:
                    try:
                        arr = ast.literal_eval(row[col])
                        if not isinstance(arr, list):
                            print(f"[Bug] Row {row_idx}: {col} không phải dạng array")
                    except:
                        print(f"[Bug] Row {row_idx}: {col} không parse được thành array")

            # Kiểm tra độ dài các array liên quan (ví dụ: tên và giá trị phải cùng số phần tử)
            group_cols = [
                ('bs_category_rev_name_rev', 'bs_group_revenue', 'bs_group_revenue_per_inv'),
                # ... thêm các nhóm khác ...
            ]
            for group in group_cols:
                lengths = []
                for col in group:
                    if col in row and row[col]:
                        try:
                            arr = ast.literal_eval(row[col])
                            lengths.append(len(arr))
                        except:
                            pass
                if lengths and len(set(lengths)) > 1:
                    print(f"[Bug] Row {row_idx}: Độ dài các array trong nhóm {group} không đồng bộ: {lengths}")

# Ví dụ sử dụng:
# validate_business_csv('assets/Agg_data/full_data_for_bs_v3.csv')