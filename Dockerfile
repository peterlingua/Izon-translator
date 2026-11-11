FROM python:3.12-slim
WORKDIR /app
COPY . .
ENV PYTHONUNBUFFERED=1
# The hosting platform sets PORT; the app listens on all interfaces when deployed.
CMD ["python", "web_app.py"]
