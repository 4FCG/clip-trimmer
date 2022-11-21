import sys
from os import path
import math
import datetime
import vlc
from PyQt5.QtCore import Qt, QThreadPool
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import QApplication, QStyle, QSlider, QHBoxLayout, QVBoxLayout, QWidget, QFrame, QLabel, QMainWindow, QPushButton
from superqt import QRangeSlider
from render import RenderWorker
from renderDialog import RenderingDialog
import mimetypes
mimetypes.init()

class ClipTrimmer(QMainWindow):
	def __init__(self, videoPath, outputPath):
		super(ClipTrimmer, self).__init__(None)

		self.videoPath = videoPath
		self.outputPath = outputPath

		self.setWindowTitle("Clip Trimmer")
		self.setWindowIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))

		# Threading pool
		self.threadpool = QThreadPool()
		print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

		# video player
		self.instance = vlc.Instance('--play-and-pause')
		self.listPlayer = self.instance.media_list_player_new()
		self.listPlayer.set_playback_mode(vlc.PlaybackMode.loop)
		self.videoPlayer = self.listPlayer.get_media_player()

		# QFRAME WONT WORK ON MAC
		self.videoFrame = QFrame()
		player_palette = self.videoFrame.palette()
		player_palette.setColor (QPalette.Window, QColor(0,0,0))
		self.videoFrame.setPalette(player_palette)
		self.videoFrame.setAutoFillBackground(True)

		# PlayButton
		self.playButton = QPushButton()
		self.playButton.setEnabled(False)
		self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
		self.playButton.clicked.connect(self.play)

		# ClipButton
		self.saveButton = QPushButton()
		self.saveButton.setEnabled(False)
		self.saveButton.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
		self.saveButton.clicked.connect(self.save)

		# ProgressBar
		self.progressBar = QSlider(Qt.Horizontal)
		self.progressBar.setRange(0, 1000)
		self.progressBar.sliderMoved.connect(self.setPosition)

		# Clip Selector
		self.clipSelector = QRangeSlider(Qt.Horizontal)
		self.clipSelector.setMinimum(0)
		self.clipSelector.setMaximum(1000)
		self.clipSelector.setValue([0, 1000])
		self.clipSelector.setBarMovesAllHandles(False)
		self.clipSelector.setTickPosition(QSlider.TicksAbove)
		self.clipSelector.sliderMoved.connect(self.clipPosition)
		self.oldClipValues = [0, 1000]

		# Sliders vertical layout
		slidersLayout = QVBoxLayout()
		slidersLayout.setContentsMargins(0, 0, 0, 0)
		slidersLayout.addWidget(self.progressBar)
		slidersLayout.addWidget(self.clipSelector)

		# Time labels
		null_time = str(datetime.time(0, 0, 0))
		self.currentTime = QLabel()
		self.currentTime.setText(null_time)
		self.videoDuration = QLabel()
		self.videoDuration.setText(null_time)

		# Layout container for controls
		controlsWidget = QWidget()
		controlsLayout = QHBoxLayout(controlsWidget)
		controlsLayout.setContentsMargins(10, 0, 10, 5)
		controlsLayout.addWidget(self.playButton)
		controlsLayout.addWidget(self.saveButton)
		controlsLayout.addWidget(self.currentTime)
		controlsLayout.addLayout(slidersLayout)
		controlsLayout.addWidget(self.videoDuration)
		controlsWidget.setMaximumHeight(60)

		# Main page container
		content = QVBoxLayout()
		content.setContentsMargins(0, 0, 0, 0)
		content.addWidget(self.videoFrame)
		content.addWidget(controlsWidget)

		mainWidget = QWidget(self)
		self.setCentralWidget(mainWidget)
		mainWidget.setLayout(content)

		# Video events
		self.eventManager = self.videoPlayer.event_manager()
		self.eventManager.event_attach(vlc.EventType.MediaPlayerPaused, self.videoStateChangedHandler)
		self.eventManager.event_attach(vlc.EventType.MediaPlayerPlaying, self.videoStateChangedHandler)
		self.eventManager.event_attach(vlc.EventType.MediaPlayerPositionChanged, self.positionChangedHandler)

		# Rendering popup screen
		self.renderPopup = RenderingDialog()

		self.loadVideo(self.videoPath)
	
	# Buttons

	# PlayButton video play pause toggle
	def play(self):
		if self.videoPlayer.is_playing():
			self.videoPlayer.pause()
		else:
			self.videoPlayer.play()
	
	# Starts rendering the clip
	def save(self):
		worker = RenderWorker(self.outputPath, self.videoPath, self.clipSelector.value())
		worker.signal.finished.connect(self.renderFinished)
		self.threadpool.start(worker)
		self.hide()
		self.renderPopup.show()
		self.renderPopup.startTimer()

	# Sets the video position to the new slider position when dragged
	def setPosition(self, position):
		if self.videoPlayer.is_playing():
			self.videoPlayer.pause()
		new_position = position / 1000.0
		self.videoPlayer.set_position(new_position if new_position < 1.0 else 0.997)
		self.setTime()

	# Handles moving of the clip selector
	def clipPosition(self, position):
		newPosition = -1
		if position[0] != self.oldClipValues[0] and position[1] == self.oldClipValues[1]:
			newPosition = position[0]
		elif position[0] == self.oldClipValues[0] and position[1] != self.oldClipValues[1]:
			newPosition = position[1]

		if newPosition >= 0:
			self.setPosition(newPosition)
			self.positionChangedHandler()

		self.oldClipValues = position

	# VideoPlayer Events

	# Called when video state changes, toggles play/pause button icons
	def videoStateChangedHandler(self, event):
		if event.type == vlc.EventType.MediaPlayerPlaying:
			self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
		else:
			self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

	# Called when video position changes, moves the progressBar
	def positionChangedHandler(self, event=None):
		currentPosition = math.ceil(self.videoPlayer.get_position() * 1000)
		self.progressBar.setValue(currentPosition)
		self.setTime()

	# Called when the video is fully loaded, sets the video duration
	def mediaParsedHandler(self, event):
		duration = datetime.time(0, 0, int(self.videoPlayer.get_length() / 1000))
		self.videoDuration.setText(str(duration))

	# Internal functions

	# Load a new video into the player
	def loadVideo(self, filePath):

		# Load media
		playlist = self.instance.media_list_new()
		media = self.instance.media_new(filePath)
		playlist.add_media(media)
		self.listPlayer.set_media_list(playlist)

		# Bind media event manager
		self.mediaEventManager = media.event_manager()
		self.mediaEventManager.event_attach(vlc.EventType.MediaParsedChanged, self.mediaParsedHandler)

		# Bind to videoFrame
		# ONLY FOR WINDOWS
		self.videoPlayer.set_hwnd(self.videoFrame.winId())
		
		# Autoplay
		self.listPlayer.play()

		self.playButton.setEnabled(True)
		self.saveButton.setEnabled(True)

	# Sets the current time clock
	def setTime(self):
		time = datetime.time(0, 0, int(self.videoPlayer.get_time() / 1000))
		self.currentTime.setText(str(time))

	# Is called when the render thread is finished
	def renderFinished(self):
		self.renderPopup.close()
		self.close()

def isVideo(filePath):
	mimestart = mimetypes.guess_type(path.basename(filePath))[0]
	if mimestart != None and mimestart.split('/')[0] == 'video':
		return True
	return False

if __name__ == '__main__':
	app = QApplication(sys.argv)

	videoPath = path.realpath(sys.argv[1])
	dirPath = path.dirname(path.realpath(sys.argv[1]))

	if isVideo(videoPath):
		window = ClipTrimmer(videoPath, dirPath)
		window.resize(640, 480)
		window.show()
		sys.exit(app.exec_())
	else:
		print("File is not a video file")