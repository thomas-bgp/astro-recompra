FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir streamlit pandas numpy plotly openpyxl pyarrow

COPY dashboard_recompra.py .
COPY vendas_tiny_bu.parquet .
COPY "Astro ADS.xlsx" .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "dashboard_recompra.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true", "--browser.gatherUsageStats=false"]
