import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.edgecolor"] = "#c3c2b7"
plt.rcParams["axes.linewidth"] = 0.8
plt.rcParams["text.color"] = "#2C2C2A"
plt.rcParams["axes.labelcolor"] = "#52514e"
plt.rcParams["xtick.color"] = "#52514e"
plt.rcParams["ytick.color"] = "#52514e"

AZUL = "#2a78d6"
VERMELHO = "#e34948"
LARANJA = "#eb6834"

# ---------------------------------------------------------------
# Grafico Q4 - Ticket medio dos 10 clientes fieis
# ---------------------------------------------------------------
labels_q4 = ["22", "1477", "929", "1116", "1691", "774", "1470", "1599", "965", "1722"]
dados_q4 = [41839.94, 41648.30, 41645.23, 40983.58, 40773.57, 40340.44, 40021.27, 39904.66, 39841.05, 39532.94]

fig, ax = plt.subplots(figsize=(8, 4.2), dpi=200)
bars = ax.bar(labels_q4, dados_q4, color=AZUL, width=0.62, zorder=3)
ax.set_ylim(39000, 42200)
ax.set_ylabel("Ticket médio (R$)")
ax.set_xlabel("ID do cliente")
ax.set_title("Ticket médio dos 10 clientes fiéis", fontsize=13, fontweight="bold", color="#26215C", pad=14)
ax.yaxis.set_major_formatter(lambda v, pos: f"R$ {v/1000:.0f}k")
ax.grid(axis="y", color="#e1e0d9", linewidth=0.8, zorder=0)
ax.spines[["top", "right"]].set_visible(False)
for spine in ["left", "bottom"]:
    ax.spines[spine].set_color("#c3c2b7")
plt.tight_layout()
plt.savefig("/home/claude/relatorio_docx/grafico_q4.png", facecolor="white")
plt.close()

# ---------------------------------------------------------------
# Grafico Q5 - Vendas medias por dia da semana
# ---------------------------------------------------------------
labels_q5 = ["Quinta", "Domingo", "Segunda", "Sábado", "Terça", "Sexta", "Quarta"]
dados_q5 = [157154.32, 157616.13, 158241.15, 164858.27, 166118.83, 170193.68, 173605.44]
cores_q5 = [VERMELHO if i == 0 else AZUL for i in range(len(labels_q5))]

fig, ax = plt.subplots(figsize=(8, 4.2), dpi=200)
ax.bar(labels_q5, dados_q5, color=cores_q5, width=0.62, zorder=3)
ax.set_ylim(150000, 176000)
ax.set_ylabel("Média de vendas por dia (R$)")
ax.set_title("Vendas médias por dia da semana (lojas físicas)", fontsize=13, fontweight="bold", color="#26215C", pad=14)
ax.yaxis.set_major_formatter(lambda v, pos: f"R$ {v/1000:.0f}k")
ax.grid(axis="y", color="#e1e0d9", linewidth=0.8, zorder=0)
ax.spines[["top", "right"]].set_visible(False)
for spine in ["left", "bottom"]:
    ax.spines[spine].set_color("#c3c2b7")
plt.tight_layout()
plt.savefig("/home/claude/relatorio_docx/grafico_q5.png", facecolor="white")
plt.close()

# ---------------------------------------------------------------
# Grafico Q6 - Previsto vs Realizado
# ---------------------------------------------------------------
meses = ["2026-01", "2026-02", "2026-03"]
previsto = [38.67, 53.67, 56.33]
realizado = [79, 68, 60]

fig, ax = plt.subplots(figsize=(8, 4.2), dpi=200)
ax.plot(meses, previsto, marker="o", color=AZUL, linewidth=2.2, markersize=8,
        markerfacecolor=AZUL, markeredgecolor="white", markeredgewidth=1.5, label="Previsto", zorder=3)
ax.plot(meses, realizado, marker="o", color=LARANJA, linewidth=2.2, markersize=8, linestyle="--",
        markerfacecolor=LARANJA, markeredgecolor="white", markeredgewidth=1.5, label="Realizado", zorder=3)
ax.set_ylim(0, 90)
ax.set_ylabel("Unidades vendidas")
ax.set_title("Previsto vs. realizado — Bússola de Bordo 702 (Q1 2026)", fontsize=13, fontweight="bold", color="#26215C", pad=14)
ax.grid(axis="y", color="#e1e0d9", linewidth=0.8, zorder=0)
ax.spines[["top", "right"]].set_visible(False)
for spine in ["left", "bottom"]:
    ax.spines[spine].set_color("#c3c2b7")
ax.legend(frameon=False, loc="upper right", fontsize=10)
plt.tight_layout()
plt.savefig("/home/claude/relatorio_docx/grafico_q6.png", facecolor="white")
plt.close()

# ---------------------------------------------------------------
# Grafico Q7 - Ranking de similaridade (horizontal)
# ---------------------------------------------------------------
labels_q7 = ["GPS Plotter 6249", "Cabo Náutico 9048", "Vela Mestra 1913", "Cabo Náutico 2105", "Motor de Popa 5331"]
dados_q7 = [0.2377, 0.2393, 0.2558, 0.2562, 0.2566]
cores_q7 = [VERMELHO if l == "Motor de Popa 5331" else AZUL for l in labels_q7]

fig, ax = plt.subplots(figsize=(8, 3.6), dpi=200)
ax.barh(labels_q7, dados_q7, color=cores_q7, height=0.58, zorder=3)
ax.set_xlim(0, 0.30)
ax.set_xlabel("Similaridade de cosseno")
ax.set_title("Top 5 produtos mais similares ao Motor de Popa 1949", fontsize=13, fontweight="bold", color="#26215C", pad=14)
ax.grid(axis="x", color="#e1e0d9", linewidth=0.8, zorder=0)
ax.spines[["top", "right"]].set_visible(False)
for spine in ["left", "bottom"]:
    ax.spines[spine].set_color("#c3c2b7")
plt.tight_layout()
plt.savefig("/home/claude/relatorio_docx/grafico_q7.png", facecolor="white")
plt.close()

print("Graficos gerados com sucesso.")
