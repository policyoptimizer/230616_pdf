import requests

def download_file_from_google_drive(id, destination):
    URL = "https://docs.google.com/uc?export=download"
    session = requests.Session()

    response = session.get(URL, params={'id': id}, stream=True)
    token = get_confirm_token(response)

    if token:
        params = {'id': id, 'confirm': token}
        response = session.get(URL, params=params, stream=True)

    save_response_content(response, destination)

def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value
    return None

def save_response_content(response, destination):
    CHUNK_SIZE = 32768

    with open(destination, "wb") as f:
        for chunk in response.iter_content(CHUNK_SIZE):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)

# Example usage:
file_id = "1ZIAzoJuNDZyGvduojvvuiz6WrOkw_x0c"
destination = "UNICEF.pdf"
download_file_from_google_drive(file_id, destination)

import streamlit as st
import gdown
from PyPDF4 import PdfFileReader, PdfFileWriter, PdfFileMerger
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io
import os

st.title("PDF 파일 처리")

# 파일 ID와 이름을 dictionary 형태로 저장
files = {
    "1ZIAzoJuNDZyGvduojvvuiz6WrOkw_x0c": "UNICEF.pdf",
    "1ZFGl_Mf3pU8L_sWlC96TjzJOUC9u3zKG": "SPA.pdf",
    "1ZEfXH-x48RMKEkAEjNxDFDvKri8hpx8h": "JPNY.pdf",
    "1Y_enHhlGNuO2pWbaZBOFlm4veTDRixQI": "EUHR.pdf",
    "1ZPgqWALfJoUYkEnIUNRZNIxhbebW7TQ0": "CHNFA.pdf",
    "1ZOStemFX4b6_yWpN4KKZqfogglJq0OnT": "CHNF.pdf",
    "1dVY9wthkt1ieMHQCr0GdE85X5M1ELke7": "ENG.pdf"
}

# 각 파일을 다운로드
st.write("파일을 다운로드 중입니다...")
for file_id, file_name in files.items():
    url = f'https://drive.google.com/uc?id={file_id}'
    gdown.download(url, file_name, quiet=False)

st.success("다운로드 완료!")

def add_page_number(input_pdf_path, output_pdf_path, type, num_sections, page_info):
    positions = {
        'UNICEF': (210, 80),
        'SPA': (298, 44),
        'JPNY': (234, 222),
        'EUHR': (248, 38),
        'CHNFA': (394, 326),
        'CHNF': (248, 44),
        'ENG': (248, 44)
    }

    x_position, y_position = positions[type]

    temp_files = []  # to hold temporary file names

    for i in range(num_sections):
        reader = PdfFileReader(input_pdf_path)
        writer = PdfFileWriter()

        total_pages, from_page, to_page = page_info[i]

        for i in range(from_page, to_page + 1):
            packet = io.BytesIO()

            # We create a new PDF with Reportlab
            can = canvas.Canvas(packet, pagesize=letter)
            page_number_text = "{0}              {1}".format(i, total_pages)
            can.drawString(x_position, y_position, page_number_text)
            can.save()

            # Move to the beginning of the StringIO buffer
            packet.seek(0)

            # Add the "watermark" (which is the new pdf) on the existing page
            page = reader.getPage(i - 1)
            watermark = PdfFileReader(packet)
            page.mergePage(watermark.getPage(0))

            writer.addPage(page)

        temp_file = f"temp{i+1}.pdf"
        temp_files.append(temp_file)
        with open(temp_file, "wb") as output_pdf_file:
            writer.write(output_pdf_file)

    # Merge all the temporary files into the final output file
    merger = PdfFileMerger()
    for temp_file in temp_files:
        merger.append(temp_file)

    merger.write(output_pdf_path)
    merger.close()

    # Delete temporary files
    for temp_file in temp_files:
        os.remove(temp_file)

# 사용자 입력 받기
type = st.selectbox("유형을 선택하세요.", list(files.values()))
num_sections = st.number_input("몇 개의 구간으로 나누시겠습니까?", min_value=1, value=1)

page_info = []
for i in range(num_sections):
    st.subheader(f"{i+1} 구간")
    total_pages = st.number_input(f"{i+1}. 전체 페이지 수를 입력하세요:", min_value=1, value=1)
    from_page = st.number_input(f"{i+1}. 시작 페이지 번호를 입력하세요:", min_value=1, value=1)
    to_page = st.number_input(f"{i+1}. 끝 페이지 번호를 입력하세요:", min_value=from_page, max_value=total_pages, value=total_pages)
    page_info.append((total_pages, from_page, to_page))

if st.button("번호 추가"):
    add_page_number(type, "numbered.pdf", type.split('.')[0], num_sections, page_info)
    st.success("페이지 번호가 추가되었습니다!")
