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
def caminho_absoluto(relativo):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relativo)
    return os.path.join(os.path.abspath('.'), relativo)

# ---------------- Modelos ----------------
MODEL_FILES = {'frutos': 'best.pt'}
SINGULAR = {'frutos': 'fruto'}
MODELS = {k: YOLO(caminho_absoluto(v)) for k, v in MODEL_FILES.items()}
COIN_CLASS = 'moeda'

# ---------------- Estado global ----------------
resultados = []            # acumula resultados de todas as imagens
checkbox_vars = []         # lista de (var, resultado) para checkboxes
zoom_ativo = False

# ---------------- Funções de processamento ----------------
def detectar_cor(imagem, box):
    x1, y1, x2, y2 = map(int, box)
    roi = imagem[y1:y2, x1:x2]
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


def calcular_escala(detections, names):
    for box, cls in zip(detections.xyxy, detections.cls):
        if names[int(cls)] == COIN_CLASS:
            x1, y1, x2, y2 = map(int, box)
            diam = ((x2 - x1) + (y2 - y1)) / 2
            return diam / 25.0
    return None


def calcular_tamanho(box, escala, metodo='diametro'):
    x1, y1, x2, y2 = map(int, box)
    px = (y2 - y1) if metodo == 'altura' else ((x2 - x1) + (y2 - y1)) / 2
    mm = px / escala
    return mm / 10


def processar_imagem(caminho):
    img = cv2.imread(caminho)
    orig = img.copy()
    resumo = []
    for key, model in MODELS.items():
        det = model(img)[0].boxes
        names = model.names
        escala = calcular_escala(det, names)
        if escala is None:
            raise ValueError(f'Moeda não detectada ({key})')
        info = []
        for box, cls in zip(det.xyxy, det.cls):
            nome = names[int(cls)]
            if nome == COIN_CLASS:
                x1, y1, x2, y2 = map(int, box)
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 255), 2)
                cv2.putText(img, COIN_CLASS, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            elif nome == SINGULAR.get(key):
                x1, y1, x2, y2 = map(int, box)
                t = calcular_tamanho(box, escala, 'diametro')
                c = detectar_cor(orig, box)
                info.append((round(t, 2), c))
                label = f"{round(t, 2)}cm"
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 100, 255), 2)
                cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 100, 255), 2)
        media = None
        if info:
            vals = [v[0] for v in info]
            media = round(np.mean(vals), 2)
        resumo.append({'modelo': key, 'detalhes': info, 'media': media, 'quantidade': len(info)})
    return {'imagem': os.path.basename(caminho), 'resumo': resumo, 'imagem_caixas': img}

# ---------------- Funções de interface ----------------
def selecionar_imagem():
    path = filedialog.askopenfilename(filetypes=[('Imagens', '*.jpg *.png *.jpeg')])
    if not path:
        return
    threading.Thread(target=processar_com_interface, args=(path,)).start()


def processar_com_interface(path):
    global zoom_ativo
    try:
        res = processar_imagem(path)
        # acumula resultados sem apagar anteriores
        resultados.append(res)
        exibir_resultados()
        bgr = res['imagem_caixas']
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        full = Image.fromarray(rgb)
        canvas_img.full_img = full
        mini = full.resize((canvas_width, canvas_height), Image.Resampling.LANCZOS)
        canvas_img.mini_img = mini
        tkmini = ImageTk.PhotoImage(mini)
        canvas_img.delete('all')
        canvas_img.create_image(0, 0, anchor='nw', image=tkmini)
        canvas_img.image = tkmini
        canvas_img.config(scrollregion=(0, 0, mini.width, mini.height))
        zoom_ativo = False
    except Exception as e:
        messagebox.showerror('Erro', str(e))


def exibir_resultados():
    texto.config(state='normal')
    texto.delete('1.0', 'end')
    # limpa frame de checkboxes antes
    for w in frame_cb.winfo_children():
        w.destroy()
    checkbox_vars.clear()
    for r in resultados:
        texto.insert('end', f"Imagem: {r['imagem']}\n")
        for m in r['resumo']:
            texto.insert('end', f"Frutos: {m['quantidade']} | média: {m['media']}cm\n")
            for i, det in enumerate(m['detalhes'], 1):
                texto.insert('end', f"  {i}: {det}\n")
        # checkbox para selecionar exportação desse resultado
        var = tk.BooleanVar(value=True)
        cb = tk.Checkbutton(frame_cb, text=r['imagem'], variable=var, bg='#EAF8DC')
        cb.pack(anchor='w')
        checkbox_vars.append((var, r))
        texto.insert('end', '-'*30 + '\n')
    texto.config(state='disabled')


