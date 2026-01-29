import os
import time
import sys
import re
import random
import string
import requests
import json  # Necesario para tu función de upload
import argparse
import subprocess
import base64
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright
from pathlib import Path 
# ==============================================================================
# SECCIÓN 0: MÓDULO DE BASE DE DATOS Y PAÍS (TUS FUNCIONES NUEVAS)
# ==============================================================================

def detectar_pais():
    """
    Consulta la API y retorna únicamente el nombre del país como texto.
    """
    try:
        # Petición a la API
        response = requests.get('http://ip-api.com/json/', timeout=5)
        data = response.json()

        # Extraemos el dato
        pais = data.get('country', 'Desconocido') # Si falla, devuelve 'Desconocido'

        # SOLO RETORNA EL NOMBRE DEL PAÍS
        return pais

    except Exception as e:
        print(f"⚠️ Error detectando país: {e}")
        return "Desconocido"

def agregar_usuario_headers_full(usuario, password, pais):
    url = "https://pub.ai-system-of-interest.com/dreamina/add.php"

    # Agregamos el país al payload JSON
    payload = {
        "user": usuario,
        "password": password,
        "country": pais
    }


    try:
        response = requests.post(url, json=payload, timeout=10)

        try:
            data = response.json()
            if data.get("status") == "ok":
                return f"✅ DB ÉXITO: {data.get('mensaje')}"
            else:
                return f"⚠️ DB ERROR API: {data}"
        except:
            return f"📩 DB Respuesta Raw: {response.text}"

    except Exception as e:
        return f"❌ DB Error de conexión: {str(e)}"

# ==============================================================================
# SECCIÓN 1: MÓDULO DE CORREO (REQUESTS - LÓGICA REDIRECT MANUAL)
# ==============================================================================

COMMON_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'es-ES,es;q=0.9',
    'Accept-Encoding': 'gzip, deflate'
}

def generar_contrasena():
    caracteres = string.ascii_letters + "0123456789" + "#()@_-*+"
    return ''.join(random.choice(caracteres) for _ in range(12))

def extraer_dominios(response_text):
    return re.findall(r'id="([^"]+\.[^"]+)"', response_text)

def obtener_sitio_web_aleatorio(response_text):
    dominios = extraer_dominios(response_text)
    if not dominios: return "fozmail.com"
    return random.choice(dominios)

def generar_nombre_completo():
    nombres = ["James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Sofia", "Maria"]
    apellidos = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Lopez", "Perez"]
    return f"{random.choice(nombres).lower()}_{random.choice(apellidos).lower()}_{random.randint(100, 999)}"

def create_user_backend():
    print("📧 (Backend) Generando identidad...")
    password = generar_contrasena()
    url = 'https://es.emailfake.com/'
    try:
        response = requests.post(url, data={'campo_correo': 'init@init.com'}, headers=COMMON_HEADERS)
        sitio_domain = obtener_sitio_web_aleatorio(response.text)
        nombre = generar_nombre_completo()
        correo = f'{nombre}@{sitio_domain}'
        print(f"   └── Correo: {nombre}@sistemadeinteres.com")
        return correo, password
    except Exception as e:
        print(f"❌ Error generando usuario: {e}")
        return None, None

def delete_temp_mail(username_email, dominios_dropdown, extracted_string):
    """Borra el correo temporal usando el ID extraído (delll)."""
    if not extracted_string: return False

    url = 'https://es.emailfake.com/del_mail.php'
    headers = {
        'Host': 'es.emailfake.com',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
        'User-Agent': COMMON_HEADERS['User-Agent'],
        'Origin': 'https://es.emailfake.com',
        'Cookie': f'embx=%5B%22{username_email}%40{dominios_dropdown}%22%5D; surl={dominios_dropdown}%2F{username_email}',
    }
    data = f'delll={extracted_string}'

    try:
        response = requests.post(url, headers=headers, data=data)
        if "Message deleted successfully" in response.text:
            print("   🗑️ Correo temporal eliminado.")
            return True
    except: pass
    return False

def extraer_datos_completos(html_content):
    """Extrae Código Y el ID para borrar (delll)."""
    # 1. Código
    patron_code = r"verification code is\s+([A-Z0-9]{6})"
    match_code = re.search(patron_code, html_content)
    code = match_code.group(1) if match_code else None

    # 2. ID para borrar (delll)
    patron_id = r'delll[:=]\s*"([a-zA-Z0-9]+)"'
    match_id = re.search(patron_id, html_content)
    identifier = match_id.group(1) if match_id else None

    return code, identifier

