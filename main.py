import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk
import threading
import cv2
import numpy as np
import pandas as pd
from ultralytics import YOLO
import os
import sys

# ---------------- Configuração de caminhos ----------------
def caminho_absoluto(relativo: str) -> str:
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relativo)
    return os.path.join(os.path.abspath('.'), relativo)

# ---------------- Modelos ----------------
MODEL_FILES = {'frutos': 'best.pt'}
SINGULAR = {'frutos': 'fruto'}
MODELS = {chave: YOLO(caminho_absoluto(peso)) for chave, peso in MODEL_FILES.items()}
COIN_CLASS = 'moeda'

# Limiar de confiança (separado por classe)
LIMIAR_CONF_FRUTO = 0.55   # Ajuste aqui a confiabilidade mínima para frutos
LIMIAR_CONF_MOEDA = 0.20   # Ajuste aqui a confiabilidade mínima para moeda (costuma ser menor)

# ---------------- Estado global ----------------
resultados_acumulados = []     # acumula resultados de todas as imagens
checkbox_vars = []             # lista de (tk.BooleanVar, resultado) para checkboxes

# ---------------- Viewer com zoom/pan ----------------
class ImageViewer(tk.Frame):
    """
    Canvas com zoom/pan e botões Fit/100%/Zoom In/Zoom Out.
    Use: viewer.show_image(np_array_bgr) ou viewer.show_pil(Image)
    """
    def __init__(self, master, width=300, height=400, bg='white'):
        super().__init__(master, bg=master['bg'])
        self.bg = bg

        # Toolbar
        barra = tk.Frame(self, bg=master['bg'])
        barra.pack(fill='x', pady=(0, 6))
        ttk.Button(barra, text='Fit', command=self.fit).pack(side='left', padx=(0, 6))
        ttk.Button(barra, text='100%', command=self.one_to_one).pack(side='left', padx=(0, 6))
        ttk.Button(barra, text='＋', width=3, command=lambda: self.zoom_at(1.25)).pack(side='left')
        ttk.Button(barra, text='－', width=3, command=lambda: self.zoom_at(0.8)).pack(side='left', padx=(6, 0))

        # Área scrollável
        envolt = tk.Frame(self, bg=master['bg'])
        envolt.pack()
        self.canvas = tk.Canvas(envolt, bg=self.bg, width=width, height=height, highlightthickness=0, cursor='cross')
        self.scroll_vertical = ttk.Scrollbar(envolt, orient='vertical', command=self.canvas.yview)
        self.scroll_horizontal = ttk.Scrollbar(envolt, orient='horizontal', command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.scroll_vertical.set, xscrollcommand=self.scroll_horizontal.set)

        self.canvas.grid(row=0, column=0, sticky='nsew')
        self.scroll_vertical.grid(row=0, column=1, sticky='ns')
        self.scroll_horizontal.grid(row=1, column=0, sticky='ew')

        envolt.grid_rowconfigure(0, weight=1)
        envolt.grid_columnconfigure(0, weight=1)

        # Estado
        self._pil = None           # PIL.Image original (RGB)
        self._im_tk = None         # PhotoImage exibida
        self._scale = 1.0          # escala atual
        self._fit_scale = 1.0      # escala de "fit"
        self._img_item = None      # ID do item de imagem no canvas
        self._drag_from = None

        # Bindings
        self.canvas.bind('<Configure>', self._on_canvas_resize)
        self.canvas.bind('<Double-Button-1>', self._on_double_click)
        self.canvas.bind('<ButtonPress-1>', self._start_pan)
        self.canvas.bind('<B1-Motion>', self._do_pan)
        self.canvas.bind('<ButtonRelease-1>', self._end_pan)

        # wheel (Windows/Mac/Linux)
        self.canvas.bind('<MouseWheel>', self._on_wheel)        # Windows/Mac
        self.canvas.bind('<Button-4>', self._on_wheel_linux)    # Linux scroll up
        self.canvas.bind('<Button-5>', self._on_wheel_linux)    # Linux scroll down

    # -------- API pública --------
    def show_image(self, bgr_np: np.ndarray):
        rgb = cv2.cvtColor(bgr_np, cv2.COLOR_BGR2RGB)
        self._set_pil(Image.fromarray(rgb))

    def show_pil(self, pil_image: Image.Image):
        self._set_pil(pil_image.convert('RGB'))

    def fit(self):
        if not self._pil:
            return
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        if canvas_w < 2 or canvas_h < 2:
            return
        self._fit_scale = min(canvas_w / self._pil.width, canvas_h / self._pil.height)
        self._scale = self._fit_scale
        self._render_at_scale()

    def one_to_one(self):
        if not self._pil:
            return
        self._scale = 1.0
        self._render_at_scale(center=True)

    def zoom_at(self, fator: float, x=None, y=None):
        if not self._pil:
            return
        nova_escala = max(0.05, min(self._scale * fator, 20.0))
        fator = nova_escala / self._scale
        self._scale = nova_escala

        if x is None or y is None:
            x = self.canvas.winfo_width() // 2
            y = self.canvas.winfo_height() // 2
        vx, vy = self.canvas.canvasx(x), self.canvas.canvasy(y)

        self._render_at_scale()
        # Mantém ponto sob o cursor
        total_w, total_h = max(1, self._image_width()), max(1, self._image_height())
        self.canvas.xview_moveto((vx * fator - x) / total_w)
        self.canvas.yview_moveto((vy * fator - y) / total_h)

    # -------- Internos --------
    def _set_pil(self, pil: Image.Image):
        self._pil = pil
        self._scale = 1.0
        self._fit_scale = 1.0
        self._render_at_scale()
        self.fit()  # Ajuste inicial

    def _image_width(self) -> int:
        return int(self._pil.width * self._scale)

    def _image_height(self) -> int:
        return int(self._pil.height * self._scale)

    def _render_at_scale(self, center: bool=False):
        if not self._pil:
            return
        w, h = self._image_width(), self._image_height()
        if w < 1 or h < 1:
            return
        redimensionada = self._pil.resize((w, h), Image.Resampling.LANCZOS)
        self._im_tk = ImageTk.PhotoImage(redimensionada)

        if self._img_item is None:
            self._img_item = self.canvas.create_image(0, 0, anchor='nw', image=self._im_tk)
        else:
            self.canvas.itemconfig(self._img_item, image=self._im_tk)

        self.canvas.config(scrollregion=(0, 0, w, h))
        if center:
            cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
            self.canvas.xview_moveto(max(0, (w - cw) / 2) / max(1, w))
            self.canvas.yview_moveto(max(0, (h - ch) / 2) / max(1, h))

    def _on_canvas_resize(self, _e):
        if self._pil and abs(self._scale - self._fit_scale) < 1e-3:
            self.fit()
        elif self._pil:
            self.canvas.config(scrollregion=(0, 0, self._image_width(), self._image_height()))

    def _on_double_click(self, _e):
        if self._pil is None:
            return
        if abs(self._scale - self._fit_scale) < 1e-3:
            self.one_to_one()
        else:
            self.fit()

    def _start_pan(self, e):
        self.canvas.scan_mark(e.x, e.y)
        self._drag_from = (e.x, e.y)

    def _do_pan(self, e):
        if self._drag_from is None:
            return
        self.canvas.scan_dragto(e.x, e.y, gain=1)

    def _end_pan(self, _e):
        self._drag_from = None

    def _on_wheel(self, e):
        fator = 1.12 if (e.delta > 0) else (1/1.12)
        if (e.state & 0x4):  # Ctrl pressionado
            fator = 1.05 if (e.delta > 0) else (1/1.05)
        self.zoom_at(fator, e.x, e.y)

    def _on_wheel_linux(self, e):
        fator = 1.12 if (e.num == 4) else (1/1.12)
        self.zoom_at(fator, e.x, e.y)

