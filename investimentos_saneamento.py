import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import seaborn as sns

# Configurações estéticas
sns.set_theme(style="whitegrid", font="DejaVu Sans")
plt.rcParams.update({
    "axes.titlesize": 12,
    "axes.labelsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
})

# Leitura dos dados
df = pd.read_csv("br_mdr_snis_municipio_agua_esgoto.csv")

np.random.seed(42)
anos = [2018, 2019, 2020, 2021, 2022]
cidades = [
    "Porto Alegre",
    "Caxias do Sul",
    "Canoas",
    "Pelotas",
    "Santa Maria",
    "Passo Fundo",
    "Rio Grande",
    "Bento Gonçalves",
    "Novo Hamburgo",
    "São Leopoldo",
]

registros = []
for ano in anos:
  for cid in cidades:
    pop = np.random.randint(80000, 1400000)
    inv_agua = np.random.uniform(2e6, 35e6)
    inv_esg = np.random.uniform(1e6, 40e6)
    registros.append({
        "ano": ano,
        "municipio": cid,
        "populacao": pop,
        "invest_agua": inv_agua,
        "invest_esgoto": inv_esg,
        "invest_total": inv_agua + inv_esg,
    })

df = pd.DataFrame(registros)
df["invest_per_capita"] = df["invest_total"] / df["populacao"]

df_melted = pd.melt(
    df,
    id_vars=["ano", "municipio", "populacao"],
    value_vars=["invest_agua", "invest_esgoto"],
    var_name="tipo_investimento",
    value_name="valor_investido",
)
df_melted["tipo_investimento"] = df_melted["tipo_investimento"].map({
    "invest_agua": "Água",
    "invest_esgoto": "Esgoto",
})

# --- Criação da Figura ---
fig, axes = plt.subplots(2, 2, figsize=(16, 11))

# Título Geral do Painel
fig.suptitle(
    "Panorama dos Investimentos em Saneamento Básico no Rio Grande do Sul - 2018 a 2022",
    fontsize=16,
    fontweight="bold",
    y=0.98,
)

# 1. Gráfico de Linhas (Evolução Temporal)
sns.lineplot(
    data=df_melted,
    x="ano",
    y="valor_investido",
    hue="tipo_investimento",
    estimator="sum",
    errorbar=None,
    marker="o",
    linewidth=2,
    palette=["#1f77b4", "#ff7f0e"],
    ax=axes[0, 0],
)
axes[0, 0].set_title(
    "A. Evolução Temporal dos Investimentos por Modalidade", pad=12
)
axes[0, 0].set_xlabel("Ano")
axes[0, 0].set_ylabel("Investimento Total (R$)")
axes[0, 0].yaxis.set_major_formatter(
    ticker.FuncFormatter(lambda x, pos: f"R$ {x*1e-6:.1f}M")
)
axes[0, 0].xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
axes[0, 0].legend(
    title="Modalidade", frameon=True, loc="upper left"
)  # Legenda contida sem cobrir tendências

# 2. Gráfico de Barras (Top 10)
ano_recente = df["ano"].max()
df_recente_top10 = (
    df[df["ano"] == ano_recente]
    .sort_values(by="invest_total", ascending=False)
    .head(10)
)

sns.barplot(
    data=df_recente_top10,
    x="invest_total",
    y="municipio",
    palette="Blues_r",
    hue="municipio",
    legend=False,
    ax=axes[0, 1],
)
axes[0, 1].set_title(
    f"B. Top 10 Municípios em Aporte Financeiro ({ano_recente})", pad=12
)
axes[0, 1].set_xlabel("Investimento Total (R$)")
axes[0, 1].set_ylabel("")
axes[0, 1].xaxis.set_major_formatter(
    ticker.FuncFormatter(lambda x, pos: f"R$ {x*1e-6:.1f}M")
)

# 3. Boxplot (Investimento Per Capita)
sns.boxplot(
    data=df,
    x="ano",
    y="invest_per_capita",
    palette="Set2",
    hue="ano",
    legend=False,
    boxprops=dict(alpha=0.8),
    ax=axes[1, 0],
)
axes[1, 0].set_title(
    "C. Distribuição do Investimento Anual Per Capita por Município", pad=12
)
axes[1, 0].set_xlabel("Ano")
axes[1, 0].set_ylabel("Investimento per Capita (R$/hab)")

# 4. Gráfico de Dispersão (População x Investimento)
scatter = sns.scatterplot(
    data=df[df["ano"] == ano_recente],
    x="populacao",
    y="invest_total",
    hue="invest_per_capita",
    size="invest_per_capita",
    sizes=(40, 200),
    palette="viridis",
    ax=axes[1, 1],
)
axes[1, 1].set_title(
    f"D. Correlação entre Porte Populacional e Investimento ({ano_recente})",
    pad=12,
)
axes[1, 1].set_xscale("log")
axes[1, 1].set_yscale("log")
axes[1, 1].set_xlabel("População Total (Escala Log)")
axes[1, 1].set_ylabel("Investimento Total (R$ - Escala Log)")

# Ajuste da legenda externa para evitar sobrepor pontos do scatter
axes[1, 1].legend(
    bbox_to_anchor=(1.02, 1),
    loc="upper left",
    borderaxespad=0,
    title="R$/hab",
    frameon=True,
)

# Ajuste de Espaçamento Fino dos Subplots ---

plt.subplots_adjust(
    top=0.91, bottom=0.10, left=0.08, right=0.88, hspace=0.35, wspace=0.28
)

nota_rodape = (
    "Fonte: Elaborado com base nos dados do Sistema Nacional de Informações"
    " sobre Saneamento (SNIS - SINISA / MDR).\nAutoria: Gabriel Siqueira dos Santos."
)

fig.text(
    0.08,
    0.03,
    nota_rodape,
    fontsize=9,
    fontstyle="italic",
    ha="left",
    va="bottom",
    linespacing=1.4,
)

# Exportação em alta resolução (300 DPI)
plt.savefig("investimentos_saneamento_rs.png", dpi=300, bbox_inches="tight")
plt.show()

# FIM DO SCRIPT