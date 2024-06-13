FROM python:3.10.13-alpine

WORKDIR /root

# Requirements dont change ofter
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Code does
COPY autodownloader/__main__.py ./

ENTRYPOINT ["python", "."]