# ---------------- Funções de processamento ----------------
def detectar_cor(imagem_bgr: np.ndarray, caixa_xyxy) -> str:
    x1, y1, x2, y2 = map(int, caixa_xyxy)
    roi = imagem_bgr[y1:y2, x1:x2]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    h, s, v = np.mean(hsv.reshape(-1, 3), axis=0)
    if s < 40 and v > 200: return 'branco'
    if v < 50: return 'preto'
    if s < 60: return 'cinza'
    if h < 10 or h > 160: return 'vermelho'
    if 10 <= h < 20: return 'laranja'
    if 20 <= h < 35: return 'amarelo'
    if 35 <= h < 85: return 'verde'
    if 85 <= h < 125: return 'azul'
    if 125 <= h < 150: return 'roxo'
    if 10 <= h < 20 and s > 100 and v < 150: return 'marrom'
    return 'desconhecido'

def calcular_escala(caixas, nomes_classes, conf_min_moeda: float) -> float | None:
    """
    Retorna pixels_por_mm (px/mm) calculado pela moeda detectada com confiança >= conf_min_moeda.
    """
    for caixa_xyxy, classe_id, confianca in zip(caixas.xyxy, caixas.cls, caixas.conf):
        if nomes_classes[int(classe_id)] == COIN_CLASS and float(confianca) >= conf_min_moeda:
            x1, y1, x2, y2 = map(int, caixa_xyxy)
            diametro_px = ((x2 - x1) + (y2 - y1)) / 2
            return diametro_px / 25.0  # 25 mm
    return None

