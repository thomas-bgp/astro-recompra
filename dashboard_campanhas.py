"""
Astro — Campanhas × Vendas  (v3)
Duas abas: Por Estado  |  Por Marca
Foco em PRIMEIRA COMPRA: o aumento de ads gera novos clientes?
Inclui regressão e ANOVA para testar o efeito estatístico.
Dark-mode native.
"""

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from scipy.stats import linregress, pearsonr, spearmanr, f_oneway
import re

# ═══════════════════════════════════════
# PATHS & CONSTANTS
# ═══════════════════════════════════════

DATA_PATH = Path(__file__).parent / "vendas_tiny_bu.parquet"
_ads_new = Path(__file__).parent / "astro_ads.xlsx"
_ads_old = Path(__file__).parent / "Astro ADS.xlsx"
ADS_PATH = _ads_new if _ads_new.exists() else _ads_old

STATE_MAP = {
    'State of Acre': 'AC', 'State of Alagoas': 'AL', 'State of Amapa': 'AP',
    'State of Amazonas': 'AM', 'State of Bahia': 'BA', 'Ceara': 'CE',
    'Federal District': 'DF', 'State of Espirito Santo': 'ES', 'State of Goias': 'GO',
    'State of Maranhao': 'MA', 'State of Mato Grosso': 'MT',
    'State of Mato Grosso do Sul': 'MS', 'State of Minas Gerais': 'MG',
    'State of Para': 'PA', 'State of Paraiba': 'PB', 'State of Parana': 'PR',
    'State of Pernambuco': 'PE', 'State of Piaui': 'PI',
    'State of Rio de Janeiro': 'RJ', 'State of Rio Grande do Norte': 'RN',
    'State of Rio Grande do Sul': 'RS', 'State of Rondonia': 'RO',
    'State of Roraima': 'RR', 'State of Santa Catarina': 'SC',
    'State of Sao Paulo': 'SP', 'State of Sergipe': 'SE', 'State of Tocantins': 'TO',
}

MARCA_NORMALIZE = {
    "3M": "3M", "Biosolvit": "Biosolvit", "Bracol": "Bracol", "Camper": "Camper",
    "Cartom": "Cartom", "Danny": "Danny", "Delta Plus": "Delta Plus",
    "Fujiwara": "Fujiwara", "Imbat": "Imbat", "Innpro": "Innpro",
    "Kadesh": "Kadesh", "Kalipso": "Kalipso", "MG Cinto": "MG Cinto",
    "Maicol": "Maicol", "Marluvas": "Marluvas", "Medix": "Medix",
    "Nutriex": "Nutriex", "Soft Work": "Soft Works", "SuperSafety": "Super Safety",
    "Volk": "Volk",
}

DATE_START = pd.Timestamp("2026-03-17")
ACCENT = "#4fc3f7"
TEXT_COLOR = "#ddd"
GRID_COLOR = "rgba(255,255,255,0.06)"

PLOTLY_LAYOUT = dict(
    font=dict(family="Inter", size=13, color=TEXT_COLOR),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=20, r=20, t=50, b=20),
    xaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
    yaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
)


def _extract_marca(camp):
    m = re.match(r"\[Pmax\]\s*-\s*(.+)", camp)
    if m:
        return MARCA_NORMALIZE.get(m.group(1).strip())
    if "Marluvas" in camp:
        return "Marluvas"
    if "Cartom" in camp:
        return "Cartom"
    return None


def _apply_dark(fig):
    fig.update_layout(**PLOTLY_LAYOUT)
    fig.update_xaxes(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR, tickfont_color=TEXT_COLOR)
    fig.update_yaxes(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR, tickfont_color=TEXT_COLOR)
    return fig


# ═══════════════════════════════════════
# PAGE CONFIG & STYLING
# ═══════════════════════════════════════

