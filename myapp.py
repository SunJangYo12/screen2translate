
#sudo apt install tesseract-ocr
#pip install pytesseract pillow pyqt5 pyperclip


import sys
import pytesseract
import pyperclip
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QTimer, QRect
from PyQt5.QtGui import QScreen

class OCRBox(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(200, 200, 400, 150)  # posisi & ukuran kotak

        # timer: tiap 3 detik ambil teks
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.capture_and_ocr)
        self.timer.start(3000)

        self.show()

    def capture_and_ocr(self):
        # ambil screenshot area kotak
        screen = QApplication.primaryScreen()
        geo = self.geometry()
        pixmap = screen.grabWindow(0, geo.x(), geo.y(), geo.width(), geo.height())

        # simpan sementara
        img_path = "capture.png"
        pixmap.save(img_path)

        # OCR
        text = pytesseract.image_to_string(img_path)

        if text.strip():
            pyperclip.copy(text)
            print("Teks OCR:", text.strip())
        else:
            print("Tidak ada teks terdeteksi.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    box = OCRBox()
    sys.exit(app.exec_())


