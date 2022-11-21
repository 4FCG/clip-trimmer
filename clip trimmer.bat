@echo off
CALL "%~dp0env\Scripts\activate.bat"
python "%~dp0cropper.py" %*
pause