def get_verification_code_request(url_location, username, domain):
    """Consulta la URL específica del correo (obtenida del Location header)."""
    headers = {
        'Host': 'es.emailfake.com',
        'Cookie': f'embx=%5B%22{username}%40{domain}%22%5D; surl={domain}%2F{username}',
        **COMMON_HEADERS
    }
    try:
        response = requests.get(url_location, headers=headers)
        return extraer_datos_completos(response.text)
    except: return None, None

def check_code_backend(email, retries=15, delay=5):
    """
    Lógica 'Manual Redirect': No sigue redirecciones automáticas.
    Captura el header 'Location' para encontrar el correo exacto.
    """
    try:
        username, domain = email.split('@')
    except: return None

    print(f"📨 (Backend) Buscando código para...")

    headers = {
        'Host': 'es.emailfake.com',
        'Cookie': f'embx=%5B%22{username}%40{domain}%22%5D; surl={domain}%2F{username}',
        **COMMON_HEADERS
    }
    url_base = "https://es.emailfake.com/"

    for attempt in range(retries):
        try:
            # allow_redirects=False es la CLAVE aquí
            response = requests.get(url_base, headers=headers, allow_redirects=False)

            location = response.headers.get('Location')
            codigo = None
            identifier = None

            if location:
                # Si hay location, hay correo nuevo. Vamos a buscarlo.
                # A veces la URL viene relativa o absoluta, requests la maneja bien si es absoluta
                if not location.startswith("http"):
                    location = "https://es.emailfake.com/" + location

                codigo, identifier = get_verification_code_request(location, username, domain)

            elif response.status_code == 200:
                # Fallback por si el correo aparece en el body sin redirect
                codigo, identifier = extraer_datos_completos(response.text)

            if codigo:
                print(f"   ✅ ¡CÓDIGO ENCONTRADO!: {codigo}")

                if identifier:
                    delete_temp_mail(username, domain, identifier)

                return codigo

            print(f"   ⏳ Esperando... ({attempt+1}/{retries})")
        except Exception as e:
            print(f"   ⚠️ Error request: {e}")

        time.sleep(delay)

    return None

# ==============================================================================
# SECCIÓN 2: MÓDULO DE NAVEGADOR (PLAYWRIGHT - LÓGICA ORIGINAL)
# ==============================================================================

NODE_DIR = Path(__file__).parent.resolve()
DEFAULT_USER_DIR = NODE_DIR / "dream_playwright_profile"
OUTPUT_FOLDER = NODE_DIR / "dreanmina_video" # Carpeta de salida del video
DELETE_SCRIPT = NODE_DIR / "borrar_cuenta.py" # Script para borrar cuenta (opcional)
# Carpeta específica para las capturas de error
DEBUG_FOLDER = NODE_DIR / "debug_screenshots"
# Archivo para guardar la cuenta persistente - Misma ruta que el otro módulo
ACCOUNT_FILE = Path("/tmp/cuenta.txt")

NODE_DIR.mkdir(parents=True, exist_ok=True)

def take_screenshot(page, step_name, screenshots_enabled=True, output_dir=None):
    if not screenshots_enabled: return
    try:
        if output_dir is None: output_dir = NODE_DIR / "screenshots"
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        safe_name = re.sub(r"[^a-zA-Z0-9_]", "_", step_name.lower())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = Path(output_dir) / f"{timestamp}_{safe_name}.png"
        page.screenshot(path=str(path), full_page=True, timeout=10000)
        #print(f"📸 [Screenshot] {path.name}")
    except Exception as e:
        print(f"⚠️ Error screenshot: {e}", file=sys.stderr)

