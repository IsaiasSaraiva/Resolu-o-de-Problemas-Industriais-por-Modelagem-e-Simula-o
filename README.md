# 🧠 Resolução de Problemas Industriais por Modelagem e Simulação

📖 **Visão Geral**

Este repositório é referente à disciplina **Resolução de Problemas Industriais por Modelagem e Simulação** do programa de pós-graduação da **Universidade Federal do Amazonas (UFAM)**.

O projeto aborda a análise de um problema de controle em um sistema dinâmico, utilizando dados experimentais do **TCLab (Thermal Control Lab)**, e integra um estudo de **eficiência computacional na gestão desses dados**.


---

## 💡 Conceitos Principais

### 🔹 Modelagem e Simulação de Sistemas Dinâmicos

- O **TCLab** simula um processo industrial de controle de temperatura (aquecimento e resfriamento).  
- A interface permite a **visualização e análise das curvas de temperatura (T1 e T2)** em resposta aos **atuadores (Q1 e Q2)**, com a adição de **setpoints interativos** para referência.

### 🔹 Eficiência Computacional (Compressão de Dados)

- Todo o arquivo de dados **CSV** (que representa os dados reais de experimento por 7 dias) é submetido à **compressão e descompressão Huffman** a nível de bytes.  
- Este processo simula a necessidade industrial de **armazenar ou transmitir grandes volumes de dados de sensores** com a máxima eficiência, permitindo a **reconstrução exata do sinal** para análise.  
- O aplicativo exibe métricas cruciais como a **taxa de compressão** e os **tempos de execução do algoritmo**.

---

## 🚀 Aplicação Interativa (`interface.py`)

O arquivo `interface.py` é um **aplicativo web interativo** construído com a biblioteca **Streamlit**. Ele oferece as seguintes funcionalidades:

- 📂 **Upload:** Permite o upload de arquivos CSV de experimentos do TCLab.  
- ⚙️ **Processamento Huffman:** Realiza a compressão e, imediatamente, a descompressão dos dados carregados, garantindo sua integridade.  
- 📊 **Visualização Dinâmica:** Gera gráficos interativos (**Plotly**) de Temperaturas (T1, T2) e Atuadores (Q1, Q2) ao longo do tempo.  
- 🎚️ **Análise de Setpoints:** Sliders laterais permitem definir **setpoints** para T1 e T2, facilitando a visualização de desvios e o projeto de controladores.  
- 📈 **Métricas de Performance:** Apresenta um painel lateral com o resumo da compressão, incluindo **tamanho original**, **tamanho comprimido** e **porcentagem de redução**.

---

## ⚙️ Como Executar

### 🧩 Pré-requisitos

Certifique-se de ter o **Python** instalado em sua máquina.

---

###  Clonar este repositório
```bash
  git clone
```

### 1️⃣ Criar e Ativar o Ambiente Virtual

É uma boa prática isolar as dependências do projeto:

```bash
# Cria o ambiente virtual (venv)
python -m venv venv

# Ativa o ambiente virtual
# No Windows (Command Prompt)
venv\Scripts\activate.bat

# No Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# No Linux/macOS
source venv/bin/activate

# Instalar as dependências que estão no arquivo requiriments.txt
pip install requiriments

# Executar o arquivo interace.py:
streamlit run interface.py
