FROM python:3.8

RUN apt-get update

RUN mkdir /app

COPY . /app

WORKDIR /app

RUN python -m pip install --upgrade pip
RUN python -m pip install -r requirements.txt

EXPOSE 8000
EXPOSE 5432

CMD ["uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"]