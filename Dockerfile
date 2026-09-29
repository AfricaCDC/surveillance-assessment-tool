FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    AFRICA_CDC_DB_PATH=/data/africa_cdc_web.db

WORKDIR /app
RUN groupadd --gid 10001 app && useradd --uid 10001 --gid app --no-create-home app \
    && mkdir /data && chown app:app /data
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY server.py surveillance_app.py report_builder.py standard_assessment_template.xlsx ./
COPY static/ ./static/

USER 10001:10001
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import json,urllib.request; assert json.load(urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=3))['status']=='ok'"
CMD ["python", "server.py", "--host", "0.0.0.0", "--port", "8080", "--no-browser"]
