import csv
import io

import pandas as pd
import PyPDF2
from PIL import Image




def extract_text_from_csv(file):

    text = "\n".join(
        [",".join(row) for row in csv.reader(file.file.read().decode().splitlines())]
    )

    df = pd.read_csv(io.StringIO(file.file.read().decode()))

    # Add a fake null column
    df["column1"] = None

    null_columns = df.columns[df.isna().all()].tolist()
    # Kiểm tra các cột có toàn giá trị 0
    zero_columns = df.columns[(df == 0).all()].tolist()
    if null_columns:
        print(f"Warning: The following columns contain all null values: {null_columns}")
    if zero_columns:
        print(f"Warning: The following columns contain all zeros: {zero_columns}")

    # Convert back to text format
    text = df.to_csv(index=False)

    return text


