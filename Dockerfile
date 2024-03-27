FROM docker.io/python:3.11
WORKDIR /app
ADD . .
RUN pip install poetry
RUN poetry install --without=dev --no-root

CMD ["invoices"]