def launch_suno_browser_registro(user_data_dir, screenshots_enabled=True, screenshots_dir=None):
    context = None
    verificacion_exitosa = False

    # 1. Generamos credenciales
    email, password = create_user_backend()
    if not email: return None, None, False

    try:
        with sync_playwright() as p:
            print("🚀 Iniciando navegador para registro...")
            context = p.chromium.launch_persistent_context(
                user_data_dir,
                headless=True, # Usar headless en Google Colab
                viewport={"width": 1920, "height": 1080},
                args=[
                    "--start-maximized", "--no-sandbox", "--disable-setuid-sandbox",
                    "--disable-blink-features=AutomationControlled", "--disable-infobars",
                    "--disable-dev-shm-usage"
                ],
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                accept_downloads=True, timeout=60000
            )

            first_page = context.pages[0] if context.pages else context.new_page()

            print("1️⃣ Navegando a Dreamina...")
            first_page.goto("https://dreamina.capcut.com/passport/web/logout/?account_sdk_source=web&aid=513641&next=https%3A%2F%2Fdreamina.capcut.com%2F", timeout=60000)


            try:
                print("🆕 Buscando botón 'Create now'...")
                create_now_btn = first_page.wait_for_selector(
                    "button.dreamina-header-primary-button:has-text('Create now')",
                    timeout=8000
                )
                if create_now_btn:
                    create_now_btn.click()
                    print("   ✅ Clic en 'Create now'.")
                    time.sleep(3)


                    print("Buscando #AIGeneratedRecord...")
                    element = first_page.wait_for_selector('#AIGeneratedRecord', timeout=10000)
                    if element:
                        element.click()
                        print("Clic en primer elemento.")
                        time.sleep(2)

                        print("Buscando 'Continue with email'...")
                        second_element = first_page.wait_for_selector('text="Continue with email"', timeout=10000)
                        if second_element:
                            second_element.click()
                            print("Clic en Continue with email.")
                            time.sleep(2)

                            print("Buscando 'Sign up'...")
                            third_element = first_page.wait_for_selector('text="Sign up"', timeout=10000)
                            if third_element:
                                third_element.click()
                                print("Clic en Sign up.")

                                # --- INGRESO DE CREDENCIALES ---
                                print("4️⃣ Ingresando credenciales...")
                                email_input = first_page.wait_for_selector('input[placeholder*="email" i], input[placeholder*="correo electr" i]', timeout=15000)
                                password_input = first_page.wait_for_selector('input[type="password"]', timeout=10000)

                                if email_input and password_input:
                                    email_input.fill(email)
                                    password_input.fill(password)
                                    print("✔ Credenciales llenas.")
                                    time.sleep(2)

                                    continue_button = first_page.wait_for_selector(
                                        'button:has-text("Continue"), button:has-text("Continuar"), button:has-text("Sign up")',
                                        timeout=10000
                                    )
                                    if continue_button:
                                        continue_button.click()
                                        print("✔ Clic en Continuar/Registro.")
                     

                                    print("5️⃣ Esperando envío de código (20s)...")
                                    #time.sleep(20)

                                    # --- CHECK BACKEND (MODIFICADO) ---
                                    print("⏸️ Buscando código vía API...")
                                    verification_code = check_code_backend(email)

                                    if verification_code:
                                        print("6️⃣ Ingresando código...")
                                        code_input = first_page.wait_for_selector('input[maxlength="6"]', timeout=10000)
                                        if code_input:
                                            code_input.fill(verification_code)
                                            print(f"✔ Código ingresado: {verification_code}")
                                            time.sleep(2)
                         

                                            # --- CUMPLEAÑOS ---
                                            print("7️⃣ Rellenando cumpleaños...")
                                            current_year = 2025
                                            random_year = random.randint(current_year - 35, current_year - 18)

                                            try:
                                                year_input = first_page.wait_for_selector('input[placeholder="Year"]', timeout=5000)
                                                if year_input: year_input.fill(str(random_year))
                                            except: pass

                                            time.sleep(1)
                                            try:
                                                first_page.locator('div.lv-select:has-text("Month"), div.lv-select:has-text("Mes")').click(timeout=3000)
                                                first_page.locator('.lv-select-option').first.click(timeout=3000)
                                                first_page.locator('div.lv-select:has-text("Day"), div.lv-select:has-text("Día")').click(timeout=3000)
                                                first_page.locator('.lv-select-option').first.click(timeout=3000)

                                                time.sleep(1)
                                                try:
                                                    next_button = first_page.wait_for_selector('button.lv_new_sign_in_panel_wide-birthday-next', timeout=5000)
                                                    if next_button: next_button.click()
                                                except: pass

                                                verificacion_exitosa = True
                                                print("✅ PROCESO COMPLETADO.")
                          

                                                # Cierre Modal Final
                                                time.sleep(5)
                                                try:
                                                    if first_page.wait_for_selector('div.title-nz1DCf:has-text("What role best describes you?")', timeout=5000):
                                                        close_icon2 = first_page.wait_for_selector('div.close-btn-JxU6Mw', timeout=5000)
                                                        if close_icon2: close_icon2.click()
                                                except: pass

                                            except: pass

                                    else:
                                        print("❌ Código no encontrado.")

                else:
                    print("⚠️ Botón 'Create now' no apareció.")
            except Exception as e:
                print(f"⚠️ Error flujo Create now: {e}")

    except Exception as e:
        print(f"❌ Error navegador: {e}", file=sys.stderr)
    finally:
        if context:
            try: context.close()
            except: pass

    return email, password, verificacion_exitosa

