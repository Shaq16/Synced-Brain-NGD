FROM python:3.10

WORKDIR /app

# Copy only requirements (for caching)
COPY backend/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy only backend (important optimization)
COPY backend/ backend/

# Run FastAPI properly
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]