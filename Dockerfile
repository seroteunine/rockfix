FROM python:3.11.11-slim

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Copy everything into the rockfix subdirectory
RUN mkdir -p rockfix
COPY requirements.txt rockfix/
COPY . rockfix/rockfix/

RUN pip install --no-cache-dir -r rockfix/requirements.txt

WORKDIR /workspace/rockfix

ENTRYPOINT ["python3", "-m", "rockfix"]