_MULTIPAGE = False
if not _MULTIPAGE:
    st.set_page_config(page_title="Astro — Campanhas × Vendas", page_icon="📊", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    .block-container { max-width: 1300px; padding-top: 1.5rem; }
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .hero-title {
        font-size: 2.4rem; font-weight: 900; line-height: 1.1;
        background: linear-gradient(135deg, #4fc3f7, #81d4fa);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0.3rem;
    }
    .hero-sub { font-size: 1.1rem; color: #999; margin-bottom: 1.5rem; }
    .section-title {
        font-size: 1.3rem; font-weight: 700; color: #e8e8ec;
        margin: 1.8rem 0 0.3rem 0; padding-bottom: 0.3rem;
        border-bottom: 2px solid rgba(79,195,247,0.3);
    }
    .metric-row { display: flex; gap: 0.8rem; margin: 0.8rem 0 1.2rem 0; flex-wrap: wrap; }
    .mini-card {
        background: rgba(255,255,255,0.05); border-radius: 10px; padding: 0.9rem 1.2rem;
        border: 1px solid rgba(255,255,255,0.08); text-align: center; flex: 1; min-width: 120px;
    }
    .mini-card .val { font-size: 1.4rem; font-weight: 800; color: #e8e8ec; }
    .mini-card .lbl { font-size: 0.6rem; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-top: 0.15rem; }
    .legend { font-size: 0.78rem; color: #888; margin: 0.3rem 0 0.6rem 0; }
    .legend span { padding: 2px 8px; border-radius: 4px; margin-right: 6px; font-weight: 600; }
    .lg { background: rgba(46,125,50,0.3); color: #66bb6a; }
    .ly { background: rgba(249,168,37,0.3); color: #fdd835; }
    .lr { background: rgba(198,40,40,0.3); color: #ef5350; }
    .buyer-bar { display: flex; border-radius: 6px; overflow: hidden; height: 24px; margin: 0.2rem 0; }
    .buyer-bar div { display: flex; align-items: center; justify-content: center; font-size: 0.68rem; font-weight: 700; color: #fff; }
    .divider { border: none; border-top: 1px solid rgba(255,255,255,0.06); margin: 2rem 0; }
    .stat-box {
        background: rgba(255,255,255,0.04); border-radius: 10px; padding: 1.2rem 1.5rem;
        border: 1px solid rgba(255,255,255,0.08); margin: 0.8rem 0;
    }
    .stat-box h4 { color: #4fc3f7; margin: 0 0 0.5rem 0; font-size: 1rem; }
    .stat-box p { color: #ccc; margin: 0.2rem 0; font-size: 0.9rem; }
    .stat-sig { color: #66bb6a; font-weight: 700; }
    .stat-nosig { color: #ef5350; font-weight: 700; }
    .footer-text { text-align:center; color:#555; font-size:0.8rem; padding: 2rem 0; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════

def _file_sig(path):
    """File size + mtime as cache-bust key."""
    return (path.stat().st_size, int(path.stat().st_mtime))


@st.cache_data
def load_vendas(_sig=None):
    df = pd.read_parquet(DATA_PATH)
    df = df[df["situacao"] != "Cancelado"].copy()
    df["data_pedido"] = pd.to_datetime(df["data_pedido"])
    df["valor_rateado"] = pd.to_numeric(df["valor_rateado"], errors="coerce")
    df["total_pedido"] = pd.to_numeric(df["total_pedido"], errors="coerce")
    return df


@st.cache_data
def load_ads(_sig=None):
    ads = pd.read_excel(ADS_PATH, sheet_name="Planilha1")
    ads["Day"] = pd.to_datetime(ads["Day"])
    ads["uf"] = ads["State (Geographic)"].map(STATE_MAP)
    ads["marca"] = ads["Campaign Name"].apply(_extract_marca)
    ads["spend"] = pd.to_numeric(ads["Cost (Spend)"], errors="coerce").fillna(0)
    return ads


@st.cache_data
def compute_profile_ltv_primeira_compra(df):
    """LTV potencial por perfil (UF × marca, UF × sub_categoria, marca × sub_categoria).
    Usa APENAS clientes pré-campanha (antes de 17/03) como base histórica.
    Para cada perfil, calcula a receita média de vida desses clientes."""
    client_rev = df.groupby("cliente_id")["valor_rateado"].sum().reset_index()
    client_rev.columns = ["cliente_id", "receita_total"]

    first = (
        df.sort_values("data_pedido")
        .drop_duplicates("cliente_id", keep="first")[
            ["cliente_id", "cliente_uf", "marca", "sub_categoria", "cliente_tipo_pessoa", "data_pedido"]
        ]
    )
    first.columns = ["cliente_id", "uf_p", "marca_p", "subcat_p", "tipo_p", "data_p"]
    profiles = first.merge(client_rev, on="cliente_id")

    # Base histórica: clientes adquiridos ANTES da campanha
    hist = profiles[profiles["data_p"] < DATE_START]

    # LTV médio por perfil UF × marca
    ltv_uf_marca = hist.groupby(["uf_p", "marca_p"]).agg(
        ltv=("receita_total", "mean"), n=("cliente_id", "nunique")
    ).reset_index()

    # LTV médio por perfil UF × sub_categoria
    ltv_uf_subcat = hist.groupby(["uf_p", "subcat_p"]).agg(
        ltv=("receita_total", "mean"), n=("cliente_id", "nunique")
    ).reset_index()

    # LTV médio por perfil marca × sub_categoria
    ltv_marca_subcat = hist.groupby(["marca_p", "subcat_p"]).agg(
        ltv=("receita_total", "mean"), n=("cliente_id", "nunique")
    ).reset_index()

    # LTV marginal por UF e por marca (fallback)
    ltv_uf = hist.groupby("uf_p").agg(ltv=("receita_total", "mean")).reset_index()
    ltv_marca = hist.groupby("marca_p").agg(ltv=("receita_total", "mean")).reset_index()

    return profiles, ltv_uf_marca, ltv_uf_subcat, ltv_marca_subcat, ltv_uf, ltv_marca


@st.cache_data
def build_regression_data(df, ads, group_col, ads_group_col):
    """Monta dataset diário para regressão: spend × novos clientes.
    Usa TODO o histórico overlapping para máximo de observações."""
    # Novos clientes por dia × grupo
    novos = df[df["Recompra"] == "Novo"].drop_duplicates("numero")
    grp_novos = novos.groupby([group_col, "data_pedido"]).agg(
        n_novos=("cliente_id", "nunique"),
        receita_novos=("valor_rateado", "sum"),
    ).reset_index()

    # Ads por dia × grupo
    ads_sub = ads[ads[ads_group_col].notna()]
    grp_ads = ads_sub.groupby([ads_group_col, "Day"])["spend"].sum().reset_index()

    merged = grp_ads.merge(
        grp_novos,
        left_on=[ads_group_col, "Day"],
        right_on=[group_col, "data_pedido"],
        how="inner",
    )
    return merged


# ═══════════════════════════════════════
# FORMAT & COLOR
# ═══════════════════════════════════════

def _fmt_brl(v):
    if pd.isna(v) or v == 0:
        return ""
    if abs(v) >= 1000:
        return f"R$ {v:,.0f}".replace(",", ".")
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_int(v):
    if pd.isna(v) or v == 0:
        return ""
    return f"{int(v)}"


def _fmt_number(v):
    if pd.isna(v) or v == 0:
        return ""
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_pct(v):
    if pd.isna(v) or v == 0:
        return ""
    return f"{v:+.0f}%"


def _color_roas(val):
    if pd.isna(val) or val == 0:
        return ""
    if val > 10:
        return "background-color: rgba(46,125,50,0.35); color: #66bb6a"
    if val >= 8:
        return "background-color: rgba(249,168,37,0.35); color: #fdd835"
    return "background-color: rgba(198,40,40,0.35); color: #ef5350"


def _color_pct(val):
    if pd.isna(val) or val == 0:
        return ""
    if val > 10:
        return "background-color: rgba(46,125,50,0.3); color: #66bb6a"
    if val > 0:
        return "background-color: rgba(46,125,50,0.15); color: #a5d6a7"
    if val > -10:
        return "background-color: rgba(198,40,40,0.15); color: #ef9a9a"
    return "background-color: rgba(198,40,40,0.3); color: #ef5350"


def _color_vs_mean(series_mean):
    t80 = series_mean * 0.8

    def _c(val):
        if pd.isna(val) or val == 0:
            return ""
        if val >= series_mean:
            return "background-color: rgba(46,125,50,0.35); color: #66bb6a"
        if val >= t80:
            return "background-color: rgba(249,168,37,0.35); color: #fdd835"
        return "background-color: rgba(198,40,40,0.35); color: #ef5350"

    return _c


def _neutral(v):
    return "" if pd.isna(v) or v == 0 else "color: #e8e8ec"


# ═══════════════════════════════════════
# RENDER: styled table
# ═══════════════════════════════════════

def render_table(pivot, color_fn, fmt_fn, key):
    if pivot.empty:
        st.info("Sem dados.")
        return
    p = pivot.copy()
    p.columns = [c.strftime("%d/%m") if hasattr(c, "strftime") else str(c) for c in p.columns]
    styled = (
        p.style.map(color_fn).format(fmt_fn)
        .set_properties(**{"text-align": "center", "font-size": "0.82rem", "font-weight": "600", "min-width": "65px"})
        .set_table_styles([
            {"selector": "th", "props": [("background", "rgba(255,255,255,0.05)"), ("color", "#aaa"),
                                          ("font-size", "0.72rem"), ("text-align", "center"), ("padding", "4px 5px")]},
            {"selector": "td", "props": [("padding", "4px 5px")]},
            {"selector": "th.row_heading", "props": [("text-align", "left"), ("min-width", "70px"),
                                                       ("color", "#ccc"), ("font-weight", "700")]},
        ])
    )
    st.dataframe(styled, use_container_width=True, key=key)


# ═══════════════════════════════════════
# BUILDERS
# ═══════════════════════════════════════

def build_pivot(df, gcol, vcol, dates, agg="sum", dcol="data_pedido"):
    d = df.groupby([gcol, dcol])[vcol].agg(agg).reset_index()
    p = d.pivot_table(index=gcol, columns=dcol, values=vcol, aggfunc=agg, fill_value=0)
    p = p.reindex(columns=dates, fill_value=0)
    if agg == "sum":
        p.loc["TOTAL"] = p.sum()
    else:
        ov = df.groupby(dcol)[vcol].agg(agg)
        p.loc["TOTAL"] = ov.reindex(dates, fill_value=0)
    return p


def build_ads_pivot(ads, gcol, dates):
    s = ads[ads[gcol].notna()]
    d = s.groupby([gcol, "Day"])["spend"].sum().reset_index()
    p = d.pivot_table(index=gcol, columns="Day", values="spend", aggfunc="sum", fill_value=0)
    p = p.reindex(columns=dates, fill_value=0)
    p.loc["TOTAL"] = p.sum()
    return p


def build_novos_pivot(df, gcol, dates, dcol="data_pedido"):
    """Contagem de clientes NOVOS por dia × grupo."""
    novos = df[df["Recompra"] == "Novo"].drop_duplicates("numero")
    d = novos.groupby([gcol, dcol])["cliente_id"].nunique().reset_index()
    d.columns = [gcol, dcol, "n"]
    p = d.pivot_table(index=gcol, columns=dcol, values="n", aggfunc="sum", fill_value=0)
    p = p.reindex(columns=dates, fill_value=0)
    p.loc["TOTAL"] = p.sum()
    return p


def build_vendas_novos_pivot(df, gcol, dates, dcol="data_pedido"):
    """Receita APENAS de primeira compra por dia × grupo."""
    novos = df[df["Recompra"] == "Novo"]
    d = novos.groupby([gcol, dcol])["valor_rateado"].sum().reset_index()
    p = d.pivot_table(index=gcol, columns=dcol, values="valor_rateado", aggfunc="sum", fill_value=0)
    p = p.reindex(columns=dates, fill_value=0)
    p.loc["TOTAL"] = p.sum()
    return p


def build_roas_pivot(v, c):
    idx = v.index.union(c.index)
    vr = v.reindex(idx, fill_value=0)
    cr = c.reindex(idx, fill_value=0)
    with np.errstate(divide="ignore", invalid="ignore"):
        r = vr / cr.replace(0, np.nan)
    return r.fillna(0)


def build_budget_dow_variation(camp_pivot):
    """Variação vs média do MESMO DIA DA SEMANA dentro do período atual.
    Resolve o problema sáb/dom: compara sábado com média dos sábados,
    segunda com média das segundas, etc.
    Resultado: +10% = 'gastou 10% a mais que a média das terças deste período'."""
    if camp_pivot.empty or len(camp_pivot.columns) < 7:
        return pd.DataFrame()

    dates = camp_pivot.columns
    dows = pd.Series([d.dayofweek for d in dates], index=dates)

    # Média por grupo × DOW dentro do período
    result = camp_pivot.copy().astype(float)
    for idx in camp_pivot.index:
        for dow in range(7):
            dow_cols = [d for d in dates if d.dayofweek == dow]
            if not dow_cols:
                continue
            vals = camp_pivot.loc[idx, dow_cols]
            avg = vals.mean()
            for d in dow_cols:
                if avg > 0:
                    result.loc[idx, d] = (camp_pivot.loc[idx, d] / avg - 1) * 100
                else:
                    result.loc[idx, d] = 0
    return result


def build_budget_weekly(camp_pivot):
    """Agrega gasto por semana (Seg-Dom) para mostrar tendência semanal."""
    if camp_pivot.empty:
        return pd.DataFrame()
    dates = camp_pivot.columns
    # Assign each date to a week number (ISO)
    weeks = {}
    for d in dates:
        wk = d.isocalendar()[1]
        yr = d.isocalendar()[0]
        key = f"S{wk}/{str(yr)[-2:]}"
        weeks.setdefault(key, []).append(d)

    weekly = pd.DataFrame(index=camp_pivot.index)
    for wk_label, wk_dates in weeks.items():
        weekly[wk_label] = camp_pivot[wk_dates].sum(axis=1)

    # Add % change between weeks
    if len(weekly.columns) >= 2:
        cols = list(weekly.columns)
        change_df = pd.DataFrame(index=weekly.index)
        for i in range(1, len(cols)):
            prev = weekly[cols[i - 1]].replace(0, np.nan)
            change_df[f"{cols[i]} vs ant."] = ((weekly[cols[i]] / prev) - 1) * 100
        return weekly, change_df
    return weekly, pd.DataFrame()


def build_budget_share(camp_pivot):
    """Share de budget: % do gasto total indo para cada estado/marca por dia."""
    totals = camp_pivot.loc["TOTAL"] if "TOTAL" in camp_pivot.index else camp_pivot.sum()
    share = camp_pivot.div(totals.replace(0, np.nan)) * 100
    return share.fillna(0)


def build_ltv_primeira_compra_daily(df_period, profiles, ltv_lookup, fallback_lookup, gcol, dates, dcol="data_pedido"):
    """LTV potencial dos novos clientes usando média HISTÓRICA do perfil.
    ltv_lookup: {(key1, key2): ltv} do perfil histórico.
    fallback_lookup: {key: ltv} marginal (só UF ou só marca)."""
    novos = df_period[df_period["Recompra"] == "Novo"].drop_duplicates(subset=["cliente_id", dcol])
    buyers = novos[["cliente_id", dcol]].merge(profiles, on="cliente_id", how="left")

    if gcol == "cliente_uf":
        buyers["ltv_perfil"] = buyers.apply(
            lambda r: ltv_lookup.get((r["uf_p"], r["marca_p"]),
                      fallback_lookup.get(r["uf_p"], np.nan)), axis=1)
        grp_col = "uf_p"
    else:
        buyers["ltv_perfil"] = buyers.apply(
            lambda r: ltv_lookup.get((r["marca_p"], r["subcat_p"]),
                      fallback_lookup.get(r["marca_p"], np.nan)), axis=1)
        grp_col = "marca_p"

    grp = buyers.groupby([grp_col, dcol])["ltv_perfil"].mean().reset_index()
    grp.columns = [gcol, dcol, "ltv"]
    p = grp.pivot_table(index=gcol, columns=dcol, values="ltv", aggfunc="mean", fill_value=0)
    p = p.reindex(columns=dates, fill_value=0)
    ov = buyers.groupby(dcol)["ltv_perfil"].mean()
    p.loc["TOTAL"] = ov.reindex(dates, fill_value=0)
    return p


def build_growth_diag(venda, camp, novos_pivot, ltv_pivot, gcol):
    v = venda.drop("TOTAL", errors="ignore").sum(axis=1)
    c = camp.drop("TOTAL", errors="ignore").sum(axis=1)
    n = novos_pivot.drop("TOTAL", errors="ignore").sum(axis=1)
    ltv_avg = ltv_pivot.drop("TOTAL", errors="ignore").replace(0, np.nan).mean(axis=1)
    idx = v.index.union(c.index).union(n.index)
    v = v.reindex(idx, fill_value=0)
    c = c.reindex(idx, fill_value=0)
    n = n.reindex(idx, fill_value=0)
    ltv_avg = ltv_avg.reindex(idx, fill_value=0)
    d = pd.DataFrame({gcol: idx, "gasto": c.values, "vendas": v.values,
                       "novos": n.values.astype(int), "ltv_perfil": ltv_avg.values})
    d["valor_potencial"] = d["novos"] * d["ltv_perfil"]
    d["roas"] = d["vendas"] / d["gasto"].replace(0, np.nan)
    d["cac"] = d["gasto"] / d["novos"].replace(0, np.nan)
    d["sh_budget"] = d["gasto"] / d["gasto"].sum() * 100
    d["sh_vendas"] = d["vendas"] / d["vendas"].sum() * 100
    d["gap"] = d["sh_vendas"] - d["sh_budget"]

    def _verd(r):
        if r["gasto"] == 0 and r["vendas"] > 0:
            return "Orgânico"
        if r["gasto"] == 0:
            return "Sem dados"
        if r["gap"] > 3:
            return "Eficiente"
        if r["gap"] < -3:
            return "Atenção"
        return "Neutro"

    d["veredicto"] = d.apply(_verd, axis=1)
    return d.sort_values("gap", ascending=False)


# ═══════════════════════════════════════
# REGRESSION & ANOVA
# ═══════════════════════════════════════

def run_regression_by_group(reg_data, group_col, ads_group_col):
    """Regressão linear: n_novos ~ spend, por grupo. Retorna DataFrame de resultados."""
    results = []
    for name, sub in reg_data.groupby(ads_group_col):
        if len(sub) < 15:
            continue
        x, y = sub["spend"].values, sub["n_novos"].values
        slope, intercept, r, p, se = linregress(x, y)
        results.append({
            "grupo": name, "n_obs": len(sub),
            "slope": slope, "intercept": intercept,
            "R²": r ** 2, "p_value": p, "se": se,
            "spend_medio": x.mean(), "novos_medio": y.mean(),
            "significativo": "Sim" if p < 0.05 else "Não",
        })
    return pd.DataFrame(results).sort_values("R²", ascending=False)


def run_anova_by_group(reg_data, ads_group_col):
    """ANOVA: divide spend em 3 faixas (Baixo/Médio/Alto) e testa se novos diferem."""
    results = []
    for name, sub in reg_data.groupby(ads_group_col):
        if len(sub) < 30:
            continue
        tercis = pd.qcut(sub["spend"], 3, labels=["Baixo", "Médio", "Alto"], duplicates="drop")
        groups = [sub.loc[tercis == lbl, "n_novos"].values for lbl in tercis.unique()]
        groups = [g for g in groups if len(g) >= 5]
        if len(groups) < 2:
            continue
        f_stat, p_val = f_oneway(*groups)
        medias = {lbl: sub.loc[tercis == lbl, "n_novos"].mean() for lbl in tercis.unique()}
        results.append({
            "grupo": name, "n_obs": len(sub),
            "F": f_stat, "p_value": p_val,
            "media_baixo": medias.get("Baixo", 0),
            "media_medio": medias.get("Médio", 0),
            "media_alto": medias.get("Alto", 0),
            "significativo": "Sim" if p_val < 0.05 else "Não",
        })
    return pd.DataFrame(results).sort_values("F", ascending=False)


# ═══════════════════════════════════════
# RENDER FUNCTIONS
# ═══════════════════════════════════════

def render_cards(vendas, spend, novos, ltv_medio, ticket, n_dias):
    roas = (novos * ltv_medio) / spend if spend > 0 else 0
    st.markdown(f"""
    <div class="metric-row">
        <div class="mini-card"><div class="val">{_fmt_brl(vendas)}</div><div class="lbl">Vendas 1a compra</div></div>
        <div class="mini-card"><div class="val">{_fmt_brl(spend)}</div><div class="lbl">Gasto Ads</div></div>
        <div class="mini-card"><div class="val">{novos}</div><div class="lbl">Novos Clientes</div></div>
        <div class="mini-card"><div class="val">{roas:.1f}x</div><div class="lbl">ROAS LTV</div></div>
        <div class="mini-card"><div class="val">{_fmt_brl(ltv_medio)}</div><div class="lbl">LTV Pot. Perfil</div></div>
        <div class="mini-card"><div class="val">{_fmt_brl(ticket)}</div><div class="lbl">Ticket 1a compra</div></div>
    </div>""", unsafe_allow_html=True)


def render_roas_legend():
    st.markdown('<div class="legend"><span class="lg">&gt; 10x</span><span class="ly">8–10x</span><span class="lr">&lt; 8x</span></div>', unsafe_allow_html=True)


def render_mean_legend(m):
    st.markdown(f'<div class="legend"><span class="lg">&gt; média ({_fmt_brl(m)})</span><span class="ly">80–100%</span><span class="lr">&lt; 80%</span></div>', unsafe_allow_html=True)


def render_budget_legend():
    st.markdown('<div class="legend"><span class="lg">&gt;+10%</span><span style="background:rgba(46,125,50,0.15);color:#a5d6a7;padding:2px 8px;border-radius:4px;margin-right:6px;font-weight:600">0 a +10%</span><span style="background:rgba(198,40,40,0.15);color:#ef9a9a;padding:2px 8px;border-radius:4px;margin-right:6px;font-weight:600">0 a -10%</span><span class="lr">&lt;-10%</span></div>', unsafe_allow_html=True)


def render_diag_table(diag, gcol, key):
    show = diag[[gcol, "gasto", "novos", "ltv_perfil", "valor_potencial", "cac", "sh_budget", "sh_vendas", "gap", "veredicto"]].copy()
    show.columns = [gcol, "Gasto", "Novos", "LTV Perfil", "Valor Potencial", "CAC", "Sh.Budget%", "Sh.Vendas%", "Gap(pp)", "Veredicto"]

    def _sv(v):
        m = {"Eficiente": "background:rgba(46,125,50,0.25);color:#66bb6a;font-weight:700",
             "Atenção": "background:rgba(198,40,40,0.25);color:#ef5350;font-weight:700",
             "Orgânico": "background:rgba(79,195,247,0.2);color:#4fc3f7;font-weight:700"}
        return m.get(v, "")

    def _sg(v):
        if pd.isna(v): return ""
        return "color:#66bb6a;font-weight:700" if v > 3 else ("color:#ef5350;font-weight:700" if v < -3 else "color:#aaa")

    styled = (show.style.map(_sv, subset=["Veredicto"]).map(_sg, subset=["Gap(pp)"])
              .format({"Gasto": _fmt_brl, "Novos": lambda v: f"{int(v)}" if pd.notna(v) and v > 0 else "",
                       "LTV Perfil": _fmt_brl, "Valor Potencial": _fmt_brl,
                       "CAC": lambda v: _fmt_brl(v) if pd.notna(v) and v > 0 else "",
                       "Sh.Budget%": lambda v: f"{v:.1f}%" if pd.notna(v) else "",
                       "Sh.Vendas%": lambda v: f"{v:.1f}%" if pd.notna(v) else "",
                       "Gap(pp)": lambda v: f"{v:+.1f}" if pd.notna(v) else ""})
              .set_properties(**{"text-align": "center", "font-size": "0.85rem"})
              .set_properties(subset=[gcol], **{"text-align": "left", "font-weight": "700"}))
    st.dataframe(styled, use_container_width=True, key=key, hide_index=True)


def render_scatter_novos(diag, gcol, key):
    """Dois scatters: Gasto × Novos Clientes e Gasto × Valor Potencial (Novos * LTV)."""
    p = diag[(diag["gasto"] > 0) & (diag["novos"] > 0)].copy()
    if p.empty:
        return

    col1, col2 = st.columns(2)

    # Scatter 1: Gasto x Novos Clientes
    with col1:
        fig1 = px.scatter(p, x="gasto", y="novos", text=gcol,
                          color_discrete_sequence=[ACCENT],
                          labels={"gasto": "Gasto Ads (R$)", "novos": "Novos Clientes"})
        fig1.update_traces(textposition="top center", textfont_size=9,
                           marker=dict(size=13, line=dict(width=1, color="#333")))
        # Trend line
        if len(p) >= 3:
            slope, intercept, r, _, _ = linregress(p["gasto"], p["novos"])
            mx = p["gasto"].max() * 1.15
            x_line = [0, mx]
            y_line = [intercept, slope * mx + intercept]
            fig1.add_trace(go.Scatter(x=x_line, y=y_line, mode="lines",
                                      line=dict(color="#66bb6a", width=2, dash="dash"),
                                      name=f"R²={r**2:.2f}"))
        _apply_dark(fig1)
        fig1.update_layout(title="Gasto × Novos Clientes", height=420,
                           legend=dict(y=0.99, x=0.01, bgcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig1, use_container_width=True, key=f"{key}_novos")

    # Scatter 2: Gasto x Valor Potencial (Novos * LTV)
    with col2:
        p2 = p[p["valor_potencial"] > 0].copy()
        if p2.empty:
            st.info("Sem dados de LTV para scatter.")
            return
        fig2 = px.scatter(p2, x="gasto", y="valor_potencial", text=gcol,
                          color_discrete_sequence=["#f9a825"],
                          labels={"gasto": "Gasto Ads (R$)", "valor_potencial": "Valor Potencial (Novos × LTV)"})
        fig2.update_traces(textposition="top center", textfont_size=9,
                           marker=dict(size=13, line=dict(width=1, color="#333")))
        # Break-even line (valor potencial = gasto)
        mx2 = p2["gasto"].max() * 1.15
        fig2.add_trace(go.Scatter(x=[0, mx2], y=[0, mx2], mode="lines",
                                  line=dict(color="rgba(239,83,80,0.4)", dash="dot"),
                                  name="Break-even"))
        # Trend line
        if len(p2) >= 3:
            slope2, intercept2, r2, _, _ = linregress(p2["gasto"], p2["valor_potencial"])
            y_line2 = [intercept2, slope2 * mx2 + intercept2]
            fig2.add_trace(go.Scatter(x=[0, mx2], y=y_line2, mode="lines",
                                      line=dict(color="#66bb6a", width=2, dash="dash"),
                                      name=f"R²={r2**2:.2f}"))
        _apply_dark(fig2)
        fig2.update_layout(title="Gasto × Valor Potencial (Novos × LTV)", height=420,
                           legend=dict(y=0.99, x=0.01, bgcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig2, use_container_width=True, key=f"{key}_potencial")


def render_regression_scatter(reg_data, ads_group_col, key):
    """Scatter: spend diário × novos clientes (todo histórico) com regressão."""
    # Global regression
    x, y = reg_data["spend"].values, reg_data["n_novos"].values
    slope, intercept, r, p, se = linregress(x, y)
    r_pearson, p_pearson = pearsonr(x, y)
    r_spearman, p_spearman = spearmanr(x, y)

    fig = px.scatter(reg_data, x="spend", y="n_novos", opacity=0.3,
                     labels={"spend": "Gasto Diário Ads (R$)", "n_novos": "Novos Clientes no Dia"},
                     color_discrete_sequence=[ACCENT])
    # Trend line
    x_line = np.linspace(x.min(), x.max(), 100)
    y_line = slope * x_line + intercept
    fig.add_trace(go.Scatter(x=x_line, y=y_line, mode="lines",
                             line=dict(color="#66bb6a", width=3),
                             name=f"Regressão (R²={r**2:.3f})"))
    _apply_dark(fig)
    fig.update_layout(title="Regressão: Gasto Diário → Novos Clientes (histórico completo)", height=460,
                      legend=dict(y=0.99, x=0.01, bgcolor="rgba(0,0,0,0)"))
    st.plotly_chart(fig, use_container_width=True, key=key)

    # Stats box
    sig = p_pearson < 0.05
    cls = "stat-sig" if sig else "stat-nosig"
    verdict = "SIGNIFICATIVO" if sig else "NÃO SIGNIFICATIVO"
    st.markdown(f"""
    <div class="stat-box">
        <h4>Resultado da Regressão Linear (dados agregados)</h4>
        <p><b>n =</b> {len(x)} observações diárias (todo o histórico Jan/2025 – Mar/2026)</p>
        <p><b>Pearson r =</b> {r_pearson:.4f} &nbsp; (p = {p_pearson:.2e}) &nbsp;
           <b>Spearman r =</b> {r_spearman:.4f} &nbsp; (p = {p_spearman:.2e})</p>
        <p><b>R² =</b> {r**2:.4f} &nbsp; → &nbsp; <b>{r**2*100:.1f}%</b> da variação de novos clientes é explicada pelo gasto em ads</p>
        <p><b>Slope =</b> {slope:.5f} &nbsp; → &nbsp; cada <b>R$ 1.000</b> a mais em ads gera ~<b>{slope*1000:.1f}</b> novos clientes</p>
        <p><b>Veredicto:</b> <span class="{cls}">{verdict}</span> a p &lt; 0.05</p>
    </div>""", unsafe_allow_html=True)


def render_regression_by_group(reg_results, key):
    if reg_results.empty:
        st.info("Dados insuficientes para regressão por grupo (mínimo 15 obs).")
        return

    show = reg_results[["grupo", "n_obs", "R²", "slope", "p_value", "significativo"]].copy()
    show["novos_por_1k"] = show["slope"] * 1000
    show = show[["grupo", "n_obs", "R²", "novos_por_1k", "p_value", "significativo"]]
    show.columns = ["Grupo", "N obs", "R²", "Novos/R$1k", "p-value", "Sig."]

    def _cs(v):
        return "color:#66bb6a;font-weight:700" if v == "Sim" else "color:#ef5350"

    styled = (show.style.map(_cs, subset=["Sig."])
              .format({"R²": "{:.4f}", "Novos/R$1k": "{:.2f}", "p-value": "{:.2e}"})
              .set_properties(**{"text-align": "center", "font-size": "0.85rem"})
              .set_properties(subset=["Grupo"], **{"text-align": "left", "font-weight": "700"}))
    st.dataframe(styled, use_container_width=True, key=key, hide_index=True)


def render_anova(anova_results, key):
    if anova_results.empty:
        st.info("Dados insuficientes para ANOVA por grupo (mínimo 30 obs).")
        return

    show = anova_results[["grupo", "n_obs", "media_baixo", "media_medio", "media_alto", "F", "p_value", "significativo"]].copy()
    show.columns = ["Grupo", "N", "Novos (Gasto Baixo)", "Novos (Gasto Médio)", "Novos (Gasto Alto)", "F", "p-value", "Sig."]

    def _cs(v):
        return "color:#66bb6a;font-weight:700" if v == "Sim" else "color:#ef5350"

    styled = (show.style.map(_cs, subset=["Sig."])
              .format({"Novos (Gasto Baixo)": "{:.1f}", "Novos (Gasto Médio)": "{:.1f}",
                       "Novos (Gasto Alto)": "{:.1f}", "F": "{:.2f}", "p-value": "{:.2e}"})
              .set_properties(**{"text-align": "center", "font-size": "0.85rem"})
              .set_properties(subset=["Grupo"], **{"text-align": "left", "font-weight": "700"}))
    st.dataframe(styled, use_container_width=True, key=key, hide_index=True)


def render_buyer_bars(nr, pj, dates):
    st.markdown('<div class="section-title">8. Perfil do Comprador por Dia</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.caption("Novo vs Recompra")
        for d in dates:
            if d not in nr.index: continue
            n = nr.loc[d].get("Novo", 0)
            r = nr.loc[d].get("Recompra", 0)
            t = n + r
            if t == 0: continue
            st.markdown(f'<div style="font-size:0.7rem;color:#aaa;margin-top:2px">{d.strftime("%d/%m")} — {t}ped (N:{n} R:{r})</div>'
                        f'<div class="buyer-bar"><div style="width:{max(n/t*100,1):.0f}%;background:#1a73e8">N{n}</div>'
                        f'<div style="width:{max(r/t*100,1):.0f}%;background:#4fc3f7">R{r}</div></div>', unsafe_allow_html=True)
    with c2:
        st.caption("PF vs PJ")
        for d in dates:
            if d not in pj.index: continue
            f_ = pj.loc[d].get("F", 0)
            j_ = pj.loc[d].get("J", 0)
            t = f_ + j_
            if t == 0: continue
            st.markdown(f'<div style="font-size:0.7rem;color:#aaa;margin-top:2px">{d.strftime("%d/%m")} — {t}ped (PF:{f_} PJ:{j_})</div>'
                        f'<div class="buyer-bar"><div style="width:{max(f_/t*100,1):.0f}%;background:#f9a825">PF{f_}</div>'
                        f'<div style="width:{max(j_/t*100,1):.0f}%;background:#ef6c00">PJ{j_}</div></div>', unsafe_allow_html=True)


def render_methodology():
    st.sidebar.markdown("### Metodologia")
    with st.sidebar.expander("ROAS LTV"):
        st.markdown(
            "**ROAS LTV = (Novos Clientes × LTV Potencial do Perfil) / Gasto Ads.** "
            "Mostra o retorno potencial de vida, não só a 1a compra. "
            "Verde > 10x | Amarelo 8–10x | Vermelho < 8x."
        )
    with st.sidebar.expander("LTV Potencial do Perfil"):
        st.markdown(
            "**Perfil** = UF + marca da 1a compra do cliente. "
            "**LTV potencial** = receita média total de todos os clientes históricos com esse perfil (desde Jan/2024). "
            "Na célula: média dos LTVs dos perfis dos **novos clientes** adquiridos naquele dia. "
            "Responde: *os novos clientes que estamos adquirindo hoje têm perfis de alto ou baixo retorno?*"
        )
    with st.sidebar.expander("Tendência do Budget"):
        st.markdown(
            "**3 visões complementares:**\n\n"
            "**2a. Variação DOW:** compara cada dia com a média do mesmo dia da semana "
            "no período do dashboard. Terça vs média das terças, sáb vs média dos sábs. "
            "Elimina distorção de ciclicidade semanal.\n\n"
            "**2b. Alocação (% share):** quanto do budget total vai para cada estado/marca "
            "em cada dia. Mostra mudanças de estratégia de alocação.\n\n"
            "**2c. Tendência semanal:** agrega por semana ISO e mostra % variação "
            "semana-a-semana. Visão limpa da direção estratégica."
        )
    with st.sidebar.expander("Regressão: Ads → Novos"):
        st.markdown(
            "**Regressão linear** entre gasto diário em ads e número de novos clientes adquiridos. "
            "Usa **todo o histórico** (Jan/2025 a Mar/2026, ~400+ obs) para máximo poder estatístico. "
            "**R²** = % da variação de novos clientes explicada pelo gasto. "
            "**Slope** = quantos novos clientes adicionais a cada R$1.000 de gasto. "
            "**p-value < 0.05** = relação estatisticamente significativa."
        )
    with st.sidebar.expander("ANOVA: Faixas de Gasto"):
        st.markdown(
            "Divide os dias em 3 faixas de gasto (Baixo/Médio/Alto, por tercis) e testa via "
            "ANOVA se a média de novos clientes difere significativamente entre as faixas. "
            "**F alto + p < 0.05** = o nível de gasto impacta a aquisição de novos clientes."
        )
    with st.sidebar.expander("Diagnóstico de Growth"):
        st.markdown(
            "**Share Budget** vs **Share Vendas** por estado/marca. "
            "Gap positivo = vende mais do que gasta (eficiente). "
            "Gap negativo = gasta mais do que vende (possível aumento de base sem conversão)."
        )


# ═══════════════════════════════════════
# RENDER TAB
# ═══════════════════════════════════════

def render_tab(df_p, ads_p, profiles, reg_data, dates, gcol, ads_gcol, prefix, ltv_lookup, ltv_fallback):
    # 1. Gasto Campanha
    st.markdown(f'<div class="section-title">1. Gasto Campanha por {gcol.replace("cliente_uf","Estado").replace("marca","Marca")}</div>', unsafe_allow_html=True)
    camp = build_ads_pivot(ads_p, ads_gcol, dates)
    render_table(camp, _neutral, _fmt_brl, f"{prefix}_camp")

    # 2. Variação do Budget (DOW-adjusted + semanal)
    st.markdown('<div class="section-title">2. Tendência do Budget</div>', unsafe_allow_html=True)
    with st.expander("Como é calculado?"):
        st.markdown(
            "**Problema:** comparar dia-a-dia gera distorções (sáb→seg = +10.000%). "
            "**Solução:** cada célula compara o gasto daquele dia com a **média do mesmo dia da semana** "
            "dentro do período do dashboard. Ex: terça 01/04 vs média de todas as terças. "
            "+15% = gastou 15% acima do normal para terças nesse estado. "
            "A tabela semanal agrega por semana ISO e mostra variação semana-a-semana."
        )

    st.caption("2a. Variação vs média do mesmo dia da semana (período atual)")
    dow_var = build_budget_dow_variation(camp)
    if not dow_var.empty:
        render_budget_legend()
        render_table(dow_var, _color_pct, _fmt_pct, f"{prefix}_dow")
    else:
        st.caption("Necessário 7+ dias para análise DOW.")

    st.caption("2b. Alocação: % do budget total por dia")
    share = build_budget_share(camp)
    render_table(share, _color_pct, lambda v: f"{v:.1f}%" if not pd.isna(v) and v > 0 else "", f"{prefix}_share")

    st.caption("2c. Tendência semanal (total por semana + variação)")
    weekly, wk_chg = build_budget_weekly(camp)
    if not weekly.empty:
        render_table(weekly, _neutral, _fmt_brl, f"{prefix}_wk")
    if not wk_chg.empty:
        render_budget_legend()
        render_table(wk_chg, _color_pct, _fmt_pct, f"{prefix}_wkchg")

    # 3. Novos Clientes (contagem)
    st.markdown('<div class="section-title">3. Novos Clientes Adquiridos por Dia</div>', unsafe_allow_html=True)
    novos_pv = build_novos_pivot(df_p, gcol, dates)
    render_table(novos_pv, _neutral, _fmt_int, f"{prefix}_novos")

    # 4. Vendas de Primeira Compra
    st.markdown('<div class="section-title">4. Vendas de Primeira Compra (R$)</div>', unsafe_allow_html=True)
    vnovos = build_vendas_novos_pivot(df_p, gcol, dates)
    render_table(vnovos, _neutral, _fmt_brl, f"{prefix}_vnovos")

    # 5. LTV Potencial do Perfil (calcular ANTES do ROAS)
    ltv_pv = build_ltv_primeira_compra_daily(df_p, profiles, ltv_lookup, ltv_fallback, gcol, dates)

    # 6. ROAS LTV (valor potencial / gasto)
    label = gcol.replace("cliente_uf", "Estado").replace("marca", "Marca")
    st.markdown(f'<div class="section-title">5. ROAS LTV por {label}</div>', unsafe_allow_html=True)
    with st.expander("Como é calculado?"):
        st.markdown(
            "**ROAS LTV = (Novos Clientes x LTV Potencial do Perfil) / Gasto em Ads**, por dia e grupo. "
            "Mostra o retorno potencial considerando o valor de vida do perfil, não só a 1a compra."
        )
    render_roas_legend()
    ltv_value = novos_pv * ltv_pv.reindex(novos_pv.index, fill_value=0).reindex(columns=novos_pv.columns, fill_value=0)
    roas = build_roas_pivot(ltv_value, camp)
    render_table(roas, _color_roas, _fmt_number, f"{prefix}_roas")

    # 6. LTV Potencial do Perfil (tabela)
    st.markdown(f'<div class="section-title">6. LTV Potencial do Perfil — Novos Clientes</div>', unsafe_allow_html=True)
    with st.expander("Como é calculado?"):
        st.markdown(
            "Perfil = UF + marca da 1a compra. LTV potencial = receita média histórica de clientes com mesmo perfil. "
            "Mostra a média dos LTVs potenciais dos **novos clientes** adquiridos naquele dia. "
            "Permite avaliar se os ads estão atraindo perfis de alto ou baixo valor."
        )
    vals = ltv_pv.replace(0, np.nan).values.flatten()
    ltv_m = float(np.nanmean(vals)) if np.any(~np.isnan(vals)) else 1
    render_mean_legend(ltv_m)
    render_table(ltv_pv, _color_vs_mean(ltv_m), _fmt_brl, f"{prefix}_ltv")

    # 7. Ticket Médio primeira compra
    st.markdown('<div class="section-title">7. Ticket Médio — Primeira Compra</div>', unsafe_allow_html=True)
    novos_df = df_p[df_p["Recompra"] == "Novo"]
    if not novos_df.empty:
        tk = build_pivot(novos_df.drop_duplicates("numero"), gcol, "total_pedido", dates, agg="mean")
        tvals = tk.replace(0, np.nan).values.flatten()
        tm = float(np.nanmean(tvals)) if np.any(~np.isnan(tvals)) else 1
        render_mean_legend(tm)
        render_table(tk, _color_vs_mean(tm), _fmt_brl, f"{prefix}_tk")

    # 8. Perfil comprador
    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    nr, pj = build_buyer_profile_daily(df_p, dates)
    render_buyer_bars(nr, pj, sorted(dates))

    # 9. Scatter eficiência
    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.markdown(f'<div class="section-title">9. Scatter: Eficiencia de Aquisicao</div>', unsafe_allow_html=True)
    st.caption("Esquerda: quantos novos clientes o gasto gera. Direita: qual o valor potencial (novos x LTV do perfil).")
    diag = build_growth_diag(vnovos, camp, novos_pv, ltv_pv, gcol)
    render_scatter_novos(diag, gcol, f"{prefix}_scat")

    # 10. Diagnóstico Growth
    st.markdown(f'<div class="section-title">10. Diagnóstico de Growth</div>', unsafe_allow_html=True)
    with st.expander("O que significa?"):
        st.markdown(
            "Share Budget vs Share Vendas de 1a compra. "
            "Gap negativo = gasta mais do que converte — pode ser ampliação de base sem conversão imediata."
        )
    render_diag_table(diag, gcol, f"{prefix}_diag")

    # 11. Regressão: Ads → Novos Clientes
    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">11. Análise Estatística: Efeito Ads → Novos Clientes</div>', unsafe_allow_html=True)
    st.caption("Dados: todo o histórico Jan/2025 – Mar/2026 para máximo poder estatístico")

    if reg_data is not None and not reg_data.empty:
        render_regression_scatter(reg_data, ads_gcol, f"{prefix}_reg_scat")

        st.markdown("**Regressão por grupo:**")
        reg_res = run_regression_by_group(reg_data, gcol, ads_gcol)
        render_regression_by_group(reg_res, f"{prefix}_reg_grp")

        st.markdown("**ANOVA — Faixas de Gasto:**")
        with st.expander("O que é essa análise?"):
            st.markdown(
                "Divide os dias em 3 faixas de gasto (tercis: Baixo/Médio/Alto) por grupo. "
                "Testa se a **média de novos clientes difere significativamente** entre faixas. "
                "F alto + p < 0.05 = aumentar gasto **de fato** aumenta novos clientes nesse grupo."
            )
        anova_res = run_anova_by_group(reg_data, ads_gcol)
        render_anova(anova_res, f"{prefix}_anova")


def build_buyer_profile_daily(df, dates, dcol="data_pedido"):
    orders = df.drop_duplicates("numero")
    nr = orders.groupby([dcol, "Recompra"])["numero"].count().unstack(fill_value=0)
    pj = orders.groupby([dcol, "cliente_tipo_pessoa"])["numero"].count().unstack(fill_value=0)
    return nr, pj


# ═══════════════════════════════════════
# MAIN
# ═══════════════════════════════════════

def main():
    st.markdown('<div class="hero-title">Campanhas &times; Vendas</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">O aumento de ads gera novos clientes? Análise de primeira compra + regressão.</div>',
                unsafe_allow_html=True)

    df = load_vendas(_sig=_file_sig(DATA_PATH))
    ads = load_ads(_sig=_file_sig(ADS_PATH))
    profiles, ltv_uf_marca, ltv_uf_subcat, ltv_marca_subcat, ltv_uf, ltv_marca = compute_profile_ltv_primeira_compra(df)

    # Build lookup dicts for fast profile matching
    ltv_lookup_estado = {(r["uf_p"], r["marca_p"]): r["ltv"] for _, r in ltv_uf_marca.iterrows()}
    ltv_fallback_estado = {r["uf_p"]: r["ltv"] for _, r in ltv_uf.iterrows()}
    ltv_lookup_marca = {(r["marca_p"], r["subcat_p"]): r["ltv"] for _, r in ltv_marca_subcat.iterrows()}
    ltv_fallback_marca = {r["marca_p"]: r["ltv"] for _, r in ltv_marca.iterrows()}

    end = max(df["data_pedido"].max(), ads["Day"].max())
    dates = pd.date_range(DATE_START, end, freq="D")

    df_p = df[(df["data_pedido"] >= DATE_START) & (df["data_pedido"] <= end)]
    ads_p = ads[(ads["Day"] >= DATE_START) & (ads["Day"] <= end)]

    if df_p.empty:
        st.warning("Sem vendas no período.")
        return

    # Sidebar
    st.sidebar.markdown("### Período")
    st.sidebar.info(f"**{DATE_START.strftime('%d/%m/%Y')}** até **{end.strftime('%d/%m/%Y')}** ({len(dates)} dias)")
    st.sidebar.caption(f"Ads até {ads['Day'].max().strftime('%d/%m/%Y')}. Vendas até {df['data_pedido'].max().strftime('%d/%m/%Y')}.")
    render_methodology()

    # Summary (primeira compra)
    novos_df = df_p[df_p["Recompra"] == "Novo"]
    vendas_novos = novos_df["valor_rateado"].sum()
    spend_total = ads_p["spend"].sum()
    n_novos = novos_df["cliente_id"].nunique()
    hist_profiles = profiles[profiles["data_p"] < DATE_START]
    ltv_medio = hist_profiles["receita_total"].mean()
    ticket_novos = novos_df.drop_duplicates("numero")["total_pedido"].mean() if not novos_df.empty else 0

    render_cards(vendas_novos, spend_total, n_novos, ltv_medio, ticket_novos, len(dates))
    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # Regression data (full history)
    reg_uf = build_regression_data(df, ads, "cliente_uf", "uf")
    reg_marca = build_regression_data(df, ads, "marca", "marca")

    tab_e, tab_m = st.tabs(["Por Estado", "Por Marca"])

    with tab_e:
        render_tab(df_p, ads_p, profiles, reg_uf, dates, "cliente_uf", "uf", "e",
                   ltv_lookup_estado, ltv_fallback_estado)

    with tab_m:
        render_tab(df_p, ads_p, profiles, reg_marca, dates, "marca", "marca", "m",
                   ltv_lookup_marca, ltv_fallback_marca)

    st.markdown('<div class="footer-text">Astro — Campanhas × Vendas v3 | Análise de primeira compra | Tiny ERP + Google Ads</div>',
                unsafe_allow_html=True)


if __name__ == "__main__":
    main()
