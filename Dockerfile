FROM python:3.10

# تثبيت ffmpeg
RUN apt update && apt install -y ffmpeg

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

CMD ["python", "tiktok.py"]
