FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Copy all files (including static/ and templates/)
COPY . .

# Ensure the database folder exists for SQLite
RUN mkdir -p instance

EXPOSE 5000

# Start Flask using Gunicorn
# Using 'app:app' because your main file is named app.py
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]