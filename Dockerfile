FROM python:3.10.13-alpine

WORKDIR /root
COPY __main__.py ./

ENTRYPOINT ["python", "."]
