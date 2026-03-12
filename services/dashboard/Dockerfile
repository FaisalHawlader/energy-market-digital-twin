FROM python:3.11-slim
WORKDIR /app
COPY services/dashboard /app/dashboard
RUN pip install --no-cache-dir -r /app/dashboard/requirements.txt
ENV PYTHONPATH=/app
CMD ["streamlit", "run", "/app/dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
