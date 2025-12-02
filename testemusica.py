#!/usr/bin/env python3

import random
import threading
import os
from time import sleep, time
from ev3dev2.motor import (SpeedPercent, MoveTank, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C)
from ev3dev2.sensor.lego import ColorSensor, UltrasonicSensor, GyroSensor
from ev3dev2.sensor import INPUT_1, INPUT_2, INPUT_4
from ev3dev2.sound import Sound





# --- Constantes de Comportamento ---
OBSTACLE_STOP_DISTANCE_CM = 8
# Distância para parar à frente do inimigo
OBJECT_SEARCH_DISTANCE_CM = 40     # Distância para considerar "inimigo encontrado"
LINE_COLOR_NAME = 'Red'            # Cor da linha a seguir até ao inimigo

# --- Constantes de Afinação ---
SPIN_SEARCH_SPEED = 15             # Velocidade de rotação durante a procura da linha  
SEARCH_TIME_LEFT_S = 0.5           # Duração da procura para a esquerda
SEARCH_TIME_RIGHT_S = 3.0          # Duração da procura para a direita

enemies = [None] * 6

INIMIGO_STATS = {
    "Tanque": {
        "cor": "Green",
        "forca": 200,
        "num_ataques": 2,
        "vida_max": 200,
    },
    "Artilharia": {
        "cor": "Yellow",
        "forca": 500,
        "num_ataques": 1,
        "vida_max": 50,
    },
    "Infantaria": {
        "cor": "Blue",
        "forca": 100,
        "num_ataques": 3,
        "vida_max": 100,
    }
}

class Inimigo:
    def __init__(self, tipo):
        """
        Cria um inimigo com base no tipo (ex: 'Tanque', 'Infantaria').
        Se o tipo não existir, levanta um erro.
        """
        if tipo not in INIMIGO_STATS:
            raise ValueError("Tipo de inimigo desconhecido: {}".format(tipo))
        
        # Carregar estatísticas do dicionário
        stats = INIMIGO_STATS[tipo]
        
        self.tipo = tipo
        self.cor = stats['cor']
        self.forca = stats['forca']
        self.num_ataques = stats['num_ataques']
        self.vida_max = stats['vida_max']
        
        # A vida atual começa cheia
        self.vida_atual = self.vida_max

    def receber_dano(self, dano):
        """
        Reduz a vida do inimigo. Retorna True se morreu, False se continua vivo.
        """
        self.vida_atual -= dano
        if self.vida_atual < 0:
            self.vida_atual = 0
        
        print("{} (Cor: {}) sofreu {} de dano. Vida restante: {}/{}".format(
            self.tipo, self.cor, dano, self.vida_atual, self.vida_max
        ))
        
        return self.vida_atual == 0

    def esta_vivo(self):
        """Retorna True se a vida for maior que 0."""
        return self.vida_atual > 0

    def curar(self):
        """Restaura a vida ao máximo."""
        self.vida_atual = self.vida_max
        print("{} foi reparado/curado completamente.".format(self.tipo))

    def __str__(self):
        """Representação completa do objeto em texto."""
        status = "VIVO" if self.esta_vivo() else "DESTRUIDO"
        
        # Agora inclui Forca e Num_Ataques
        return "[Tipo: {} | Cor: {} | Vida: {}/{} | Forca: {} | Atqs: {} | Status: {}]".format(
            self.tipo, 
            self.cor, 
            self.vida_atual, 
            self.vida_max, 
            self.forca,       # Adicionado
            self.num_ataques, # Adicionado
            status
        )


def inicializar_inimigos_por_cor(lista_cores):
    """
    Recebe: ['Empty', 'Green', 'Empty', ...]
    Retorna: [None, Objeto(Tanque), None, ...]
    """
    lista_objetos_inimigos = []

    print("--- A processar deteccoes ---")

    for i, cor in enumerate(lista_cores):
        if cor == "Empty":
            # Se o slot estiver vazio, guardamos None (ou "Empty")
            lista_objetos_inimigos.append(None) 
        else:
            # Precisamos descobrir qual o INIMIGO que tem esta cor
            tipo_encontrado = None
            
            # Procura no dicionário qual a chave (Tipo) que tem esta cor
            for tipo, stats in INIMIGO_STATS.items():
                if stats['cor'] == cor:
                    tipo_encontrado = tipo
                    break
            
            if tipo_encontrado:
                # Cria o objeto Inimigo
                novo_inimigo = Inimigo(tipo_encontrado)
                lista_objetos_inimigos.append(novo_inimigo)
                print("Slot {}: Criado {} (Cor: {})".format(i+1, tipo_encontrado, cor))
            else:
                # Caso detete uma cor que não está no dicionário (ex: Red)
                print("Slot {}: Cor '{}' desconhecida. Ignorado.".format(i+1, cor))
                lista_objetos_inimigos.append(None)

    return lista_objetos_inimigos


