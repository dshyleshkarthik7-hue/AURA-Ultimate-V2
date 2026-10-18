FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    QT_X11_NO_MITSHM=1

WORKDIR /app

# OpenCV's GUI backend and pyttsx3 need native runtime libraries.
# The desktop UI still requires a host display and a camera device at runtime.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 libgtk-3-0 espeak-ng \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]
