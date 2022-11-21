# Clip Trimmer

A GUI tool to quickly trim your clips.

Only for windows, Your python version must be >= 3.7

This tool requires that you have VLC media player installed.
https://www.videolan.org/vlc/

You also need to have ffmpeg installed to PATH.
https://phoenixnap.com/kb/ffmpeg-windows


To use the bundled "clip trimmer.bat" file you must use the bundled "install.bat" This creates a virtual env called env, and installs all requirements in it.
This app is designed to be used with the "Open With" menu of windows.
You can do this opening a video file with the "clip trimmer.bat" file.


If you would rather do this yourself, you can manually install the requirements and run the app by using:
```
python "pathto/cropper.py" "pathto/file.mp4"
```