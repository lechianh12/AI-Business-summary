def read_column_data(column_file_path):
    try:
        with open(column_file_path, "r", encoding="utf-8") as file:
            content = file.read().strip()
        return content
    except Exception as e:
        print(f"Lỗi khi đọc file {column_file_path}: {str(e)}")
        return ""


# ... giữ nguyên generate_retail_system_prompt ...
