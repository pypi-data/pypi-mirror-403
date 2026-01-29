import gradio as gr
import time
import subprocess
import sys
import os
import glob
import requests
import shutil
import zipfile
from IPython.display import display, Markdown

# Intentamos importar los módulos
try:
    from dt2v import *
    from di2v import *
    from di22v import *
except ImportError:
    pass

# ==========================================
# 0. DEFINIR RUTA BASE Y SALIDA
# ==========================================
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = "/content/dreamina_video" # Directorio de trabajo

# Crear directorio si no existe
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==========================================
# 1. CONFIGURACIÓN Y DATOS
# ==========================================

RATIOS_VISUAL = {
    "21:9": "21:9 ▬",
    "16:9": "16:9 ▭",
    "4:3":  "4:3 ▤",
    "1:1":  "1:1 ■",
    "3:4":  "3:4 ▥",
    "9:16": "9:16 ▯"
}

MODEL_SPECS = {
    "Video 3.5 Pro": {
        "durations": ["5s", "10s", "12s"],
        "ratios": list(RATIOS_VISUAL.values())
    },
    "Video 3.0 Fast": {
        "durations": ["5s", "10s"],
        "ratios": list(RATIOS_VISUAL.values())
    },
    "Sora 2": {
        "durations": ["4s", "8s"],
        "ratios": [RATIOS_VISUAL["16:9"], RATIOS_VISUAL["9:16"]]
    },
    "Veo 3": {
        "durations": ["8s"],
        "ratios": [RATIOS_VISUAL["16:9"], RATIOS_VISUAL["9:16"]]
    },
    "Video 3.0": {
        "durations": ["5s", "10s"],
        "ratios": list(RATIOS_VISUAL.values())
    },
    "Video S2.0 Pro": {
        "durations": ["5s"],
        "ratios": list(RATIOS_VISUAL.values())
    }
}

# ==========================================
# 2. VALIDACIÓN DE ACCESO (PAÍS)
# ==========================================

def obtener_bandera_emoji(codigo_pais):
    if not codigo_pais: return ""
    return "".join([chr(ord(c) + 127397) for c in codigo_pais.upper()])

def obtener_modelos_permitidos():
    paises_permitidos = [
        "Australia", "Austria", "Belgium", "Brazil", "China", "Finland",
        "France", "Germany", "Hong Kong", "Indonesia", "Israel", "Italy",
        "Japan", "Malaysia", "Netherlands", "Poland", "Portugal",
        "Saudi Arabia", "Singapore", "Spain", "Sweden", "Switzerland",
        "Taiwan", "Thailand", "Turkey", "United Arab Emirates",
        "United Kingdom", "United States", "Vietnam", "Argentina"
    ]

    try:
        response = requests.get('http://ip-api.com/json/', timeout=5)
        data = response.json()
        pais = data.get('country')
        codigo = data.get('countryCode')
        ip = data.get('query')
        bandera = obtener_bandera_emoji(codigo)

        if pais not in paises_permitidos:
            display(Markdown(f"### ⚠️ ACCESO DETECTADO\n> **País:** {pais} {bandera}\n> Habilitando modelos básicos."))
            return list(MODEL_SPECS.keys())

        if pais == "United States":
            display(Markdown(f"### ✅ ACCESO RESTRINGIDO (USA)\n> **País:** {pais} {bandera}\n> **IP:** `{ip}`\n> **Modelos:** Limitados."))
            return ["Video 3.5 Pro", "Video 3.0"]

        display(Markdown(f"### ✅ ACCESO TOTAL\n> **País:** {pais} {bandera}\n> **IP:** `{ip}`\n> **Modelos:** Todos desbloqueados."))
        return list(MODEL_SPECS.keys())

    except Exception as e:
        print(f"Error validando IP: {e}")
        return list(MODEL_SPECS.keys())

# --- EJECUCIÓN DE VALIDACIÓN ---
model_list = obtener_modelos_permitidos()
if not model_list:
    model_list = list(MODEL_SPECS.keys())

