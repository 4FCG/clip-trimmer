python -m venv "%~dp0env"
CALL "%~dp0env\Scripts\activate.bat"
pip install -r "%~dp0requirements.txt"
pause