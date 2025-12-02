from time import sleep, time
from ev3dev2.motor import (SpeedPercent, MoveTank, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C)
from ev3dev2.sensor.lego import ColorSensor, UltrasonicSensor, GyroSensor
from ev3dev2.sensor import INPUT_1, INPUT_2, INPUT_4
from tools import clamp_speed
from config import OBJECT_SEARCH_DISTANCE_CM, LINE_COLOR_NAME, SPIN_SEARCH_SPEED, SEARCH_TIME_LEFT_S, SEARCH_TIME_RIGHT_S


# Segue em linha reta com correção do giroscópio
def follow_straight_on_line(tank_pair, gyro, base_speed, kp, target_angle):
    current_angle = gyro.angle
    correction = current_angle - target_angle
    turn_power = kp * correction
    left_speed = clamp_speed(base_speed + turn_power)
    right_speed = clamp_speed(base_speed - turn_power)
    tank_pair.on(SpeedPercent(left_speed), SpeedPercent(right_speed))



# Gira o robô para a esquerda ou direita
def perform_search_spin(tank_pair, color_sensor, us_sensor, duration_s, left_speed, right_speed, distance_check_func):
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



# Reorienta o robot quando perde a linha vermelha
def search_for_lost_line(tank_pair, color_sensor, us_sensor, gyro, distance_check_func):
    tank_pair.off()
    
    # Procura à esquerda
    search_result = perform_search_spin(
        tank_pair, color_sensor, us_sensor,
        duration_s=SEARCH_TIME_LEFT_S,
        left_speed=SPIN_SEARCH_SPEED,
        right_speed=-SPIN_SEARCH_SPEED,
        distance_check_func=distance_check_func
    )
    
    # Encontra a linha à esquerda
    if search_result == 'FOUND_LINE':
        gyro.reset()
        return 'FOUND_LINE'
    
    # Encontra um inimigo ao regressar à linha a partir da esquerda
    if search_result == 'TARGET_REACHED':
        return 'TARGET_REACHED'

    # Não encontrou à esquerda, vai procurar à direita
    search_result = perform_search_spin(
        tank_pair, color_sensor, us_sensor,
        duration_s=SEARCH_TIME_RIGHT_S,
        left_speed=-SPIN_SEARCH_SPEED,
        right_speed=SPIN_SEARCH_SPEED,
        distance_check_func=distance_check_func
    )

    # Encontra a linha à direita
    if search_result == 'FOUND_LINE':
        gyro.reset()
        return 'FOUND_LINE'

    # Encontra um inimigo ao regressar à linha a partir da direita
    if search_result == 'TARGET_REACHED':
        return 'TARGET_REACHED'
    
    # Não encontrou a linha à direita, nem à esquerda
    print("Perdi-me! Nao consigo encontrar a linha vermelha!") # O 'ã' em 'Nao' foi removido para evitar erros de codificacao.
    return 'NOT_FOUND'



# Deixa a linha vermelha
def leave_current_line(tank_pair, color_sensor, spin_speed):
    tank_pair.on(left_speed=SpeedPercent(spin_speed * -1), right_speed=SpeedPercent(spin_speed))