def rolar_dado_digital():
    return random.randint(1, 6)

def imprimir_setup_inicial():
    """
    Rola os dados para 6 slots e imprime uma tabela com os resultados.
    Esta função é para demonstração e não afeta o estado do jogo.
    """
    print("=" * 60)
    # Usamos .format() aqui para alinhar o texto
    print("{:<10} | {:<18} | {:<20}".format("Posicao", "Tipo de atacante", "Turno inicial (1-6)"))
    print("=" * 60)
    
    for i in range(1, 7):
        dado_tipo = rolar_dado_digital()
        dado_turno = rolar_dado_digital()
    
        if dado_tipo <= 2:
            unidade = "Tanque"
        elif dado_tipo <= 4:
            unidade = "Artilharia"
        else:
            unidade = "Infantaria"
    
        # Substituimos o f"{variavel}" por "{}".format(variavel)
        print("Slot{:<4} | {:<18} | {:<20}".format(i, unidade, dado_turno))
    
    print("=" * 60)



# FUNÇÕES DE ATAQUES

# Função para tocar ficheiro WAV (ataque de som)
def play_wav(file_path, volume=100):
    # print("a tocar som") # Comentado para não poluir o log
    try:
        speaker = Sound()
        speaker.set_volume(volume)
        speaker.play_file(file_path)
    except:
        pass

# Função para realizar um ataque por toque
def perform_touch_attack(tank_pair):
    print(">>> INICIAR ATAQUE DE TOQUE <<<")
    
    # 1. Investida: Avança 100% de velocidade
    tank_pair.on_for_rotations(SpeedPercent(-55), SpeedPercent(-55), 0.2)
    sleep(0.2)
    # 2. Recuo: Volta para trás a mesma distância
    tank_pair.on_for_rotations(SpeedPercent(55), SpeedPercent(55), 0.2)
    print(">>> Ataque de toque concluido. <<<")




 # Função para atacar com a grua
    # Gira até encontra a linha vermelha novamente (aprox. 180 graus)
    # Ativa o motor (grua)
    # Volta a girar até encontra a linha vermelha, regressando à posição original (aprox. 180 graus)
def perform_attack_maneuver(tank_pair, weapon_motor, color_sensor):

    tank_pair.on_for_rotations(SpeedPercent(30), SpeedPercent(30), 0.5)


    print("A rodar 180 graus (a procura da linha vermelha)...")
    # Começa a girar para a direita
    tank_pair.on(SpeedPercent(20), SpeedPercent(-20))
    # IMPORTANTE: Espera um pouco 'cego' para garantir que sai da linha onde está atualmente
    # Se não fizermos isto, ele deteta a linha imediatamente e para.
    sleep(1.0)
    # Continua a girar até ver Vermelho
    while color_sensor.color_name != LINE_COLOR_NAME:
        sleep(0.01)
    tank_pair.off()
    print("Posicao de ataque alcancada (Linha encontrada).")
    # --- FASE 2: EXECUTAR ATAQUE ---
    print("A ativar arma...")
    tank_pair.on_for_rotations(SpeedPercent(20), SpeedPercent(20), 0.5)
    # Roda a 100% de velocidade por 2 segundos
    weapon_motor.on_for_seconds(SpeedPercent(70), seconds=2)
    # --- FASE 3: VOLTAR À POSIÇÃO INICIAL ---
    print("Ataque concluido. A voltar a posicao inicial...")
    tank_pair.on_for_rotations(SpeedPercent(-20), SpeedPercent(-20), 0.5)
    # Gira no sentido oposto (para a esquerda) para desfazer a rotação
    tank_pair.on(SpeedPercent(-20), SpeedPercent(20))
    # Espera 'cega' para sair da linha atual
    sleep(1.0)
    # Continua a girar até ver Vermelho de novo
    while color_sensor.color_name != LINE_COLOR_NAME:
        sleep(0.01)
    tank_pair.off()
    print("Posicao inicial recuperada.") 
    tank_pair.on_for_rotations(SpeedPercent(-20), SpeedPercent(-20), 0.5)





