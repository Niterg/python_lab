FROM python:3.9

WORKDIR /app

COPY ./chat-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./chat-service/app /app/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]