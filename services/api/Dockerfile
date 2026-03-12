FROM python:3.11-slim
WORKDIR /app
COPY services/shared /app/shared
COPY services/api /app/api
RUN pip install --no-cache-dir -r /app/api/requirements.txt
ENV PYTHONPATH=/app
CMD ["python", "-m", "api.main"]
