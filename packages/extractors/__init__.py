import os, re, docx2txt, PyPDF2, numpy as np, statistics as stat
from packages.testing import exec_time
from PIL import Image


class ExtractFromDocument(object):
    def __init__(self, location):
        if os.path.exists(location) and os.path.isfile(location):
            self.loc = location

    def get_content(self):
        file_path = self.loc
        if os.path.exists(file_path):
            ext = file_path.strip(" ").split(".")[-1]
            try:
                raw_content = None

                if ext == "txt":
                    raw_content = self.get_txt_content(file_path)
                elif ext == "pdf":
                    raw_content = self.get_pdf_content(file_path)
                elif ext == "docx":
                    raw_content = docx2txt.process(file_path)
                else:
                    print("Invalid file type. Needs to be .txt .pdf")
            except Exception:
                return None

            processed = self.process_raw(raw_content)
            if raw_content is not None and processed.replace(" ", "") != "":
                return processed
            else:
                return None
        else:
            raise Exception("Error. File path does not exist: "+file_path)

    @staticmethod
    def process_raw(raw_text):
        raw_text = re.sub(' +', ' ', raw_text.replace("\n", "")).strip(" ").lower()
        processed = ""

        for word in raw_text.split(" "):
            word = str(word).strip()

            if len(word) > 2 and word not in ('b', 'j', 'c', 'ii', 'w'):
                processed += " " + word

        processed = processed.strip(" ").replace("'s", "")
        return processed

    @staticmethod
    def get_txt_content(file_path):
        file = open(file_path, "r")
        content = file.read()
        file.close()
        return content

    @staticmethod
    def get_pdf_content(file_path):
        text = ""
        pdf_f = open(file_path, 'rb')
        pdf = PyPDF2.PdfFileReader(pdf_f)

        for i in range(pdf.numPages):
            pdf_page = pdf.getPage(i)
            text += pdf_page.extractText()
        pdf_f.close()

        return text


class ExtractFromImage(object):
    def __init__(self, location):
        if os.path.exists(location) and os.path.isfile(location):
            self.loc = location
        else:
            raise Exception("Location needs to be a file and exist.")

    @exec_time
    def get_content(self):
        loc = self.loc
        img_np = np.array(Image.open(loc).getdata())
        size = len(img_np)
        portion = size/3
        print(size)
        print(int(portion))
        print(int(size-portion))
        img_np = np.mean(img_np, axis=1)
        img_mean = np.mean(img_np)  # subtract mean
        img_np = img_np - img_mean
        img_np[img_np < 0] = 0  # flatten values in array
        img_np[img_np > 0] = 1  # flatten values in array
        img_np = img_np[0:int(size):5]
        img_np = img_np.astype(int)
        print(len(img_np))
        return img_np.tolist()


class ExtractFromAudio(object):
    def __init__(self):
        pass


class ExtractFromAudiovisual(object):
    def __init__(self):
        pass
