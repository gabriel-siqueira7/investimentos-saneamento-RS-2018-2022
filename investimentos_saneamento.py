import json
import urllib.request
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
import seaborn as sns

# Configurações estéticas globais
sns.set_theme(style="whitegrid", font="DejaVu Sans")
plt.rcParams.update({
    "axes.titlesize": 12,
    "axes.labelsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
})

print("1. Carregando base do SNIS (RS, 2018-2022)...")

colunas_relevantes = [
    "ano",
    "id_municipio",
    "sigla_uf",
    "populacao_urbana",
    "populacao_atendida_agua",
    "investimento_agua_prestador",
    "investimento_agua_municipio",
    "investimento_agua_estado",
    "investimento_esgoto_prestador",
    "investimento_esgoto_municipio",
    "investimento_esgoto_estado",
]

df_raw = pd.read_csv(
    "br_mdr_snis_municipio_agua_esgoto.csv", usecols=colunas_relevantes
)

# Filtra Rio Grande do Sul e período 2018-2022
df = df_raw[
    (df_raw["sigla_uf"] == "RS") & (df_raw["ano"].between(2018, 2022))
].copy()

# Preenche nulos com zero nos valores financeiros
cols_invest = [
    "investimento_agua_prestador",
    "investimento_agua_municipio",
    "investimento_agua_estado",
    "investimento_esgoto_prestador",
    "investimento_esgoto_municipio",
    "investimento_esgoto_estado",
]
df[cols_invest] = df[cols_invest].fillna(0)

# Consolida os investimentos nominais
df["invest_agua_nominal"] = (
    df["investimento_agua_prestador"]
    + df["investimento_agua_municipio"]
    + df["investimento_agua_estado"]
)

df["invest_esgoto_nominal"] = (
    df["investimento_esgoto_prestador"]
    + df["investimento_esgoto_municipio"]
    + df["investimento_esgoto_estado"]
)

# --- DEFLACIONAMENTO PELO IPCA (Valores a preços de Dezembro/2022) ---
print("2. Aplicando deflacionador IPCA para valores constantes de 2022...")
fatores_ipca = {
    2018: 1.2608,
    2019: 1.2152,
    2020: 1.1626,
    2021: 1.0579,
    2022: 1.0000,
}

df["fator_deflator"] = df["ano"].map(fatores_ipca)
df["invest_agua"] = df["invest_agua_nominal"] * df["fator_deflator"]
df["invest_esgoto"] = df["invest_esgoto_nominal"] * df["fator_deflator"]
df["invest_total"] = df["invest_agua"] + df["invest_esgoto"]

# Trata população consolidando urbana e atendida para evitar zerados
df["populacao"] = df["populacao_urbana"].fillna(0)
df["populacao"] = (
    df["populacao"]
    .replace(0, pd.NA)
    .fillna(df["populacao_atendida_agua"])
    .fillna(0)
)

# Calcula investimento real per capita (R$ de 2022 por habitante)
df["invest_per_capita"] = df.apply(
    lambda row: (row["invest_total"] / row["populacao"])
    if row["populacao"] > 0
    else 0,
    axis=1,
)

print("3. Vinculando nomes dos municípios via código IBGE...")
df["id_ibge_int"] = pd.to_numeric(df["id_municipio"], errors="coerce")
df["municipio"] = None

try:
  url_ibge = (
      "https://servicodados.ibge.gov.br/api/v1/localidades/estados/43/municipios"
  )
  ibge_df = pd.read_json(url_ibge)
  mapa_ibge = dict(zip(ibge_df["id"].astype(int), ibge_df["nome"]))
  df["municipio"] = df["id_ibge_int"].map(mapa_ibge)
except Exception:
  pass

mapa_offline = {
    4314902: "Porto Alegre",
    4305108: "Caxias do Sul",
    4304606: "Canoas",
    4314407: "Pelotas",
    4316907: "Santa Maria",
    4309209: "Gravataí",
    4323002: "Viamão",
    4313409: "Novo Hamburgo",
    4318705: "São Leopoldo",
    4315602: "Rio Grande",
    4300604: "Alvorada",
    4314100: "Passo Fundo",
    4320008: "Sapucaia do Sul",
    4322400: "Uruguaiana",
    4321204: "Santa Cruz do Sul",
    4303004: "Cachoeirinha",
    4302105: "Bento Gonçalves",
    4301602: "Bagé",
    4307005: "Erechim",
    4311403: "Lajeado",
    4310207: "Ijuí",
    4309308: "Guaíba",
    4321600: "Santana do Livramento",
    4321451: "Santa Rosa",
    4322608: "Venâncio Aires",
    4304408: "Canela",
    4309100: "Gramado",
    4307609: "Farroupilha",
    4322509: "Vacaria",
    4312401: "Montenegro",
}

df["municipio"] = (
    df["municipio"]
    .fillna(df["id_ibge_int"].map(mapa_offline))
    .fillna("IBGE " + df["id_municipio"].astype(str))
)

