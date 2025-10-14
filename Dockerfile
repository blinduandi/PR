# HTTP File Server Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy source code
COPY src/ ./src/
COPY content/ ./content/

# Make the server script executable
RUN chmod +x src/server.py src/client.py

# Create a non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port 8000
EXPOSE 8000

# Default command to run the server
CMD ["python", "src/server.py", "content"]