def salvar_planilha():
    sel = [r for v, r in checkbox_vars if v.get()]
    if not sel:
        messagebox.showwarning('Aviso', 'Nenhum selecionado')
        return
    p = filedialog.asksaveasfilename(defaultextension='.xlsx', filetypes=[('Excel','*.xlsx')])
    if not p:
        return
    rows = []
    for r in sel:
        for m in r['resumo']:
            for i, det in enumerate(m['detalhes'], 1):
                rows.append({'Imagem': r['imagem'], 'Item': i, 'Tamanho': det[0], 'Cor': det[1], 'Média': m['media']})
    pd.DataFrame(rows).to_excel(p, index=False)
    messagebox.showinfo('Sucesso', f'Resultados salvos em: {p}')


def iniciar_pan(event):
    if zoom_ativo:
        canvas_img.scan_mark(event.x, event.y)


def mover_pan(event):
    if zoom_ativo:
        canvas_img.scan_dragto(event.x, event.y, gain=1)


def aplicar_zoom(event=None):
    global zoom_ativo
    if not hasattr(canvas_img, 'full_img'):
        return
    if not zoom_ativo:
        full = canvas_img.full_img
        tkfull = ImageTk.PhotoImage(full)
        canvas_img.delete('all')
        canvas_img.create_image(0, 0, anchor='nw', image=tkfull)
        canvas_img.image = tkfull
        scroll_y.grid()
        scroll_x.grid()
        canvas_img.config(scrollregion=(0, 0, full.width, full.height))
        zoom_ativo = True
    else:
        mini = canvas_img.mini_img
        tkmini = ImageTk.PhotoImage(mini)
        canvas_img.delete('all')
        canvas_img.create_image(0, 0, anchor='nw', image=tkmini)
        canvas_img.image = tkmini
        scroll_y.grid_remove()
        scroll_x.grid_remove()
        canvas_img.config(scrollregion=(0, 0, mini.width, mini.height))
        zoom_ativo = False

# ---------------- Inicialização GUI ----------------
root = tk.Tk()
root.title('Contador de Frutos')
root.geometry('1024x768')
root.configure(bg='#EAF8DC')
style = ttk.Style(root)
style.theme_use('clam')
style.configure('TButton', background='#6CBF4B', foreground='white', font=('Segoe UI', 10, 'bold'), padding=6)

# Botões
frame_btn = tk.Frame(root, bg='#EAF8DC')
frame_btn.pack(pady=10)
btn_sel = ttk.Button(frame_btn, text='Selecionar Imagem', command=selecionar_imagem)
btn_sel.pack(side='left', padx=10)
btn_sal = ttk.Button(frame_btn, text='Salvar Resultados', command=salvar_planilha)
btn_sal.pack(side='left', padx=10)

# Canvas de imagem (retrato)
canvas_width, canvas_height = 300, 400
frame_img = tk.Frame(root, bg='#EAF8DC')
frame_img.pack(padx=20, pady=10)
canvas_img = tk.Canvas(frame_img, bg='white', cursor='cross', width=canvas_width, height=canvas_height)
canvas_img.grid(row=0, column=0)
scroll_y = ttk.Scrollbar(frame_img, orient='vertical', command=canvas_img.yview)
scroll_x = ttk.Scrollbar(frame_img, orient='horizontal', command=canvas_img.xview)
canvas_img.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
scroll_y.grid(row=0, column=1, sticky='ns')
scroll_x.grid(row=1, column=0, sticky='ew')

# Resultados de texto
frame_txt = tk.Frame(root, bg='#EAF8DC')
frame_txt.pack(fill='x', padx=20)
texto = tk.Text(frame_txt, height=10, font=('Consolas', 9), bg='#F5FFF0')
texto.pack(side='left', fill='x', expand=True)
scroll_txt = ttk.Scrollbar(frame_txt, orient='vertical', command=texto.yview)
texto.configure(yscrollcommand=scroll_txt.set)
scroll_txt.pack(side='right', fill='y')

# ---------------- Lista de seleção com scroll ----------------
frame_cb_container = tk.LabelFrame(root, text='Selecionar imagens para exportar', bg='#EAF8DC')
frame_cb_container.pack(fill='both', expand=False, padx=20, pady=(0,20))
canvas_cb = tk.Canvas(frame_cb_container, bg='#EAF8DC', bd=0, highlightthickness=0, height=120)
scrollbar_cb = ttk.Scrollbar(frame_cb_container, orient='vertical', command=canvas_cb.yview)
frame_cb = tk.Frame(canvas_cb, bg='#EAF8DC')

frame_cb.bind('<Configure>', lambda e: canvas_cb.configure(scrollregion=canvas_cb.bbox('all')))
canvas_cb.create_window((0,0), window=frame_cb, anchor='nw')
canvas_cb.configure(yscrollcommand=scrollbar_cb.set)
canvas_cb.pack(side='left', fill='x', expand=True)
scrollbar_cb.pack(side='right', fill='y')

# Bindings de zoom/pan
canvas_img.bind('<Double-Button-1>', aplicar_zoom)
canvas_img.bind('<ButtonPress-1>', iniciar_pan)
canvas_img.bind('<B1-Motion>', mover_pan)

root.mainloop()
