import os
from tika import parser


class ToText(object):
    def __init__(self):
        pass

    def process(self, file_path):
        if os.path.exists(file_path):
            path, file = os.path.split(file_path)
            text = ""
            file_ext = file.split(".")[-1]
            if file_ext == "pdf":
                pdf_file = parser.from_file(file_path)
                pdf_file_content = pdf_file["content"]
                print(pdf_file_content)
        else:
            print("File does not exist.")

    def format_handler(self, file):
        file_ext = file.split(".")[-1]
        if file_ext == "pdf":
            pass

tt = ToText()
tt.process(file_path=r"C:/Marumo/Applications/FileAlchemy/Source/PWA_FILEALCHEMY_V1/flaskr/static/user_files_dump/QUOTATION 007.pdf")