# FUNÇÕES DE MOVIMENTO E LÓGICA

# Helper para garantir que a velocidade do motor está entre -100 e 100
def _clamp_speed(speed):
    if speed > 100:
        return 100
    if speed < -100:
        return -100
    return speed

# Função para o robot seguir em linha reta com correção do giroscópio
def _follow_straight_on_line(tank_pair, gyro, base_speed, kp, target_angle):
    current_angle = gyro.angle
    correction = current_angle - target_angle
    turn_power = kp * correction
    # Aplicar clamp para evitar erros de velocidade inválida
    left_speed = _clamp_speed(base_speed + turn_power)
    right_speed = _clamp_speed(base_speed - turn_power)
    tank_pair.on(SpeedPercent(left_speed), SpeedPercent(right_speed))


# Função para realizar a procura girando
def _perform_search_spin(tank_pair, color_sensor, us_sensor, duration_s, left_speed, right_speed, distance_check_func):
    tank_pair.on(SpeedPercent(left_speed), SpeedPercent(right_speed))
    start_search_time = time()
    while (time() - start_search_time) < duration_s:
        if color_sensor.color_name == LINE_COLOR_NAME:
            return 'FOUND_LINE'
        current_distance = us_sensor.distance_centimeters
        if distance_check_func(current_distance):
            return 'TARGET_REACHED'
        sleep(0.01)
    return 'NOT_FOUND'


# Função para reorientar o robot quando perde a linha vermelha
def _search_for_lost_line(tank_pair, color_sensor, us_sensor, gyro, distance_check_func):
    tank_pair.off()
    print("Perdi a linha vermelha. Vou procurar a esquerda...")
    search_result = _perform_search_spin(
        tank_pair, color_sensor, us_sensor,
        duration_s=SEARCH_TIME_LEFT_S,
        left_speed=SPIN_SEARCH_SPEED,
        right_speed=-SPIN_SEARCH_SPEED,
        distance_check_func=distance_check_func
    )
    if search_result == 'FOUND_LINE':
        print("Encontrei a linha a esquerda!")
        gyro.reset()
        return 'FOUND_LINE'
    if search_result == 'TARGET_REACHED':
        print("Encontrei um inimigo ao regressar a linha!")
        return 'TARGET_REACHED'
    print("Nao encontrei a esquerda. Vou tentar a direita...")
    search_result = _perform_search_spin(
        tank_pair, color_sensor, us_sensor,
        duration_s=SEARCH_TIME_RIGHT_S,
        left_speed=-SPIN_SEARCH_SPEED,
        right_speed=SPIN_SEARCH_SPEED,
        distance_check_func=distance_check_func
    )
    if search_result == 'FOUND_LINE':
        print("Encontrei a linha a direita!")
        gyro.reset()
        return 'FOUND_LINE'
    if search_result == 'TARGET_REACHED':
        print("Encontrei um inimigo ao regressar a linha!")
        return 'TARGET_REACHED'
    print("Perdi-me! Nao consigo encontrar a linha vermelha!")
    return 'NOT_FOUND'




def follow_line_until_obstacle(tank_pair, gyro, color_sensor, us_sensor, base_speed, kp):
    """
    Phase 1: Follow line until dist_phase_1.
    Phase 2: Drive straight (blind) until dist_phase_2.
    """
    dist_phase_1 = 15
    dist_phase_2 = 8
    
    # --- PHASE 1: Follow Line ---
    print("FASE 1: A seguir linha ate {}cm do inimigo...".format(dist_phase_1))
    gyro.reset()
    target_angle = 0
    
    # We continue as long as we are FARTHER than the phase 1 distance
    while us_sensor.distance_centimeters > dist_phase_1:
        
        if color_sensor.color_name == LINE_COLOR_NAME:
            # Standard straight movement with Gyro correction
            _follow_straight_on_line(tank_pair, gyro, base_speed, kp, target_angle)
        else:
            # Lost line logic
            # We pass a lambda to ensure we don't crash while searching
            search_status = _search_for_lost_line(
                tank_pair, color_sensor, us_sensor, gyro,
                distance_check_func=lambda d: d <= dist_phase_1
            )
            
            if search_status == 'FOUND_LINE':
                target_angle = 0 # Reset angle reference if we recovered the line
                continue
            else:
                # If line is completely lost or we hit the distance during search
                break 
        sleep(0.01)

    # --- PHASE 2: Blind Charge (No Line Check) ---
    print("FASE 2: Linha ignorada. A avancar a direito ate {}cm...".format(dist_phase_2))
    
    # Reset gyro to 0 to ensure we drive perfectly straight from this point
    gyro.reset() 
    

    # We continue as long as we are FARTHER than the phase 2 distance
    while us_sensor.distance_centimeters > dist_phase_2:
        
        # Simple P-Control to keep robot straight using Gyro
        # (This ensures "moving forward" actually goes straight and doesn't drift)
        current_angle = gyro.angle
        error = 0 - current_angle # Target is 0
        correction = error * kp
        
        # Apply speed with correction (no color check here!)
        # Aplicar clamp para evitar erros de velocidade inválida
        left_speed = _clamp_speed(base_speed - correction)
        right_speed = _clamp_speed(base_speed + correction)
        tank_pair.on(left_speed, right_speed)
        
        sleep(0.01)

    # --- STOP ---
    tank_pair.off()
    print("ALVO ALCANCADO: Inimigo a < {}cm.".format(dist_phase_2))


