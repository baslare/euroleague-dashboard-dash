FROM python:3.10.6-slim

COPY ./requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY ./app /app
WORKDIR /app
EXPOSE 8050
# CMD ["gunicorn", "-b", "0.0.0.0:8050", "--reload", "main:server"]