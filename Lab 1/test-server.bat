@echo off
echo ==========================================
echo HTTP File Server Testing Script
echo ==========================================
echo.
echo STEP 1: Replace placeholder files with real files
echo   - Replace content\*.placeholder with real PNG/PDF files
echo   - Make sure you have: logo.png, networking-basics.pdf, python-guide.pdf
echo.
pause
echo.
echo STEP 2: Building Docker container...
docker-compose build
echo.
echo STEP 3: Starting server...
docker-compose up -d
echo.
echo STEP 4: Checking container status...
docker ps
echo.
echo TESTING URLS - Open these in your browser:
echo   1. Main page: http://localhost:8000/
echo   2. Directory listing: http://localhost:8000/books/
echo   3. PDF file: http://localhost:8000/networking-basics.pdf  
echo   4. PNG image: http://localhost:8000/logo.png
echo   5. 404 test: http://localhost:8000/nonexistent.html
echo.
echo STEP 5: Testing client (run these commands after browser tests):
echo   python src\client.py localhost 8000 / downloads
echo   python src\client.py localhost 8000 /networking-basics.pdf downloads
echo.
echo STEP 6: View server logs:
echo   docker-compose logs http-file-server
echo.
echo STEP 7: Stop server when done:
echo   docker-compose down
echo.
pause