initial_model = model_list[0]
initial_ratios = MODEL_SPECS[initial_model]["ratios"]
initial_durations = MODEL_SPECS[initial_model]["durations"]

# ==========================================
# 3. CSS FUTURISTA & ESTILO TARJETAS
# ==========================================
futuristic_css = """
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Roboto+Mono&display=swap');

:root {
    --neon-cyan: #00f3ff;
    --neon-pink: #ff00ff;
    --dark-bg: #0a0a0f;
    --panel-bg: rgba(20, 20, 35, 0.95);
    --card-bg: #151520;
}

.gradio-container {
    background-color: var(--dark-bg) !important;
    background-image: radial-gradient(circle at 50% 50%, #1a1a2e 0%, #000000 100%);
    font-family: 'Orbitron', sans-serif !important;
    color: var(--neon-cyan) !important;
}

#main-title h1 {
    text-transform: uppercase;
    letter-spacing: 3px;
    text-shadow: 0 0 10px var(--neon-cyan);
    text-align: center;
}

.dark-panel, .tabs, .tabitem {
    background-color: var(--panel-bg) !important;
    border: 1px solid #333;
    border-radius: 8px !important;
}

textarea, input[type="text"], .gr-dropdown {
    background-color: rgba(0,0,0,0.6) !important;
    border: 1px solid #444 !important;
    color: var(--neon-cyan) !important;
    font-family: 'Roboto Mono', monospace !important;
}

.ratio-group {
    display: flex !important;
    flex-wrap: wrap !important;
    gap: 8px !important;
}
.ratio-group .wrap { background: transparent !important; border: none !important; }
.ratio-group input[type="radio"] { display: none !important; }
.ratio-group label {
    background: var(--card-bg) !important;
    border: 1px solid #444 !important;
    border-radius: 10px !important;
    padding: 8px 12px !important;
    text-align: center !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    min-width: 70px !important;
    box-shadow: 0 4px 6px rgba(0,0,0,0.4) !important;
}
.ratio-group label:hover { border-color: var(--neon-cyan) !important; background: #202030 !important; }
.ratio-group label.selected {
    background: rgba(0, 243, 255, 0.15) !important;
    border: 1px solid var(--neon-cyan) !important;
    color: white !important;
    box-shadow: 0 0 10px rgba(0, 243, 255, 0.3) !important;
}
.ratio-group span { font-family: 'Roboto Mono', monospace !important; font-size: 0.85rem !important; }

.generate-btn {
    background: linear-gradient(90deg, var(--neon-cyan), #0055ff) !important;
    border: none !important;
    color: black !important;
    font-weight: 900 !important;
    text-transform: uppercase;
    letter-spacing: 2px;
    box-shadow: 0 0 15px var(--neon-cyan);
}
.generate-btn:hover { transform: scale(1.02); }

.merge-btn {
    background: linear-gradient(90deg, #ff00ff, #ff5500) !important;
    color: white !important;
    font-weight: 900 !important;
    text-transform: uppercase;
    letter-spacing: 2px;
    border: 1px solid white !important;
    box-shadow: 0 0 15px var(--neon-pink);
}
.merge-btn:hover { transform: scale(1.02); }

.log-box textarea {
    background-color: #050505 !important;
    border: 1px solid var(--neon-pink) !important;
    color: var(--neon-pink) !important;
    font-family: 'Roboto Mono', monospace !important;
    font-size: 0.8rem !important;
}
"""

# ==========================================
# 4. BACKEND & EXECUTION
# ==========================================