# Função para regressar ao centro após se aproximar do inimigo
def follow_line_return_to_distance(tank_pair, gyro, color_sensor, us_sensor, return_speed, kp, target_distance_cm):
    print("Estou a regressar do inimigo... Vou parar quando estiver a >= {}cm.".format(target_distance_cm))
    gyro.reset()
    target_angle = 0

    print("Recuo de seguranca para reencontrar linha...")
    # Nota: Usamos velocidade positiva (30) porque no teu codigo o negativo (-70) e para a frente
    tank_pair.on_for_rotations(SpeedPercent(30), SpeedPercent(30), 0.5)


    stop_condition_check = lambda dist: dist >= target_distance_cm
    while not stop_condition_check(us_sensor.distance_centimeters):
        if color_sensor.color_name == LINE_COLOR_NAME:
            _follow_straight_on_line(tank_pair, gyro, return_speed, kp, target_angle)
        else:
            search_status = _search_for_lost_line(
                tank_pair, color_sensor, us_sensor, gyro,
                distance_check_func=stop_condition_check
            )
            if search_status == 'FOUND_LINE':
                target_angle = 0
                continue
            else:
                break 
        sleep(0.01)
    tank_pair.off()
    if stop_condition_check(us_sensor.distance_centimeters):
        print("Retorno concluido: Inimigo detetado a >= {:.1f}cm. A parar...".format(us_sensor.distance_centimeters))
    else:
        print("Perdi a linha vermelha enquanto regressava do inimigo! A parar...")


#perform_touch_attack(tank_pair)
#perform_attack_maneuver(tank_pair, medium_motor, color_sensor)
# Função para sair da linha atual e preparar para procurar a próxima

def _leave_current_line(tank_pair, color_sensor, spin_speed):
    print("A sair da linha vermelha atual...")
    tank_pair.on(left_speed=SpeedPercent(spin_speed * -1), right_speed=SpeedPercent(spin_speed))
    
    print("Fora da linha.")
# --- 1. The Music Worker Function ---
def background_music_loop(stop_event):
    """
    Plays a wav file in a loop until the robot finishes scanning.
    """
    speaker = Sound()
    
    # CHANGE THIS to your exact file name. 
    # Standard EV3 sounds: 'System/searching.wav', 'System/scanning.wav', 'Information/analyzing.wav'
    # Custom files: '/home/robot/my_song.wav'
    SOUND_FILE = 'search_song.wav' 

    while not stop_event.is_set():
        try:
            # play_type=1 (WAIT_FOR_COMPLETE) ensures the song finishes before restarting
            speaker.play_file(SOUND_FILE, volume=100, play_type=Sound.PLAY_WAIT_FOR_COMPLETE)
        except Exception as e:
            # If the file isn't found, we print ONCE and stop trying to play to prevent spamming errors
            print("!!! SOUND ERROR: Could not find file: {}".format(SOUND_FILE))
            print("Switching to beep fallback...")
            while not stop_event.is_set():
                speaker.tone(440, 500)
            return

