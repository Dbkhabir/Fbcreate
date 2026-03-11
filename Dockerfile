FROM python:3.11

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install --with-deps chromium

# Copy app
COPY . .

CMD ["python", "bot.py"]
