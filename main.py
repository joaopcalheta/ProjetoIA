#!/usr/bin/env python3

from time import sleep, time
from ev3dev2.motor import (SpeedPercent, MoveTank, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C)
from ev3dev2.sensor.lego import ColorSensor, UltrasonicSensor, GyroSensor
from ev3dev2.sensor import INPUT_1, INPUT_2, INPUT_4
from ev3dev2.sound import Sound

# --- Constantes de Comportamento ---
OBSTACLE_STOP_DISTANCE_CM = 8
# Distância para parar à frente do inimigo
OBJECT_SEARCH_DISTANCE_CM = 45     # Distância para considerar "inimigo encontrado"
LINE_COLOR_NAME = 'Red'            # Cor da linha a seguir até ao inimigo

# --- Constantes de Afinação ---
SPIN_SEARCH_SPEED = 15             # Velocidade de rotação durante a procura da linha  
SEARCH_TIME_LEFT_S = 0.5           # Duração da procura para a esquerda
SEARCH_TIME_RIGHT_S = 3.0          # Duração da procura para a direita

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

# Função para o robot seguir em linha reta com correção do giroscópio
def _follow_straight_on_line(tank_pair, gyro, base_speed, kp, target_angle):
    current_angle = gyro.angle
    correction = current_angle - target_angle
    turn_power = kp * correction
    left_speed = base_speed + turn_power
    right_speed = base_speed - turn_power
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
        tank_pair.on(base_speed - correction, base_speed + correction)
        
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


# Função para sair da linha atual e preparar para procurar a próxima
def _leave_current_line(tank_pair, color_sensor, spin_speed):
    print("A sair da linha vermelha atual...")
    tank_pair.on(left_speed=SpeedPercent(spin_speed * -1), right_speed=SpeedPercent(spin_speed))
    while color_sensor.color_name == LINE_COLOR_NAME: 
        sleep(0.01)
    print("Fora da linha.")


# Função com a lógica principal do robot (loop)
def run_challenge(tank_pair, medium_motor, color_sensor, us_sensor, gyro, spin_speed, forward_speed):

    KP_GAIN = 1.5 
    turn_count = 0  # Contador de turnos
    
    try:
        while True:
            
            # --- ESPERA POR ENTER PARA INICIAR O TURNO ---
            tank_pair.off() # Garante que está parado
            print("\n" + "="*40)
            print(" PRONTO PARA O TURNO {}".format(turn_count))
            print(" Pressione [ENTER] no teclado para iniciar...")
            print("="*40)
            
            # Esta função pausa o programa até receberes um Enter no terminal
            input() 
            
            print(">>> A INICIAR TURNO {} <<<".format(turn_count))
            # ---------------------------------------------------
            
            
            # Estado 1 - Gira à procura da linha vermelha
            print("--- ESTADO 1: A procurar linha vermelha... ---")
            tank_pair.on(left_speed=SpeedPercent(spin_speed * -1), right_speed=SpeedPercent(spin_speed))
            while color_sensor.color_name != LINE_COLOR_NAME:
                sleep(0.01) 
            
            
            # Estado 2 - Encontra a linha, pára e verifica se há inimigo no slot em frente
            tank_pair.off()
            print("--- ESTADO 2: Linha vermelha detetada! A parar e a verificar existencia de inimigo... ---")
            sleep(0.1) 
            distance_cm = us_sensor.distance_centimeters
            
            print("Distancia lida: {} cm".format(distance_cm))
            
            if distance_cm < OBJECT_SEARCH_DISTANCE_CM:

                # Estado 3 - Deteta inimigo em frente e aproxima-se
                print("--- ESTADO 3: Inimigo detetado! A aproximar-se...")
                follow_line_until_obstacle(
                    tank_pair=tank_pair, gyro=gyro, color_sensor=color_sensor,
                    us_sensor=us_sensor, base_speed=forward_speed, kp=KP_GAIN
                )
                
                # --- EXECUTAR O ATAQUE ---
                #perform_touch_attack(tank_pair)
                perform_attack_maneuver(tank_pair, medium_motor, color_sensor)
                # -------------------------

                # Estado 4 - Regressa do inimigo seguindo a linha
                
                play_wav("nein.wav")
                
                print("--- ESTADO 4: Fim de ataque! A regressar para o centro...")
                sleep(0.5)
                return_speed = forward_speed * -1 
                start_distance_cm = distance_cm 

                follow_line_return_to_distance(
                    tank_pair=tank_pair, gyro=gyro, color_sensor=color_sensor,
                    us_sensor=us_sensor, return_speed=return_speed, kp=KP_GAIN,
                    target_distance_cm=start_distance_cm - 0.8
                )
                
                # Ignora a linha atual para voltar ao ESTADO 1
                _leave_current_line(tank_pair, color_sensor, spin_speed)

            else:
                # Nenhum inimigo detetado em frente
                print("Nenhum inimigo detetado neste slot.")
                _leave_current_line(tank_pair, color_sensor, spin_speed)
            
            # Incrementa o turno no final do ciclo
            turn_count += 1

    except KeyboardInterrupt:
        print("\nPrograma interrompido pelo utilizador.")
    except Exception as e:
        print("Ocorreu um erro durante o ciclo: {}".format(e))
    finally:
        tank_pair.off()
        medium_motor.off()
        print("Motores parados.")


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


def main():
    tank_pair, medium_motor, color_sensor, us_sensor, gyro_sensor = initialize_hardware()
    
    if tank_pair is not None:
        run_challenge(
            tank_pair=tank_pair,
            medium_motor=medium_motor, 
            color_sensor=color_sensor, 
            us_sensor=us_sensor, 
            gyro=gyro_sensor,
            spin_speed=20,
            forward_speed=-20
        )
    else:
        print("Falha ao inicializar hardware. A sair...")


if __name__ == "__main__":
    main()