def calcular_tamanho_cm(caixa_xyxy, pixels_por_mm: float, modo: str='diametro') -> float:
    x1, y1, x2, y2 = map(int, caixa_xyxy)
    px = (y2 - y1) if modo == 'altura' else ((x2 - x1) + (y2 - y1)) / 2
    mm = px / pixels_por_mm
    return mm / 10  # cm

def processar_imagem(caminho_arquivo: str) -> dict:
    imagem_bgr = cv2.imread(caminho_arquivo)
    imagem_bgr_original = imagem_bgr.copy()
    resumos_por_modelo = []

    for chave_modelo, modelo in MODELS.items():
        # Pega detecções com um conf base (o menor dos limiares)
        conf_base = min(LIMIAR_CONF_FRUTO, LIMIAR_CONF_MOEDA)
        caixas = modelo(imagem_bgr, conf=conf_base)[0].boxes
        nomes_classes = modelo.names

        # Escala somente com moedas confiáveis
        pixels_por_mm = calcular_escala(caixas, nomes_classes, conf_min_moeda=LIMIAR_CONF_MOEDA)
        if pixels_por_mm is None:
            raise ValueError(f'Moeda não detectada ({chave_modelo})')

        detalhes_frutos = []
        for caixa_xyxy, classe_id, confianca in zip(caixas.xyxy, caixas.cls, caixas.conf):
            nome_classe = nomes_classes[int(classe_id)]
            conf_float = float(confianca)

            if nome_classe == COIN_CLASS and conf_float >= LIMIAR_CONF_MOEDA:
                x1, y1, x2, y2 = map(int, caixa_xyxy)
                cv2.rectangle(imagem_bgr, (x1, y1), (x2, y2), (0, 255, 255), 2)
                cv2.putText(imagem_bgr, COIN_CLASS, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            elif nome_classe == SINGULAR.get(chave_modelo) and conf_float >= LIMIAR_CONF_FRUTO:
                x1, y1, x2, y2 = map(int, caixa_xyxy)
                tamanho_cm = calcular_tamanho_cm(caixa_xyxy, pixels_por_mm, 'diametro')
                cor_estimada = detectar_cor(imagem_bgr_original, caixa_xyxy)
                detalhes_frutos.append((round(tamanho_cm, 2), cor_estimada))

                rotulo = f"{round(tamanho_cm, 2)}cm"
                cv2.rectangle(imagem_bgr, (x1, y1), (x2, y2), (0, 100, 255), 2)
                cv2.putText(imagem_bgr, rotulo, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 100, 255), 2)

        media_cm = None
        if detalhes_frutos:
            valores = [v[0] for v in detalhes_frutos]
            media_cm = round(np.mean(valores), 2)

        resumos_por_modelo.append({
            'modelo': chave_modelo,
            'detalhes': detalhes_frutos,
            'media': media_cm,
            'quantidade': len(detalhes_frutos)
        })

    return {
        'imagem': os.path.basename(caminho_arquivo),
        'resumo': resumos_por_modelo,
        'imagem_caixas': imagem_bgr
    }

# ---------------- Funções de interface ----------------
def selecionar_imagem():
    caminho = filedialog.askopenfilename(filetypes=[('Imagens', '*.jpg *.png *.jpeg')])
    if not caminho:
        return
    threading.Thread(target=processar_com_interface, args=(caminho,), daemon=True).start()

def processar_com_interface(caminho_arquivo: str):
    try:
        resultado_processado = processar_imagem(caminho_arquivo)
        # acumula resultados sem apagar anteriores
        resultados_acumulados.append(resultado_processado)
        exibir_resultados()

        # Mostra a imagem processada no viewer
        imagem_bgr_com_caixas = resultado_processado['imagem_caixas']
        viewer.show_image(imagem_bgr_com_caixas)
    except Exception as e:
        messagebox.showerror('Erro', str(e))

