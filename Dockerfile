FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir streamlit pandas numpy plotly openpyxl pyarrow matplotlib

COPY dashboard_recompra.py .
COPY vendas_tiny_bu.parquet .
COPY astro_ads.xlsx .

RUN mkdir -p /app/.streamlit && echo '[theme]\nbase = "dark"\n\n[server]\nheadless = true\nport = 8501\naddress = "0.0.0.0"\n\n[browser]\ngatherUsageStats = false' > /app/.streamlit/config.toml

EXPOSE 8501

CMD ["streamlit", "run", "dashboard_recompra.py"]