def monitor_process(command, log_buffer, scene_index=None):
    my_env = os.environ.copy()
    my_env["PYTHONIOENCODING"] = "utf-8"

    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1, universal_newlines=True, env=my_env,
        cwd=BASE_PATH
    )

    while True:
        line = process.stdout.readline()
        if not line and process.poll() is not None: break
        if line:
            log_buffer += line
            yield log_buffer, None

    # Espera breve para asegurar escritura en disco
    time.sleep(2)

    list_of_files = glob.glob(os.path.join(OUTPUT_DIR, "*.mp4"))
    
    # Lógica para encontrar el video recién creado y renombrarlo si es una escena numerada
    final_video = None
    if list_of_files:
        latest_file = max(list_of_files, key=os.path.getctime)
        final_video = latest_file

        if scene_index is not None and final_video:
            new_name = os.path.join(OUTPUT_DIR, f"scene_{scene_index}.mp4")
            
            # Si ya existe un archivo con ese nombre (de un intento anterior), lo borramos
            if os.path.exists(new_name) and os.path.abspath(latest_file) != os.path.abspath(new_name):
                os.remove(new_name)
            
            # Renombrar solo si no es el mismo archivo
            if os.path.abspath(latest_file) != os.path.abspath(new_name):
                shutil.move(latest_file, new_name)
                final_video = new_name
                log_buffer += f"\n> 🏷️ RENOMBRADO A: scene_{scene_index}.mp4"

    if final_video:
        log_buffer += f"\n> ✅ VIDEO GENERADO: {os.path.basename(final_video)}"
    else:
        log_buffer += "\n> ❌ ERROR: No se generó el video."

    yield log_buffer, final_video

def limpiar_ratio(ratio_visual):
    if not ratio_visual: return "16:9"
    return ratio_visual.split(" ")[0]

# --- FUNCIONES WRAPPER ---

def ejecutar_txt(prompt, model, ratio_vis, duration):
    ratio = limpiar_ratio(ratio_vis)
    log = f"> TXT-2-VIDEO\n> MODELO: {model}\n> RATIO: {ratio}\n> DURACIÓN: {duration}\n"
    yield None, log
    
    script_path = os.path.join(BASE_PATH, "dt2v.py")
    if not os.path.exists(script_path):
        yield None, f"{log}\n❌ Error crítico: No se encuentra {script_path}"
        return

    cmd = [sys.executable, "-u", script_path, "--prompt", prompt, "--model", model, "--ratio", ratio, "--duration", duration]
    for l, v in monitor_process(cmd, log): yield v, l

def ejecutar_img(prompt, model, duration, img):
    if not img: yield None, "> Error: Faltan imágenes."; return
    log = f"> IMG-2-VIDEO\n> MODELO: {model}\n> DURACIÓN: {duration}\n"
    yield None, log
    
    script_path = os.path.join(BASE_PATH, "di2v.py")
    if not os.path.exists(script_path):
        yield None, f"{log}\n❌ Error crítico: No se encuentra {script_path}"
        return

    cmd = [sys.executable, "-u", script_path, "--prompt", prompt, "--model", model, "--duration", duration, "--image", img]
    for l, v in monitor_process(cmd, log): yield v, l

# --- NUEVA FUNCIÓN: ESCENA INDIVIDUAL DUAL MORPH ---
def ejecutar_escena_dual(index, model, duration, img1, img2, prompt):
    if not img1 or not img2:
        return None, f"❌ Error en Escena {index}: Faltan imágenes de Inicio o Fin."

    log = f"> DUAL MORPH - ESCENA {index}\n> MODELO: {model}\n> DURACIÓN: {duration}\n"
    yield None, log

    script_path = os.path.join(BASE_PATH, "di22v.py")
    if not os.path.exists(script_path):
        yield None, f"{log}\n❌ Error crítico: No se encuentra {script_path}"
        return

    p_text = prompt if prompt and str(prompt).strip() != "" else "animate smoothly"
    
    cmd = [sys.executable, "-u", script_path, "--prompt", p_text, "--model", model, "--duration", duration, "--image", img1, "--image_end", img2]
    
    # Pasamos 'index' para que monitor_process renombre el archivo a scene_{index}.mp4
    for l, v in monitor_process(cmd, log, scene_index=index):
        yield v, l

