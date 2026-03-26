# Use a slim version of Python for a smaller image size
FROM python:3.10-slim

# Set environment variables to prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Install system dependencies (needed for some Python packages)
RUN apt-get update && apt-get install -y --no-install-recommends gcc libsqlite3-dev && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Copy all your project files (HTML, CSS, JS, Python)
COPY . .

# Create the directory for your SQLite database if it doesn't exist
RUN mkdir -p instance

# Expose the port (AWS uses 80 for web traffic)
EXPOSE 5000

# Start the app using Gunicorn
# Replace 'app:app' with 'your_filename:app_variable_name' if different
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "app:app"]