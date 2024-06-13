FROM python:3.10.13-alpine

WORKDIR /root
COPY __main__.py requirements.txt ./
RUN pip install -r requirements.txt

ENTRYPOINT ["python", "."]
