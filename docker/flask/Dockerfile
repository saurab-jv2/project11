FROM python:3.12-slim

WORKDIR /app

COPY flask-app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY flask-app/ .

ENV PYTHONUNBUFFERED=1

EXPOSE 5000

CMD ["python", "app.py"]