# --- NUEVA FUNCIÓN: UNIR ESCENAS Y ZIP ---
def unir_escenas():
    log = "🔍 BUSCANDO ESCENAS GENERADAS (scene_1 a scene_6)...\n"
    yield None, None, log

    files_to_concat = []
    
    # Buscar escenas en orden 1 a 6
    for i in range(1, 7):
        path = os.path.join(OUTPUT_DIR, f"scene_{i}.mp4")
        if os.path.exists(path):
            files_to_concat.append(path)
            log += f"> Encontrada: Escena {i}\n"
    
    if len(files_to_concat) < 1:
        log += "❌ No se encontraron escenas válidas para unir."
        yield None, None, log
        return

    # Crear lista para ffmpeg
    list_path = os.path.join(OUTPUT_DIR, "concat_list.txt")
    with open(list_path, "w") as f:
        for file_path in files_to_concat:
            # Formato seguro para ffmpeg
            f.write(f"file '{file_path}'\n")
    
    output_merged = os.path.join(OUTPUT_DIR, "final_merged_movie.mp4")
    if os.path.exists(output_merged): os.remove(output_merged)

    log += f"> Uniendo {len(files_to_concat)} clips...\n"
    yield None, None, log

    # Comando FFmpeg concat
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", 
        "-i", list_path, "-c", "copy", output_merged
    ]
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.wait()
    
    if os.path.exists(output_merged):
        log += "✅ FUSIÓN COMPLETADA: final_merged_movie.mp4\n"
    else:
        log += "❌ Error crítico al unir videos con FFmpeg.\n"
        yield None, None, log
        return

    # --- COMPRIMIR EN ZIP ---
    log += "> Generando archivo ZIP descargable...\n"
    zip_path = os.path.join(OUTPUT_DIR, "pack_completo.zip")
    
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        # Agregar video final
        zipf.write(output_merged, os.path.basename(output_merged))
        # Agregar escenas individuales
        for file in files_to_concat:
            zipf.write(file, os.path.basename(file))
            
    log += f"✅ ZIP LISTO: {os.path.basename(zip_path)}\n"
    
    yield output_merged, zip_path, log

def update_ui(model_name):
    specs = MODEL_SPECS.get(model_name, MODEL_SPECS[initial_model])
    return (
        gr.update(choices=specs["ratios"], value=specs["ratios"][0]),
        gr.update(choices=specs["durations"], value=specs["durations"][0])
    )

# ==========================================
# 5. INTERFAZ GRADIO
# ==========================================

theme = gr.themes.Monochrome(
    primary_hue="cyan", neutral_hue="slate", radius_size=gr.themes.sizes.radius_none
)

