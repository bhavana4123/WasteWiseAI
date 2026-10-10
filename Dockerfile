FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    WASTEWISE_ENV=production \
    PORT=8080
WORKDIR /app
COPY backend/requirements-production.txt /app/requirements-production.txt
RUN pip install --no-cache-dir -r requirements-production.txt \
    && groupadd --gid 10001 wastewise \
    && useradd --uid 10001 --gid 10001 --no-create-home wastewise
COPY backend /app/backend
COPY engine /app/engine
COPY scripts/common.py /app/scripts/common.py
# Verification needs raw sources and evidence files as well as the CSVs.
COPY data /app/data
RUN find /app/data -type d -exec chmod 555 {} + \
    && find /app/data -type f -exec chmod 444 {} +
USER 10001:10001
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.getenv('PORT','8080')+'/api/health',timeout=5)" || exit 1
CMD ["python", "-m", "backend"]
