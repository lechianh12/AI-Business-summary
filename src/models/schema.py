# Định nghĩa các retailer ID và tên file tương ứng
RETAILER_OPTIONS = {
    "285727": "",
    "541173": "",
    "500577674": "",
    "500603355": "",
}

# Định nghĩa các lựa chọn thời gian
TIME_PERIOD_OPTIONS = {
    "tháng này": "month_current",
    "7 ngày gần nhất": "days_7",
    "30 ngày gần nhất": "days_30",
    "năm này": "year_current",
    "quý này": "quarter_current",
}

# Định nghĩa các lựa chọn màn hình
SCREEN_OPTIONS = {
    "Tổng quan kinh doanh": "business_overview",
    "Tổng quan hàng hóa": "product_overview",
    "Tổng quan khách hàng": "customer_overview",
    "Chi phí - Lợi nhuận": "cost_profit",
    "Tồn kho": "stock",
    "Phân loại khách hàng": "customer_segmentation",
}

SCREEN_TO_CSV_MAP = {
    "business_overview": "full_data_for_bs_v4.csv",
    "product_overview": "full_data_for_bs_v4.csv",
    "customer_overview": "full_data_for_bs_v4.csv",
    "cost_profit": "cost_rev_for_bs.csv",
    "stock": "stock_for_bs.csv",
    "customer_segmentation": "customer_seg_for_bs.csv",
}