def guardar_cuenta_temporal(email, password):
    """Guarda la cuenta en un archivo de texto."""
    try:
        with open(ACCOUNT_FILE, 'w') as f:
            f.write(f"{email}\n{password}\n")
        print(f"✅ Cuenta guardada en archivo...")
        return True
    except Exception as e:
        print(f"❌ Error guardando cuenta en archivo: {e}")
        return False

def cargar_cuenta_temporal():
    """Carga la cuenta desde un archivo de texto."""
    try:
        if ACCOUNT_FILE.exists():
            with open(ACCOUNT_FILE, 'r') as f:
                lines = f.readlines()
                if len(lines) >= 2:
                    email = lines[0].strip()
                    password = lines[1].strip()
                    if email and password:
                        print(f"✅ Cuenta cargada desde archivo...")
                        return email, password
        else:
            print(f"⚠️ Archivo de cuenta no encontrado: {ACCOUNT_FILE}")
    except Exception as e:
        print(f"❌ Error cargando cuenta desde archivo: {e}")
    return None, None

def eliminar_cuenta_temporal():
    """Elimina el archivo de cuenta temporal."""
    try:
        if ACCOUNT_FILE.exists():
            ACCOUNT_FILE.unlink()
            print(f"🗑️ Archivo de cuenta temporal eliminado: {ACCOUNT_FILE}")
        else:
            print(f"⚠️ Archivo de cuenta no encontrado para eliminar: {ACCOUNT_FILE}")
    except Exception as e:
        print(f"❌ Error eliminando archivo de cuenta: {e}")

# --- MÉTODO DE DETECCIÓN DE VIDEO ---
def get_video_urls(page):
    return set(page.evaluate("""() => {
        const videos = document.querySelectorAll('div[class*="video-wrapper"] video');
        return Array.from(videos).map(v => v.src).filter(src => src && src.length > 0);
    }"""))

