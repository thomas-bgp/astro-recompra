"""
Astro — A História da Recompra
Duas abas: storytelling + dashboard analítico.
Dark-mode native.
"""

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from itertools import combinations
from pathlib import Path

import re

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
    '3M': '3M', 'Biosolvit': 'Biosolvit', 'Bracol': 'Bracol', 'Camper': 'Camper',
    'Cartom': 'Cartom', 'Danny': 'Danny', 'Delta Plus': 'Delta Plus',
    'Fujiwara': 'Fujiwara', 'Imbat': 'Imbat', 'Innpro': 'Innpro',
    'Kadesh': 'Kadesh', 'Kalipso': 'Kalipso', 'MG Cinto': 'MG Cinto',
    'Maicol': 'Maicol', 'Marluvas': 'Marluvas', 'Medix': 'Medix',
    'Nutriex': 'Nutriex', 'Soft Work': 'Soft Works', 'SuperSafety': 'Super Safety',
    'Volk': 'Volk',
}


def _extract_marca(camp):
    m = re.match(r'\[Pmax\]\s*-\s*(.+)', camp)
    if m:
        return MARCA_NORMALIZE.get(m.group(1).strip())
    if 'Marluvas' in camp:
        return 'Marluvas'
    if 'Cartom' in camp:
        return 'Cartom'
    return None

st.set_page_config(page_title="Astro — A História da Recompra", layout="wide")

