#!/usr/bin/env python3

from time import sleep, time
from ev3dev2.motor import (SpeedPercent, MoveTank, OUTPUT_B, OUTPUT_C)
from ev3dev2.sensor.lego import ColorSensor, UltrasonicSensor, GyroSensor
from ev3dev2.sensor import INPUT_1, INPUT_2, INPUT_4

# --- Constantes de Comportamento ---
OBSTACLE_STOP_DISTANCE_CM = 10     # Distância para parar à frente do inimigo
OBJECT_SEARCH_DISTANCE_CM = 45     # Distância para considerar "inimigo encontrado"
LINE_COLOR_NAME = 'Red'            # Cor da linha a seguir até ao inimigo

# --- Constantes de Afinação ---
SPIN_SEARCH_SPEED = 15             # Velocidade de rotação durante a procura da linha  
SEARCH_TIME_LEFT_S = 0.5           # Duração da procura para a esquerda
SEARCH_TIME_RIGHT_S = 3.0          # Duração da procura para a direita


# Função para o robot seguir em linha reta com correção do giroscópio
def _follow_straight_on_line(tank_pair, gyro, base_speed, kp, target_angle):
    current_angle = gyro.angle
    correction = current_angle - target_angle
    turn_power = kp * correction
    left_speed = base_speed + turn_power
    right_speed = base_speed - turn_power
    tank_pair.on(SpeedPercent(left_speed), SpeedPercent(right_speed))


# Função para realizar a procura girando
    # Gira até ficar em direção a um slot de inimigo (encontra a linha vermelha)
    # Quando encontra a linha, verifica se existe um inimigo no slot em frente (deteta distancia)
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
    # Tenta encontrar a linha girando primeiro para a esquerda, depois para a direita
    # Se encontrar linha vermelha, retorna 'FOUND_LINE'
    # Se encontrar um inimigo ao regressar à linha (deteta distância), retorna 'TARGET_REACHED'
    # Se não encontrar linha vermelha, retorna 'NOT_FOUND'
def _search_for_lost_line(tank_pair, color_sensor, us_sensor, gyro, distance_check_func):
    tank_pair.off()
    print("Perdi a linha vermelha. Vou procurar à esquerda...")
    search_result = _perform_search_spin(
        tank_pair, color_sensor, us_sensor,
        duration_s=SEARCH_TIME_LEFT_S,
        left_speed=SPIN_SEARCH_SPEED,
        right_speed=-SPIN_SEARCH_SPEED,
        distance_check_func=distance_check_func
    )
    if search_result == 'FOUND_LINE':
        print("Encontrei a linha à esquerda!")
        gyro.reset()
        return 'FOUND_LINE'
    if search_result == 'TARGET_REACHED':
        print("Encontrei um inimigo ao regressar à linha!")
        return 'TARGET_REACHED'
    print("Não encontrei à esquerda. Vou tentar à direita...")
    search_result = _perform_search_spin(
        tank_pair, color_sensor, us_sensor,
        duration_s=SEARCH_TIME_RIGHT_S,
        left_speed=-SPIN_SEARCH_SPEED,
        right_speed=SPIN_SEARCH_SPEED,
        distance_check_func=distance_check_func
    )
    if search_result == 'FOUND_LINE':
        print("Encontrei a linha à direita!")
        gyro.reset()
        return 'FOUND_LINE'
    if search_result == 'TARGET_REACHED':
        print("Encontrei um inimigo ao regressar à linha!")
        return 'TARGET_REACHED'
    print("Perdi-me! Não consigo encontrar a linha vermelha!")
    return 'NOT_FOUND'


# Função para seguir a linha até estar perto do inimigo
    # Pára quando estiver a OBJECT_SEARCH_DISTANCE_CM ou menos do inimigo
    # Pára se perder a linha
def follow_line_until_obstacle(tank_pair, gyro, color_sensor, us_sensor, base_speed, kp):
    print("Estou a ir em direção ao inimigo... Vou parar quando estiver a <= {}cm.".format(OBSTACLE_STOP_DISTANCE_CM))
    gyro.reset()
    target_angle = 0
    stop_condition_check = lambda dist: dist <= OBSTACLE_STOP_DISTANCE_CM
    while not stop_condition_check(us_sensor.distance_centimeters):
        if color_sensor.color_name == LINE_COLOR_NAME:
            _follow_straight_on_line(tank_pair, gyro, base_speed, kp, target_angle)
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
        print("Avanço concluído: Inimigo detetado a < {}cm. A parar...".format(OBSTACLE_STOP_DISTANCE_CM))
    else:
        print("Perdi a linha vermelha enquanto ia em direção ao inimigo! A parar...")


# Função para regressar ao centro após se aproximar do inimigo
    # Pára quando estiver a target_distance_cm ou mais do inimigo
    # target_distance_cm é a distância inicial que tinha ao inimigo antes de se aproximar menos 0.8cm
    # Pára se perder a linha
