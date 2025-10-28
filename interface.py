import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import heapq
from io import StringIO, BytesIO
import time
import numpy as np

# ====================================================
# Huffman (opera sobre BYTES para ser mais robusto)
# ====================================================
class HuffmanNode:
    def __init__(self, byte_val, freq):
        self.byte_val = byte_val  # None para nó interno, caso contrário 0-255
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq


def build_huffman_tree_from_bytes(data_bytes: bytes):
    freq = Counter(data_bytes)
    heap = [HuffmanNode(b, f) for b, f in freq.items()]
    heapq.heapify(heap)
    if not heap:
        return None
    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        merged = HuffmanNode(None, left.freq + right.freq)
        merged.left = left
        merged.right = right
        heapq.heappush(heap, merged)
    return heap[0]


def build_codes_from_tree(root):
    codes = {}
    def walk(node, prefix):
        if node is None:
            return
        if node.byte_val is not None:
            codes[node.byte_val] = prefix or "0"  # handle single-symbol case
            return
        walk(node.left, prefix + "0")
        walk(node.right, prefix + "1")
    walk(root, "")
    return codes


def huffman_compress_bytes(data_bytes: bytes):
    start = time.perf_counter()
    root = build_huffman_tree_from_bytes(data_bytes)
    if root is None:
        return "", {}, 0.0
    codes = build_codes_from_tree(root)
    # encode
    encoded_bits = "".join(codes[b] for b in data_bytes)
    comp_time = time.perf_counter() - start
    return encoded_bits, codes, comp_time


def huffman_decompress_bits(encoded_bits: str, codes: dict):
    start = time.perf_counter()
    reverse_map = {v: k for k, v in codes.items()}
    decoded_bytes = bytearray()
    cur = ""
    for bit in encoded_bits:
        cur += bit
        if cur in reverse_map:
            decoded_bytes.append(reverse_map[cur])
            cur = ""
    dec_time = time.perf_counter() - start
    return bytes(decoded_bytes), dec_time


# ====================================================
# Helpers: downsampling inteligente para plotting
# ====================================================
def downsample_df_for_plot(df: pd.DataFrame, x_col: str, max_points: int = 3000):
    n = len(df)
    if n <= max_points:
        return df
    # choose indices evenly spaced
    idx = np.linspace(0, n - 1, max_points).astype(int)
    return df.iloc[idx].reset_index(drop=True)


# ====================================================
# Streamlit UI
# ====================================================
st.set_page_config(page_title="TCLab — Huffman + Setpoints (Streamlit)", layout="wide", page_icon="🌡️")
st.title("🌡️ TCLab — Compressão Huffman ")

st.markdown("""
- Envie o CSV do TCLab (colunas esperadas: **Time (s)**, **T1**, **T2**, **Q1**, **Q2**).
- O script comprime e descomprime com Huffman internamente e exibe:
  - Gráfico de Temperaturas (T1, T2) com linhas de setpoint;
  - Gráfico de Atuadores (Q1, Q2).
- Os sliders `T1_setpoint` e `T2_setpoint` atualizam o gráfico.
""")

# Upload
uploaded_file = st.file_uploader("📂 Envie o arquivo CSV do TCLab (ex: tclab_data_7days.csv):", type=["csv"])
if uploaded_file is None:
    st.info("Envie um CSV para começar. O CSV deve conter a coluna 'Time (s)'.")
    st.stop()

# Leitura do conteúdo do arquivo como bytes (necessário para Huffman)
file_bytes = uploaded_file.read()
original_size_bytes = len(file_bytes)

# Cache: compress + decompress (usa bytes como chave)
@st.cache_data(show_spinner=False)
def compress_decompress_cached(file_bytes_blob: bytes):
    # compress
    encoded_bits, codes_map, comp_time = huffman_compress_bytes(file_bytes_blob)
    # size em bytes (estimativa: bits -> bytes)
    compressed_bytes_est = (len(encoded_bits) + 7) // 8
    # decompress
    decoded_bytes, dec_time = huffman_decompress_bits(encoded_bits, codes_map)
    return {
        "encoded_bits": encoded_bits,
        "codes_map": codes_map,
        "comp_time": comp_time,
        "dec_time": dec_time,
        "compressed_bytes_est": compressed_bytes_est,
        "decoded_bytes": decoded_bytes
    }

with st.spinner("🔧 Executando compressão/descompressão (Huffman)"):
    info = compress_decompress_cached(file_bytes)

# Verificações básicas
decoded_bytes = info["decoded_bytes"]
if decoded_bytes != file_bytes:
    st.warning("⚠️ Aviso: o conteúdo descomprimido difere do original (inconsistência detectada).")
# tamanho e tempos
comp_time = info["comp_time"]
dec_time = info["dec_time"]
compressed_bytes_est = info["compressed_bytes_est"]
compression_ratio = 100.0 * (1 - compressed_bytes_est / max(1, original_size_bytes))

# Exibir resumo
st.sidebar.subheader("Resumo da Compressão")
st.sidebar.write(f"Tamanho original: **{original_size_bytes:,}** bytes")
st.sidebar.write(f"Tamanho comprimido (estimado): **{compressed_bytes_est:,}** bytes")
st.sidebar.write(f"Redução: **{compression_ratio:.2f}%**")
st.sidebar.write(f"Tempo compressão: **{comp_time:.3f} s**")
st.sidebar.write(f"Tempo descompressão: **{dec_time:.3f} s**")

# Construir DataFrame a partir dos bytes decodificados (assume utf-8 CSV)
try:
    text = decoded_bytes.decode("utf-8")
except UnicodeDecodeError:
    # tenta com latin1
    text = decoded_bytes.decode("latin1")

