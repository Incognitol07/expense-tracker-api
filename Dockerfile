# Use the official Python 3.12 image
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Copy only the dependency files first (for caching)
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port your app runs on (default FastAPI port is 8000)
EXPOSE 8000

# Command to run the FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
