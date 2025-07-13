# Contador de Frutos (Plant AI)

Este é um aplicativo de desktop, construído com **Tkinter** e **YOLO**, que:

1. Detecta frutos e uma moeda de referência em imagens  
2. Calcula o tamanho médio dos frutos (em centímetros)  
3. Identifica a cor de cada fruto  
4. Gera uma planilha `.xlsx` com os resultados  

---

## 📥 Pré-requisitos

- **Computador com Windows (10+) ou macOS (10.15+)**  
- **Acesso à Internet**  
- **Nenhuma experiência prévia em terminal é necessária!**  

### 1. Instalar o Python 3.8+  

#### Windows  
1. Abra o navegador e acesse:  
   `https://www.python.org/downloads/windows/`  
2. Clique em **Download Python 3.x.x** (versão estável).  
3. Execute o instalador baixado.  
4. **Importante:** marque a caixinha **“Add Python 3.x to PATH”** antes de clicar em **Install Now**.  
5. Aguarde a instalação e feche o instalador.

#### macOS  
1. Abra o navegador e acesse:  
   `https://www.python.org/downloads/macos/`  
2. Baixe o instalador `.pkg`.  
3. Abra o arquivo e siga os passos na tela (ele já adiciona o Python ao PATH por padrão).  

---

## 🛠️ Instalação do Projeto

1. **Baixar o projeto**  
   - **Opção A – Download ZIP:**  
     1. No navegador, vá para `https://github.com/SEU_USUARIO/plant-ai`  
     2. Clique em **Code** ▶️ **Download ZIP**  
     3. Extraia o arquivo ZIP em qualquer pasta do seu computador  
   - **Opção B – Git (se quiser aprender no futuro):**  
     ```bash
     git clone https://github.com/SEU_USUARIO/plant-ai.git
     ```  
2. **Abrir a pasta do projeto**  
   - No **Windows Explorer**, entre na pasta `plant-ai`  
   - No **macOS Finder**, entre na pasta `plant-ai`  
3. **Instalar as dependências**  
   - Na barra de endereços do Windows Explorer (ou Finder), digite `cmd` (Windows) ou abra o **Terminal** (macOS) e pressione Enter.  
   - Na janela que abrir (Prompt de Comando, PowerShell ou Terminal), digite:
     ```bash
     pip install --upgrade pip
     pip install -r requirements.txt
     ```  
   - Aguarde enquanto o Python baixa e instala tudo.
4. **Colocar o modelo**  
   - Copie o arquivo `best.pt` (seu modelo YOLO treinado) para dentro da pasta `plant-ai`, se ainda não estiver lá.

---

## 🚀 Como Executar

1. **Abra o Prompt de Comando / PowerShell / Terminal** exatamente dentro da pasta `plant-ai` (veja acima como fazer).  
2. Digite:
   ```bash
   python main.py
   ```  
3. Pressione **Enter**. A janela do aplicativo será aberta automaticamente.

---

## 💻 Uso Básico do App

1. Clique em **Selecionar Imagem** e escolha sua foto (`.jpg`, `.png` ou `.jpeg`).  
2. Clique em **Processar** para:
   - Detectar a moeda de 25 mm e os frutos  
   - Desenhar retângulos ao redor de cada objeto  
   - Calcular o tamanho médio dos frutos  
   - Identificar a cor predominante de cada fruto  
3. Marque as caixas ao lado das imagens que quer exportar.  
4. Clique em **Salvar Resultados**, escolha onde salvar o arquivo `.xlsx` e pronto!

---

## ❓ Dicas e Solução de Problemas

- **“’pip’ não reconhecido”**  
  - Significa que o Python não foi adicionado ao PATH.  
  - Reinstale o Python no Windows e **marque** “Add Python 3.x to PATH”.  
- **Tkinter não abre ou dá erro**  
  ```bash
  python -m tkinter
  ```  
  - Se abrir uma janela vazia, está tudo certo.  
- **Moeda não detectada**  
  - Certifique-se de que a moeda de 25 mm esteja bem visível, sem sombras ou objetos por cima.

---

## 📝 Licença

Este projeto é **livre** para uso e modificação.  
Sinta-se à vontade para adaptá-lo às suas necessidades!  

*Desenvolvido como parte do projeto Plant AI — LMGVB / Unimontes*