# --- 2. The Main Search Function ---
def search_enemies(tank_pair, medium_motor, color_sensor, us_sensor, gyro, spin_speed, forward_speed):
    
    # --- Configuration ---
    KP_GAIN = 1.5
    FULL_TURN_MIN_ANGLE = 340 
    LINE_COLOR_NAME = 'Red'       # <--- Verify this matches your mat (Red/Blue/Black)
    
    # --- START MUSIC THREAD ---
    stop_sound_event = threading.Event()
    music_thread = threading.Thread(target=background_music_loop, args=(stop_sound_event,))
    music_thread.daemon = True 
    music_thread.start()

    try:
        # --- INITIALIZATION ---
        enemies_log = ["Empty"] * 6
        gyro.reset()
        accumulated_angle = 0 
        current_line_index = 0
        tank_pair.off()
        
        scanning = True
        is_start_position = True 

        # --- THE MAIN LOOP ---
        while scanning:
            
            # A. MOVEMENT LOGIC
            if not is_start_position:
                gyro.reset()
                
                # 1. Start Spinning
                tank_pair.on(left_speed=SpeedPercent(spin_speed * -1), right_speed=SpeedPercent(spin_speed))
                sleep(0.5) 

                # 2. Wait for Line
                print("Searching for next line...")
                while color_sensor.color_name != LINE_COLOR_NAME:
                    sleep(0.01)
                
                tank_pair.off()
                
                # 3. Calculate Angle
                segment_angle = abs(gyro.angle)
                accumulated_angle += segment_angle
                print("Angle: {} | Total: {}".format(segment_angle, accumulated_angle))

                # 4. Check for Skips (Logic to detect if we missed a line)
                if segment_angle > 90 and current_line_index < 5:
                    num_skipped = round(segment_angle / 60) - 1
                    if num_skipped > 0:
                        print("Skipped {} lines.".format(num_skipped))
                        current_line_index += num_skipped

                # 5. Check Completion
                if accumulated_angle >= FULL_TURN_MIN_ANGLE or current_line_index == 6:
                    print("--- 360 Turn Complete ---")
                    scanning = False
                    break 
            
            # B. RADAR & ATTACK LOGIC
            print("--- Checking Slot {} ---".format(current_line_index + 1))
            sleep(0.2) 
            distance_cm = us_sensor.distance_centimeters
            
            if distance_cm < OBJECT_SEARCH_DISTANCE_CM:
                print("Enemy detected at {}cm".format(distance_cm))
                
                # --- ACTION: Approach ---
                # (Ensure 'follow_line_until_obstacle' is defined in your file)
                follow_line_until_obstacle(
                    tank_pair=tank_pair, gyro=gyro, color_sensor=color_sensor,
                    us_sensor=us_sensor, base_speed=forward_speed, kp=KP_GAIN
                )
                
                # --- ACTION: Log Color ---
                detected_color = color_sensor.color_name
                print("Logged Color: {}".format(detected_color))
                if current_line_index < 6:
                    enemies_log[current_line_index] = detected_color
                
                # --- ACTION: Return ---
                return_speed = forward_speed * -1
                # (Ensure 'follow_line_return_to_distance' is defined in your file)
                follow_line_return_to_distance(
                    tank_pair=tank_pair, gyro=gyro, color_sensor=color_sensor,
                    us_sensor=us_sensor, return_speed=return_speed, kp=KP_GAIN,
                    target_distance_cm=distance_cm - 0.8 
                )
            else:
                print("Slot {} is Empty".format(current_line_index + 1))
                if current_line_index < 6:
                    enemies_log[current_line_index] = "Empty"

            # Prepare for next loop
            is_start_position = False
            current_line_index += 1
            
            if current_line_index >= 6:
                print("Max slots reached. Returning to start...")
                # Loop continues to movement logic to spin back to start line

        return enemies_log

    finally:
        # --- CLEANUP ---
        print("Stopping Music...")
        
        # 1. Signal the thread loop to stop (so it doesn't try to start the song again)
        stop_sound_event.set()
        
        # 2. FORCE KILL the sound immediately
        # This sends a system command to kill the 'aplay' process used by play_file
        os.system("pkill aplay") 
        
        # 3. Join the thread and stop motors
        music_thread.join(timeout=1) # Add a timeout so it doesn't hang
        tank_pair.off()