# Prepara base em formato long para o gráfico de linhas
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

print("4. Construindo painel integrado Seaborn...")
fig, axes = plt.subplots(2, 2, figsize=(16, 11))

# Título Principal especificando valores a preços constantes
fig.suptitle(
    "Investimentos Reais em Saneamento Básico no RS (2018–2022) — Preços"
    " Constantes (IPCA Dez/2022)",
    fontsize=15,
    fontweight="bold",
    y=0.98,
)

# --- Gráfico A: Evolução Temporal por Modalidade ---
sns.lineplot(
    data=df_melted,
    x="ano",
    y="valor_investido",
    hue="tipo_investimento",
    estimator="sum",
    errorbar=None,
    marker="o",
    linewidth=2.5,
    palette=["#1f77b4", "#ff7f0e"],
    ax=axes[0, 0],
)
axes[0, 0].set_title(
    "A. Evolução dos Investimentos Reais no RS (IPCA Dez/2022)", pad=12
)
axes[0, 0].set_xlabel("Ano")
axes[0, 0].set_ylabel("Investimento Total Real (R$)")
axes[0, 0].yaxis.set_major_formatter(
    ticker.FuncFormatter(lambda x, pos: f"R$ {x*1e-6:.1f}M")
)
axes[0, 0].xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
axes[0, 0].legend(title="Modalidade", frameon=True, loc="upper left")

# --- Gráfico B: Top 10 Municípios (2022) ---
ano_recente = int(df["ano"].max())
df_recente = df[df["ano"] == ano_recente].copy()
df_top10 = (
    df_recente.groupby("municipio")["invest_total"]
    .sum()
    .reset_index()
    .sort_values(by="invest_total", ascending=False)
    .head(10)
)

sns.barplot(
    data=df_top10,
    x="invest_total",
    y="municipio",
    palette="Blues_r",
    hue="municipio",
    legend=False,
    ax=axes[0, 1],
)
axes[0, 1].set_title(
    f"B. Top 10 Municípios em Investimento Real ({ano_recente})", pad=12
)
axes[0, 1].set_xlabel("Investimento Total Real (R$)")
axes[0, 1].set_ylabel("")
axes[0, 1].xaxis.set_major_formatter(
    ticker.FuncFormatter(lambda x, pos: f"R$ {x*1e-6:.1f}M")
)

# --- Gráfico C: Boxplot Per Capita Real ---
df_com_investimento = df[df["invest_per_capita"] > 0].copy()

sns.boxplot(
    data=df_com_investimento,
    x="ano",
    y="invest_per_capita",
    palette="Set2",
    hue="ano",
    legend=False,
    showfliers=False,
    ax=axes[1, 0],
)
axes[1, 0].set_title(
    "C. Distribuição do Investimento Real Per Capita (excl. outliers extremos)",
    pad=12,
)
axes[1, 0].set_xlabel("Ano")
axes[1, 0].set_ylabel("Investimento Real por Habitante (R$ 2022/hab)")

# --- Gráfico D: Dispersão População vs. Investimento (2022) ---
df_scatter = df_recente[
    (df_recente["populacao"] > 100) & (df_recente["invest_total"] > 1000)
].copy()

sns.scatterplot(
    data=df_scatter,
    x="populacao",
    y="invest_total",
    hue="invest_per_capita",
    size="invest_per_capita",
    sizes=(30, 220),
    palette="viridis",
    ax=axes[1, 1],
)
axes[1, 1].set_xscale("log")
axes[1, 1].set_yscale("log")
axes[1, 1].set_title(
    f"D. Dispersão: População Urbana vs. Investimento Real ({ano_recente})",
    pad=12,
)
axes[1, 1].set_xlabel("População Urbana (Escala Log)")
axes[1, 1].set_ylabel("Investimento Total Real (R$ - Escala Log)")
axes[1, 1].legend(
    bbox_to_anchor=(1.02, 1),
    loc="upper left",
    borderaxespad=0,
    title="R$ 2022/hab",
    frameon=True,
)

# Ajuste de layout
plt.subplots_adjust(
    top=0.91, bottom=0.11, left=0.08, right=0.88, hspace=0.35, wspace=0.28
)

nota_rodape = (
    "Fonte: Elaborado com base nos microdados do SNIS - SINIS / MDR.\nValores"
    " corrigidos pela inflação acumulada do IPCA/IBGE a preços de Dezembro de"
    " 2022.\nAutoria: Gabriel Siqueira dos Santos."
)
fig.text(
    0.08,
    0.025,
    nota_rodape,
    fontsize=9,
    fontstyle="italic",
    ha="left",
    va="bottom",
    linespacing=1.3,
)

print("5. Salvando figura atualizada...")
plt.savefig("investimentos_saneamento_rs.png", dpi=300, bbox_inches="tight")
print(
    "Concluído com sucesso! Os gráficos agora refletem os valores reais"
    " deflacionados."
)
plt.show()

# FIM DO SCRIPT