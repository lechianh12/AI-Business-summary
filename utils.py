import csv

import PyPDF2


def extract_text_from_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file.file)
    return "".join([page.extract_text() or "" for page in pdf_reader.pages])


def extract_text_from_csv(file):
    text = "\n".join(
        [",".join(row) for row in csv.reader(file.file.read().decode().splitlines())]
    )
    return text


def extract_text_from_txt(file):
    return file.file.read().decode()
