"""
Astro — Agressividade de Budget
Tese: aumentos bruscos de verba travam o Google Ads e derrubam performance.
Remove sáb/dom e outliers (<3 desvios). Mostra % aumento vs performance por estado.
"""

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from scipy.stats import pearsonr, linregress
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
    "3M": "3M", "Biosolvit": "Biosolvit", "Bracol": "Bracol", "Camper": "Camper",
    "Cartom": "Cartom", "Danny": "Danny", "Delta Plus": "Delta Plus",
    "Fujiwara": "Fujiwara", "Imbat": "Imbat", "Innpro": "Innpro",
    "Kadesh": "Kadesh", "Kalipso": "Kalipso", "MG Cinto": "MG Cinto",
    "Maicol": "Maicol", "Marluvas": "Marluvas", "Medix": "Medix",
    "Nutriex": "Nutriex", "Soft Work": "Soft Works", "SuperSafety": "Super Safety",
    "Volk": "Volk",
}
ACCENT = "#4fc3f7"
TEXT_COLOR = "#ddd"
GRID_COLOR = "rgba(255,255,255,0.06)"
PLOTLY_LAYOUT = dict(
    font=dict(family="Inter", size=13, color=TEXT_COLOR),
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
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
    return fig


def _file_sig(path):
    return (path.stat().st_size, int(path.stat().st_mtime))


# ═══════════════════════════════════════
_MULTIPAGE = False
if not _MULTIPAGE:
    st.set_page_config(page_title="Astro — Agressividade de Budget", page_icon="⚡", layout="wide")
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    .block-container { max-width: 1300px; padding-top: 1.5rem; }
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .hero-title { font-size: 2.2rem; font-weight: 900; background: linear-gradient(135deg, #ef5350, #f9a825);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.3rem; }
    .hero-sub { font-size: 1rem; color: #999; margin-bottom: 1.5rem; }
    .section-title { font-size: 1.3rem; font-weight: 700; color: #e8e8ec;
        margin: 1.8rem 0 0.3rem 0; padding-bottom: 0.3rem; border-bottom: 2px solid rgba(249,168,37,0.3); }
    .stat-box { background: rgba(255,255,255,0.04); border-radius: 10px; padding: 1.2rem 1.5rem;
        border: 1px solid rgba(255,255,255,0.08); margin: 0.8rem 0; }
    .stat-box h4 { color: #f9a825; margin: 0 0 0.5rem 0; }
    .stat-box p { color: #ccc; margin: 0.2rem 0; font-size: 0.9rem; }
    .divider { border: none; border-top: 1px solid rgba(255,255,255,0.06); margin: 2rem 0; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════
# DATA
# ═══════════════════════════════════════

@st.cache_data
def load_vendas(_sig=None):
    df = pd.read_parquet(DATA_PATH)
    df = df[df["situacao"] != "Cancelado"].copy()
    df["data_pedido"] = pd.to_datetime(df["data_pedido"])
    df["valor_rateado"] = pd.to_numeric(df["valor_rateado"], errors="coerce")
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
def build_agressividade(ads, df, group_col, ads_group_col):
    """Para cada estado/marca por dia:
    1. Gasto diário (só dias úteis, sem outliers)
    2. % variação vs dia anterior
    3. Performance = novos clientes / gasto * 1000
    4. Testa se aumento brusco derruba performance
    """
    # Ads diário por grupo
    ads_sub = ads[ads[ads_group_col].notna()].copy()
    ads_daily = ads_sub.groupby([ads_group_col, "Day"])["spend"].sum().reset_index()
    ads_daily.columns = ["grupo", "day", "spend"]

    # Remove sáb/dom
    ads_daily["dow"] = ads_daily["day"].dt.dayofweek
    ads_daily = ads_daily[ads_daily["dow"] < 5].drop(columns="dow")

    # Novos clientes por grupo × dia
    novos = df[df["Recompra"] == "Novo"].drop_duplicates("numero")
    novos_daily = novos.groupby([group_col, "data_pedido"])["cliente_id"].nunique().reset_index()
    novos_daily.columns = ["grupo", "day", "novos"]

    # Merge
    merged = ads_daily.merge(novos_daily, on=["grupo", "day"], how="left")
    merged["novos"] = merged["novos"].fillna(0).astype(int)

    # Remove outliers: spend < mean - 3*std por grupo
    clean = []
    for grupo, sub in merged.groupby("grupo"):
        if len(sub) < 10:
            continue
        mu = sub["spend"].mean()
        sigma = sub["spend"].std()
        lower = mu - 3 * sigma
        sub_clean = sub[sub["spend"] >= max(lower, 1)].copy()
        if len(sub_clean) < 5:
            continue
        clean.append(sub_clean)

    if not clean:
        return pd.DataFrame()

    merged = pd.concat(clean).sort_values(["grupo", "day"])

    # % variação dia-a-dia (dentro de cada grupo)
    merged["spend_prev"] = merged.groupby("grupo")["spend"].shift(1)
    merged["pct_change"] = (merged["spend"] / merged["spend_prev"] - 1) * 100
    merged = merged.dropna(subset=["pct_change"])

    # Performance = novos / spend * 1000
    merged["perf"] = merged["novos"] / merged["spend"].replace(0, np.nan) * 1000

    # Agressividade bins
    merged["agressividade"] = pd.cut(
        merged["pct_change"],
        bins=[-np.inf, -20, -5, 5, 20, 50, np.inf],
        labels=["Queda >20%", "Queda 5-20%", "Estavel", "Aumento 5-20%", "Aumento 20-50%", "Aumento >50%"]
    )

    return merged


def build_weekly_agressividade(ads, df, group_col, ads_group_col):
    """Mesmo conceito mas semanal: % aumento da verba semana a semana. Desde marco 2026."""
    ads_sub = ads[(ads[ads_group_col].notna()) & (ads["Day"] >= "2026-03-01")].copy()
    ads_sub["dow"] = ads_sub["Day"].dt.dayofweek
    ads_sub = ads_sub[ads_sub["dow"] < 5]
    ads_sub["week"] = ads_sub["Day"].dt.isocalendar().week.astype(int)
    ads_sub["year"] = ads_sub["Day"].dt.isocalendar().year.astype(int)

    weekly_ads = ads_sub.groupby([ads_group_col, "year", "week"])["spend"].sum().reset_index()
    weekly_ads.columns = ["grupo", "year", "week", "spend"]

    novos = df[df["Recompra"] == "Novo"].drop_duplicates("numero").copy()
    novos["dow"] = novos["data_pedido"].dt.dayofweek
    novos = novos[novos["dow"] < 5]
    novos["week"] = novos["data_pedido"].dt.isocalendar().week.astype(int)
    novos["year"] = novos["data_pedido"].dt.isocalendar().year.astype(int)
    weekly_novos = novos.groupby([group_col, "year", "week"])["cliente_id"].nunique().reset_index()
    weekly_novos.columns = ["grupo", "year", "week", "novos"]

    merged = weekly_ads.merge(weekly_novos, on=["grupo", "year", "week"], how="left")
    merged["novos"] = merged["novos"].fillna(0).astype(int)
    merged = merged.sort_values(["grupo", "year", "week"])

    merged["spend_prev"] = merged.groupby("grupo")["spend"].shift(1)
    merged["pct_change"] = (merged["spend"] / merged["spend_prev"] - 1) * 100
    merged["perf"] = merged["novos"] / merged["spend"].replace(0, np.nan) * 1000
    merged["perf_prev"] = merged.groupby("grupo")["perf"].shift(1)
    merged["perf_change"] = (merged["perf"] / merged["perf_prev"] - 1) * 100
    merged["wk_label"] = "S" + merged["week"].astype(str) + "/" + merged["year"].astype(str).str[-2:]
    merged = merged.dropna(subset=["pct_change"])

    return merged


# ═══════════════════════════════════════
# MAIN
# ═══════════════════════════════════════

def main():
    st.markdown('<div class="hero-title">Agressividade de Budget (desde 01/03/2026)</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">Aumentos bruscos de verba travam o Google e derrubam performance?</div>',
                unsafe_allow_html=True)

    df = load_vendas(_sig=_file_sig(DATA_PATH))
    ads = load_ads(_sig=_file_sig(ADS_PATH))

    st.sidebar.markdown("### Filtros")
    st.sidebar.caption("Exclui sabados/domingos e dias com gasto < 3 desvios da media")

    tab_uf, tab_marca, tab_carteira = st.tabs(["Por Estado", "Por Marca", "Evolucao da Carteira"])

    for tab, gcol, ads_gcol, prefix in [
        (tab_uf, "cliente_uf", "uf", "uf"),
        (tab_marca, "marca", "marca", "mk"),
    ]:
        with tab:
            label = "Estado" if gcol == "cliente_uf" else "Marca"

            wk = build_weekly_agressividade(ads, df, gcol, ads_gcol)
            if wk.empty:
                st.warning("Dados insuficientes.")
                continue

            # ── 1. SCATTER SEMANAL ──
            st.markdown(f'<div class="section-title">1. % Aumento Semanal do Gasto vs Performance por {label}</div>', unsafe_allow_html=True)
            with st.expander("O que e esta analise?"):
                st.markdown(
                    "**Tese:** quando o trafego aumenta demais a verba de uma semana para outra, "
                    "o Google 'trava' — o algoritmo nao consegue otimizar e a performance cai. "
                    "Aqui medimos: **% de aumento do gasto semana-a-semana** vs "
                    "**performance (novos clientes por R$1.000 gastos)**. "
                    "Agregado por semana (seg-sex, sem sabados/domingos). "
                    "Se a linha de tendencia desce = aumento brusco derruba performance."
                )

            top_groups = wk.groupby("grupo")["spend"].sum().nlargest(10).index
            wk_top = wk[wk["grupo"].isin(top_groups)]

            fig = px.scatter(
                wk_top, x="pct_change", y="perf", color="grupo",
                size="spend", hover_data=["wk_label", "novos", "spend"],
                labels={"pct_change": "% Variacao do Gasto (semana-a-semana)",
                        "perf": "Performance (Novos / R$1k)", "grupo": label},
            )
            valid = wk_top.dropna(subset=["pct_change", "perf"])
            valid = valid[np.isfinite(valid["perf"])]
            if len(valid) >= 5:
                slope, intercept, r, p, _ = linregress(valid["pct_change"], valid["perf"])
                x_range = np.linspace(valid["pct_change"].min(), valid["pct_change"].max(), 50)
                fig.add_trace(go.Scatter(
                    x=x_range, y=slope * x_range + intercept,
                    mode="lines", line=dict(color="#ef5350", width=3),
                    name=f"Tendencia (R²={r**2:.3f})"
                ))
            fig.add_vline(x=0, line_dash="dot", line_color="rgba(255,255,255,0.2)")
            _apply_dark(fig)
            fig.update_layout(title=f"Agressividade Semanal vs Performance ({label})", height=500,
                              legend=dict(y=1.0, x=0.01, bgcolor="rgba(0,0,0,0)"))
            st.plotly_chart(fig, use_container_width=True, key=f"{prefix}_scatter")

            # Stats globais
            if len(valid) >= 5:
                r_val, p_val = pearsonr(valid["pct_change"], valid["perf"])
                sig = "SIM" if p_val < 0.05 else "NAO"
                sig_cls = "color:#ef5350;font-weight:700" if p_val < 0.05 else "color:#66bb6a"
                direction = "NEGATIVA (aumento brusco DERRUBA performance)" if r_val < 0 else "POSITIVA (sem evidencia de travamento)"
                st.markdown(f"""
                <div class="stat-box">
                    <h4>Resultado Global: Agressividade Semanal x Performance</h4>
                    <p><b>n =</b> {len(valid)} semanas (top {len(top_groups)} {label.lower()}s, historico completo)</p>
                    <p><b>Pearson r =</b> {r_val:.4f} — Correlacao {direction}</p>
                    <p><b>p-value =</b> {p_val:.2e} — Significativo? <span style="{sig_cls}">{sig}</span></p>
                </div>""", unsafe_allow_html=True)

            st.markdown("<hr class='divider'>", unsafe_allow_html=True)

            # ── 2. FAIXA DE AGRESSIVIDADE SEMANAL ──
            st.markdown(f'<div class="section-title">2. Performance por Faixa de Agressividade Semanal</div>', unsafe_allow_html=True)

            wk_all = wk.dropna(subset=["pct_change", "perf"])
            wk_all = wk_all[np.isfinite(wk_all["perf"])].copy()
            wk_all["faixa"] = pd.cut(
                wk_all["pct_change"],
                bins=[-np.inf, -20, -5, 5, 20, 50, np.inf],
                labels=["Queda >20%", "Queda 5-20%", "Estavel", "Aumento 5-20%", "Aumento 20-50%", "Aumento >50%"]
            )

            faixa = wk_all.groupby("faixa", observed=True).agg(
                n_semanas=("perf", "count"),
                perf_media=("perf", "mean"),
                spend_medio=("spend", "mean"),
                novos_medio=("novos", "mean"),
            ).reset_index()
            faixa.columns = ["Faixa", "N semanas", "Perf (novos/R$1k)", "Gasto medio/sem", "Novos medio/sem"]

            fig2 = px.bar(faixa, x="Faixa", y="Perf (novos/R$1k)",
                          color="Perf (novos/R$1k)",
                          color_continuous_scale=["#ef5350", "#fdd835", "#66bb6a"],
                          text="N semanas",
                          labels={"Perf (novos/R$1k)": "Novos / R$1k"})
            fig2.update_traces(texttemplate="%{text} sem", textposition="outside")
            _apply_dark(fig2)
            fig2.update_layout(title="Performance Media por Faixa de Agressividade (Semanal)", height=400, showlegend=False)
            st.plotly_chart(fig2, use_container_width=True, key=f"{prefix}_faixa")

            styled = faixa.style.format({
                "Perf (novos/R$1k)": "{:.2f}",
                "Gasto medio/sem": lambda v: f"R$ {v:,.0f}",
                "Novos medio/sem": "{:.1f}",
            }).set_properties(**{"text-align": "center", "font-size": "0.9rem"})
            st.dataframe(styled, use_container_width=True, key=f"{prefix}_faixa_tbl", hide_index=True)

            st.markdown("<hr class='divider'>", unsafe_allow_html=True)

            # ── 3. TIMELINE: agressividade vs perf semana a semana por grupo ──
            st.markdown(f'<div class="section-title">3. Timeline: Gasto vs Performance por {label} (semana a semana)</div>', unsafe_allow_html=True)

            sel_groups = st.multiselect(
                f"Selecione {label.lower()}s", sorted(top_groups),
                default=sorted(top_groups)[:5], key=f"{prefix}_sel"
            )
            if sel_groups:
                wk_sel = wk[wk["grupo"].isin(sel_groups)].copy()
                fig_t = go.Figure()
                for grupo in sel_groups:
                    sub = wk_sel[wk_sel["grupo"] == grupo].sort_values(["year", "week"])
                    fig_t.add_trace(go.Scatter(
                        x=sub["wk_label"], y=sub["pct_change"],
                        mode="lines+markers", name=f"{grupo} (% gasto)",
                        line=dict(width=2),
                    ))
                    fig_t.add_trace(go.Scatter(
                        x=sub["wk_label"], y=sub["perf_change"],
                        mode="lines+markers", name=f"{grupo} (% perf)",
                        line=dict(width=2, dash="dot"),
                        opacity=0.6,
                    ))
                fig_t.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.2)")
                _apply_dark(fig_t)
                fig_t.update_layout(
                    title="% Variacao Semanal: Gasto (solido) vs Performance (pontilhado)",
                    height=450, yaxis_title="% variacao",
                    legend=dict(y=-0.3, x=0, orientation="h", bgcolor="rgba(0,0,0,0)"),
                )
                st.plotly_chart(fig_t, use_container_width=True, key=f"{prefix}_timeline")

            st.markdown("<hr class='divider'>", unsafe_allow_html=True)

            # ── 4. QUEM SOFRE MAIS ──
            st.markdown(f'<div class="section-title">4. Quem Sofre Mais com Agressividade? (por {label})</div>', unsafe_allow_html=True)
            st.caption("Correlacao semanal individual: % variacao gasto x performance")

            corr_results = []
            for grupo, sub in wk.groupby("grupo"):
                sub_valid = sub.dropna(subset=["pct_change", "perf"])
                sub_valid = sub_valid[np.isfinite(sub_valid["perf"])]
                if len(sub_valid) < 5:
                    continue
                r_g, p_g = pearsonr(sub_valid["pct_change"], sub_valid["perf"])
                corr_results.append({
                    "Grupo": grupo, "N semanas": len(sub_valid),
                    "Correlacao": r_g, "p-value": p_g,
                    "Significativo": "Sim" if p_g < 0.05 else "Nao",
                    "Efeito": "Trava" if r_g < -0.15 and p_g < 0.10 else ("Neutro" if abs(r_g) < 0.15 else "OK"),
                })

            if corr_results:
                corr_df = pd.DataFrame(corr_results).sort_values("Correlacao")

                def _color_effect(v):
                    if v == "Trava":
                        return "background:rgba(198,40,40,0.3);color:#ef5350;font-weight:700"
                    if v == "OK":
                        return "background:rgba(46,125,50,0.3);color:#66bb6a;font-weight:700"
                    return ""

                styled_c = (corr_df.style
                    .map(_color_effect, subset=["Efeito"])
                    .format({"Correlacao": "{:.4f}", "p-value": "{:.2e}"})
                    .set_properties(**{"text-align": "center", "font-size": "0.9rem"})
                    .set_properties(subset=["Grupo"], **{"text-align": "left", "font-weight": "700"}))
                st.dataframe(styled_c, use_container_width=True, key=f"{prefix}_corr", hide_index=True)

                travas = corr_df[corr_df["Efeito"] == "Trava"]
                if not travas.empty:
                    st.markdown(f"""
                    <div class="stat-box">
                        <h4>ALERTA: {len(travas)} {label.lower()}(s) com evidencia de travamento</h4>
                        <p>{', '.join(travas['Grupo'].tolist())} — nesses grupos, aumentos bruscos de verba semanal
                        estao correlacionados com queda de performance (menos novos por R$ investido).</p>
                        <p><b>Recomendacao:</b> aumentar budget de forma progressiva (max 15-20%/semana).</p>
                    </div>""", unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="stat-box">
                        <h4>Sem evidencia forte de travamento</h4>
                        <p>Nenhum grupo apresentou correlacao negativa significativa entre agressividade semanal e performance.
                        O Google nao esta sendo travado pelos aumentos atuais.</p>
                    </div>""", unsafe_allow_html=True)


    # ══════════════════════════════════════════════
    # TAB CARTEIRA — serie temporal de LTV comprado
    # ══════════════════════════════════════════════
    with tab_carteira:
        st.markdown('<div class="section-title">Evolucao da Carteira: estamos comprando mais LTV?</div>', unsafe_allow_html=True)
        with st.expander("O que esta analise mostra?"):
            st.markdown(
                "**Tese:** com a mesma verba, estamos distribuindo melhor o gasto entre marcas e estados, "
                "adquirindo clientes de perfis com LTV mais alto. "
                "Aqui mostramos semana a semana: quanto de LTV potencial estamos 'comprando' "
                "e qual a eficiencia (LTV comprado por R$ gasto)."
            )

        # Build profile LTV lookup (historico pre-campanha)
        client_rev = df.groupby("cliente_id")["valor_rateado"].sum().reset_index()
        client_rev.columns = ["cliente_id", "receita_total"]
        first_purchase = (
            df.sort_values("data_pedido")
            .drop_duplicates("cliente_id", keep="first")[
                ["cliente_id", "cliente_uf", "marca", "data_pedido"]
            ]
        )
        profiles = first_purchase.merge(client_rev, on="cliente_id")
        hist = profiles[profiles["data_pedido"] < pd.Timestamp("2026-03-17")]
        ltv_by_uf_marca = hist.groupby(["cliente_uf", "marca"])["receita_total"].mean().to_dict()
        ltv_by_uf = hist.groupby("cliente_uf")["receita_total"].mean().to_dict()
        ltv_by_marca = hist.groupby("marca")["receita_total"].mean().to_dict()

        # Weekly: novos clientes + LTV perfil + gasto — desde marco 2026
        CART_START = pd.Timestamp("2026-03-01")
        novos_orders = df[(df["Recompra"] == "Novo") & (df["data_pedido"] >= CART_START)].drop_duplicates("numero").copy()
        novos_orders["dow"] = novos_orders["data_pedido"].dt.dayofweek
        novos_orders = novos_orders[novos_orders["dow"] < 5]
        novos_orders["week"] = novos_orders["data_pedido"].dt.isocalendar().week.astype(int)
        novos_orders["year"] = novos_orders["data_pedido"].dt.isocalendar().year.astype(int)

        # Assign profile LTV to each new client
        novos_orders["ltv_perfil"] = novos_orders.apply(
            lambda r: ltv_by_uf_marca.get((r["cliente_uf"], r["marca"]),
                      ltv_by_uf.get(r["cliente_uf"],
                      ltv_by_marca.get(r["marca"], 0))), axis=1
        )

        # Weekly aggregation
        wk_novos = novos_orders.groupby(["year", "week"]).agg(
            n_novos=("cliente_id", "nunique"),
            ltv_total=("ltv_perfil", "sum"),
            ltv_medio=("ltv_perfil", "mean"),
        ).reset_index()

        ads_wk = ads[ads["Day"] >= CART_START].copy()
        ads_wk["dow"] = ads_wk["Day"].dt.dayofweek
        ads_wk = ads_wk[ads_wk["dow"] < 5]
        ads_wk["week"] = ads_wk["Day"].dt.isocalendar().week.astype(int)
        ads_wk["year"] = ads_wk["Day"].dt.isocalendar().year.astype(int)
        wk_spend = ads_wk.groupby(["year", "week"])["spend"].sum().reset_index()

        wk_cart = wk_novos.merge(wk_spend, on=["year", "week"], how="outer").fillna(0)
        wk_cart["eficiencia"] = wk_cart["ltv_total"] / wk_cart["spend"].replace(0, np.nan)
        wk_cart["ltv_por_novo"] = wk_cart["ltv_total"] / wk_cart["n_novos"].replace(0, np.nan)
        wk_cart["wk_label"] = "S" + wk_cart["week"].astype(int).astype(str) + "/" + wk_cart["year"].astype(int).astype(str).str[-2:]
        wk_cart = wk_cart.sort_values(["year", "week"])
        # % variacao semana a semana
        wk_cart["ltv_pct"] = wk_cart["ltv_total"].pct_change() * 100
        wk_cart["spend_pct"] = wk_cart["spend"].pct_change() * 100

        # ── 1. LTV comprado + % variacao semanal ──
        st.markdown('<div class="section-title">1. LTV Comprado e % Variacao Semanal (desde 01/03/2026)</div>', unsafe_allow_html=True)
        st.caption("Barras = LTV potencial comprado. Linhas = % variacao semana-a-semana (LTV e Budget)")

        fig_ltv = go.Figure()
        fig_ltv.add_trace(go.Bar(
            x=wk_cart["wk_label"], y=wk_cart["ltv_total"],
            name="LTV Comprado (R$)", marker_color=ACCENT, opacity=0.4,
        ))
        wk_pct = wk_cart.dropna(subset=["ltv_pct"])
        fig_ltv.add_trace(go.Scatter(
            x=wk_pct["wk_label"], y=wk_pct["ltv_pct"],
            name="% Var. LTV", mode="lines+markers",
            line=dict(color="#66bb6a", width=3), yaxis="y2",
        ))
        fig_ltv.add_trace(go.Scatter(
            x=wk_pct["wk_label"], y=wk_pct["spend_pct"],
            name="% Var. Budget", mode="lines+markers",
            line=dict(color="#ef5350", width=2, dash="dot"), yaxis="y2",
        ))
        fig_ltv.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.15)")
        _apply_dark(fig_ltv)
        fig_ltv.update_layout(
            title="LTV Comprado (barras) + % Variacao Semanal de LTV e Budget (linhas)",
            height=430,
            yaxis=dict(title="LTV Comprado (R$)"),
            yaxis2=dict(title="% Variacao Semanal", overlaying="y", side="right",
                        gridcolor="rgba(0,0,0,0)", zeroline=True, zerolinecolor="rgba(255,255,255,0.15)"),
            legend=dict(y=1.05, x=0, orientation="h", bgcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig_ltv, use_container_width=True, key="cart_ltv")

        # ── 2. Eficiencia: LTV comprado / gasto ──
        st.markdown('<div class="section-title">2. Eficiencia: LTV Comprado por R$ Gasto</div>', unsafe_allow_html=True)
        st.caption("Quanto de LTV potencial cada R$1 em ads compra. Subindo = distribuicao melhorando.")

        fig_ef = go.Figure()
        fig_ef.add_trace(go.Scatter(
            x=wk_cart["wk_label"], y=wk_cart["eficiencia"],
            mode="lines+markers", name="LTV / R$ Gasto",
            line=dict(color="#66bb6a", width=3),
            marker=dict(size=10),
        ))
        # Trend line
        wk_valid = wk_cart.dropna(subset=["eficiencia"])
        if len(wk_valid) >= 3:
            x_idx = np.arange(len(wk_valid))
            slope_e, intercept_e, r_e, _, _ = linregress(x_idx, wk_valid["eficiencia"].values)
            fig_ef.add_trace(go.Scatter(
                x=wk_valid["wk_label"], y=slope_e * x_idx + intercept_e,
                mode="lines", line=dict(color="#f9a825", width=2, dash="dash"),
                name=f"Tendencia ({'subindo' if slope_e > 0 else 'caindo'})",
            ))
        _apply_dark(fig_ef)
        fig_ef.update_layout(title="Eficiencia Semanal: LTV Comprado / Gasto Ads", height=380,
                             legend=dict(y=1.05, x=0, orientation="h", bgcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig_ef, use_container_width=True, key="cart_ef")

        if len(wk_valid) >= 3:
            direction = "SUBINDO" if slope_e > 0 else "CAINDO"
            st.markdown(f"""
            <div class="stat-box">
                <h4>Tendencia da Eficiencia: {direction}</h4>
                <p>A cada semana, a eficiencia (LTV/gasto) {"aumenta" if slope_e > 0 else "diminui"} em media {abs(slope_e):.2f}x.
                {"Estamos comprando mais LTV com o mesmo dinheiro — a distribuicao entre marcas/estados esta melhorando." if slope_e > 0 else "A eficiencia esta caindo — revisar alocacao."}</p>
            </div>""", unsafe_allow_html=True)

        # ── 3. LTV medio por novo cliente (qualidade) ──
        st.markdown('<div class="section-title">3. LTV Medio por Novo Cliente (Qualidade da Aquisicao)</div>', unsafe_allow_html=True)
        st.caption("Se o LTV medio sobe, estamos atraindo perfis melhores. Reflete a qualidade da distribuicao.")

        fig_q = go.Figure()
        fig_q.add_trace(go.Scatter(
            x=wk_cart["wk_label"], y=wk_cart["ltv_medio"],
            mode="lines+markers", name="LTV Medio/Novo Cliente",
            line=dict(color=ACCENT, width=3), marker=dict(size=10),
        ))
        fig_q.add_trace(go.Bar(
            x=wk_cart["wk_label"], y=wk_cart["n_novos"],
            name="Novos Clientes", marker_color="rgba(255,255,255,0.1)", yaxis="y2",
        ))
        _apply_dark(fig_q)
        fig_q.update_layout(
            title="LTV Medio por Novo Cliente (linha) + Volume (barras)",
            height=380,
            yaxis=dict(title="LTV Medio (R$)"),
            yaxis2=dict(title="Novos Clientes", overlaying="y", side="right",
                        gridcolor="rgba(0,0,0,0)"),
            legend=dict(y=1.05, x=0, orientation="h", bgcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig_q, use_container_width=True, key="cart_q")

        st.markdown("<hr class='divider'>", unsafe_allow_html=True)

        # ── 4. Composicao: por estado ──
        st.markdown('<div class="section-title">4. De Onde Vem o LTV? Composicao por Estado</div>', unsafe_allow_html=True)
        st.caption("Proporcao do LTV comprado vindo de cada estado, semana a semana. Diversificacao = menos risco.")

        novos_uf_wk = novos_orders.groupby(["year", "week", "cliente_uf"]).agg(
            ltv_sum=("ltv_perfil", "sum"),
        ).reset_index()
        novos_uf_wk["wk_label"] = "S" + novos_uf_wk["week"].astype(str) + "/" + novos_uf_wk["year"].astype(str).str[-2:]
        last_wks = sorted(wk_cart["wk_label"].unique())
        novos_uf_wk = novos_uf_wk[novos_uf_wk["wk_label"].isin(last_wks)]
        # Top 8 UFs
        top_ufs = novos_uf_wk.groupby("cliente_uf")["ltv_sum"].sum().nlargest(8).index
        novos_uf_wk_top = novos_uf_wk[novos_uf_wk["cliente_uf"].isin(top_ufs)]
        outros = novos_uf_wk[~novos_uf_wk["cliente_uf"].isin(top_ufs)].groupby("wk_label")["ltv_sum"].sum().reset_index()
        outros["cliente_uf"] = "Outros"
        plot_data = pd.concat([novos_uf_wk_top[["wk_label", "cliente_uf", "ltv_sum"]], outros])

        fig_comp = px.bar(
            plot_data, x="wk_label", y="ltv_sum", color="cliente_uf",
            labels={"wk_label": "Semana", "ltv_sum": "LTV Comprado (R$)", "cliente_uf": "Estado"},
            barmode="stack",
        )
        _apply_dark(fig_comp)
        fig_comp.update_layout(title="Composicao do LTV Comprado por Estado", height=420,
                               legend=dict(y=1.05, x=0, orientation="h", bgcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig_comp, use_container_width=True, key="cart_comp_uf")

        # ── 5. Composicao: por marca ──
        st.markdown('<div class="section-title">5. De Onde Vem o LTV? Composicao por Marca</div>', unsafe_allow_html=True)

        novos_mk_wk = novos_orders.groupby(["year", "week", "marca"]).agg(
            ltv_sum=("ltv_perfil", "sum"),
        ).reset_index()
        novos_mk_wk["wk_label"] = "S" + novos_mk_wk["week"].astype(str) + "/" + novos_mk_wk["year"].astype(str).str[-2:]
        novos_mk_wk = novos_mk_wk[novos_mk_wk["wk_label"].isin(last_wks)]
        top_mks = novos_mk_wk.groupby("marca")["ltv_sum"].sum().nlargest(8).index
        novos_mk_wk_top = novos_mk_wk[novos_mk_wk["marca"].isin(top_mks)]
        outros_m = novos_mk_wk[~novos_mk_wk["marca"].isin(top_mks)].groupby("wk_label")["ltv_sum"].sum().reset_index()
        outros_m["marca"] = "Outras"
        plot_m = pd.concat([novos_mk_wk_top[["wk_label", "marca", "ltv_sum"]], outros_m])

        fig_comp_m = px.bar(
            plot_m, x="wk_label", y="ltv_sum", color="marca",
            labels={"wk_label": "Semana", "ltv_sum": "LTV Comprado (R$)", "marca": "Marca"},
            barmode="stack",
        )
        _apply_dark(fig_comp_m)
        fig_comp_m.update_layout(title="Composicao do LTV Comprado por Marca", height=420,
                                 legend=dict(y=1.05, x=0, orientation="h", bgcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig_comp_m, use_container_width=True, key="cart_comp_mk")

        # ── 6. HHI: concentracao ──
        st.markdown('<div class="section-title">6. Indice de Diversificacao (Herfindahl)</div>', unsafe_allow_html=True)
        st.caption("HHI baixo = budget bem distribuido. Se cai ao longo do tempo, a estrategia de diversificacao esta funcionando.")

        # HHI por UF por semana
        hhi_data = []
        for wk_l in last_wks:
            sub_uf = novos_uf_wk[novos_uf_wk["wk_label"] == wk_l]
            total_uf = sub_uf["ltv_sum"].sum()
            if total_uf > 0:
                shares_uf = (sub_uf["ltv_sum"] / total_uf * 100) ** 2
                hhi_uf = shares_uf.sum()
            else:
                hhi_uf = np.nan
            sub_mk = novos_mk_wk[novos_mk_wk["wk_label"] == wk_l]
            total_mk = sub_mk["ltv_sum"].sum()
            if total_mk > 0:
                shares_mk = (sub_mk["ltv_sum"] / total_mk * 100) ** 2
                hhi_mk = shares_mk.sum()
            else:
                hhi_mk = np.nan
            hhi_data.append({"wk_label": wk_l, "HHI Estado": hhi_uf, "HHI Marca": hhi_mk})

        hhi_df = pd.DataFrame(hhi_data)

        fig_hhi = go.Figure()
        fig_hhi.add_trace(go.Scatter(
            x=hhi_df["wk_label"], y=hhi_df["HHI Estado"],
            mode="lines+markers", name="HHI Estado",
            line=dict(color=ACCENT, width=3),
        ))
        fig_hhi.add_trace(go.Scatter(
            x=hhi_df["wk_label"], y=hhi_df["HHI Marca"],
            mode="lines+markers", name="HHI Marca",
            line=dict(color="#f9a825", width=3),
        ))
        fig_hhi.add_hline(y=2500, line_dash="dot", line_color="rgba(239,83,80,0.5)",
                          annotation_text="Concentrado (>2500)")
        _apply_dark(fig_hhi)
        fig_hhi.update_layout(title="Indice Herfindahl-Hirschman (menor = mais diversificado)", height=380,
                              legend=dict(y=1.05, x=0, orientation="h", bgcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig_hhi, use_container_width=True, key="cart_hhi")

        hhi_valid = hhi_df.dropna()
        if len(hhi_valid) >= 3:
            x_h = np.arange(len(hhi_valid))
            sl_uf, _, r_uf, _, _ = linregress(x_h, hhi_valid["HHI Estado"].values)
            sl_mk, _, r_mk, _, _ = linregress(x_h, hhi_valid["HHI Marca"].values)
            dir_uf = "CAINDO (diversificando)" if sl_uf < 0 else "SUBINDO (concentrando)"
            dir_mk = "CAINDO (diversificando)" if sl_mk < 0 else "SUBINDO (concentrando)"
            st.markdown(f"""
            <div class="stat-box">
                <h4>Tendencia de Diversificacao</h4>
                <p><b>HHI Estado:</b> {dir_uf} ({sl_uf:+.1f} por semana)</p>
                <p><b>HHI Marca:</b> {dir_mk} ({sl_mk:+.1f} por semana)</p>
                <p>{"A distribuicao esta melhorando — estamos comprando LTV de mais fontes." if sl_uf < 0 and sl_mk < 0 else "Revisar: a carteira pode estar se concentrando demais em poucos estados/marcas."}</p>
            </div>""", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