# ═══════════════════════════════════════
# STYLING — dark mode native
# ═══════════════════════════════════════
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    .block-container { max-width: 1100px; padding-top: 2rem; }
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .hero-number {
        font-size: 5rem; font-weight: 900; line-height: 1;
        background: linear-gradient(135deg, #4fc3f7, #81d4fa);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .hero-sub { font-size: 1.3rem; color: #aab; font-weight: 400; margin-top: 0.5rem; }
    .hero-sub b { color: #4fc3f7; }
    .section-num {
        font-size: 0.85rem; font-weight: 700; letter-spacing: 3px;
        color: #4fc3f7; text-transform: uppercase; margin-bottom: 0.2rem;
    }
    .section-title {
        font-size: 2rem; font-weight: 800; color: #e8e8ec;
        margin-bottom: 0.3rem; line-height: 1.2;
    }
    .section-desc { font-size: 1.05rem; color: #999; margin-bottom: 1.5rem; }
    .insight-box {
        background: rgba(26, 115, 232, 0.12);
        border-left: 4px solid #4fc3f7; border-radius: 8px;
        padding: 1.2rem 1.5rem; margin: 1rem 0;
    }
    .insight-box p { margin: 0; color: #ddd; font-size: 1rem; }
    .insight-box strong { color: #4fc3f7; }
    .warning-box {
        background: rgba(249, 168, 37, 0.12);
        border-left: 4px solid #f9a825; border-radius: 8px;
        padding: 1rem 1.5rem; margin: 1rem 0;
    }
    .warning-box p { margin: 0; color: #ddd; font-size: 0.95rem; }
    .warning-box strong { color: #f9a825; }
    .metric-card {
        background: rgba(255,255,255,0.05); border-radius: 12px; padding: 1.5rem;
        border: 1px solid rgba(255,255,255,0.1); text-align: center;
    }
    .metric-card .value { font-size: 2.2rem; font-weight: 800; color: #e8e8ec; }
    .metric-card .label {
        font-size: 0.8rem; color: #888; margin-top: 0.3rem;
        text-transform: uppercase; letter-spacing: 1px;
    }
    .divider { border: none; border-top: 1px solid rgba(255,255,255,0.08); margin: 3rem 0; }
    .product-header { font-size: 1.6rem; font-weight: 700; color: #e8e8ec; padding: 1rem 0 0.5rem 0; }
    .tag {
        display: inline-block; padding: 4px 12px; border-radius: 20px;
        font-size: 0.8rem; font-weight: 600; margin-right: 6px;
    }
    .tag-green { background: rgba(46,125,50,0.25); color: #66bb6a; }
    .tag-blue { background: rgba(21,101,192,0.25); color: #64b5f6; }
    .tag-orange { background: rgba(230,81,0,0.25); color: #ffb74d; }
    .tag-red { background: rgba(198,40,40,0.25); color: #ef5350; }
    .footer-text { text-align:center; color:#666; font-size:0.85rem; padding: 1rem 0 3rem 0; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════
# THEME CONSTANTS
# ═══════════════════════════════════════
ACCENT = "#4fc3f7"
ACCENT2 = "#1a73e8"
DIM = "rgba(79,195,247,0.35)"
TEXT_COLOR = "#ddd"
GRID_COLOR = "rgba(255,255,255,0.06)"
PALETTE = ["#4fc3f7", "#1a73e8", "#81d4fa", "#0d47a1", "#4dd0e1",
           "#00838f", "#80deea", "#1565c0", "#006064", "#b2ebf2"]

PLOTLY_LAYOUT = dict(
    font=dict(family="Inter", size=13, color=TEXT_COLOR),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=20, r=20, t=40, b=20),
    xaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
    yaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
)


def _apply_dark(fig):
    """Apply dark theme to any plotly figure."""
    fig.update_layout(**PLOTLY_LAYOUT)
    fig.update_xaxes(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR, tickfont_color=TEXT_COLOR)
    fig.update_yaxes(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR, tickfont_color=TEXT_COLOR)
    return fig


# ═══════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════

@st.cache_data
def load_data():
    df = pd.read_parquet(DATA_PATH)
    df = df[df["situacao"] != "Cancelado"].copy()
    df["data_pedido"] = pd.to_datetime(df["data_pedido"])
    df["valor_rateado"] = pd.to_numeric(df["valor_rateado"], errors="coerce")
    df["mes"] = df["data_pedido"].dt.to_period("M").astype(str)
    return df


@st.cache_data
def load_ads_and_cross(df):
    """Load Ads data, cross with Tiny NEW CLIENTS by UF × marca × month.
    CAC = spend / clientes novos (not all orders)."""
    ads = pd.read_excel(ADS_PATH, sheet_name="Planilha1")
    ads["uf"] = ads["State (Geographic)"].map(STATE_MAP)
    ads["marca"] = ads["Campaign Name"].apply(_extract_marca)
    ads["mes"] = pd.to_datetime(ads["Day"]).dt.to_period("M").astype(str)
    ads = ads[ads["marca"].notna()].copy()

    # Ads aggregated by UF × marca × month
    ads_monthly = ads.groupby(["uf", "marca", "mes"]).agg(
        spend=("Cost (Spend)", "sum"),
        clicks=("Clicks", "sum"),
        impressions=("Impressions", "sum"),
    ).reset_index()

    # Tiny: total sales (all orders) by UF × marca × month
    vendas = df.groupby(["cliente_uf", "marca", "mes"]).agg(
        pedidos=("numero", "nunique"),
        receita=("valor_rateado", "sum"),
    ).reset_index()

    # Tiny: NEW CLIENTS ONLY by UF × marca × month
    orders = df.drop_duplicates("numero")[["numero", "cliente_id", "data_pedido", "Recompra", "mes"]]
    first = orders.sort_values("data_pedido").drop_duplicates("cliente_id", keep="first")
    novos_orders = first[first["Recompra"] == "Novo"]
    fi_novos = df[df["numero"].isin(set(novos_orders["numero"]))]

    cli_marca = fi_novos[["cliente_id", "marca", "cliente_uf"]].dropna(
        subset=["marca"]
    ).drop_duplicates(subset=["cliente_id", "marca"])
    cli_marca = cli_marca.merge(novos_orders[["cliente_id", "mes"]], on="cliente_id")

    novos_by = cli_marca.groupby(["cliente_uf", "marca", "mes"]).agg(
        clientes_novos=("cliente_id", "nunique"),
    ).reset_index()

    # Cross: ads + vendas + novos
    cross = ads_monthly.merge(
        vendas, left_on=["uf", "marca", "mes"],
        right_on=["cliente_uf", "marca", "mes"], how="inner",
    )
    cross = cross.merge(
        novos_by, left_on=["uf", "marca", "mes"],
        right_on=["cliente_uf", "marca", "mes"], how="left",
        suffixes=("", "_novos"),
    )
    cross["clientes_novos"] = cross["clientes_novos"].fillna(0).astype(int)
    cross["cac"] = cross["spend"] / cross["clientes_novos"].replace(0, float("nan"))
    cross["roas"] = cross["receita"] / cross["spend"].replace(0, float("nan"))

    return cross


@st.cache_data
def build_recompra_by_uf_marca(fi, clients, novos):
    """Recompra rate by UF and by UF x marca from first-order data."""
    first_row = fi.sort_values("data_pedido").drop_duplicates("cliente_id", keep="first")
    first_meta = first_row[["cliente_id", "cliente_uf", "marca"]].copy()
    first_meta = first_meta[first_meta["cliente_id"].isin(novos)]
    first_meta = first_meta.merge(
        clients[["cliente_id", "recomprou", "receita_total"]], on="cliente_id"
    )

    # By UF
    rec_uf = first_meta.groupby("cliente_uf").agg(
        clientes=("cliente_id", "nunique"),
        recompraram=("recomprou", "sum"),
        ltv_medio=("receita_total", "mean"),
    ).reset_index()
    rec_uf.columns = ["uf", "clientes", "recompraram", "ltv_medio"]
    rec_uf["taxa_recompra"] = rec_uf["recompraram"] / rec_uf["clientes"]

    # By UF x marca (dedup: 1 row per client x marca)
    fi_marca = fi[["cliente_id", "marca"]].dropna().drop_duplicates()
    fi_marca = fi_marca[fi_marca["cliente_id"].isin(novos)]
    fi_marca = fi_marca.merge(
        clients[["cliente_id", "recomprou", "receita_total"]], on="cliente_id"
    )
    fi_marca = fi_marca.merge(
        first_meta[["cliente_id", "cliente_uf"]].drop_duplicates(), on="cliente_id"
    )
    rec_uf_marca = fi_marca.groupby(["cliente_uf", "marca"]).agg(
        clientes=("cliente_id", "nunique"),
        recompraram=("recomprou", "sum"),
        ltv_medio=("receita_total", "mean"),
    ).reset_index()
    rec_uf_marca.columns = ["uf", "marca", "clientes", "recompraram", "ltv_medio"]
    rec_uf_marca["taxa_recompra"] = rec_uf_marca["recompraram"] / rec_uf_marca["clientes"]

    # By marca only
    rec_marca = fi_marca.groupby("marca").agg(
        clientes=("cliente_id", "nunique"),
        recompraram=("recomprou", "sum"),
        ltv_medio=("receita_total", "mean"),
    ).reset_index()
    rec_marca["taxa_recompra"] = rec_marca["recompraram"] / rec_marca["clientes"]

    return rec_uf, rec_uf_marca, rec_marca


@st.cache_data
def build_core(df):
    orders = df.drop_duplicates("numero")[["numero", "cliente_id", "data_pedido", "Recompra"]]
    first = orders.sort_values("data_pedido").drop_duplicates("cliente_id", keep="first")
    novos = set(first[first["Recompra"] == "Novo"]["cliente_id"])
    df_novo = df[df["cliente_id"].isin(novos)].copy()
    first_nums = set(first[first["cliente_id"].isin(novos)]["numero"])
    fi = df_novo[df_novo["numero"].isin(first_nums)].copy()
    subs = df_novo[~df_novo["numero"].isin(first_nums)].copy()

    recomprou = (
        df_novo.groupby("cliente_id")["Recompra"]
        .apply(lambda x: (x == "Recompra").any())
        .reset_index()
    )
    recomprou.columns = ["cliente_id", "recomprou"]

    client_stats = df_novo.groupby("cliente_id").agg(
        total_orders=("numero", "nunique"),
        first_date=("data_pedido", "min"),
        last_date=("data_pedido", "max"),
        receita_total=("valor_rateado", "sum"),
    ).reset_index()
    client_stats["meses_ativo"] = (
        (client_stats["last_date"] - client_stats["first_date"]).dt.days / 30.44
    )
    client_stats["pedidos_por_mes"] = client_stats.apply(
        lambda r: (r["total_orders"] - 1) / max(r["meses_ativo"], 1)
        if r["total_orders"] > 1 else 0, axis=1
    )
    client_stats = client_stats.merge(recomprou, on="cliente_id")

    if len(subs) > 0:
        tk_sub = subs.groupby("cliente_id").agg(
            receita_sub=("valor_rateado", "sum"),
            orders_sub=("numero", "nunique"),
        ).reset_index()
        tk_sub["ticket_recorrente"] = tk_sub["receita_sub"] / tk_sub["orders_sub"]
        client_stats = client_stats.merge(
            tk_sub[["cliente_id", "ticket_recorrente"]], on="cliente_id", how="left"
        )
    client_stats["ticket_recorrente"] = client_stats.get("ticket_recorrente", 0).fillna(0)

    return df_novo, fi, subs, client_stats, novos


@st.cache_data
def build_product_metrics(fi, client_stats):
    fi_dedup = fi[["cliente_id", "seo_title", "marca", "sub_categoria",
                    "categoria_mae"]].dropna(subset=["seo_title"]).drop_duplicates(
        subset=["cliente_id", "seo_title"]
    )
    fi_dedup = fi_dedup.merge(
        client_stats[["cliente_id", "recomprou", "total_orders",
                      "pedidos_por_mes", "receita_total", "ticket_recorrente"]],
        on="cliente_id",
    )
    gw = (
        fi_dedup.groupby(["seo_title", "marca", "sub_categoria", "categoria_mae"])
        .agg(
            clientes_1a=("cliente_id", "nunique"),
            recompraram=("recomprou", "sum"),
            media_orders=("total_orders", "mean"),
            media_ped_mes=("pedidos_por_mes", "mean"),
            ltv_medio=("receita_total", "mean"),
            ticket_recorrente=("ticket_recorrente", "mean"),
        )
        .reset_index()
    )
    gw["taxa_recompra"] = gw["recompraram"] / gw["clientes_1a"]
    return gw


@st.cache_data
def build_subcat_metrics(fi, client_stats):
    fi_dedup = fi[["cliente_id", "sub_categoria"]].dropna().drop_duplicates()
    fi_dedup = fi_dedup.merge(
        client_stats[["cliente_id", "recomprou", "total_orders",
                      "pedidos_por_mes", "receita_total"]],
        on="cliente_id",
    )
    sc = (
        fi_dedup.groupby("sub_categoria")
        .agg(
            clientes=("cliente_id", "nunique"),
            recompraram=("recomprou", "sum"),
            media_orders=("total_orders", "mean"),
            media_ped_mes=("pedidos_por_mes", "mean"),
            ltv_medio=("receita_total", "mean"),
        )
        .reset_index()
    )
    sc["taxa_recompra"] = sc["recompraram"] / sc["clientes"]
    return sc


@st.cache_data
def build_combos(fi, client_stats):
    basket_items = fi[["cliente_id", "sub_categoria"]].dropna().drop_duplicates()
    basket = (
        basket_items.groupby("cliente_id")["sub_categoria"]
        .apply(lambda x: frozenset(x))
        .reset_index()
    )
    basket.columns = ["cliente_id", "basket"]
    basket = basket.merge(
        client_stats[["cliente_id", "recomprou", "total_orders", "pedidos_por_mes"]],
        on="cliente_id",
    )

    singles = build_subcat_metrics(fi, client_stats)
    singles_lookup = singles.set_index("sub_categoria")["taxa_recompra"].to_dict()

    pair_rows = []
    for _, r in basket.iterrows():
        items = sorted(r["basket"])
        if len(items) >= 2:
            for a, b in combinations(items, 2):
                pair_rows.append({
                    "item_a": a, "item_b": b,
                    "cliente_id": r["cliente_id"],
                    "recomprou": r["recomprou"],
                })
    if not pair_rows:
        return pd.DataFrame()
    pair_df = pd.DataFrame(pair_rows)
    combos = (
        pair_df.groupby(["item_a", "item_b"])
        .agg(clientes=("cliente_id", "nunique"), recompraram=("recomprou", "sum"))
        .reset_index()
    )
    combos["taxa_recompra"] = combos["recompraram"] / combos["clientes"]
    combos["combo"] = combos["item_a"] + "  +  " + combos["item_b"]
    combos["solo_a"] = combos["item_a"].map(singles_lookup)
    combos["solo_b"] = combos["item_b"].map(singles_lookup)
    combos["melhor_solo"] = combos[["solo_a", "solo_b"]].max(axis=1)
    combos["uplift"] = combos["taxa_recompra"] - combos["melhor_solo"]
    return combos


# ═══════════════════════════════════════
# UI HELPERS
# ═══════════════════════════════════════

def render_metric(value, label):
    st.markdown(f"""
    <div class="metric-card">
        <div class="value">{value}</div>
        <div class="label">{label}</div>
    </div>
    """, unsafe_allow_html=True)


def section_header(num, title, desc=""):
    st.markdown(f"""
    <div class="section-num">{num}</div>
    <div class="section-title">{title}</div>
    <div class="section-desc">{desc}</div>
    """, unsafe_allow_html=True)


def insight(text):
    st.markdown(f'<div class="insight-box"><p>{text}</p></div>', unsafe_allow_html=True)


def warning(text):
    st.markdown(f'<div class="warning-box"><p>{text}</p></div>', unsafe_allow_html=True)


# ═══════════════════════════════════════
# TAB 1: STORYTELLING
# ═══════════════════════════════════════

def tab_story(df, df_novo, fi, subs, clients, novos, gw, subcat, combos, taxa_global):
    total_novos = len(novos)
    total_recompra = clients["recomprou"].sum()

    # ── HERO ──
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown(f'<div class="hero-number">{taxa_global:.0%}</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="hero-sub">'
            'dos seus clientes novos fazem uma segunda compra.<br>'
            'Mas esse numero muda <b>drasticamente</b> dependendo do que eles compram no primeiro carrinho.'
            '</div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        render_metric(f"{total_novos:,}", "clientes novos analisados")
        st.markdown("<br>", unsafe_allow_html=True)
        render_metric(f"{total_recompra:,}", "fizeram recompra")

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # ── 01: THE SPREAD ──
    section_header(
        "01 — O PRODUTO IMPORTA",
        "A taxa de recompra varia de 6% a 72% dependendo do primeiro carrinho.",
        "Filtramos produtos com pelo menos 30 clientes novos para evitar ruido.",
    )

    min_cli = st.slider("Minimo de clientes novos por produto", 10, 500, 200, key="min_story")
    gw_f = gw[gw["clientes_1a"] >= min_cli].copy()

    top = gw_f.nlargest(20, "taxa_recompra")
    bot = gw_f.nsmallest(10, "taxa_recompra")
    spread = pd.concat([top, bot]).drop_duplicates("seo_title")
    spread = spread.sort_values("taxa_recompra", ascending=True)

    fig = go.Figure()
    colors = [ACCENT if v >= taxa_global else DIM for v in spread["taxa_recompra"]]
    fig.add_trace(go.Bar(
        x=spread["taxa_recompra"], y=spread["seo_title"],
        orientation="h", marker_color=colors,
        text=spread["taxa_recompra"].apply(lambda v: f" {v:.0%}"),
        textposition="outside", textfont=dict(size=12, color=TEXT_COLOR),
        hovertemplate=(
            "<b>%{y}</b><br>Taxa: %{x:.1%}<br>"
            "Clientes: %{customdata[0]:,}<br>"
            "LTV: R$ %{customdata[1]:,.0f}<extra></extra>"
        ),
        customdata=spread[["clientes_1a", "ltv_medio"]].values,
    ))
    fig.add_vline(x=taxa_global, line_dash="dot", line_color="#ef5350",
                  annotation_text=f"Media {taxa_global:.0%}",
                  annotation_font_color=TEXT_COLOR, annotation_position="top")
    _apply_dark(fig)
    fig.update_layout(
        height=max(500, len(spread) * 28),
        xaxis=dict(tickformat=".0%", range=[0, min(spread["taxa_recompra"].max() * 1.15, 1)]),
        yaxis=dict(tickfont=dict(size=11, color=TEXT_COLOR)),
    )
    st.plotly_chart(fig, use_container_width=True)

    best = gw_f.nlargest(1, "taxa_recompra").iloc[0]
    worst = gw_f.nsmallest(1, "taxa_recompra").iloc[0]
    insight(
        f"Quem entra comprando <strong>{best['seo_title']}</strong> tem "
        f"<strong>{best['taxa_recompra']:.0%}</strong> de chance de voltar. "
        f"Ja quem entra com <strong>{worst['seo_title']}</strong> "
        f"tem so <strong>{worst['taxa_recompra']:.0%}</strong>. "
        f"Diferenca de <strong>{best['taxa_recompra'] - worst['taxa_recompra']:.0%}</strong>."
    )

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # ── 02: CATEGORIES ──
    section_header(
        "02 — POR QUE CONSUMIVEIS VENCEM",
        "Categorias de consumo recorrente (luvas, respiradores) geram mais recompra que duraveis (calcados).",
    )

    sc_f = subcat[subcat["clientes"] >= 30].sort_values("taxa_recompra", ascending=True)
    fig2 = go.Figure()
    cat_colors = [ACCENT if v >= taxa_global else DIM for v in sc_f["taxa_recompra"]]
    fig2.add_trace(go.Bar(
        x=sc_f["taxa_recompra"], y=sc_f["sub_categoria"],
        orientation="h", marker_color=cat_colors,
        text=sc_f.apply(lambda r: f" {r['taxa_recompra']:.0%}  ({r['clientes']:,} cli)", axis=1),
        textposition="outside", textfont=dict(size=11, color=TEXT_COLOR),
    ))
    fig2.add_vline(x=taxa_global, line_dash="dot", line_color="#ef5350",
                   annotation_text=f"Media {taxa_global:.0%}",
                   annotation_font_color=TEXT_COLOR)
    _apply_dark(fig2)
    fig2.update_layout(height=max(400, len(sc_f) * 26), xaxis=dict(tickformat=".0%"))
    st.plotly_chart(fig2, use_container_width=True)

    top_cat = sc_f.nlargest(3, "taxa_recompra")
    bot_cat = sc_f.nsmallest(3, "taxa_recompra")
    insight(
        f"<strong>Top 3</strong>: {', '.join(top_cat['sub_categoria'])} "
        f"(media {top_cat['taxa_recompra'].mean():.0%}). "
        f"<strong>Bottom 3</strong>: {', '.join(bot_cat['sub_categoria'])} "
        f"(media {bot_cat['taxa_recompra'].mean():.0%}). "
        f"Luvas e respiradores sao <strong>consumiveis</strong> — acabam e o cliente volta."
    )

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # ── 03: COMBOS ──
    section_header(
        "03 — O EFEITO DO COMBO",
        "Quando certas categorias sao compradas juntas no primeiro carrinho, "
        "a chance de recompra sobe.",
    )

    if len(combos) > 0:
        combos_f = combos[combos["clientes"] >= 30].copy()
        top_combos = combos_f.nlargest(15, "uplift")

        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            name="Melhor item solo",
            x=top_combos["combo"], y=top_combos["melhor_solo"],
            marker_color="rgba(255,255,255,0.15)",
            text=top_combos["melhor_solo"].apply(lambda v: f"{v:.0%}"),
            textposition="outside", textfont_color=TEXT_COLOR,
        ))
        fig3.add_trace(go.Bar(
            name="Combo junto",
            x=top_combos["combo"], y=top_combos["taxa_recompra"],
            marker_color=ACCENT,
            text=top_combos.apply(
                lambda r: f"{r['taxa_recompra']:.0%} (+{r['uplift']:.0%})", axis=1
            ),
            textposition="outside", textfont_color=TEXT_COLOR,
        ))
        _apply_dark(fig3)
        fig3.update_layout(
            barmode="group", height=500,
            yaxis=dict(tickformat=".0%"),
            xaxis=dict(tickangle=-45, tickfont=dict(size=9)),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, font_color=TEXT_COLOR),
        )
        st.plotly_chart(fig3, use_container_width=True)

        best_combo = top_combos.iloc[0]
        insight(
            f"<strong>{best_combo['combo']}</strong>: quando comprados juntos, "
            f"<strong>{best_combo['taxa_recompra']:.0%}</strong> voltam — "
            f"uplift de <strong>+{best_combo['uplift']:.0%}</strong> vs melhor "
            f"item solo ({best_combo['melhor_solo']:.0%})."
        )
        warning(
            "Combos servem para <strong>cross-sell no site</strong> (sugestoes na pagina, bundles). "
            "No Google Ads, anuncie o produto individual."
        )

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # ── 04: SCATTER ──
    section_header(
        "04 — VOLUME vs RECOMPRA",
        "O produto ideal tem alto volume E alta recompra. "
        "Tamanho da bolha = LTV medio.",
    )

    fig4 = px.scatter(
        gw_f, x="clientes_1a", y="taxa_recompra",
        size="ltv_medio", color="categoria_mae",
        hover_name="seo_title",
        hover_data={"clientes_1a": ":,", "taxa_recompra": ":.1%",
                    "ltv_medio": ":,.0f", "media_ped_mes": ":.2f"},
        labels={"clientes_1a": "Clientes novos",
                "taxa_recompra": "Taxa de recompra",
                "categoria_mae": "Categoria"},
        color_discrete_sequence=PALETTE,
    )
    fig4.add_hline(y=taxa_global, line_dash="dot", line_color="#ef5350")
    _apply_dark(fig4)
    fig4.update_yaxes(tickformat=".0%")
    fig4.update_layout(height=550, legend=dict(font_color=TEXT_COLOR))
    st.plotly_chart(fig4, use_container_width=True)

    insight(
        "Canto <strong>superior direito</strong> = muitos clientes E alta recompra. "
        "Melhores candidatos para Google Ads."
    )

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # ── 05: GOOGLE ADS vs VENDAS REAIS ──
    section_header(
        "05 — GOOGLE ADS vs VENDAS REAIS",
        "Cruzamos spend do Ads com clientes NOVOS do Tiny (nao conversoes do Google). "
        "CAC = quanto gastou em Ads / quantos clientes novos entraram naquele estado x marca.",
    )

    cross_raw = load_ads_and_cross(df)
    rec_uf, rec_uf_marca, rec_marca = build_recompra_by_uf_marca(fi, clients, novos)

    # ── Date filter ──
    all_months = sorted(cross_raw["mes"].unique())
    default_idx = all_months.index("2026-02") if "2026-02" in all_months else len(all_months) - 1
    ads_c1, ads_c2 = st.columns([1, 2])
    with ads_c1:
        sel_month = st.selectbox(
            "Periodo", all_months, index=default_idx, key="ads_month_story"
        )
    with ads_c2:
        st.markdown(f"<br><span style='color:#888'>Mostrando: <strong style='color:{ACCENT}'>{sel_month}</strong></span>",
                    unsafe_allow_html=True)

    cross = cross_raw[cross_raw["mes"] == sel_month].copy()

    # ── By Marca ──
    cr_marca = cross.groupby("marca").agg(
        spend=("spend", "sum"), clientes_novos=("clientes_novos", "sum"),
        pedidos=("pedidos", "sum"), receita=("receita", "sum"),
        clicks=("clicks", "sum"),
    ).reset_index()
    cr_marca["cac"] = cr_marca["spend"] / cr_marca["clientes_novos"].replace(0, float("nan"))
    cr_marca["roas"] = cr_marca["receita"] / cr_marca["spend"].replace(0, float("nan"))
    cr_marca = cr_marca.merge(rec_marca[["marca", "taxa_recompra", "ltv_medio"]], on="marca", how="left")
    cr_marca = cr_marca[cr_marca["clientes_novos"] >= 3]

    st.markdown("**Marca: CAC (Custo de Aquisicao de Cliente) vs Taxa de Recompra**")
    st.caption("CAC = spend Ads / clientes NOVOS no Tiny. Bolha = spend. Ideal = canto inferior direito.")

    if len(cr_marca) > 0:
        fig_ads_m = px.scatter(
            cr_marca, x="taxa_recompra", y="cac",
            size="spend", text="marca",
            hover_data={"spend": ":,.0f", "clientes_novos": ":,", "roas": ":.1f",
                        "taxa_recompra": ":.1%", "cac": ":,.0f"},
            labels={"taxa_recompra": "Taxa Recompra (historica)", "cac": "CAC (R$)"},
            color_discrete_sequence=[ACCENT],
        )
        fig_ads_m.update_traces(textposition="top center", textfont=dict(size=11, color=TEXT_COLOR))
        _apply_dark(fig_ads_m)
        fig_ads_m.update_xaxes(tickformat=".0%")
        fig_ads_m.update_layout(height=450, showlegend=False)
        st.plotly_chart(fig_ads_m, use_container_width=True, key="ads_marca_scatter")

        best = cr_marca.nsmallest(1, "cac").iloc[0]
        worst = cr_marca.nlargest(1, "cac").iloc[0]
        insight(
            f"Em <strong>{sel_month}</strong>, menor CAC: <strong>{best['marca']}</strong> "
            f"(R$ {best['cac']:,.0f}/cliente — {best['clientes_novos']:,} novos). "
            f"Maior CAC: <strong>{worst['marca']}</strong> "
            f"(R$ {worst['cac']:,.0f}/cliente — {worst['clientes_novos']:,} novos)."
        )

    # ── By UF ──
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**Estado: CAC vs Taxa de Recompra**")
    cr_uf = cross.groupby("uf").agg(
        spend=("spend", "sum"), clientes_novos=("clientes_novos", "sum"),
        pedidos=("pedidos", "sum"), receita=("receita", "sum"),
    ).reset_index()
    cr_uf["cac"] = cr_uf["spend"] / cr_uf["clientes_novos"].replace(0, float("nan"))
    cr_uf["roas"] = cr_uf["receita"] / cr_uf["spend"].replace(0, float("nan"))
    cr_uf = cr_uf.merge(rec_uf[["uf", "taxa_recompra", "ltv_medio"]], on="uf", how="left")
    cr_uf = cr_uf[cr_uf["clientes_novos"] >= 3]

    if len(cr_uf) > 0:
        fig_ads_uf = px.scatter(
            cr_uf, x="taxa_recompra", y="cac",
            size="spend", text="uf",
            hover_data={"spend": ":,.0f", "clientes_novos": ":,", "roas": ":.1f",
                        "taxa_recompra": ":.1%", "cac": ":,.0f"},
            labels={"taxa_recompra": "Taxa Recompra", "cac": "CAC (R$)"},
            color_discrete_sequence=[ACCENT],
        )
        fig_ads_uf.update_traces(textposition="top center", textfont=dict(size=11, color=TEXT_COLOR))
        _apply_dark(fig_ads_uf)
        fig_ads_uf.update_xaxes(tickformat=".0%")
        fig_ads_uf.update_layout(height=450, showlegend=False)
        st.plotly_chart(fig_ads_uf, use_container_width=True, key="ads_uf_scatter")

    # ── Heatmap UF x Marca: CPA Real ──
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**Heatmap: CAC por UF x Marca**")
    st.caption("Cor = CAC (mais escuro = mais caro para adquirir cliente). Celulas com 3+ clientes novos.")

    cr_full = cross.groupby(["uf", "marca"]).agg(
        spend=("spend", "sum"), clientes_novos=("clientes_novos", "sum"),
        pedidos=("pedidos", "sum"), receita=("receita", "sum"),
    ).reset_index()
    cr_full["cac"] = cr_full["spend"] / cr_full["clientes_novos"].replace(0, float("nan"))
    cr_full = cr_full[cr_full["clientes_novos"] >= 3]

    if len(cr_full) > 0:
        heat_pivot = cr_full.pivot_table(index="uf", columns="marca", values="cac", aggfunc="first")
        heat_pivot = heat_pivot.dropna(how="all").dropna(axis=1, how="all")

        fig_heat = px.imshow(
            heat_pivot.values,
            x=heat_pivot.columns.tolist(),
            y=heat_pivot.index.tolist(),
            color_continuous_scale="YlOrRd",
            aspect="auto",
            labels=dict(color="CAC (R$)"),
            text_auto=",.0f",
        )
        _apply_dark(fig_heat)
        fig_heat.update_layout(height=500)
        fig_heat.update_traces(textfont=dict(size=10))
        st.plotly_chart(fig_heat, use_container_width=True, key="ads_heatmap")

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # ── 06: DEEP DIVE ──
    section_header(
        "06 — RAIO-X DO PRODUTO",
        "Selecione um produto para ver sua historia completa: "
        "quem compra, onde funciona, o que compram depois, e se ele e o driver do carrinho.",
    )

    # Build lookup: merge gw with Feb sales, sort by pedidos_feb desc
    gw_dedup = gw_f.sort_values("clientes_1a", ascending=False).drop_duplicates("seo_title", keep="first")
    vendas_feb = (
        df[df["mes"] == "2026-02"]
        .groupby("seo_title")
        .agg(pedidos_feb=("numero", "nunique"))
        .reset_index()
    )
    gw_dedup = gw_dedup.merge(vendas_feb, on="seo_title", how="left")
    gw_dedup["pedidos_feb"] = gw_dedup["pedidos_feb"].fillna(0).astype(int)
    gw_dedup = gw_dedup.sort_values("pedidos_feb", ascending=False)
    gw_lookup = gw_dedup.set_index("seo_title")[
        ["taxa_recompra", "clientes_1a", "pedidos_feb"]
    ].to_dict("index")
    options = gw_dedup["seo_title"].tolist()

    selected = st.selectbox(
        "Escolha um produto:",
        options,
        format_func=lambda x: (
            f"{gw_lookup[x]['pedidos_feb']} ped fev  ·  "
            f"{gw_lookup[x]['taxa_recompra']:.0%} recompra  ·  {x}"
        ),
    )

    if selected:
        _render_product_detail(selected, gw_f, fi, subs, clients, novos, taxa_global)

    # ── FOOTER ──
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown(
        '<div class="footer-text">'
        'Astro — Analise de Recompra · Apenas clientes novos · Exclui cancelados<br>'
        'Taxa de recompra = % de CPFs/CNPJs que fizeram pelo menos 1 compra adicional'
        '</div>',
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════
# PRODUCT DETAIL (shared by both tabs)
# ═══════════════════════════════════════

def _render_product_detail(selected, gw_f, fi, subs, clients, novos, taxa_global, prefix="s"):
    row = gw_f[gw_f["seo_title"] == selected].iloc[0]
    clients_of_prod = set(fi[fi["seo_title"] == selected]["cliente_id"].unique()) & novos
    prod_clients = clients[clients["cliente_id"].isin(clients_of_prod)]
    n_cli = len(prod_clients)
    n_recompra = prod_clients["recomprou"].sum()
    taxa = n_recompra / n_cli if n_cli > 0 else 0

    st.markdown(f'<div class="product-header">{selected}</div>', unsafe_allow_html=True)

    tags = []
    if taxa > taxa_global * 1.1:
        tags.append('<span class="tag tag-green">Acima da media</span>')
    elif taxa < taxa_global * 0.9:
        tags.append('<span class="tag tag-red">Abaixo da media</span>')
    else:
        tags.append('<span class="tag tag-blue">Na media</span>')
    tags.append(f'<span class="tag tag-blue">{row["marca"]}</span>')
    tags.append(f'<span class="tag tag-orange">{row["sub_categoria"]}</span>')
    st.markdown(" ".join(tags), unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        render_metric(f"{taxa:.0%}", "Taxa recompra")
    with m2:
        render_metric(f"{n_cli:,}", "Clientes novos")
    with m3:
        render_metric(f"{row['media_orders']:.1f}", "Pedidos total (media)")
    with m4:
        render_metric(f"{row['media_ped_mes']:.2f}", "Pedidos/mes")
    with m5:
        render_metric(f"R$ {row['ltv_medio']:,.0f}", "LTV medio")

    st.markdown("<br>", unsafe_allow_html=True)

    # Driver analysis
    fi_prod = fi[fi["cliente_id"].isin(clients_of_prod)]
    items_per_client = fi_prod.groupby("cliente_id")["seo_title"].nunique()
    solo = (items_per_client == 1).sum()
    pct_solo = solo / n_cli if n_cli > 0 else 0

    max_val = fi_prod.groupby("cliente_id")["valor_rateado"].max().reset_index()
    max_val.columns = ["cliente_id", "max_val"]
    prod_val = fi_prod[fi_prod["seo_title"] == selected].groupby("cliente_id")["valor_rateado"].sum().reset_index()
    prod_val.columns = ["cliente_id", "prod_val"]
    driver_check = max_val.merge(prod_val, on="cliente_id")
    pct_driver = (driver_check["prod_val"] >= driver_check["max_val"]).mean() if len(driver_check) > 0 else 0

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.markdown("**Driver ou superfluo?**")
        if pct_solo > 0.4 and pct_driver > 0.6:
            st.markdown('<span class="tag tag-green">DRIVER</span> Este produto e o motivo da compra.',
                        unsafe_allow_html=True)
        elif pct_solo < 0.15 and pct_driver < 0.3:
            st.markdown('<span class="tag tag-orange">COMPLEMENTAR</span> Geralmente acompanha outros.',
                        unsafe_allow_html=True)
        else:
            st.markdown('<span class="tag tag-blue">MISTO</span> As vezes driver, as vezes complemento.',
                        unsafe_allow_html=True)

        fig_driver = go.Figure(go.Pie(
            values=[pct_solo, 1 - pct_solo],
            labels=["Comprou SO este", "Comprou com outros"],
            marker_colors=[ACCENT, "rgba(255,255,255,0.1)"],
            textinfo="label+percent", hole=0.5,
            textfont=dict(size=12, color=TEXT_COLOR),
        ))
        fig_driver.update_layout(
            height=250, margin=dict(l=10, r=10, t=10, b=10),
            showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_driver, use_container_width=True, key=f"{prefix}_pie")
        st.caption(f"{pct_driver:.0%} dos carrinhos este produto e o item mais caro.")

    with col_d2:
        st.markdown("**Melhores regioes para este produto**")
        fi_uf = fi_prod.drop_duplicates("cliente_id")[["cliente_id", "cliente_uf"]]
        fi_uf = fi_uf.merge(prod_clients[["cliente_id", "recomprou"]], on="cliente_id")
        uf_agg = fi_uf.groupby("cliente_uf").agg(
            clientes=("cliente_id", "nunique"), recomprou=("recomprou", "sum"),
        ).reset_index()
        uf_agg["taxa"] = uf_agg["recomprou"] / uf_agg["clientes"]
        uf_agg = uf_agg[uf_agg["clientes"] >= 5].sort_values("taxa", ascending=True)

        fig_uf = go.Figure(go.Bar(
            x=uf_agg["taxa"], y=uf_agg["cliente_uf"],
            orientation="h",
            marker_color=[ACCENT if t >= taxa else DIM for t in uf_agg["taxa"]],
            text=uf_agg.apply(lambda r: f" {r['taxa']:.0%}  ({r['clientes']} cli)", axis=1),
            textposition="outside", textfont=dict(size=11, color=TEXT_COLOR),
        ))
        fig_uf.add_vline(x=taxa, line_dash="dot", line_color="#ef5350")
        _apply_dark(fig_uf)
        fig_uf.update_layout(
            height=max(200, len(uf_agg) * 28),
            xaxis=dict(tickformat=".0%", visible=False),
        )
        st.plotly_chart(fig_uf, use_container_width=True, key=f"{prefix}_uf")

    st.markdown("<br>", unsafe_allow_html=True)
    col_n1, col_n2 = st.columns(2)

    with col_n1:
        st.markdown("**O que compram nos pedidos seguintes**")
        st.caption("Dos clientes que entraram por este produto, o que compram depois?")
        subs_prod = subs[subs["cliente_id"].isin(clients_of_prod)]
        if len(subs_prod) > 0:
            next_prods = (
                subs_prod.groupby("seo_title")["cliente_id"]
                .nunique().sort_values(ascending=False).head(12).reset_index()
            )
            next_prods.columns = ["seo_title", "clientes"]
            next_prods["pct"] = next_prods["clientes"] / n_cli
            fig_next = go.Figure(go.Bar(
                x=next_prods["pct"][::-1], y=next_prods["seo_title"][::-1],
                orientation="h", marker_color=ACCENT,
                text=next_prods[::-1].apply(lambda r: f" {r['pct']:.0%}  ({r['clientes']})", axis=1),
                textposition="outside", textfont=dict(size=11, color=TEXT_COLOR),
            ))
            _apply_dark(fig_next)
            fig_next.update_layout(
                height=max(300, len(next_prods) * 28),
                xaxis=dict(visible=False), yaxis=dict(tickfont=dict(size=10)),
            )
            st.plotly_chart(fig_next, use_container_width=True, key=f"{prefix}_next")
        else:
            st.info("Sem dados de compras subsequentes.")

    with col_n2:
        st.markdown("**O que compram junto no 1o carrinho**")
        st.caption("Produtos que aparecem junto na primeira compra.")
        with_prods = (
            fi_prod[fi_prod["seo_title"] != selected]
            .groupby("seo_title")["cliente_id"]
            .nunique().sort_values(ascending=False).head(12).reset_index()
        )
        with_prods.columns = ["seo_title", "clientes"]
        with_prods["pct"] = with_prods["clientes"] / n_cli
        if len(with_prods) > 0:
            fig_with = go.Figure(go.Bar(
                x=with_prods["pct"][::-1], y=with_prods["seo_title"][::-1],
                orientation="h", marker_color=ACCENT2,
                text=with_prods[::-1].apply(lambda r: f" {r['pct']:.0%}  ({r['clientes']})", axis=1),
                textposition="outside", textfont=dict(size=11, color=TEXT_COLOR),
            ))
            _apply_dark(fig_with)
            fig_with.update_layout(
                height=max(300, len(with_prods) * 28),
                xaxis=dict(visible=False), yaxis=dict(tickfont=dict(size=10)),
            )
            st.plotly_chart(fig_with, use_container_width=True, key=f"{prefix}_with")
        else:
            st.info("Este produto geralmente e comprado sozinho.")

    st.markdown("<br>", unsafe_allow_html=True)
    delta = taxa - taxa_global
    delta_str = f"+{delta:.0%}" if delta > 0 else f"{delta:.0%}"
    if delta > 0:
        insight(
            f"<strong>{selected}</strong> tem taxa de recompra de "
            f"<strong>{taxa:.0%}</strong> ({delta_str} vs media de {taxa_global:.0%}). "
            f"{'E um <strong>driver</strong> de carrinho — ' if pct_driver > 0.6 else ''}"
            f"{'comprado sozinho por ' + f'{pct_solo:.0%} dos clientes. ' if pct_solo > 0.3 else ''}"
            f"LTV medio de <strong>R$ {row['ltv_medio']:,.0f}</strong>."
        )
    else:
        warning(
            f"<strong>{selected}</strong> tem taxa de recompra de "
            f"<strong>{taxa:.0%}</strong> ({delta_str} vs media de {taxa_global:.0%}). "
            f"Considere usar outro produto como porta de entrada."
        )


# ═══════════════════════════════════════
# TAB 2: DASHBOARD ANALITICO
# ═══════════════════════════════════════

def tab_dashboard(df, df_novo, fi, subs, clients, novos, gw, subcat, combos, taxa_global):
    total_novos = len(novos)
    total_recompra = clients["recomprou"].sum()
    rep = clients[clients["total_orders"] >= 2]

    # ── KPIs ──
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    with k1:
        render_metric(f"{total_novos:,}", "Clientes novos")
    with k2:
        render_metric(f"{total_recompra:,}", "Recompraram")
    with k3:
        render_metric(f"{taxa_global:.1%}", "Taxa recompra")
    with k4:
        render_metric(f"{rep['pedidos_por_mes'].median():.2f}", "Ped/mes (mediana)")
    with k5:
        render_metric(f"R$ {rep['ticket_recorrente'].mean():,.0f}", "Ticket recorrente")
    with k6:
        render_metric(f"R$ {clients[clients['recomprou']]['receita_total'].mean():,.0f}", "LTV recompra")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Filters ──
    c1, c2, c3 = st.columns(3)
    with c1:
        min_cli = st.slider("Min. clientes novos", 10, 500, 200, key="min_dash")
    with c2:
        marcas = st.multiselect("Marcas", sorted(gw["marca"].dropna().unique()), key="marcas_dash")
    with c3:
        cats = st.multiselect("Categorias", sorted(gw["categoria_mae"].dropna().unique()), key="cats_dash")

    gw_f = gw[gw["clientes_1a"] >= min_cli].copy()
    if marcas:
        gw_f = gw_f[gw_f["marca"].isin(marcas)]
    if cats:
        gw_f = gw_f[gw_f["categoria_mae"].isin(cats)]

    # ── Full table ──
    st.markdown("### Todos os Produtos — Gateway")
    st.dataframe(
        gw_f.sort_values("taxa_recompra", ascending=False)[
            ["seo_title", "marca", "sub_categoria", "clientes_1a",
             "recompraram", "taxa_recompra", "media_orders",
             "media_ped_mes", "ltv_medio", "ticket_recorrente"]
        ].style.format({
            "taxa_recompra": "{:.1%}",
            "media_orders": "{:.1f}",
            "media_ped_mes": "{:.2f}",
            "ltv_medio": "R$ {:,.0f}",
            "ticket_recorrente": "R$ {:,.0f}",
        }).background_gradient(subset=["taxa_recompra"], cmap="YlGnBu"),
        use_container_width=True,
        height=500,
    )

    # ── Sub_categoria table ──
    st.markdown("### Sub-Categorias")
    sc_f = subcat[subcat["clientes"] >= 20].sort_values("taxa_recompra", ascending=False)
    st.dataframe(
        sc_f.style.format({
            "taxa_recompra": "{:.1%}",
            "media_orders": "{:.1f}",
            "media_ped_mes": "{:.2f}",
            "ltv_medio": "R$ {:,.0f}",
        }).background_gradient(subset=["taxa_recompra"], cmap="YlGnBu"),
        use_container_width=True,
    )

    # ── Combos table ──
    if len(combos) > 0:
        st.markdown("### Combos — Uplift de Recompra")
        combos_f = combos[combos["clientes"] >= 30].sort_values("uplift", ascending=False)
        st.dataframe(
            combos_f[["combo", "clientes", "taxa_recompra", "solo_a", "solo_b",
                       "melhor_solo", "uplift"]].style.format({
                "taxa_recompra": "{:.1%}",
                "solo_a": "{:.1%}",
                "solo_b": "{:.1%}",
                "melhor_solo": "{:.1%}",
                "uplift": "{:+.1%}",
            }).background_gradient(subset=["uplift"], cmap="RdYlGn"),
            use_container_width=True,
            height=400,
        )

    # ── Google Ads x Vendas Reais ──
    st.markdown("### Google Ads x Vendas Reais (Tiny)")
    cross_raw = load_ads_and_cross(df)
    rec_uf, rec_uf_marca, rec_marca = build_recompra_by_uf_marca(fi, clients, novos)

    all_months = sorted(cross_raw["mes"].unique())
    default_idx = all_months.index("2026-02") if "2026-02" in all_months else len(all_months) - 1
    sel_month_d = st.selectbox("Periodo", all_months, index=default_idx, key="ads_month_dash")

    cross = cross_raw[cross_raw["mes"] == sel_month_d]

    # By marca
    cr_marca = cross.groupby("marca").agg(
        spend=("spend", "sum"), clientes_novos=("clientes_novos", "sum"),
        pedidos=("pedidos", "sum"), receita=("receita", "sum"),
    ).reset_index()
    cr_marca["cac"] = cr_marca["spend"] / cr_marca["clientes_novos"].replace(0, float("nan"))
    cr_marca["roas"] = cr_marca["receita"] / cr_marca["spend"].replace(0, float("nan"))
    cr_marca = cr_marca.merge(rec_marca[["marca", "taxa_recompra", "ltv_medio"]], on="marca", how="left")

    # By UF
    cr_uf = cross.groupby("uf").agg(
        spend=("spend", "sum"), clientes_novos=("clientes_novos", "sum"),
        pedidos=("pedidos", "sum"), receita=("receita", "sum"),
    ).reset_index()
    cr_uf["cac"] = cr_uf["spend"] / cr_uf["clientes_novos"].replace(0, float("nan"))
    cr_uf["roas"] = cr_uf["receita"] / cr_uf["spend"].replace(0, float("nan"))
    cr_uf = cr_uf.merge(rec_uf[["uf", "taxa_recompra", "ltv_medio"]], on="uf", how="left")

    # By UF x marca
    cr_full = cross.groupby(["uf", "marca"]).agg(
        spend=("spend", "sum"), clientes_novos=("clientes_novos", "sum"),
        pedidos=("pedidos", "sum"), receita=("receita", "sum"),
    ).reset_index()
    cr_full["cac"] = cr_full["spend"] / cr_full["clientes_novos"].replace(0, float("nan"))
    cr_full["roas"] = cr_full["receita"] / cr_full["spend"].replace(0, float("nan"))
    cr_full = cr_full.merge(rec_uf_marca[["uf", "marca", "taxa_recompra"]], on=["uf", "marca"], how="left")

    d_c1, d_c2 = st.columns(2)
    with d_c1:
        st.markdown("**Por Marca**")
        st.dataframe(
            cr_marca.sort_values("cac")[
                ["marca", "spend", "clientes_novos", "pedidos", "receita", "cac", "roas",
                 "taxa_recompra", "ltv_medio"]
            ].style.format({
                "spend": "R$ {:,.0f}", "receita": "R$ {:,.0f}",
                "cac": "R$ {:,.0f}", "roas": "{:.1f}x",
                "taxa_recompra": "{:.1%}", "ltv_medio": "R$ {:,.0f}",
            }).background_gradient(subset=["cac"], cmap="YlOrRd"),
            use_container_width=True,
        )
    with d_c2:
        st.markdown("**Por Estado**")
        st.dataframe(
            cr_uf.sort_values("cac")[
                ["uf", "spend", "clientes_novos", "pedidos", "receita", "cac", "roas",
                 "taxa_recompra", "ltv_medio"]
            ].style.format({
                "spend": "R$ {:,.0f}", "receita": "R$ {:,.0f}",
                "cac": "R$ {:,.0f}", "roas": "{:.1f}x",
                "taxa_recompra": "{:.1%}", "ltv_medio": "R$ {:,.0f}",
            }).background_gradient(subset=["cac"], cmap="YlOrRd"),
            use_container_width=True,
        )

    st.markdown("**UF x Marca — Detalhes**")
    st.dataframe(
        cr_full[cr_full["clientes_novos"] >= 3].sort_values("cac")[
            ["uf", "marca", "spend", "clientes_novos", "pedidos", "receita", "cac", "roas", "taxa_recompra"]
        ].style.format({
            "spend": "R$ {:,.0f}", "receita": "R$ {:,.0f}",
            "cac": "R$ {:,.0f}", "roas": "{:.1f}x",
            "taxa_recompra": "{:.1%}",
        }).background_gradient(subset=["cac"], cmap="YlOrRd"),
        use_container_width=True,
        height=400,
    )

    # ── Perfil: PJ vs PF ──
    st.markdown("### Perfil — PJ vs PF")
    first_row = df_novo.sort_values("data_pedido").drop_duplicates("cliente_id", keep="first")
    first_meta = first_row[["cliente_id", "cliente_tipo_pessoa", "cliente_uf", "forma_pagamento"]].copy()
    first_meta = first_meta.merge(
        clients[["cliente_id", "recomprou", "total_orders", "pedidos_por_mes", "receita_total"]],
        on="cliente_id",
    )

    perfil_tipo = first_meta.groupby("cliente_tipo_pessoa").agg(
        clientes=("cliente_id", "nunique"),
        taxa_recompra=("recomprou", "mean"),
        media_orders=("total_orders", "mean"),
        media_ped_mes=("pedidos_por_mes", "mean"),
        ltv_medio=("receita_total", "mean"),
    ).reset_index()

    fig_tp = go.Figure()
    fig_tp.add_trace(go.Bar(
        x=perfil_tipo["cliente_tipo_pessoa"].map({"J": "PJ", "F": "PF"}),
        y=perfil_tipo["taxa_recompra"],
        marker_color=[ACCENT, DIM],
        text=perfil_tipo["taxa_recompra"].apply(lambda v: f"{v:.0%}"),
        textposition="outside", textfont_color=TEXT_COLOR,
    ))
    _apply_dark(fig_tp)
    fig_tp.update_layout(height=300, yaxis=dict(tickformat=".0%"))
    c1, c2 = st.columns([1, 2])
    with c1:
        st.plotly_chart(fig_tp, use_container_width=True)
    with c2:
        st.dataframe(
            perfil_tipo.style.format({
                "taxa_recompra": "{:.1%}",
                "media_orders": "{:.1f}",
                "media_ped_mes": "{:.2f}",
                "ltv_medio": "R$ {:,.0f}",
            }),
            use_container_width=True,
        )

    # ── Product deep dive ──
    st.markdown("### Raio-X de Produto")
    gw_dedup2 = gw_f.sort_values("clientes_1a", ascending=False).drop_duplicates("seo_title", keep="first")
    vendas_feb2 = (
        df[df["mes"] == "2026-02"]
        .groupby("seo_title")
        .agg(pedidos_feb=("numero", "nunique"))
        .reset_index()
    )
    gw_dedup2 = gw_dedup2.merge(vendas_feb2, on="seo_title", how="left")
    gw_dedup2["pedidos_feb"] = gw_dedup2["pedidos_feb"].fillna(0).astype(int)
    gw_dedup2 = gw_dedup2.sort_values("pedidos_feb", ascending=False)
    gw_lookup = gw_dedup2.set_index("seo_title")[
        ["taxa_recompra", "clientes_1a", "pedidos_feb"]
    ].to_dict("index")
    options = gw_dedup2["seo_title"].tolist()

    if options:
        selected = st.selectbox(
            "Escolha um produto:",
            options,
            format_func=lambda x: (
                f"{gw_lookup[x]['pedidos_feb']} ped fev  ·  "
                f"{gw_lookup[x]['taxa_recompra']:.0%} recompra  ·  {x}"
            ),
            key="dash_product",
        )
        if selected:
            _render_product_detail(selected, gw_f, fi, subs, clients, novos, taxa_global, prefix="d")


# ═══════════════════════════════════════
# MAIN
# ═══════════════════════════════════════

def main():
    df = load_data()
    df_novo, fi, subs, clients, novos = build_core(df)
    gw = build_product_metrics(fi, clients)
    subcat = build_subcat_metrics(fi, clients)
    combos = build_combos(fi, clients)

    total_novos = len(novos)
    total_recompra = clients["recomprou"].sum()
    taxa_global = total_recompra / total_novos

    tab1, tab2 = st.tabs(["A Historia", "Dashboard"])

    with tab1:
        tab_story(df, df_novo, fi, subs, clients, novos, gw, subcat, combos, taxa_global)

    with tab2:
        tab_dashboard(df, df_novo, fi, subs, clients, novos, gw, subcat, combos, taxa_global)


if __name__ == "__main__":
    main()
