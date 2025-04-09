FROM python:3.11-slim

WORKDIR /app
COPY . .

# 🔧 Install Git + mark /app as safe
RUN apt-get update && \
    apt-get install -y git && \
    git config --global --add safe.directory /app && \
    apt-get clean

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "app.py"]

