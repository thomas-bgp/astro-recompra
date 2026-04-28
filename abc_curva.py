"""
Astro — Curva ABC por produto (seo_title)
Endpoint oculto: acessado apenas via /?view=abc no app.py
"""

from io import BytesIO
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA_PATH = Path(__file__).parent / "vendas_tiny_bu.parquet"

STATUS_EXCLUI_PADRAO = ["Cancelado"]


@st.cache_data(show_spinner="Lendo parquet...")
def _load_data() -> pd.DataFrame:
    df = pd.read_parquet(
        DATA_PATH,
        columns=["data_pedido", "valor_rateado", "seo_title", "situacao", "quantidade", "codigo"],
    )
    df["data_pedido"] = pd.to_datetime(df["data_pedido"], errors="coerce").dt.date
    df["valor_rateado"] = pd.to_numeric(df["valor_rateado"], errors="coerce")
    df["quantidade"] = pd.to_numeric(df["quantidade"], errors="coerce")
    return df


def _classify_abc(pct_acum: pd.Series) -> pd.Series:
    return pd.cut(
        pct_acum,
        bins=[-0.001, 0.80, 0.95, 1.001],
        labels=["A", "B", "C"],
    ).astype(str)


def _build_abc(df: pd.DataFrame) -> pd.DataFrame:
    agg = (
        df.dropna(subset=["seo_title"])
        .groupby("seo_title", as_index=False)
        .agg(
            faturamento=("valor_rateado", "sum"),
            quantidade=("quantidade", "sum"),
            pedidos=("valor_rateado", "size"),
            sku=("codigo", "first"),
        )
        .sort_values("faturamento", ascending=False)
        .reset_index(drop=True)
    )
    total = agg["faturamento"].sum()
    if total <= 0:
        agg["pct"] = 0.0
        agg["pct_acum"] = 0.0
        agg["classe"] = "C"
    else:
        agg["pct"] = agg["faturamento"] / total
        agg["pct_acum"] = agg["pct"].cumsum()
        agg["classe"] = _classify_abc(agg["pct_acum"])
    agg.insert(0, "rank", range(1, len(agg) + 1))
    cols = ["rank", "sku", "seo_title", "faturamento", "quantidade", "pedidos", "pct", "pct_acum", "classe"]
    return agg[cols]


def _to_excel_bytes(abc: pd.DataFrame, resumo: pd.DataFrame, periodo: str) -> bytes:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        abc.to_excel(writer, sheet_name="Curva ABC", index=False)
        resumo.to_excel(writer, sheet_name="Resumo por Classe", index=False)
        pd.DataFrame({"periodo": [periodo]}).to_excel(
            writer, sheet_name="Filtros", index=False
        )
    return buf.getvalue()


