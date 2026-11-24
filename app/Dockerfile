FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && groupadd --gid 10001 pawdrop \
    && useradd --uid 10001 --gid 10001 --no-create-home pawdrop \
    && mkdir -p /data && chown 10001:10001 /data && chmod 700 /data
COPY *.py ./
USER 10001:10001
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000", "--workers", "1", "--no-access-log", "--no-proxy-headers"]
