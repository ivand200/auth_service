FROM python:3.8

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN python -m pip install --upgrade pip
RUN python -m pip install --no-cache-dir -r /app/requirements.txt

EXPOSE 8000

COPY . /app

CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "main:app"]
