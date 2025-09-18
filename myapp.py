
#sudo apt install tesseract-ocr
#pip install pytesseract pillow pyqt5 pyperclip keyboard


import sys
import pytesseract
import pyperclip
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer, QRect
from PyQt5.QtGui import QScreen, QPainter, QColor, QCursor, QFont

import threading
import keyboard   # global hotkey: run with root
import subprocess


class ResultBox(QWidget):
    """Kotak kecil transparan untuk menampilkan hasil OCR"""
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)  # <--- padding biar ga nempel


        self.label = QLabel("", self)
        self.label.setStyleSheet("color: white; background: transparent;")
        self.label.setFont(QFont("Arial", 12))
        self.label.setWordWrap(True)

        layout.addWidget(self.label)

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

        self.adjustSize()

        new_width = self.label.width() + 20
        new_height = self.label.height() + 20

        #self.resize(300, self.label.height() + 20)
        self.resize(new_width, new_height) # ukuran window menyesuikan isi text
        self.move_to_topright()

        self.show()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setBrush(QColor(0, 0, 0, 150))  # hitam semi-transparan
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 10, 10)

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
        self.resize_margin = 10  # area sensitif untuk resize

        self.show()

    def paintEvent(self, event):
        """Kotak semi-transparan gelap"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(0, 0, 0, 30))   # hitam transparan
        painter.setPen(QColor(255, 255, 255, 150))  # garis putih
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

    def capture_and_ocr(self):
        # screenshot area kotak
        subprocess.run(["notify-send", "Wait..."])

        screen = QApplication.primaryScreen()
        geo = self.geometry()
        pixmap = screen.grabWindow(0, geo.x(), geo.y(), geo.width(), geo.height())

        img_path = "capture.png"
        pixmap.save(img_path)

        # OCR
        text = pytesseract.image_to_string(img_path)

        if text.strip():
            pyperclip.copy(text)
            print("Teks OCR:", text.strip())
            subprocess.run(["notify-send", "text copy to cliboard"])
            self.result_box.set_text(text.strip())
        else:
            print("Tidak ada teks terdeteksi.")
            subprocess.run(["notify-send", "No text detect"])

def run_hotkey(box, app):
    keyboard.add_hotkey("alt+ctrl", box.capture_and_ocr)  # tekan spasi kapan saja
    keyboard.add_hotkey("alt+esc", app.quit)
    keyboard.wait()  # biar listener tetap hidup



if __name__ == "__main__":
    print("\n\nscreen2clip v1.0\n\n")
    print("   Drag and drop the box\n")
    print(" alt+ctrl >>  to capture")
    print(" alt+esc >>  to exit")

    app = QApplication(sys.argv)

    result_box = ResultBox()
    box = OCRBox(result_box)

    # jalankan listener di thread terpisah
    hotkey_thread = threading.Thread(target=run_hotkey, args=(box, app), daemon=True)
    hotkey_thread.start()



    sys.exit(app.exec_())


