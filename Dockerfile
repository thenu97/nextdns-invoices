FROM docker.io/python:3.11 as build
WORKDIR /build
ADD . .
RUN pip install poetry
RUN poetry build

FROM docker.io/python:3.11-slim
WORKDIR /app
COPY --from=build /build/dist/*.whl .
COPY --from=build /build/invoices/template.html /app/invoices/template.html
RUN pip install *.whl && rm *.whl

CMD ["invoices"]
