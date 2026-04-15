FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    streamlit pandas numpy plotly openpyxl pyarrow \
    matplotlib scipy statsmodels

# Data files
COPY vendas_tiny_bu.parquet .
COPY astro_ads.xlsx .

# Dashboard modules
COPY dashboard_recompra.py .
COPY dashboard_campanhas.py .
COPY dashboard_agressividade.py .

# Multi-page entry
COPY app.py .
COPY pages/ pages/

# Streamlit config
RUN mkdir -p /app/.streamlit && printf '[theme]\nbase = "dark"\n\n[server]\nheadless = true\nport = 8501\naddress = "0.0.0.0"\nmaxUploadSize = 5\n\n[browser]\ngatherUsageStats = false\n' > /app/.streamlit/config.toml

EXPOSE 8501

CMD ["streamlit", "run", "app.py"]