# Regressa ao centro após se aproximar do inimigo
def follow_line_return_to_distance(tank_pair, gyro, color_sensor, us_sensor, return_speed, kp, target_distance_cm):
    gyro.reset()
    target_angle = 0

    # Pequeno recuo cego para trás para sair da cor do inimigo 
    tank_pair.on_for_rotations(SpeedPercent(30), SpeedPercent(30), 0.5)

    stop_condition_check = lambda dist: dist >= target_distance_cm
    while not stop_condition_check(us_sensor.distance_centimeters):
        if color_sensor.color_name == LINE_COLOR_NAME:
            follow_straight_on_line(tank_pair, gyro, return_speed, kp, target_angle)
        else:
            search_status = search_for_lost_line(
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



# Aproxima-se do inimigo até chegar a uma certa distância
def follow_line_until_obstacle(tank_pair, gyro, color_sensor, us_sensor, base_speed, kp):
    
    dist_phase_1 = 15   # Distância para ficar do inimigo antes de chegar à cor do inimigo (cartolina no chão à frente do inimigo)
    dist_phase_2 = 8    # Distância para ficar do inimigo após cobrir a cor do inimigo (cartolina no chão à frente do inimigo)
    
    # Fase 1 - Ficar a dist_phase_1 do inimigo (antes de chegar à cor do inimigo)
    gyro.reset()
    target_angle = 0
    while us_sensor.distance_centimeters > dist_phase_1:
        if color_sensor.color_name == LINE_COLOR_NAME:
            follow_straight_on_line(tank_pair, gyro, base_speed, kp, target_angle)
        else:
            search_status = search_for_lost_line(
                tank_pair, color_sensor, us_sensor, gyro,
                distance_check_func=lambda d: d <= dist_phase_1
            )
            if search_status == 'FOUND_LINE':
                target_angle = 0
                continue
            else:
                break 
        sleep(0.01)

    # Fase 2 - Ficar a dist_phase_2 do inimigo (após cobrir cor do inimigo)
    gyro.reset() 
    while us_sensor.distance_centimeters > dist_phase_2:
        current_angle = gyro.angle
        error = 0 - current_angle
        correction = error * kp
        left_speed = clamp_speed(base_speed - correction)
        right_speed = clamp_speed(base_speed + correction)
        tank_pair.on(left_speed, right_speed)
        sleep(0.01)

    tank_pair.off()



# Faz o reconhecimento do ambiente do novo turno
def search_enemies(tank_pair, medium_motor, color_sensor, us_sensor, gyro, spin_speed, forward_speed):

    KP_GAIN = 1.5
    
    FULL_TURN_MIN_ANGLE = 340 

    try:
        enemies_log = ["Empty"] * 6
        gyro.reset()
        accumulated_angle = 0
        current_line_index = 0
        tank_pair.off()
        
        scanning = True
        is_start_position = True

        while scanning:
            
            if not is_start_position:

                gyro.reset()
                
                # Sai da linha atual
                tank_pair.on(left_speed=SpeedPercent(spin_speed * -1), right_speed=SpeedPercent(spin_speed))
                sleep(0.5) 

                # Roda até encontrar a próxima linha
                while color_sensor.color_name != LINE_COLOR_NAME:
                    sleep(0.01)
                tank_pair.off()

                # Acumula angulo da deslocação
                segment_angle = abs(gyro.angle)
                accumulated_angle += segment_angle

                print("Angulo percorrido: {}".format(segment_angle))

                SKIPPED_LINE_ANGLE_THRESHOLD = 90
                EXPECTED_SEGMENT_ANGLE = 60
                
                # Se o ângulo for muito grande, o robot calcula as linhas que saltou
                if segment_angle > SKIPPED_LINE_ANGLE_THRESHOLD and current_line_index < 5:
                    num_skipped = round(segment_angle / EXPECTED_SEGMENT_ANGLE) - 1
                    if num_skipped > 0: # O 'ú' em 'angulo' foi removido para evitar erros de codificacao.
                        print("O angulo percorrido {} é muito grande. Foi assumido que o robot saltou {} linha(s).".format(segment_angle, num_skipped))
                        current_line_index += num_skipped

                # Se o ângulo acumulado for superior a 340 e as linhas contadas forem igual a 6, o robot para a pesquisa 
                if accumulated_angle >= FULL_TURN_MIN_ANGLE or current_line_index == 6:
                    print("O Robot realizou uma volta completa.")
                    scanning = False
                    break 
            
            sleep(0.1)
            distance_cm = us_sensor.distance_centimeters # O 'â' em 'distancia' foi removido para evitar erros de codificacao.
            
            if distance_cm < OBJECT_SEARCH_DISTANCE_CM:
                print("Inimigo detetado a {}cm (Slot {})".format(distance_cm, current_line_index + 1))
                
                # Aproxima-se do inimigo
                follow_line_until_obstacle(
                    tank_pair=tank_pair, gyro=gyro, color_sensor=color_sensor,
                    us_sensor=us_sensor, base_speed=forward_speed, kp=KP_GAIN
                )
                
                # Guarda a cor detetada
                detected_color = color_sensor.color_name # O 'ã' em 'detetada' foi removido para evitar erros de codificacao.
                print("Cor detetada: {}".format(detected_color))
                if current_line_index < 6:
                    enemies_log[current_line_index] = detected_color
                
                # Regressa ao centro
                return_speed = forward_speed * -1
                follow_line_return_to_distance(
                    tank_pair=tank_pair, gyro=gyro, color_sensor=color_sensor,
                    us_sensor=us_sensor, return_speed=return_speed, kp=KP_GAIN, # O 'â' em 'distancia' foi removido para evitar erros de codificacao.
                    target_distance_cm=distance_cm - 0.8 
                )
            else:
                print("O Slot {} esta vazio.".format(current_line_index + 1))
                if current_line_index < 6:
                    enemies_log[current_line_index] = "Empty"

            is_start_position = False
            current_line_index += 1
            
            if current_line_index >= 6:
                print("Max slots reached, returning to start...")

        return enemies_log

    except KeyboardInterrupt:
        print("\nScan interrupted by user.")
        raise
    except Exception as e:
        print("Error during scan: {}".format(e))
    finally:
        tank_pair.off()