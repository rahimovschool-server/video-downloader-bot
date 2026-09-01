FROM python:3.11-slim

# FFmpeg o'rnatish
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Avval requirements — kesh uchun
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Keyin barcha fayllar
COPY . .

# Downloads papkasi
RUN mkdir -p downloads

CMD ["python", "bot.py"]
