# No slim since we need gcc
FROM python:3.9

WORKDIR /app

COPY requirements* ./
RUN pip install --no-cache -r requirements.txt

RUN pip install --no-cache -r requirements-dev.txt

COPY . .
ENTRYPOINT ["python", "main.py"]