def follow_line_return_to_distance(tank_pair, gyro, color_sensor, us_sensor, return_speed, kp, target_distance_cm):
    print("Estou a regressar do inimigo... Vou parar quando estiver a >= {}cm.".format(target_distance_cm))
    gyro.reset()
    target_angle = 0
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
        print("Retorno concluído: Inimigo detetado a >= {:.1f}cm. A parar...".format(us_sensor.distance_centimeters))
    else:
        print("Perdi a linha vermelha enquanto regressava do inimigo! A parar...")


# Função para sair da linha atual e preparar para procurar a próxima
def _leave_current_line(tank_pair, color_sensor, spin_speed):
    print("A sair da linha vermelha atual...")
    tank_pair.on(left_speed=SpeedPercent(spin_speed * -1), right_speed=SpeedPercent(spin_speed))
    while color_sensor.color_name == LINE_COLOR_NAME: # continua a girar enquanto ainda ver a linha vermelha
        sleep(0.01)
    print("Fora da linha.")


# Função com a lógica principal do robot (loop)
def run_challenge(tank_pair, color_sensor, us_sensor, gyro, spin_speed, forward_speed):

    KP_GAIN = 1.5 
    
    try:
        while True:
            
            # Estado 1 - Gira à procura da linha vermelha
            print("--- ESTADO 1: A procurar linha vermelha... ---")
            tank_pair.on(left_speed=SpeedPercent(spin_speed * -1), right_speed=SpeedPercent(spin_speed))
            while color_sensor.color_name != LINE_COLOR_NAME:
                sleep(0.01) 
            
            
            # Estado 2 - Encontra a linha, pára e verifica se há inimigo no slot em frente
            tank_pair.off()
            print("--- ESTADO 2: Linha vermelha detetada! A parar e a verificar existência de inimigo... ---")
            sleep(0.1) 
            distance_cm = us_sensor.distance_centimeters
            # Verifica se há inimigo no slot em frente
            if distance_cm < OBJECT_SEARCH_DISTANCE_CM:


                # Estado 3 - Deteta inimigo em frente e aproxima-se do inimigo seguindo a linha
                print("--- ESTADO 3: Inimigo detetado a {:.1f} cm! A aproximar-se do inimigo...".format(distance_cm))
                follow_line_until_obstacle(
                    tank_pair=tank_pair, gyro=gyro, color_sensor=color_sensor,
                    us_sensor=us_sensor, base_speed=forward_speed, kp=KP_GAIN
                )
                

                # Estado 4 - Regressa do inimigo seguindo a linha
                print("--- ESTADO 4: Fim de aproximação ao inimigo! A regressar para o centro...")
                sleep(0.5)
                return_speed = forward_speed * -1 
                start_distance_cm = distance_cm 
                follow_line_return_to_distance(
                    tank_pair=tank_pair, gyro=gyro, color_sensor=color_sensor,
                    us_sensor=us_sensor, return_speed=return_speed, kp=KP_GAIN,
                    target_distance_cm=start_distance_cm -0.8
                )
                
                # Ignora a linha atual para voltar ao ESTADO 1
                _leave_current_line(tank_pair, color_sensor, spin_speed)

            else:

                # Nenhum inimigo detetado em frente
                print("Nenhum inimigo detetado em {:.1f} cm.".format(distance_cm))
                
                # Ignora a linha atual para voltar ao ESTADO 1
                _leave_current_line(tank_pair, color_sensor, spin_speed)
            
            sleep(1.0) # Pausa entre ciclos

    except KeyboardInterrupt:
        print("\nPrograma interrompido pelo utilizador.")
    except Exception as e:
        print("Ocorreu um erro durante o ciclo: {}".format(e))
    finally:
        tank_pair.off()
        print("Motores de locomocao parados.")


# Função para inicializar do hardware
def initialize_hardware():
    try:
        tank_pair = MoveTank(OUTPUT_B, OUTPUT_C)
        print("Motores (B, C): OK")
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
        return tank_pair, color_sensor, us_sensor, gyro_sensor
    except Exception as e:
        print("Ocorreu um erro na inicializacao dos sensores e motores (verificar ligações): {}".format(e))
        return None, None, None, None


def main():
    tank_pair, color_sensor, us_sensor, gyro_sensor = initialize_hardware() # Inicializa hardware
    
    if tank_pair is not None:
        run_challenge(
            tank_pair=tank_pair,
            color_sensor=color_sensor, 
            us_sensor=us_sensor, 
            gyro=gyro_sensor,
            spin_speed=20,      # Velocidade de rotação
            forward_speed=-20   # Velocidade de avanço
        )
    else:
        print("Falha ao inicializar hardware. A sair...")


if __name__ == "__main__":
    main()