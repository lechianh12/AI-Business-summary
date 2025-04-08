import csv
import io

import pandas as pd
import PyPDF2


def extract_text_from_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file.file)
    return "".join([page.extract_text() or "" for page in pdf_reader.pages])


def extract_text_from_csv(file):

    text = "\n".join(
        [",".join(row) for row in csv.reader(file.file.read().decode().splitlines())]
    )

    df = pd.read_csv(io.StringIO(file.file.read().decode()))

    # Add a fake null column
    df["column1"] = None

    null_columns = df.columns[df.isna().all()].tolist()

    if null_columns:
        print(f"Warning: The following columns contain all null values: {null_columns}")

    # Convert back to text format
    text = df.to_csv(index=False)

    return text


def extract_text_from_txt(file):
    return file.file.read().decode()
