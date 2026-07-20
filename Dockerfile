FROM python:3.12-slim

# Запрещаем Python создавать .pyc файлы (__pycache__).
ENV PYTHONDONTWRITEBYTECODE=1
# Отключае буферизацию stdout/stderr.
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]