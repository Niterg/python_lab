FROM python:3.9

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /chatapp
RUN apt-get update && apt-get install -y postgresql-client
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app /chatapp/app
EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]