def exibir_resultados():
    texto.config(state='normal')
    texto.delete('1.0', 'end')
    # limpa frame de checkboxes antes
    for widget in frame_cb.winfo_children():
        widget.destroy()
    checkbox_vars.clear()

    for resultado in resultados_acumulados:
        texto.insert('end', f"Imagem: {resultado['imagem']}\n")
        for resumo_modelo in resultado['resumo']:
            texto.insert('end', f"Frutos: {resumo_modelo['quantidade']} | média: {resumo_modelo['media']}cm\n")
            for indice, detalhe in enumerate(resumo_modelo['detalhes'], 1):
                texto.insert('end', f"  {indice}: {detalhe}\n")
        # checkbox para selecionar exportação desse resultado
        var_marcado = tk.BooleanVar(value=True)
        cb = tk.Checkbutton(frame_cb, text=resultado['imagem'], variable=var_marcado, bg='#EAF8DC')
        cb.pack(anchor='w')
        checkbox_vars.append((var_marcado, resultado))
        texto.insert('end', '-'*30 + '\n')

    texto.config(state='disabled')

def salvar_planilha():
    selecionados = [resultado for var, resultado in checkbox_vars if var.get()]
    if not selecionados:
        messagebox.showwarning('Aviso', 'Nenhum selecionado')
        return

    caminho_saida = filedialog.asksaveasfilename(defaultextension='.xlsx', filetypes=[('Excel','*.xlsx')])
    if not caminho_saida:
        return

    linhas = []
    for resultado in selecionados:
        for resumo_modelo in resultado['resumo']:
            for indice, detalhe in enumerate(resumo_modelo['detalhes'], 1):
                linhas.append({
                    'Imagem': resultado['imagem'],
                    'Item': indice,
                    'Tamanho (cm)': detalhe[0],
                    'Cor': detalhe[1],
                    'Média (cm)': resumo_modelo['media']
                })

    pd.DataFrame(linhas).to_excel(caminho_saida, index=False)
    messagebox.showinfo('Sucesso', f'Resultados salvos em: {caminho_saida}')

# ---------------- Inicialização GUI ----------------
root = tk.Tk()
root.title('Contador de Frutos')
root.geometry('1024x768')
root.configure(bg='#EAF8DC')
style = ttk.Style(root)
style.theme_use('clam')
style.configure('TButton', background='#6CBF4B', foreground='white', font=('Segoe UI', 10, 'bold'), padding=6)

# Botões
frame_botoes = tk.Frame(root, bg='#EAF8DC')
frame_botoes.pack(pady=10)
btn_selecionar = ttk.Button(frame_botoes, text='Selecionar Imagem', command=selecionar_imagem)
btn_selecionar.pack(side='left', padx=10)
btn_salvar = ttk.Button(frame_botoes, text='Salvar Resultados', command=salvar_planilha)
btn_salvar.pack(side='left', padx=10)

# Viewer de imagem
canvas_width, canvas_height = 500, 500
frame_imagem = tk.Frame(root, bg='#EAF8DC')
frame_imagem.pack(padx=20, pady=10)
viewer = ImageViewer(frame_imagem, width=canvas_width, height=canvas_height, bg='white')
viewer.pack()

# Resultados de texto
frame_texto = tk.Frame(root, bg='#EAF8DC')
frame_texto.pack(fill='x', padx=20)
texto = tk.Text(frame_texto, height=10, font=('Consolas', 9), bg='#F5FFF0')
texto.pack(side='left', fill='x', expand=True)
scroll_texto = ttk.Scrollbar(frame_texto, orient='vertical', command=texto.yview)
texto.configure(yscrollcommand=scroll_texto.set)
scroll_texto.pack(side='right', fill='y')

# ---------------- Lista de seleção com scroll ----------------
frame_cb_container = tk.LabelFrame(root, text='Selecionar imagens para exportar', bg='#EAF8DC')
frame_cb_container.pack(fill='both', expand=False, padx=20, pady=(0, 20))
canvas_cb = tk.Canvas(frame_cb_container, bg='#EAF8DC', bd=0, highlightthickness=0, height=120)
scrollbar_cb = ttk.Scrollbar(frame_cb_container, orient='vertical', command=canvas_cb.yview)
frame_cb = tk.Frame(canvas_cb, bg='#EAF8DC')

frame_cb.bind('<Configure>', lambda e: canvas_cb.configure(scrollregion=canvas_cb.bbox('all')))
canvas_cb.create_window((0, 0), window=frame_cb, anchor='nw')
canvas_cb.configure(yscrollcommand=scrollbar_cb.set)
canvas_cb.pack(side='left', fill='x', expand=True)
scrollbar_cb.pack(side='right', fill='y')

# Atalhos (opcional)
root.bind('<Control-0>', lambda e: viewer.one_to_one())
root.bind('<Control-f>', lambda e: viewer.fit())
root.bind('<Control-=>', lambda e: viewer.zoom_at(1.25))
root.bind('<Control-minus>', lambda e: viewer.zoom_at(0.8))

root.mainloop()