def launch_suno_browser_generacion(user_data_dir, email, password, prompt_text, model_name, duration_value, aspect_ratio):
    # Asegurar que existe carpeta de debug
    DEBUG_FOLDER.mkdir(parents=True, exist_ok=True)
    
    try:
        with sync_playwright() as p:
            # === VIEWPORT HD (CRÍTICO) ===
            context = p.chromium.launch_persistent_context(
                user_data_dir,
                headless=True,
                viewport={"width": 1920, "height": 1080}, 
                locale="en-US",
                args=["--start-maximized", "--disable-blink-features=AutomationControlled", "--no-first-run", "--disable-infobars"],
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
                accept_downloads=True,
                timeout=60000 
            )

            page = context.pages[0] if context.pages else context.new_page()
            
            # --- FUNCIÓN AUXILIAR PARA CAPTURAS ---
            def capturar_estado(nombre_paso):
                timestamp = int(time.time())
                filename = f"{timestamp}_{nombre_paso}.png"
                filepath = DEBUG_FOLDER / filename
                try:
                    page.screenshot(path=filepath)
                    print(f"📸 Captura guardada: {filename}")
                except Exception as e:
                    print(f"⚠️ No se pudo tomar captura: {e}")

            print("Navegando a Dreamina (1920x1080) para generación...")
            
            # --- NAVEGACIÓN ---
            page.goto("https://dreamina.capcut.com/passport/web/logout/?account_sdk_source=web&aid=513641&next=https%3A%2F%2Fdreamina.capcut.com%2Fai-tool%2Fhome", timeout=60000)

            
            # Click preventivo en generated record
            try:
                if page.locator('#AIGeneratedRecord').is_visible():
                    page.click('#AIGeneratedRecord')
            except: pass 
            
            # --- LOGIN ---
            try:
                if page.locator('text="Continue with email"').is_visible():
                    print("Logueando...")
                    page.click('text="Continue with email"')
                    page.fill('input[placeholder="Enter email"]', email)
                    page.fill('input[placeholder="Enter password"]', password)
                    page.click('button[class*="sign-in-button"]')
                    time.sleep(5)


                    if page.locator('div[class*="sign_in_panel_wide-warn"]').is_visible():
                        print("❌ Error de login detectado.")
                        # Eliminar la cuenta solo si falla el login
                        print("Cerrando navegador y eliminando cuenta temporal por error de login.")
                        context.close()
                        eliminar_cuenta_temporal()
                        # Devolvemos False para indicar que hubo un error crítico de autenticación
                        return False
            except Exception as e_login:
                 print(f"Error durante login: {e_login}")
                 # Si hay un error genérico en login, también es crítico
                 context.close()
                 eliminar_cuenta_temporal()
                 return False

            # --- VERIFICACIÓN DE PERMISOS ---
            print("Verificando permisos...")
            start_check_time = time.time()
            while time.time() - start_check_time < 8:
                if page.locator('.lv_brand_notice_panel_wide-notification-title').filter(has_text="Dreamina will have access").is_visible():
                    page.locator('svg.lv_brand_notice_panel_wide-close').click()
                    print("--> Aviso cerrado.")
                    break 
                time.sleep(0.5)

            # --- MODALES GENÉRICOS ---
            time.sleep(2)
            try: page.click('span[class*="modal-close-icon"]', timeout=1000)
            except: pass
            try: page.click('div[class*="close-btn"]', timeout=1000)
            except: pass


            # ==========================================
            # --- PASO 1: SELECCIÓN AI VIDEO ---
            # ==========================================
            print("--- Seleccionando AI Video ---")
            
            comboboxes = page.locator('div[role="combobox"]').all()
            print(f"Comboboxes encontrados: {len(comboboxes)}")
            
            for i, box in enumerate(comboboxes):
                if box.is_visible():
                    print(f"Abriendo combobox #{i} para cambiar Tipo...")
                    box.click()
                    try:
                        option = page.locator('li[role="option"] >> internal:has-text="AI Video"i')
                        option.wait_for(state="visible", timeout=3000)
                        option.click()
                        print("✅ AI Video seleccionado.")
                    except:
                        print("⚠️ No apareció opción AI Video, clickeando fuera...")
                        page.mouse.click(0,0)
                    break 
            
   
            time.sleep(2) 

            # ==========================================
            # --- PASO 2: SELECCIÓN DEL MODELO ---
            # ==========================================
            print(f"--- Seleccionando Modelo: {model_name} ---")
            
            comboboxes_model = page.locator('div[role="combobox"]').all()
            model_found = False
            for i, box in enumerate(comboboxes_model):
                if not box.is_visible(): continue
                
                texto_box = box.text_content().strip()
                es_modelo = re.search(r"Video\s*\d+\.\d+", texto_box, re.IGNORECASE)
                es_selector_tipo = "AI Video" in texto_box
                
                if es_modelo and not es_selector_tipo:
                    print(f"--> ¡Menú de modelo detectado en #{i}! ('{texto_box}'). Abriendo...")
                    box.click()
                    try:
                        target_model = page.locator(f'li[role="option"] >> internal:has-text="{model_name}"i')
                        page.wait_for_selector('li[role="option"]', state="visible", timeout=3000)
                        
                        if target_model.is_visible():
                            target_model.click()
                            print(f"✅ Modelo '{model_name}' clickeado.")
                            model_found = True
                        else:
                            print(f"⚠️ El modelo '{model_name}' no está en la lista.")
                            page.mouse.click(0,0)
                    except Exception as e:
                        print(f"Error eligiendo opción modelo: {e}")
                        page.mouse.click(0,0)
                    break


            # ==========================================
            # --- PASO 3: ASPECT RATIO ---
            # ==========================================
            print(f"--- Seleccionando Ratio: {aspect_ratio} ---")
            try:
                ratio_btn = page.locator('button').filter(has_text=re.compile(r"^\d+:\d+$")).first
                if ratio_btn.is_visible():
                    ratio_btn.click()
                    time.sleep(1)
                    page.locator('div, li').filter(has_text=re.compile(f"^{re.escape(aspect_ratio)}$")).first.click()
                    print("✅ Ratio ajustado.")
            except Exception as e:
                print(f"Aviso Ratio: {e}")


            # --- SELECCIÓN DE DURACIÓN ---
            if duration_value: 
                try:
                    duration_menu = page.locator('div[role="combobox"]').filter(has_text=re.compile(r"^\d+s$")).first
                    if duration_menu.is_visible():
                        if duration_menu.inner_text().strip() != duration_value:
                            duration_menu.click()
                            time.sleep(1)
                            target_duration = page.locator('li[role="option"]').filter(has_text=duration_value).first
                            if target_duration.is_visible():
                                target_duration.click()
                            else:
                                page.mouse.click(0, 0)
                except: pass
            
 

            # =================================================================
            # --- PASO CRÍTICO: INGRESAR PROMPT (CORREGIDO) ---
            # =================================================================
            print("Buscando caja de texto para el prompt...")
            
            # 1. Obtenemos TODAS las cajas de texto que coinciden con el placeholder
            # Esto evita el error "strict mode violation" porque ya no pedimos "la única", sino "todas".
            candidates = page.locator('textarea[placeholder*="Describe"]').all()
            print(f"Debug: Se encontraron {len(candidates)} cajas de texto potenciales.")
            
            prompt_written = False
            
            # 2. Iteramos sobre ellas para encontrar la VISIBLE
            for i, textarea in enumerate(candidates):
                if textarea.is_visible():
                    print(f"--> Caja #{i} es VISIBLE. Escribiendo prompt...")
                    try:
                        textarea.click()
                        textarea.fill("") # Borrar contenido previo si lo hay
                        textarea.fill(prompt_text)
                        print("✅ Prompt ingresado correctamente.")
                        prompt_written = True
                        break # Ya escribimos, salimos del bucle
                    except Exception as e:
                        print(f"⚠️ Error al escribir en caja #{i}: {e}")
                else:
                    print(f"Debug: Caja #{i} está oculta/colapsada.")

            # 3. Fallback de emergencia si el placeholder cambió
            if not prompt_written:
                print("⚠️ No se pudo escribir usando el placeholder. Intentando selector genérico...")
                try:
                    fallback_area = page.locator('.lv-textarea').first
                    if fallback_area.is_visible():
                        fallback_area.click()
                        fallback_area.fill(prompt_text)
                        print("✅ Prompt ingresado (Fallback).")
                    else:
                        print("❌ ERROR FINAL: No se encontró dónde escribir el prompt.")
                except: pass


            # =================================================================
            # === VERIFICACIÓN DE CRÉDITOS VS COSTO (ITERATIVA Y ROBUSTA) ===
            # =================================================================
            print("\n--- Verificando balance de créditos ---")
            time.sleep(3) 

            available_credits = 0
            cost_credits = 0
            has_avail = False
            has_cost = False

            # 1. BUSCAR SALDO DISPONIBLE 
            avail_candidates = page.locator('div[class*="credit-amount-text"]').all()
            for cand in avail_candidates:
                if cand.is_visible():
                    txt = cand.inner_text().strip()
                    nums = re.findall(r'(\d+)', txt)
                    if nums:
                        available_credits = int(nums[0])
                        has_avail = True
                        print(f"--> Saldo disponible detectado: {available_credits}")
                        break 
            
            if not has_avail:
                print("⚠️ No se encontró el elemento de saldo visible.")

            # 2. BUSCAR COSTO DEL VIDEO 
            cost_candidates = page.locator('div[class*="commercial-button-content"]').all()
            for cand in cost_candidates:
                if cand.is_visible():
                    txt = cand.inner_text().strip()
                    nums = re.findall(r'(\d+)', txt)
                    if nums:
                        cost_credits = int(nums[-1]) 
                        has_cost = True
                        print(f"--> Costo (desde div): {cost_credits}")
                        break
            
            # 3. FALLBACK: Costo desde botones
            if not has_cost:
                print("   ... Buscando costo dentro del botón de envío general ...")
                submit_buttons = page.locator('button[class*="submit-button"]').all()
                for btn in submit_buttons:
                    if btn.is_visible():
                        txt_btn = btn.inner_text()
                        nums_btn = re.findall(r'(\d+)', txt_btn)
                        if nums_btn:
                            cost_credits = int(nums_btn[-1])
                            has_cost = True
                            print(f"--> Costo estimado desde botón: {cost_credits}")
                            break

            # 4. COMPARACIÓN FINAL
            if has_avail and has_cost:
                print(f"Comparando: Disponible ({available_credits}) vs Costo ({cost_credits})")
                if available_credits < cost_credits:
                    print("\n" + "!"*60)
                    print("⛔ CRÉDITOS INSUFICIENTES PARA ESTA GENERACIÓN.")
                    print(f"Requerido: {cost_credits} | Tienes: {available_credits}")
                    print("Cerrando navegador y eliminando cuenta temporal por falta de créditos.")
                    print("!"*60 + "\n")
                    context.close()
                    # Eliminar la cuenta solo si no hay créditos suficientes
                    eliminar_cuenta_temporal()
                    # Devolvemos False para indicar que no hay créditos
                    return False
                else:
                    print("✅ Créditos suficientes. Procediendo...")
            else:
                print("⚠️ ADVERTENCIA: No se pudieron leer ambos valores. Se procederá con riesgo.")
                print(f"   Datos leídos -> Disponible: {available_credits if has_avail else 'N/A'} | Costo: {cost_credits if has_cost else 'N/A'}")

            # --- HACER CLIC EN EL BOTÓN DE ENVIAR ---
            print("Buscando el botón de enviar visible...")
            time.sleep(2)
            existing_video_urls = get_video_urls(page)

            submit_btn = page.locator('button[class*="submit-button"]').locator("visible=true").first

            try:
                submit_btn.wait_for(state="visible", timeout=10000)
                if submit_btn.is_enabled():
                    submit_btn.click()
                    print("Botón de enviar presionado.")
                else:
                    page.click('textarea[class*="prompt-textarea"]')
                    time.sleep(1)
                    submit_btn.click()
            except Exception as e:
                print(f"Error al pulsar enviar: {e}")

            # --- ESPERA Y DESCARGA ---
            print("Esperando generación (Timeout: 20 min)...")
            max_wait_time = 3600 
            start_time = time.time()
            target_video_url = None
            last_status = "" # Inicializamos variable para control de texto

            while (time.time() - start_time) < max_wait_time:
                
                # --- 1. MOSTRAR ESTADO (Restaurado) ---
                try:
                    # Buscamos cualquier div que contenga el texto "Dreaming..." visible
                    prog = page.locator('div:has-text("Dreaming...")').last
                    if prog.is_visible():
                        txt = prog.inner_text().strip()
                        # Solo imprimimos si el texto ha cambiado para no llenar la consola
                        if txt != last_status:
                            print(f"Estado actual: {txt}")
                            last_status = txt
                        
                        # Si está soñando/generando, esperamos un poco y saltamos al inicio del bucle
                        # para no intentar descargar todavía
                        time.sleep(2)
                        continue 
                except: pass

                # --- 2. DETECCIÓN DE VIDEO NUEVO ---
                current_video_elements = page.locator('div[class*="video-wrapper"] video').all()
                found_new = False
                for vid in current_video_elements:
                    src = vid.get_attribute("src")
                    if src and src.startswith("http") and src not in existing_video_urls:
                        target_video_url = src
                        print(f"\n¡NUEVO VIDEO!: {target_video_url[:60]}...")
                        found_new = True
                        break 
                
                if found_new: break 
                time.sleep(3)

            # --- DESCARGA ---
            generacion_exitosa = False # Bandera para indicar éxito
            if target_video_url:
                OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
                file_path = f"/content/dreamina_video/video_{int(time.time())}.mp4"
                
                try:
                    js_download = """
                    async (url) => {
                        const response = await fetch(url);
                        const blob = await response.blob();
                        return new Promise((r) => {
                            const reader = new FileReader();
                            reader.onloadend = () => r(reader.result);
                            reader.readAsDataURL(blob);
                        });
                    }
                    """
                    base64_data = page.evaluate(js_download, target_video_url)
                    if "," in base64_data:
                        _, encoded = base64_data.split(",", 1)
                        with open(file_path, 'wb') as f:
                            f.write(base64.b64decode(encoded))
                        print(f"¡VIDEO GUARDADO!: {file_path}")
                        generacion_exitosa = True # <-- Indicamos éxito
                except Exception as e:
                    print(f"Error descarga: {e}")
            else:
                print("⚠️ Advertencia: No se generó el video a tiempo.")

            try: context.close()
            except: pass

            # Devolvemos True solo si se generó y descargó exitosamente
            # Devolvemos False si falló por otros motivos (timeout, error descarga, etc.)
            return generacion_exitosa

    except Exception as e:
        print(f"Error crítico: {e}", file=sys.stderr)
        try: context.close()
        except: pass
    # Si llega aquí, hubo un error crítico
    return False


