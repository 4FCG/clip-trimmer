from PyQt5.QtCore import QRunnable, pyqtSlot, QObject, pyqtSignal
import ffmpeg
from os import path

class WorkerSignals(QObject):
    finished = pyqtSignal()

class RenderWorker(QRunnable):
	def __init__(self, ouputPath, videoPath, clipPositions):
		super(RenderWorker, self).__init__()
		self.outputPath = ouputPath
		self.videoPath = videoPath
		self.clipPositions = clipPositions
		self.signal = WorkerSignals()
	
	@pyqtSlot()
	def run(self):
		probe = ffmpeg.probe(self.videoPath)
		duration = float(probe.get('format', {}).get('duration', None))
		start = duration * (self.clipPositions[0] / 1000.0)
		end = duration * (self.clipPositions[1] / 1000.0)
		
		videoFile = ffmpeg.input(self.videoPath)

		pts = 'PTS-STARTPTS'
		video = videoFile.trim(start=start, end=end).setpts(pts)
		audio = (videoFile
					.filter('atrim', start=start, end=end)
					.filter('asetpts', pts))

		out = ffmpeg.output(video, audio, path.join(self.outputPath, f'{path.splitext(path.basename(self.videoPath))[0]}_clip.mp4'))
		out.run(overwrite_output=True)
		self.signal.finished.emit()
