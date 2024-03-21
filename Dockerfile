FROM python:3.11-slim

WORKDIR /code

COPY . /code

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

ENV TOKEN=11 WEBHOOK_PATH=11 CHAT_ID=941501054

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
