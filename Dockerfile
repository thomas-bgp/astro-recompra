FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir streamlit pandas numpy plotly openpyxl pyarrow

COPY dashboard_recompra.py .
COPY vendas_tiny_bu.parquet .
COPY astro_ads.xlsx .

EXPOSE 8501

CMD ["streamlit", "run", "dashboard_recompra.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true", "--browser.gatherUsageStats=false"]
