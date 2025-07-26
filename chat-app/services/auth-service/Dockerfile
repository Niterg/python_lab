FROM python:3.9

WORKDIR /app

COPY ./auth-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./auth-service/app /app/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]