FROM python:3.11-slim

WORKDIR /screener/long

COPY . /screener/long

RUN pip install --no-cache-dir --upgrade -r /screener/long/requirements.txt

EXPOSE 81

ENV RMUSER=text RMPASSWORD=text HOSTNAME=text

CMD ["python", "screener.py"]