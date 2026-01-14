FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc libmariadb-dev curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x entrypoint.sh wait-for-it.sh && \
    sed -i 's/\r$//' entrypoint.sh && \
    sed -i 's/\r$//' wait-for-it.sh && \
    sed -i 's/\r$//' check_data_exists.py

ENV PYTHONPATH=/app/src
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]