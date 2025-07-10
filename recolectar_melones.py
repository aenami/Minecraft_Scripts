import time
import threading
import sys  # Importamos 'sys' para leer los argumentos de la línea de comandos
import minescript

# === CONFIGURACIÓN GLOBAL ===
PITCH_FRONTAL = 33.1
DISTANCIA_LINEA_1 = 91.55
DISTANCIA_LINEA_2 = 91
TOTAL_RESETS = 35
TOTAL_PARES = 19

# === FUNCIONES BÁSICAS DE MOVIMIENTO Y ACCIÓN ===
# Se encargan de los movimientos suaves y las acciones básicas del jugador.

def mover_pitch_suave(pitch_inicial, pitch_final, yaw_constante, pasos=30, delay=0.03):
    paso = (pitch_final - pitch_inicial) / pasos
    for i in range(pasos + 1):
        pitch_actual = pitch_inicial + paso * i
        minescript.player_set_orientation(yaw=yaw_constante, pitch=pitch_actual)
        time.sleep(delay)

def mover_yaw_suave(yaw_inicial, yaw_final, pitch_constante, pasos=30, delay=0.03):
    paso = (yaw_final - yaw_inicial) / pasos
    for i in range(pasos + 1):
        yaw_actual = yaw_inicial + paso * i
        minescript.player_set_orientation(yaw=yaw_actual, pitch=pitch_constante)
        time.sleep(delay)

def avanzar_distancia(target_distancia, direccion='forward', correr=False):
    direccion_funcion = {
        'forward': minescript.player_press_forward,
        'left': minescript.player_press_left,
        'right': minescript.player_press_right,
    }

    if not correr and direccion == 'forward':
        minescript.player_press_sprint(True)

    direccion_funcion[direccion](True)
    pos_inicial = minescript.player().position

    while True:
        pos_actual = minescript.player().position
        dx = pos_actual[0] - pos_inicial[0]
        dz = pos_actual[2] - pos_inicial[2]
        distancia = (dx**2 + dz**2)**0.5
        if distancia >= target_distancia:
            break
        time.sleep(0.05)

    direccion_funcion[direccion](False)
    if correr and direccion == 'forward':
        minescript.player_press_sprint(False)

def usar_item_slot1(tiempo=0.05):
    minescript.player_inventory_select_slot(0)
    minescript.player_press_use(True)
    time.sleep(tiempo)
    minescript.player_press_use(False)
    minescript.player_inventory_select_slot(1)

# Se reposiciona para el siguiente par
def ajustar_posicion_nuevo():
    # Movimiento a la derecha
    minescript.player_press_right(True)
    time.sleep(0.4) 
    minescript.player_press_right(False)
    time.sleep(0.1)

# === PROCESOS DE RECOLECCIÓN ===
# La lógica de recolección principal se mantiene igual.
def recolectar_par_lineas(pitch_frontal=PITCH_FRONTAL):
    minescript.player_press_attack(True)
    time.sleep(0.1)
    avanzar_distancia(DISTANCIA_LINEA_1, direccion='forward')
    minescript.player_press_attack(False)

    mover_yaw_suave(yaw_inicial=180.0, yaw_final=-0.0, pitch_constante=pitch_frontal)
     # Movimiento a la Izquierda
    minescript.player_press_left(True)
    time.sleep(0.3) # Aumentar un mili segundo mas-
    minescript.player_press_left(False)
    time.sleep(0.1)

    minescript.player_press_attack(True)
    time.sleep(0.1)
    avanzar_distancia(DISTANCIA_LINEA_2, direccion='forward')
    minescript.player_press_attack(False)

# === WATCHDOG (VERIFICADOR DE MOVIMIENTO) - VERSIÓN CORREGIDA ===
def verificador_movimiento(intervalo=6, tolerancia=0.3, intentos_fallidos=3):
    """
    Este hilo se ejecuta en segundo plano para monitorear si el jugador se ha atascado.
    Si no hay movimiento significativo durante un tiempo, reinicia el proceso.
    """
    fallos = 0
    pos_anterior = minescript.player().position

    while True:
        time.sleep(intervalo)
        pos_actual = minescript.player().position
        dx = abs(pos_actual[0] - pos_anterior[0])
        dz = abs(pos_actual[2] - pos_anterior[2])
        distancia = (dx**2 + dz**2)**0.5

        if distancia < tolerancia:
            fallos += 1
            minescript.echo(f"⚠️ Jugador sin movimiento detectado. Intento #{fallos}/{intentos_fallidos}")
            if fallos >= intentos_fallidos:
                # --- INICIO DE LA LÓGICA DE REINICIO CORREGIDA ---

                # 1. Obtener el ID del job actual (el que se ha atascado).
                # Usamos job_info() que devuelve una lista de jobs.
                # El job con el atributo 'self' en True es el nuestro.
                job_info_list = minescript.job_info()
                current_job_id = None
                for job in job_info_list:
                    if job.self:
                        current_job_id = job.job_id
                        break
                
                if current_job_id is not None:
                    minescript.echo(f"🚨 Atasco detectado. Reiniciando desde el Job ID: {current_job_id}")
                    
                    # Detener cualquier movimiento para evitar más problemas.
                    minescript.player_press_forward(False)
                    minescript.player_press_attack(False)
                    minescript.player_press_left(False)
                    minescript.player_press_right(False)
                    minescript.player_press_sprint(False)

                    # Regresar al punto de inicio.
                    minescript.execute("/warp garden")
                    time.sleep(4.5) # Esperar a que el teletransporte se complete.
                    
                    # 2. Ejecutar una NUEVA instancia del script, pasándole el ID del job actual
                    # como un argumento de línea de comandos. La nueva instancia se encargará de matar a esta.
                    minescript.echo(f"Lanzando nueva instancia y pasándole el Job ID {current_job_id} para eliminar...")
                    minescript.execute(f"\\recolectar_melones {current_job_id}")

                else:
                    # Esto solo ocurriría en un caso muy raro.
                    minescript.echo("🚨 Error crítico: No se pudo obtener el ID del job actual para reiniciar.")
                
                # 3. Terminar el hilo del watchdog. El script principal también terminará,
                # ya que la nueva instancia lo matará pronto.
                return
                # --- FIN DE LA LÓGICA DE REINICIO CORREGIDA ---
        else:
            # Si hubo movimiento, se resetea el contador de fallos.
            fallos = 0

        pos_anterior = pos_actual

