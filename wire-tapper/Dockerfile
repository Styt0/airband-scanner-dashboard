FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/h9zdev/WireTapper.git .

RUN pip install --no-cache-dir -r WireTapper.txt

EXPOSE 8080

CMD ["python", "app-env.py"]