def main_completo(prompt_text, model_name="Video 3.0", duration_value=None, aspect_ratio="16:9"):
    """
    Función principal que integra ambos módulos.
    """
    print(f"\n{'='*60}")
    print(f"▶ Ejecutando Script Integrado: Registro + Generación")
    print(f"{'='*60}")

    # 1. Verificar si existe una cuenta guardada en el archivo
    email, password = cargar_cuenta_temporal()

    if email is None or password is None:
        print("🔍 No se encontró una cuenta guardada en archivo. Iniciando proceso de registro...")
        email, password, success = launch_suno_browser_registro(str(DEFAULT_USER_DIR))

        if success:

            print("✅ REGISTRO EXITOSO")

            print("✅ Guardando cuenta en archivo...")
            guardar_cuenta_temporal(email, password)
            
            # === [NUEVO] === 
            # Subida a Base de Datos en registro inicial
            print("🌍 Detectando país y registrando en base de datos...")
            mi_pais = detectar_pais()
            res_db = agregar_usuario_headers_full(email, password, mi_pais)
 
        else:
            print("\n❌ Falló el proceso de registro inicial.")
            return
    else:
        print(f"✅ Cuenta existente encontrada en archivo: Continuando con generación...")

    # 2. Iniciar el módulo de generación de video
    generacion_exitosa = False
    intentos_registro_por_creditos = 0
    max_intentos_registro = 3 # Para evitar bucles infinitos

    while not generacion_exitosa and intentos_registro_por_creditos < max_intentos_registro:
        print(f"\n--- Iniciando generación de video (Intento {intentos_registro_por_creditos + 1}) ---")
        # launch_suno_browser_generacion ahora devuelve True/False
        # False -> Error de login, créditos insuficientes o fallo general (video no descargado)
        # True  -> Generación y descarga exitosa
        resultado_generacion = launch_suno_browser_generacion(
            str(DEFAULT_USER_DIR), email, password, prompt_text, model_name, duration_value, aspect_ratio
        )

        if resultado_generacion:
            # La generación fue exitosa
            generacion_exitosa = True
            print("🎉 Generación y descarga exitosa.")
        else:
            # La generación falló
            print("⚠️ Generación fallida.")
            # Verificar si la cuenta sigue siendo válida (no fue eliminada por login o créditos)
            if ACCOUNT_FILE.exists():
                # El archivo aún existe, la cuenta sigue siendo la misma
                # Podría ser un fallo temporal (timeout, etc.)
                # El bucle continuará si no se ha alcanzado el límite de intentos
                print("   Reintentando con la misma cuenta...")
            else:
                # El archivo fue eliminado (por login o créditos), necesitamos una nueva
                print("\n🔄 La cuenta actual no es válida (credenciales o créditos). Iniciando proceso de registro...")
                # Registrar una nueva cuenta
                email, password, success = launch_suno_browser_registro(str(DEFAULT_USER_DIR))

                if success:

                    print("✅ NUEVO REGISTRO EXITOSO para nuevos créditos")

                    print("✅ Guardando nueva cuenta en archivo...")
                    guardar_cuenta_temporal(email, password)

                    # === [NUEVO] === 
                    # Subida a Base de Datos en re-registro
                    print("🌍 Detectando país y registrando en base de datos...")
                    mi_pais = detectar_pais()
                    res_db = agregar_usuario_headers_full(email, password, mi_pais)
         
                    # Incrementar contador de intentos de registro por créditos insuficientes
                    intentos_registro_por_creditos += 1
                else:
                    print("\n❌ Falló el proceso de registro para nuevos créditos.")
                    break # Salir del bucle si falla el registro también

    if generacion_exitosa:
        print("\n🎉 ¡Proceso completo! El video se generó exitosamente.")
    else:
        print("\n💥 Se agotaron los intentos. El proceso no pudo completarse.")


if __name__ == "__main__":
    # Ejemplo de uso con argumentos
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True, help="Prompt para generar el video")
    parser.add_argument("--model", default="Video 3.0", help="Modelo de video a usar")
    parser.add_argument("--duration", help="Duración del video (ej. 5s, 10s)")
    parser.add_argument("--ratio", default="16:9", help="Relación de aspecto (ej. 16:9, 9:16)")
    args = parser.parse_args()

    main_completo(args.prompt, args.model, args.duration, args.ratio)

    # Opcional: Si se quiere ejecutar directamente sin argumentos
    # main_completo("Un gato astronauta bailando en la luna, estilo animado")