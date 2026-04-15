"""
Astro — Hub Multi-Dashboard
Entry point para o Streamlit multi-page.
Os dados sao carregados aqui e compartilhados via st.cache_data.
"""

import streamlit as st

st.set_page_config(
    page_title="Astro — Dashboards",
    page_icon="📊",
    layout="wide",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .block-container { max-width: 900px; padding-top: 3rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
# Astro Distribuidora

### Dashboards disponíveis:

**1. Historia da Recompra** — Análise de recompra, produtos gateway, LTV por marca/UF

**2. Campanhas x Vendas** — Gasto diário vs novos clientes, ROAS LTV, regressão, ANOVA

**3. Agressividade de Budget** — Aumentos bruscos travam o Google? Evolução da carteira

---
Use o menu lateral para navegar entre os dashboards.
""")
