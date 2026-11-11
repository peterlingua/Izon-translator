FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
ENV PYTHONUNBUFFERED=1
# The hosting platform sets PORT.
CMD sh -c "streamlit run app.py --server.address 0.0.0.0 --server.port ${PORT:-8501} --server.headless true"
