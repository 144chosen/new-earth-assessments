FROM python:3.12-slim
WORKDIR /app
COPY server/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY server /app/server
COPY public /app/public
RUN useradd --create-home appuser && mkdir /data && chown appuser /data
USER appuser
WORKDIR /app/server
EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--threads", "2", "--timeout", "90", "app:create_app()"]
