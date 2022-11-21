import datetime
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QStyle

class RenderingDialog(QWidget):
	def __init__(self):
		super(RenderingDialog, self).__init__()
		
		self.setWindowTitle("Now Rendering Clip")
		self.resize(300, 100)
		self.setWindowIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))

		self.count = 0
		
		layout = QVBoxLayout()
		self.text = QLabel()
		layout.addWidget(QLabel("Now Rendering"))
		layout.addWidget(self.text)
		self.setLayout(layout)

		time = datetime.time(0, 0, 0)
		self.text.setText(f'Time elapsed: {str(time)}')

		self.timer = QTimer(self)
		self.timer.timeout.connect(self.setTime)

	def startTimer(self):
		self.timer.start(1000)

	def setTime(self):
		self.count += 1
		time = datetime.time(0, 0, self.count)
		self.text.setText(f'Time elapsed: {str(time)}')