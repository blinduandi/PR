# HTTP File Server Testing Guide
# Follow this guide step by step and take screenshots at each step marked with 📸

## PREPARATION (Do this first!)
# 1. Replace placeholder files with real files:
#    - content\logo.png.placeholder → content\logo.png (any PNG image)
#    - content\networking-basics.pdf.placeholder → content\networking-basics.pdf (any PDF)
#    - content\python-guide.pdf.placeholder → content\python-guide.pdf (any PDF)
#    - content\books\*.placeholder → real PNG/PDF files

## TESTING STEPS

### 📸 Screenshot 1: Project Structure
# Run: tree /f
# OR:  Get-ChildItem -Recurse

### 📸 Screenshot 2: Docker Build
# Run: docker-compose build

### 📸 Screenshot 3: Docker Start
# Run: docker-compose up -d

### 📸 Screenshot 4: Verify Container
# Run: docker ps

### 📸 Screenshot 5: Test 404 Error
# Open browser: http://localhost:8000/nonexistent.html
# Should show 404 error page

### 📸 Screenshot 6: Test HTML with Image
# Open browser: http://localhost:8000/
# Should show main page with logo

### 📸 Screenshot 7: Test PDF Download
# Open browser: http://localhost:8000/networking-basics.pdf
# Should open PDF in browser

### 📸 Screenshot 8: Test PNG Display
# Open browser: http://localhost:8000/logo.png
# Should display PNG image

### 📸 Screenshot 9: Test Directory Listing
# Open browser: http://localhost:8000/books/
# Should show directory listing with files

### 📸 Screenshot 10: Client Test - HTML
# Run: python src\client.py localhost 8000 / downloads
# Should print HTML content to terminal

### 📸 Screenshot 11: Client Test - PDF Download
# Run: python src\client.py localhost 8000 /networking-basics.pdf downloads
# Should save PDF to downloads folder

### 📸 Screenshot 12: Show Downloaded Files
# Run: Get-ChildItem downloads\
# Should show downloaded files

### 📸 Screenshot 13: Server Logs
# Run: docker-compose logs http-file-server
# Should show server access logs

### Stop the server
# Run: docker-compose down

## IMPORTANT NOTES:
# - Each screenshot should be clearly labeled
# - Include command outputs in screenshots
# - Make sure all file extensions work (.html, .png, .pdf)
# - Test both existing and non-existing files
# - Directory listing must show clickable links