with gr.Blocks(theme=theme, css=futuristic_css, title="Dreamina - Sora 2 - Veo 3") as demo:

    with gr.Row(elem_id="main-title"):
        gr.HTML(
        '''
        <div style="text-align: center; padding: 20px; background-color: #202030; border-radius: 10px;">
            <h1 style="font-size: 2.5em; color: #00B5FF; margin: 0;">⚡ Dreamina - Sora 2 - Veo 3 // GENERATOR ⚡</h1>
            <p style="font-size: 1em; color: #E0E0E0; margin: 10px 0;">
                Created by: <a href="https://www.youtube.com/@IA.Sistema.de.Interes" target="_blank" style="color: #00B5FF; text-decoration: none;">IA(Sistema de Interés)</a>
            </p>
        </div>
        '''
    )

    with gr.Row():
        # --- SIDEBAR CONFIG ---
        with gr.Column(scale=1, elem_classes="dark-panel"):
            gr.Markdown("### // CONFIG //", elem_classes="section-header")

            dd_model = gr.Dropdown(
                choices=model_list, value=initial_model,
                label="Neural Core (Model)", interactive=True
            )

            rb_ratio = gr.Radio(
                choices=initial_ratios, value=initial_ratios[0],
                label="Aspect Ratio", elem_classes="ratio-group"
            )

            rb_duration = gr.Radio(
                choices=initial_durations, value=initial_durations[0],
                label="Duration", elem_classes="ratio-group"
            )

            gr.Markdown("---")
            gr.Markdown("<div style='text-align: center; color: var(--neon-pink)'>SYSTEM ONLINE</div>")

        # --- MAIN TABS ---
        with gr.Column(scale=3):
            with gr.Tabs(elem_classes="dark-panel"):

                # Tab 1: Texto
                with gr.TabItem("TXT 2 VID"):
                    t1_p = gr.Textbox(label="Prompt", lines=2, placeholder="Describe tu video...")
                    t1_btn = gr.Button("► GENERAR VIDEO", elem_classes="generate-btn")
                    with gr.Row():
                        t1_vid = gr.Video(label="Resultado", interactive=False)
                        t1_log = gr.Textbox(label="System Log", lines=10, elem_classes="log-box")
                    t1_btn.click(ejecutar_txt, inputs=[t1_p, dd_model, rb_ratio, rb_duration], outputs=[t1_vid, t1_log])

                # Tab 2: Imagen
                with gr.TabItem("IMG 2 VID"):
                    with gr.Row():
                        t2_img = gr.Image(label="Input Image", type="filepath", height=200)
                        t2_p = gr.Textbox(label="Motion Prompt", lines=4)
                    t2_btn = gr.Button("► ANIMAR IMAGEN", elem_classes="generate-btn")
                    with gr.Row():
                        t2_vid = gr.Video(label="Resultado")
                        t2_log = gr.Textbox(label="System Log", lines=10, elem_classes="log-box")
                    t2_btn.click(ejecutar_img, inputs=[t2_p, dd_model, rb_duration, t2_img], outputs=[t2_vid, t2_log])

                # Tab 3: Dual Morph (Multi-Scene)
                with gr.TabItem("DUAL MORPH (SCENES)"):
                    gr.Markdown("#### Genera cada escena individualmente. Al finalizar, usa el botón 'UNIR' para fusionar.")
                    
                    # --- LOOP PARA CREAR 6 ESCENAS ---
                    for i in range(1, 7):
                        with gr.Accordion(f"🎬 SCENE {i}", open=(i==1)): # Solo la primera abierta
                            with gr.Row():
                                with gr.Column(scale=1):
                                    s_img1 = gr.Image(label="Start Frame", type="filepath", height=120)
                                    s_img2 = gr.Image(label="End Frame", type="filepath", height=120)
                                with gr.Column(scale=2):
                                    s_prompt = gr.Textbox(label="Transition Prompt", lines=2)
                                    s_btn = gr.Button(f"► GENERAR ESCENA {i}", elem_classes="generate-btn")
                                with gr.Column(scale=2):
                                    s_vid = gr.Video(label=f"Resultado {i}")
                                    s_log = gr.Textbox(label="Log", lines=4, elem_classes="log-box")
                            
                            # Componente oculto para pasar el índice fijo 'i' a la función
                            idx_hidden = gr.Number(value=i, visible=False)
                            
                            s_btn.click(
                                ejecutar_escena_dual, 
                                inputs=[idx_hidden, dd_model, rb_duration, s_img1, s_img2, s_prompt], 
                                outputs=[s_vid, s_log]
                            )

                    gr.Markdown("---")
                    
                    # --- ZONA DE FUSIÓN (MERGE) ---
                    with gr.Row(elem_classes="dark-panel"):
                        with gr.Column(scale=1, min_width=200):
                            btn_merge = gr.Button("✨ UNIR TODAS & DESCARGAR ZIP ✨", elem_classes="merge-btn")
                        with gr.Column(scale=3):
                            out_merged = gr.Video(label="Película Completa")
                            out_zip = gr.File(label="Descargar Pack (ZIP)")
                            log_merge = gr.Textbox(label="Log Fusión", lines=4, elem_classes="log-box")
                    
                    btn_merge.click(unir_escenas, inputs=None, outputs=[out_merged, out_zip, log_merge])

    dd_model.change(fn=update_ui, inputs=dd_model, outputs=[rb_ratio, rb_duration])

demo.queue().launch(share=True, debug=True)