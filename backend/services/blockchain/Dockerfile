FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt


COPY .solcx /root/.solcx

RUN chmod +x /root/.solcx/solc-v0.8.0

COPY . .

EXPOSE 8004

CMD ["python", "manage.py", "runserver", "0.0.0.0:8004"]