FROM python:3.9

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /authapp

COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app /authapp/app
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]