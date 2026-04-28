FROM python:3.10

WORKDIR /app

# Copy only requirements first (for caching)
COPY backend/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy rest of code
COPY . .

CMD ["python", "-m", "backend.app.main"]