# Função para inicializar do hardware
def initialize_hardware():
    try:
        # Inicializa Motores de Tanque
        tank_pair = MoveTank(OUTPUT_B, OUTPUT_C)
        print("Motores Tanque (B, C): OK")
        
        # Inicializa Motor Médio (Arma) na Porta A
        medium_motor = MediumMotor(OUTPUT_A)
        print("Motor Medio (A): OK")

        # Inicializa Sensores
        color_sensor = ColorSensor(INPUT_4)
        color_sensor.mode = 'COL-COLOR'
        print("Sensor de Cor (Porta 4): OK.")
        
        us_sensor = UltrasonicSensor(INPUT_1)
        us_sensor.mode = 'US-DIST-CM'
        print("Sensor Ultrassonico (Porta 1): OK.")
        
        gyro_sensor = GyroSensor(INPUT_2)
        gyro_sensor.mode = 'GYRO-ANG' 
        print("Sensor Giroscopio (Porta 2): OK.")
        
        sleep(2.0) 
        gyro_sensor.reset()
        
        return tank_pair, medium_motor, color_sensor, us_sensor, gyro_sensor
    except Exception as e:
        print("Ocorreu um erro na inicializacao dos sensores e motores: {}".format(e))
        return None, None, None, None, None


def run_game_loop(tank_pair, medium_motor, color_sensor, us_sensor, gyro, spin_speed, forward_speed):
    """
    Controla os turnos do jogo.
    """
    turn_count = 1

    try:
        while True:
            print("\n=== PREPARAR PARA O TURNO {} ===".format(turn_count))
            
            # 1. Espera pelo Enter para começar
            input(">>> Pressione ENTER para procurar inimigos...")
            
            # 2. Executa a pesquisa (retorna o log)
            enemies_log = search_enemies(
                tank_pair=tank_pair,
                medium_motor=medium_motor, 
                color_sensor=color_sensor, 
                us_sensor=us_sensor, 
                gyro=gyro,
                spin_speed=spin_speed,
                forward_speed=forward_speed
            )

            # 3. Imprime o resultado
            print("\nResultado do Turno {}: {}".format(turn_count, enemies_log))
            
            # 4. Atualiza o array global 'enemies' com novos inimigos encontrados.
            #    Não substitui inimigos que já existem.
            print("\n--- A atualizar o estado dos inimigos ---")
            novos_inimigos = inicializar_inimigos_por_cor(enemies_log)
            
            for i, novo_inimigo in enumerate(novos_inimigos):
                # Se o slot no array principal está vazio e um novo inimigo foi detectado
                if enemies[i] is None and novo_inimigo is not None:
                    print("Novo inimigo adicionado na Posicao {}".format(i))
                    enemies[i] = novo_inimigo # Adiciona a nova instância
            
            # 5. Imprime o estado atual do campo de batalha
            print("\n--- Campo de Batalha Atual (Turno {}) ---".format(turn_count))
            for i, inimigo in enumerate(enemies):
                if inimigo is None:
                    print("Posicao {}: Vazio".format(i))
                else:
                    print("Posicao {}: {}".format(i, inimigo))
            print("turno acabado")
            
            # 6. Incrementa o turno
            turn_count += 1
            print("-" * 30)

    except KeyboardInterrupt:
        print("\nPrograma interrompido pelo utilizador.")
    except Exception as e:
        print("Erro: {}".format(e))
    finally:
        tank_pair.off()
        medium_motor.off()



def main():
    tank_pair, medium_motor, color_sensor, us_sensor, gyro_sensor = initialize_hardware()
    
    if tank_pair is not None:

        # --- PHASE 0: Wait for Start ---
        # Using input() to simulate waiting for "Enter" key in the console
        imprimir_setup_inicial()
        
        run_game_loop(
            tank_pair=tank_pair,
            medium_motor=medium_motor, 
            color_sensor=color_sensor, 
            us_sensor=us_sensor, 
            gyro=gyro_sensor,
            spin_speed=20,
            forward_speed=-20
        )





        # # --- Processar e imprimir o relatório final de inimigos ---
        # print("\n" + "="*40)
        # print("--- RELATORIO FINAL DE INIMIGOS ---")
        # for i, color in enumerate(enemies_log):
        #     position = i + 1
        #     if color == "Empty":
        #         print("Posicao {}: Vazio".format(position))
        #     else:
        #         found_enemy = False
        #         # Procura no dicionário importado qual inimigo corresponde à cor
        #         for enemy_type, stats in INIMIGO_STATS.items():
        #             if stats['cor'] == color:
        #                 print("Posicao {}: Encontrado - {}".format(position, enemy_type))
        #                 found_enemy = True
        #                 break
                
        #         if not found_enemy:
        #             # Lida com cores detetadas mas não definidas no dicionário
        #             print("Posicao {}: Inimigo de cor desconhecida ({})".format(position, color))

        # print("="*40)
    else:
        print("Falha ao inicializar hardware. A sair...")


if __name__ == "__main__":
    main()