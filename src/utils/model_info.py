

#In ra thời gian phản hồi.
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