def _fmt_brl(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def main():
    st.title("Curva ABC — Astro")
    st.caption("Produto: `seo_title` | Valor: `valor_rateado` | Data: `data_pedido`")

    df = _load_data()
    d_min, d_max = df["data_pedido"].min(), df["data_pedido"].max()

    with st.sidebar:
        st.header("Filtros — Curva ABC")

        default_ini = pd.Timestamp(d_max).replace(day=1).date() - pd.Timedelta(days=365)
        default_ini = max(default_ini, d_min)

        periodo = st.date_input(
            "Período (data do pedido)",
            value=(default_ini, d_max),
            min_value=d_min,
            max_value=d_max,
            format="DD/MM/YYYY",
        )

        if isinstance(periodo, tuple) and len(periodo) == 2:
            dt_ini, dt_fim = periodo
        else:
            dt_ini, dt_fim = default_ini, d_max

        situacoes = sorted(df["situacao"].dropna().unique().tolist())
        excluir_status = st.multiselect(
            "Excluir situações",
            options=situacoes,
            default=[s for s in STATUS_EXCLUI_PADRAO if s in situacoes],
        )

    mask = (
        df["data_pedido"].between(dt_ini, dt_fim)
        & ~df["situacao"].isin(excluir_status)
    )
    df_f = df.loc[mask].copy()

    if df_f.empty:
        st.warning("Nenhum pedido no período/filtro selecionado.")
        return

    abc = _build_abc(df_f)

    resumo = (
        abc.groupby("classe", as_index=False)
        .agg(
            produtos=("seo_title", "count"),
            faturamento=("faturamento", "sum"),
        )
        .assign(pct_faturamento=lambda x: x["faturamento"] / x["faturamento"].sum())
        .sort_values("classe")
    )

    total_fat = abc["faturamento"].sum()
    n_prod = len(abc)
    n_a = (abc["classe"] == "A").sum()
    n_b = (abc["classe"] == "B").sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Faturamento", f"R$ {total_fat:,.0f}".replace(",", "."))
    c2.metric("Produtos únicos", f"{n_prod:,}".replace(",", "."))
    c3.metric("Classe A (80%)", f"{n_a} ({n_a / n_prod:.0%})")
    c4.metric("Classe B (15%)", f"{n_b} ({n_b / n_prod:.0%})")

    st.markdown("### Curva ABC")
    fig = go.Figure()
    cores = {"A": "#10b981", "B": "#f59e0b", "C": "#ef4444"}
    for classe, grp in abc.groupby("classe"):
        fig.add_trace(
            go.Scatter(
                x=grp["rank"],
                y=grp["pct_acum"] * 100,
                mode="markers",
                name=f"Classe {classe} ({len(grp)})",
                marker=dict(size=5, color=cores.get(classe, "#888")),
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "Rank: %{x}<br>"
                    "Acumulado: %{y:.2f}%<br>"
                    "Faturamento: R$ %{customdata[1]:,.2f}<extra></extra>"
                ),
                customdata=grp[["seo_title", "faturamento"]].values,
            )
        )
    fig.add_hline(y=80, line_dash="dash", line_color="#10b981", annotation_text="80%")
    fig.add_hline(y=95, line_dash="dash", line_color="#f59e0b", annotation_text="95%")
    fig.update_layout(
        xaxis_title="Produtos (rank)",
        yaxis_title="% acumulado do faturamento",
        height=450,
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Resumo por classe")
    resumo_disp = resumo.copy()
    resumo_disp["faturamento"] = resumo_disp["faturamento"].map(_fmt_brl)
    resumo_disp["pct_faturamento"] = resumo_disp["pct_faturamento"].map(lambda v: f"{v:.1%}")
    st.dataframe(resumo_disp, use_container_width=True, hide_index=True)

    st.markdown("### Produtos")
    filtro_classe = st.multiselect(
        "Filtrar classes", options=["A", "B", "C"], default=["A", "B", "C"]
    )
    busca = st.text_input("Buscar produto (seo_title)")

    abc_view = abc[abc["classe"].isin(filtro_classe)].copy()
    if busca:
        abc_view = abc_view[abc_view["seo_title"].str.contains(busca, case=False, na=False)]

    abc_view_disp = abc_view.copy()
    abc_view_disp["faturamento"] = abc_view_disp["faturamento"].map(_fmt_brl)
    abc_view_disp["pct"] = abc_view_disp["pct"].map(lambda v: f"{v:.3%}")
    abc_view_disp["pct_acum"] = abc_view_disp["pct_acum"].map(lambda v: f"{v:.2%}")

    st.dataframe(abc_view_disp, use_container_width=True, hide_index=True, height=500)

    st.markdown("### Exportar")
    periodo_str = f"{dt_ini:%d/%m/%Y} a {dt_fim:%d/%m/%Y}"
    excel_bytes = _to_excel_bytes(abc, resumo, periodo_str)
    nome_arquivo = f"curva_abc_{dt_ini:%Y%m%d}_{dt_fim:%Y%m%d}.xlsx"

    st.download_button(
        label="📥 Baixar Excel",
        data=excel_bytes,
        file_name=nome_arquivo,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


if __name__ == "__main__":
    st.set_page_config(page_title="Astro — Curva ABC", layout="wide")
    main()
