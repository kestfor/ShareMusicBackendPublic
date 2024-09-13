FROM python:3.10-alpine
COPY requirements.txt requirements.txt
RUN pip install --upgrade --prefer-binary --no-cache-dir -r requirements.txt
WORKDIR /bots/ShareMusicBackend
COPY . .
CMD ["uvicorn", "backend.app:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "8000"]