df = pd.read_csv(StringIO(text))

# Verifica existência da coluna Time (s)
if "Time (s)" not in df.columns:
    st.error("O CSV precisa conter a coluna 'Time (s)'. Verifique o arquivo e reenvie.")
    st.stop()

# Garante colunas numéricas
for col in ["T1", "T2", "Q1", "Q2"]:
    if col not in df.columns:
        st.error(f"Coluna esperada '{col}' não encontrada no CSV.")
        st.stop()
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Convert Time (s) para numérico (mantendo o nome)
df["Time (s)"] = pd.to_numeric(df["Time (s)"], errors='coerce')

# Sidebar: escolha de downsampling e max pontos
st.sidebar.subheader("Performance e Visualização")
max_points = st.sidebar.number_input("Máx pontos a plotar (downsample)", min_value=500, max_value=100000, value=3000, step=500)
auto_downsample = st.sidebar.checkbox("Ativar downsampling automático (recomendado)", value=True)

# Sidebar: setpoints (sliders) — atualização em tempo real
st.sidebar.subheader("Setpoints (T1 / T2)")
t1_min, t1_max = float(df["T1"].min()), float(df["T1"].max())
t2_min, t2_max = float(df["T2"].min()), float(df["T2"].max())

# definir ranges um pouco mais largos para permitir setpoint fora do range atual
pad1 = max(1.0, (t1_max - t1_min) * 0.1)
pad2 = max(1.0, (t2_max - t2_min) * 0.1)

T1_setpoint = st.sidebar.slider("T1 setpoint", min_value=(t1_min - pad1), max_value=(t1_max + pad1),
                                value=float((t1_min + t1_max) / 2), step=0.1)
T2_setpoint = st.sidebar.slider("T2 setpoint", min_value=(t2_min - pad2), max_value=(t2_max + pad2),
                                value=float((t2_min + t2_max) / 2), step=0.1)

# Filtro temporal opcional (por dia/hora) — se houver coluna com data, você pode implementar; aqui filtramos por intervalo de Time (s)
st.sidebar.subheader("Filtro Time (s)")
min_time_s = int(df["Time (s)"].min())
max_time_s = int(df["Time (s)"].max())
time_range = st.sidebar.slider("Intervalo Time (s)", min_value=min_time_s, max_value=max_time_s,
                               value=(min_time_s, max_time_s), step=1)

# Aplica filtro de tempo
df_filtered = df[(df["Time (s)"] >= time_range[0]) & (df["Time (s)"] <= time_range[1])].reset_index(drop=True)

# Downsample para plot
if auto_downsample:
    plot_df = downsample_df_for_plot(df_filtered, "Time (s)", max_points=int(max_points))
else:
    plot_df = df_filtered.copy()

# Layout Principal: gráficos lado a lado
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Temperaturas e Setpoints")
    fig_temp = go.Figure()
    # linhas T1 e T2 (downsampled)
    fig_temp.add_trace(go.Scatter(
        x=plot_df["Time (s)"], y=plot_df["T1"], mode="lines", name="T1"
    ))
    fig_temp.add_trace(go.Scatter(
        x=plot_df["Time (s)"], y=plot_df["T2"], mode="lines", name="T2"
    ))
    # linhas de setpoint (constantes) — estendem no intervalo exibido
    x0, x1 = plot_df["Time (s)"].min(), plot_df["Time (s)"].max()
    fig_temp.add_trace(go.Scatter(x=[x0, x1], y=[T1_setpoint, T1_setpoint],
                                  mode="lines", name="T1_setpoint", line=dict(dash="dash")))
    fig_temp.add_trace(go.Scatter(x=[x0, x1], y=[T2_setpoint, T2_setpoint],
                                  mode="lines", name="T2_setpoint", line=dict(dash="dash")))
    fig_temp.update_layout(template="plotly_dark",
                           xaxis_title="Time (s)",
                           yaxis_title="Temperatura (°C)",
                           height=540,
                           hovermode="x unified")
    st.plotly_chart(fig_temp, use_container_width=True)

with col2:
    st.subheader("Atuadores (Q1, Q2)")
    fig_q = go.Figure()
    fig_q.add_trace(go.Bar(x=plot_df["Time (s)"], y=plot_df["Q1"], name="Q1", marker_line_width=0))
    fig_q.add_trace(go.Bar(x=plot_df["Time (s)"], y=plot_df["Q2"], name="Q2", marker_line_width=0))
    fig_q.update_layout(template="plotly_dark",
                        xaxis_title="Time (s)",
                        yaxis_title="Potência (%)",
                        barmode="overlay",
                        height=540,
                        hovermode="x unified")
    st.plotly_chart(fig_q, use_container_width=True)

# Estatísticas e informações de performance
st.markdown("---")
c1, c2, c3 = st.columns([1,1,1])
with c1:
    st.metric("Amostras (filtro)", f"{len(df_filtered):,}")
    st.metric("Amostras (plotted)", f"{len(plot_df):,}")
with c2:
    st.metric("Compressão (estim.)", f"{compression_ratio:.2f}%")
    st.metric("Tamanho comprimido (bytes)", f"{compressed_bytes_est:,}")
with c3:
    st.metric("Tempo compressão", f"{comp_time:.3f} s")
    st.metric("Tempo descompressão", f"{dec_time:.3f} s")

# Mostrar um pequeno preview dos dados (limitado)
st.subheader("Preview dos Dados (amostra)")
st.dataframe(df_filtered.head(200).reset_index(drop=True))

st.markdown("---")
st.caption("Observações: Huffman implementado direto no script. Para arquivos muito grandes a compressão/descompressão em memória pode ser lenta; por isso há downsampling para manter interatividade.")