# === FLUJO PRINCIPAL DE RECOLECCIÓN ===
def iniciar_recoleccion():
    """
    Contiene el bucle principal que realiza toda la secuencia de recolección.
    Se ha simplificado para eliminar la lógica de reinicio recursiva.
    """
    for reset in range(1, TOTAL_RESETS + 1):
        minescript.echo(f"🌱 Recolección número {reset}")

        for i in range(TOTAL_PARES):
            par_actual = i + 1
            minescript.echo(f"  → Recolectando par #{par_actual}")

            if par_actual % 2 == 0 or par_actual == 1:
                usar_item_slot1()

            recolectar_par_lineas(pitch_frontal=PITCH_FRONTAL)

            # Saltar el bloque de obsidiana
            minescript.player_press_jump(True)
            time.sleep(0.2)
            minescript.player_press_jump(False)
            minescript.player_press_forward(True)
            time.sleep(0.3)
            minescript.player_press_forward(False)

            if par_actual < TOTAL_PARES:
                mover_yaw_suave(yaw_inicial=-0.0, yaw_final=180.0, pitch_constante=PITCH_FRONTAL)
                # Posicionarse en el siguiente par de crops a farmear
                ajustar_posicion_nuevo()

        minescript.echo("✅ ¡Recolección completa de 19 pares!")

        # Logica para reiniciar el recorrido
        # Detener cualquier movimiento para evitar más problemas.
        minescript.player_press_forward(False)
        minescript.player_press_attack(False)
        minescript.player_press_sprint(False)
        time.sleep(0.5)
        minescript.execute(f"/warp garden")
        time.sleep(1.5)

        # Mover la camara del jugador
        estado_inicial = minescript.player()
        yaw_actual = estado_inicial.yaw
        pitch_actual = estado_inicial.pitch

        # Ajustar la vista del jugador a la posición inicial.
        mover_pitch_suave(pitch_actual, PITCH_FRONTAL, yaw_actual)
        mover_yaw_suave(yaw_actual, 180.0, PITCH_FRONTAL)

# === FUNCIÓN PRINCIPAL (MAIN) - VERSIÓN CORREGIDA ===
def main():
    """
    Punto de entrada del script.
    Ahora incluye la lógica para matar la instancia anterior si es necesario.
    """
    # --- LÓGICA PARA MATAR LA INSTANCIA ANTERIOR ---
    # sys.argv es una lista que contiene los argumentos pasados al script.
    # sys.argv[0] es siempre el nombre del script.
    # Si hay más de 1 argumento, significa que se nos pasó un ID de job para matar.
    if len(sys.argv) > 1:
        try:
            job_id_to_kill = sys.argv[1]
            minescript.echo(f"Esta es una nueva instancia. Intentando eliminar el job anterior (ID: {job_id_to_kill})...")
            # Damos un pequeño respiro para asegurar que el comando de ejecución
            # del script viejo se haya completado antes de matarlo.
            time.sleep(1)
            minescript.execute(f"\\killjob {job_id_to_kill}")
            minescript.echo(f"✅ Instancia anterior (Job ID: {job_id_to_kill}) eliminada con éxito.")
        except Exception as e:
            minescript.echo(f"🚨 No se pudo eliminar el job anterior. Error: {e}")
    # --- FIN DE LA LÓGICA DE ELIMINACIÓN ---

    # El resto del flujo de inicio es el mismo.
    minescript.echo("🚀 Iniciando script de recolección de melones...")
    estado_inicial = minescript.player()
    yaw_actual = estado_inicial.yaw
    pitch_actual = estado_inicial.pitch

    # Ajustar la vista del jugador a la posición inicial.
    mover_pitch_suave(pitch_actual, PITCH_FRONTAL, yaw_actual)
    mover_yaw_suave(yaw_actual, 180.0, PITCH_FRONTAL)

    # Iniciar el watchdog en un hilo separado.
    threading.Thread(target=verificador_movimiento, daemon=True).start()
    
    # Iniciar la recolección.
    iniciar_recoleccion()
    
    minescript.echo("✅ Script finalizado con éxito.")

# --- Punto de entrada para ejecutar el script ---
if __name__ == "__main__":
    main()
