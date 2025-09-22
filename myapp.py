
#sudo apt install tesseract-ocr
#pip install pytesseract pillow pyqt5 pyperclip keyboard requests


import sys
import pytesseract
import pyperclip
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer, QRect
from PyQt5.QtGui import QScreen, QPainter, QColor, QCursor, QFont, QPen

import threading
import keyboard   # global hotkey: run with root
import subprocess
import requests
import urllib.parse
import socket
import re

class ResultBox(QWidget):
    """Kotak kecil transparan untuk menampilkan hasil OCR"""
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)

        self.label = QLabel("", self)
        self.label.setFont(QFont("Arial", 13))
        self.label.setWordWrap(True)

        self.resize(300, 100)
        self.move_to_topright()
        self.show()

    def move_to_topright(self):
        screen_geo = QApplication.primaryScreen().geometry()
        x = screen_geo.width() - self.width() - 10
        y = 10
        self.move(x, y)

    def set_text(self, text):
        self.label.setText(text)
        self.label.adjustSize()

        new_width = self.label.width() + 20
        new_height = self.label.height() + 20

        #self.resize(300, self.label.height() + 20)
        self.resize(new_width, new_height) # ukuran window menyesuikan isi text

        self.move_to_topright()
        self.show()


    def mousePressEvent(self, event):
        self.close()


class OCRBox(QWidget):
    def __init__(self, result_box):
        super().__init__()
        self.result_box = result_box
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(200, 200, 400, 150)  # posisi & ukuran kotak


        # variabel drag/resize
        self.dragging = False
        self.resizing = False
        self.drag_pos = None
        self.resize_margin = 50  # area sensitif untuk resize

        self.show()

    def paintEvent(self, event):
        """Kotak semi-transparan gelap"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(0, 0, 0, 0))   # hitam transparan

        pen = QPen(QColor(255, 0, 0))  # garis merah
        pen.setWidth(2)

        painter.setPen(pen)
        painter.drawRect(self.rect())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            rect = self.rect()
            margin = self.resize_margin
            # cek apakah klik di pinggir kotak → resize
            if rect.adjusted(margin, margin, -margin, -margin).contains(event.pos()):
                self.dragging = True
            else:
                self.resizing = True
            self.drag_pos = event.globalPos()
            self.start_geom = self.geometry()

    def mouseMoveEvent(self, event):
        if self.dragging or self.resizing:
            diff = event.globalPos() - self.drag_pos
            geo = QRect(self.start_geom)
            if self.dragging:
                geo.moveTopLeft(self.start_geom.topLeft() + diff)
            elif self.resizing:
                geo.setBottomRight(self.start_geom.bottomRight() + diff)
            self.setGeometry(geo)
        else:
            # ubah cursor kalau di pinggir (resize)
            margin = self.resize_margin
            if self.rect().adjusted(margin, margin, -margin, -margin).contains(event.pos()):
                self.setCursor(Qt.SizeAllCursor)  # drag
            else:
                self.setCursor(Qt.SizeFDiagCursor)  # resize

    def mouseReleaseEvent(self, event):
        self.dragging = False
        self.resizing = False

    def clean_hyphenation(self, text: str) -> str:
       # hapus tanda hubung di akhir baris, sambungkan langsung
       text = re.sub(r'-\s*\n\s*', '', text)
       # normalisasi newline ganda → 1 newline
       text = re.sub(r'\n+', '\n', text)
       return text



    def translate(self, text, target="id"):
        base_url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": "auto",   # source language auto detect
            "tl": target,  # target language
            "dt": "t",
            "q": text,
        }
        url = f"{base_url}?{urllib.parse.urlencode(params)}"
        resp = requests.get(url)
        resp.raise_for_status()

        data = resp.json()

        return "".join([seg[0] for seg in data[0] if seg[0]])


    def ocr_remote(self, img_path):
        ip = "192.168.0.100"

        print(f"[+] with ocr api from {ip}")
        self.result_box.set_text("OCR remote api Wait...".strip())

        client = socket.socket()
        client.connect((ip, 5001))

        with open(img_path, "rb") as f:
            client.sendall(f.read())

        client.shutdown(socket.SHUT_WR)

        response = client.recv(1024).decode()

        client.close()
        return response

    def clip_translate(self):
        self.result_box.set_text("clipoard...".strip())
        text = pyperclip.paste()

        text = self.clean_hyphenation(text)

        mytranslate = self.translate(text, "id")

        self.result_box.set_text(mytranslate)


    def capture_and_ocr(self):
        # screenshot area kotak
        self.result_box.set_text("OCR Wait...".strip())

        screen = QApplication.primaryScreen()
        geo = self.geometry()
        pixmap = screen.grabWindow(0, geo.x(), geo.y(), geo.width(), geo.height())

        img_path = "/tmp/capture.png"
        pixmap.save(img_path)

        # OCR
        #text = pytesseract.image_to_string(img_path)
        text = self.ocr_remote(img_path)

        text = self.clean_hyphenation(text)

        if text.strip():
            #pyperclip.copy(text)
            self.result_box.set_text("Translate...".strip())

            mytranslate = self.translate(text, "id")

            self.result_box.set_text(mytranslate.strip())
        else:
            self.result_box.set_text("Failed!".strip())

def run_hotkey(box, app):
    keyboard.add_hotkey("alt+ctrl", box.capture_and_ocr)
    keyboard.add_hotkey("alt+shift", box.clip_translate)
    keyboard.add_hotkey("alt+esc", app.quit)
    keyboard.wait()  # biar listener tetap hidup



if __name__ == "__main__":
    print("\n  >> screen2clip v1.0\n")
    print("Help:")
    print("  alt+ctrl > to capture")
    print("  alt+shift > to capture using clipboard")
    print("  alt+esc > to exit\n\n")

    app = QApplication(sys.argv)

    result_box = ResultBox()
    box = OCRBox(result_box)

    # jalankan listener di thread terpisah
    hotkey_thread = threading.Thread(target=run_hotkey, args=(box, app), daemon=True)
    hotkey_thread.start()



    sys.exit(app.exec_())


