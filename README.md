# Contador de Frutos (Plant AI)

Este é um aplicativo de desktop (Tkinter + YOLO) que:

1. Detecta frutos e uma moeda de referência em imagens.
2. Calcula o tamanho médio dos frutos (cm).
3. Identifica a cor de cada fruto.
4. Gera uma planilha `.xlsx` com os resultados.

---

## 📥 Pré-requisitos

- **Python 3.8+** instalado no seu computador.  
  - Caso ainda não tenha o Python instalado, baixe o instalador em: https://www.python.org/downloads/  
- (Opcional, mas recomendado) **venv** para criar um ambiente virtual.

---

## 🛠️ Instalação

1. **Clone** ou **baixe** este repositório sem precisar estar logado:
   - **Via Git** (se tiver Git instalado):
     ```bash
     git clone https://github.com/SEU_USUARIO/plant-ai.git
     cd plant-ai
     ```
   - **Via Download ZIP**:
     1. Acesse `https://github.com/SEU_USUARIO/plant-ai` em qualquer navegador.
     2. Clique em **Code** e depois em **Download ZIP**.
     3. Extraia o ZIP e abra a pasta `plant-ai`.

2. **Crie** e **ative** um ambiente virtual:
   - **Windows**  
     ```bash
     python -m venv .venv
     .venv\Scripts\activate
     ```
   - **macOS/Linux**  
     ```bash
     python -m venv .venv
     source .venv/bin/activate
     ```

3. **Atualize** o pip e **instale** as dependências:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt


