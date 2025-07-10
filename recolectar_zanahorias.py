import time
import threading
import sys  # Se importa 'sys' para leer los argumentos de la línea de comandos
import minescript

# === CONFIGURACIÓN GLOBAL ===
# Distancia a recorrer lateralmente para farmear las hileras.
DISTANCIA_HILERA = 92.6 
# Distancia a avanzar para reposicionarse en las parcelas de 8 hileras.
DISTANCIA_REPOSICION = 8.25
# Cantidad de parcelas de 8 hileras que hay que farmear.
CANTIDAD_PARCELAS_GRANDES = 9
# Pitch (ángulo vertical) constante para mantener la vista del jugador.
PITCH_CONSTANTE = 6.0 # Un valor razonable para mirar ligeramente hacia abajo.

# === FUNCIONES BÁSICAS DE MOVIMIENTO Y ACCIÓN ===
# Estas funciones se reutilizan del script anterior para un control preciso.

def mover_yaw_suave(yaw_inicial, yaw_final, pitch_constante, pasos=30, delay=0.02):
    """Gira la cámara del jugador (yaw) de forma fluida."""
    paso = (yaw_final - yaw_inicial) / pasos
    for i in range(pasos + 1):
        yaw_actual = yaw_inicial + paso * i
        minescript.player_set_orientation(yaw=yaw_actual, pitch=pitch_constante)
        time.sleep(delay)

def mover_pitch_suave(pitch_inicial, pitch_final, yaw_constante, pasos=30, delay=0.03):
    paso = (pitch_final - pitch_inicial) / pasos
    for i in range(pasos + 1):
        pitch_actual = pitch_inicial + paso * i
        minescript.player_set_orientation(yaw=yaw_constante, pitch=pitch_actual)
        time.sleep(delay)

def mover_distancia(distancia_objetivo, direccion='forward'):
    """Mueve al jugador una distancia específica en una dirección cardinal."""
    mapa_direccion = {
        'forward': minescript.player_press_forward,
        'left': minescript.player_press_left,
        'right': minescript.player_press_right,
    }
    mapa_direccion[direccion](True)
    pos_inicial = minescript.player().position
    while True:
        pos_actual = minescript.player().position
        dx = pos_actual[0] - pos_inicial[0]
        dz = pos_actual[2] - pos_inicial[2]
        distancia_recorrida = (dx**2 + dz**2)**0.5
        if distancia_recorrida >= distancia_objetivo:
            break
        time.sleep(0.05)
    mapa_direccion[direccion](False)

# === LÓGICA DE RECOLECCIÓN POR TIPO DE PARCELA ===

def recolectar_parcela_4_hileras():
    """Ejecuta la secuencia para recolectar una parcela de 4 hileras."""
    minescript.echo("  -> Recolectando parcela de 4 hileras...")
    minescript.player_press_attack(True)
    mover_distancia(DISTANCIA_HILERA, direccion='right')
    minescript.player_press_attack(False)

def recolectar_parcela_8_hileras():
    """Ejecuta la secuencia completa para una parcela de 8 hileras."""
    minescript.echo("  -> Recolectando parcela de 8 hileras...")
    
    # Primera mitad (4 hileras)
    minescript.player_press_attack(True)
    mover_distancia(DISTANCIA_HILERA, direccion='right')
    minescript.player_press_attack(False)

    # Reposicionamiento para la segunda mitad
    minescript.echo("    - Reposicionando para las siguientes 4 hileras...")
    minescript.player_press_jump(True)
    minescript.player_press_forward(True)
    time.sleep(0.5)
    minescript.player_press_jump(False)
    minescript.player_press_forward(False)
    
    mover_distancia(DISTANCIA_REPOSICION, direccion='forward')
    
    yaw_actual = minescript.player().yaw
    mover_yaw_suave(yaw_actual, yaw_actual + 180, PITCH_CONSTANTE)

    # Alinearse con el bloque
    minescript.player_press_forward(True)
    time.sleep(0.3)
    minescript.player_press_forward(False)

    # Segunda mitad (las 4 hileras restantes)
    minescript.player_press_attack(True)
    mover_distancia(DISTANCIA_HILERA, direccion='right')
    minescript.player_press_attack(False)

def transicion_entre_parcelas():
    """Gira 180 grados para encarar la siguiente parcela."""
    minescript.echo("  -> Girando para la siguiente parcela...")
    yaw_actual = minescript.player().yaw
    mover_yaw_suave(yaw_actual, yaw_actual + 180, PITCH_CONSTANTE)

# === WATCHDOG (VERIFICADOR DE MOVIMIENTO) ===
# Esta sección es idéntica a la versión corregida anterior, garantizando robustez.
def verificador_movimiento(intervalo=6, tolerancia=0.3, intentos_maximos=3):
    """Este hilo se ejecuta en segundo plano para monitorear si el jugador se ha atascado."""
    intentos_fallidos = 0
    pos_anterior = minescript.player().position
    while True:
        time.sleep(intervalo)
        pos_actual = minescript.player().position
        distancia = ((pos_actual[0] - pos_anterior[0])**2 + (pos_actual[2] - pos_anterior[2])**2)**0.5

        if distancia < tolerancia:
            intentos_fallidos += 1
            minescript.echo(f"⚠️ Jugador sin movimiento. Intento #{intentos_fallidos}/{intentos_maximos}")
            if intentos_fallidos >= intentos_maximos:
                job_info_list = minescript.job_info()
                current_job_id = next((job.job_id for job in job_info_list if job.self), None)
                
                if current_job_id:
                    minescript.echo(f"🚨 Atasco detectado. Reiniciando desde el Job ID: {current_job_id}")
                    for press_func in [minescript.player_press_forward, minescript.player_press_attack, minescript.player_press_left, minescript.player_press_right, minescript.player_press_sprint]:
                        press_func(False)
                    
                    minescript.execute("/warp garden")
                    time.sleep(4.5)
                    
                    # El nombre del script debe coincidir con el nombre del archivo guardado.
                    # Asumiendo que se llama 'recolectar_zanahorias.py'
                    minescript.echo(f"Lanzando nueva instancia y pasando Job ID {current_job_id} para eliminar...")
                    minescript.execute(f"\\recolectar_zanahorias {current_job_id}")
                else:
                    minescript.echo("🚨 Error crítico: No se pudo obtener el ID del job actual para reiniciar.")
                return
        else:
            intentos_fallidos = 0
        pos_anterior = pos_actual

# === FLUJO PRINCIPAL DE RECOLECCIÓN ===
def flujo_principal_recoleccion():
    """Contiene el bucle principal que realiza toda la secuencia de recolección."""
    while True: # Bucle infinito para que el farmeo sea continuo.
        minescript.echo("🌱 Iniciando nuevo ciclo completo de recolección.")
        
        # 1. Primera parcela de 4 hileras
        recolectar_parcela_4_hileras()
        transicion_entre_parcelas()

        # Alineación para la primera parcela grande
        minescript.player_press_forward(True)
        time.sleep(0.3)
        minescript.player_press_forward(False)

        # 2. Bucle para las 9 parcelas de 8 hileras
        for i in range(CANTIDAD_PARCELAS_GRANDES):
            minescript.echo(f"🌿 Recolectando parcela grande #{i + 1}/{CANTIDAD_PARCELAS_GRANDES}")
            recolectar_parcela_8_hileras()
            # No girar en la última parcela grande, ya que la secuencia para la pequeña es diferente
            if i < CANTIDAD_PARCELAS_GRANDES - 1:
                transicion_entre_parcelas()

        # 3. Última parcela de 4 hileras
        # Se necesita una transición especial aquí después de la última parcela de 8.
        transicion_entre_parcelas()
        recolectar_parcela_4_hileras()

        # 4. Reinicio del ciclo
        minescript.echo("✅ Ciclo completo terminado. Reiniciando en el warp...")
        minescript.execute("/warp garden")
        time.sleep(3) # Tiempo de espera para la carga del warp.
        
        # Reorientar la cámara para el inicio del siguiente ciclo.
        yaw_actual = minescript.player().yaw
        estado_inicial = minescript.player()
        yaw_actual = estado_inicial.yaw
        pitch_actual = estado_inicial.pitch

        # Ajustar la vista del jugador a la posición inicial.
        mover_pitch_suave(pitch_actual, PITCH_CONSTANTE, yaw_actual)
        mover_yaw_suave(yaw_actual, -90.0, PITCH_CONSTANTE)

# === FUNCIÓN PRINCIPAL (MAIN) ===
def main():
    """Punto de entrada del script y gestión del reinicio por watchdog."""
    # Lógica para matar la instancia anterior si es necesario.
    if len(sys.argv) > 1:
        try:
            job_id_to_kill = sys.argv[1]
            minescript.echo(f"Nueva instancia. Eliminando job anterior (ID: {job_id_to_kill})...")
            time.sleep(1)
            minescript.execute(f"\\killjob {job_id_to_kill}")
            minescript.echo(f"✅ Instancia anterior (ID: {job_id_to_kill}) eliminada.")
        except Exception as e:
            minescript.echo(f"🚨 No se pudo eliminar el job anterior. Error: {e}")

    minescript.echo("🚀 Iniciando script de recolección de zanahorias...")
    
    # Ajustar la vista inicial del jugador
    estado_inicial = minescript.player()
    yaw_actual = estado_inicial.yaw
    pitch_actual = estado_inicial.pitch

    # Ajustar la vista del jugador a la posición inicial.
    mover_pitch_suave(pitch_actual, PITCH_CONSTANTE, yaw_actual)
    mover_yaw_suave(yaw_actual, -90.0, PITCH_CONSTANTE)

    # Iniciar el watchdog en un hilo separado.
    threading.Thread(target=verificador_movimiento, daemon=True).start()
    
    # Iniciar la recolección.
    flujo_principal_recoleccion()
    
    minescript.echo("✅ Script finalizado.")

# --- Punto de entrada para ejecutar el script ---
if __name__ == "__main__":
    main()