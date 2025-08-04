<<<<<<< HEAD
FROM python:3.12-slim

ENV PIP_ROOT_USER_ACTION=ignore

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

=======
FROM python:3.12-slim

ENV PIP_ROOT_USER_ACTION=ignore

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

>>>>>>> 89f974fa8c9c5ebca981103561fb77154912bc04
CMD uvicorn main:app --host 0.0.0.0 --port $PORT