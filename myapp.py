
#sudo apt install tesseract-ocr
#pip install pytesseract pillow pyqt5 pyperclip


import sys
import pytesseract
import pyperclip
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QTimer, QRect
from PyQt5.QtGui import QScreen, QPainter, QColor, QCursor

class OCRBox(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(200, 200, 400, 150)  # posisi & ukuran kotak

        # OCR timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.capture_and_ocr)
        self.timer.start(30000)

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
        painter.setBrush(QColor(0, 0, 0, 100))   # hitam transparan
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
        else:
            print("Tidak ada teks terdeteksi.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    box = OCRBox()
    sys.exit(app.exec_())


