FROM python:3.11-slim

WORKDIR /screener/short

COPY . /screener/short

RUN pip install --no-cache-dir --upgrade -r /screener/short/requirements.txt

EXPOSE 82

ENV RMUSER=text RMPASSWORD=text HOSTNAME=text

CMD ["python", "screener.py"]