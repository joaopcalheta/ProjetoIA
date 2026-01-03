from time import sleep, time
import random
import threading
import os
from ev3dev2.motor import (SpeedPercent, MoveTank, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C)
from ev3dev2.sensor.lego import ColorSensor, UltrasonicSensor, GyroSensor
from ev3dev2.sensor import INPUT_1, INPUT_2, INPUT_4
from tools import clamp_speed
from config import OBJECT_SEARCH_DISTANCE_CM, LINE_COLOR_NAME, SPIN_SEARCH_SPEED, SEARCH_TIME_LEFT_S, SEARCH_TIME_RIGHT_S
from tools import background_music_loop


# Controla o movimento do robot em linha reta utilizando o giroscópio para correções
# Ajusta a potência de cada motor proporcionalmente ao erro de ângulo detectado
def follow_straight_on_line(tank_pair, gyro, base_speed, kp, target_angle):
    current_angle = gyro.angle
    correction = current_angle - target_angle
    turn_power = kp * correction
    left_speed = clamp_speed(base_speed + turn_power)
    right_speed = clamp_speed(base_speed - turn_power)
    tank_pair.on(SpeedPercent(left_speed), SpeedPercent(right_speed))



# Gira o robot em busca de alvos ou da linha vermelha
# Monitora simultaneamente o sensor de cor (para encontrar a linha) e o ultrassónico (para detectar inimigos)
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
# Realiza uma busca alternada (esquerda e depois direita) até reencontrar a linha vermelha no solo
def search_for_lost_line(tank_pair, color_sensor, us_sensor, gyro, distance_check_func):
    tank_pair.off()
    
    # Procura primeiro à esquerda
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
    print("Perdi-me! Nao consigo encontrar a linha vermelha!")
    return 'NOT_FOUND'



# Força o robot a rodar para fora da linha atual.
def leave_current_line(tank_pair, color_sensor, spin_speed):
    tank_pair.on(left_speed=SpeedPercent(spin_speed * -1), right_speed=SpeedPercent(spin_speed))



# Faz o robot regressar a uma certa distância do inimigo após cobrir a cor do inimigo
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



# Conduz o robot em direção ao inimigo seguindo a linha vermelha em 2 fases:
# Fase 1 - Ficar a dist_phase_1 do inimigo (antes de chegar à cor do inimigo)
# Fase 2 - Ficar a dist_phase_2 do inimigo (após cobrir cor do inimigo)
def follow_line_until_obstacle(tank_pair, gyro, color_sensor, us_sensor, base_speed, kp):
    
    dist_phase_1 = 15   # Distância até ao inimigo antes de chegar à cor do inimigo
    dist_phase_2 = 8    # Distância até ao inimigo após cobrir a cor do inimigo
    
    # Fase 1
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

    # Fase 2
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


# Realiza o reconhecimento circular do campo no início de cada turno.
# Aproxima-se a cada inimigo detetado, regista a cor do inimigo e depois recua para o centro.
# Apenas aproxima dos inimigos que ainda não foram registados, ou seja, que estão marcados como None na lista de inimigos.
# Retorna uma lista com as cores dos inimigos detetados em cada um dos 6 slots.
def search_enemies(tank_pair, medium_motor, color_sensor, us_sensor, gyro, spin_speed, forward_speed, enemies):

    KP_GAIN = 1.5
    
    FULL_TURN_MIN_ANGLE = 340 

    stop_sound_event = threading.Event()
    music_thread = threading.Thread(target=background_music_loop, args=(stop_sound_event,))
    music_thread.daemon = True 
    music_thread.start()

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
                tank_pair.on(left_speed=SpeedPercent(spin_speed * -1), right_speed=SpeedPercent(spin_speed))
                sleep(0.5) 
                # Roda até encontrar a próxima linha
                while color_sensor.color_name != LINE_COLOR_NAME:
                    sleep(0.01)
                tank_pair.off()
                segment_angle = abs(gyro.angle)
                accumulated_angle += segment_angle
                print("Angulo percorrido: {}".format(segment_angle))

                # Lógica para detectar se o robot saltou linhas baseado no ângulo percorrido.
                SKIPPED_LINE_ANGLE_THRESHOLD = 90
                EXPECTED_SEGMENT_ANGLE = 60
                
                if segment_angle > SKIPPED_LINE_ANGLE_THRESHOLD and current_line_index < 5:
                    num_skipped = round(segment_angle / EXPECTED_SEGMENT_ANGLE) - 1
                    if num_skipped > 0:
                        print("O angulo percorrido {} e muito grande. Foi assumido que o robot saltou {} linha(s).".format(segment_angle, num_skipped))
                        current_line_index += num_skipped

                if accumulated_angle >= FULL_TURN_MIN_ANGLE or current_line_index == 6:
                    print("O Robot realizou uma volta completa.")
                    scanning = False
                    break 
            
            sleep(0.1)
            distance_cm = us_sensor.distance_centimeters 
            
            # Verifica se o slot atual ja foi registado
            # Se ja foi registado, apenas avança para o próximo slot
            # Se não foi registado, aproxima,verifica se há um inimigo e regista a cor
            if distance_cm < OBJECT_SEARCH_DISTANCE_CM:
                print("Inimigo detetado a {}cm (Slot {})".format(distance_cm, current_line_index + 1))
                if(enemies[current_line_index] is None):
                
                    follow_line_until_obstacle(
                        tank_pair=tank_pair, gyro=gyro, color_sensor=color_sensor,
                        us_sensor=us_sensor, base_speed=forward_speed, kp=KP_GAIN
                    )
                    
                    # Guarda a cor detetada
                    detected_color = color_sensor.color_name 
                    print("Cor detetada: {}".format(detected_color))
                    if current_line_index < 6:
                        enemies_log[current_line_index] = detected_color
                    
                    # Regressa ao centro para continuar a busca dos restantes slots
                    return_speed = forward_speed * -1
                    follow_line_return_to_distance(
                        tank_pair=tank_pair, gyro=gyro, color_sensor=color_sensor,
                        us_sensor=us_sensor, return_speed=return_speed, kp=KP_GAIN, 
                        target_distance_cm=distance_cm - 0.8 
                    )
            else:
                print("O Slot {} esta vazio.".format(current_line_index + 1))
                if current_line_index < 6:
                    enemies_log[current_line_index] = "Empty"

            is_start_position = False
            current_line_index += 1
            
            # Completa a volta após 6 slots
            if current_line_index >= 6:
                print("Numero de slots alcancado. A regressar ao inicio...")

        return enemies_log

    except KeyboardInterrupt:
        print("\nPrograma interrompido pelo utilizador.")
        raise
    except Exception as e:
        print("Erro durante o reconhecimento do ambiente: {}".format(e))
    finally:
        print("A parar a musica...")
        stop_sound_event.set()
        os.system("pkill aplay") 
        music_thread.join(timeout=1)
        tank_pair.off()


# Realiza a sequencia de combate: rotação até ao slot do inimigo-alvo, aproximação, ataque e regresso ao centro
# Gira o robot no centro do campo de batalha até encontrar a linha do slot alvo.
def rotate_perform_action_return(tank_pair, color_sensor, gyro, us_sensor, spin_speed, forward_speed, scheduled_actions):

    FULL_TURN_MIN_ANGLE = 340           # Ângulo mínimo para considerar que o robot deu uma volta completa
    SKIPPED_LINE_ANGLE_THRESHOLD = 90   # Ângulo acima do qual o robot considera que saltou uma ou mais linhas
    EXPECTED_SEGMENT_ANGLE = 60         # Ângulo esperado entre duas linhas consecutivas
    KP_GAIN = 1.5                       # Ganho proporcional para correção de trajetória


    # Verifica se o índice do slot atual esta na lista de acoes agendadas
    # Realiza o ataque ao inimigo no slot atual
    def check_and_attack(current_idx):
        if current_idx in scheduled_actions:
            print("Linha {} (Alvo) alcancada. A verificar se existe inimigo...".format(current_idx))
        
            sleep(0.1) 
            distance_cm = us_sensor.distance_centimeters

            if distance_cm < OBJECT_SEARCH_DISTANCE_CM:
                print("Inimigo detetado a {}cm. A aproximar...".format(distance_cm)) 
                
                follow_line_until_obstacle(
                    tank_pair=tank_pair, 
                    gyro=gyro, 
                    color_sensor=color_sensor,
                    us_sensor=us_sensor, 
                    base_speed=forward_speed, 
                    kp=KP_GAIN
                )
                tank_pair.off()
                sleep(0.5)

                # Executa o callback de ataque (definido em robot_heal_attack_logic.py).
                scheduled_actions[current_idx]()
                
                return_speed = forward_speed * -1
                follow_line_return_to_distance(
                    tank_pair=tank_pair, 
                    gyro=gyro, 
                    color_sensor=color_sensor,
                    us_sensor=us_sensor, 
                    return_speed=return_speed, 
                    kp=KP_GAIN, 
                    target_distance_cm=distance_cm - 2
                )
            else:
                print("Nao existe nenhum inimigo no slot para atacar.")
            

            tank_pair.off()
            sleep(0.2)

    try:
        gyro.reset()
        tank_pair.off()
        accumulated_angle = 0
        current_line_index = 0
        scanning = True
        
        print("A iniciar rotina de rotacao para ataques multiplos. Alvos: ", end="")
        print([slot + 1 for slot in scheduled_actions.keys()])
        
        # Verifica se o primeiro slot é um alvo antes de iniciar o loop de rotação
        check_and_attack(current_line_index)

        # Loop de rotação e ataque nos slots agendados
        # Condição de paragem: se o robot deu uma volta completa ou passou por todas as 6 linhas
        while scanning:
            
            if accumulated_angle >= FULL_TURN_MIN_ANGLE or current_line_index >= 6:
                print("Volta completa. De regresso a posicao inicial.")
                break

            gyro.reset()
            
            tank_pair.on(left_speed=spin_speed * -1, right_speed=spin_speed)
            sleep(0.5) 

            while color_sensor.color_name != LINE_COLOR_NAME:
                sleep(0.01)
            
            tank_pair.off()

            segment_angle = abs(gyro.angle)
            accumulated_angle += segment_angle
            
            # Lógica para corrigir se o robot saltar uma ou mais linhas
            if segment_angle > SKIPPED_LINE_ANGLE_THRESHOLD and current_line_index < 5:
                num_skipped = round(segment_angle / EXPECTED_SEGMENT_ANGLE) - 1
                if num_skipped > 0:
                    print("O robot saltou {} linha(s). A corrigir indice.".format(num_skipped))
                    current_line_index += num_skipped

            current_line_index += 1
            print("Chegou a Linha {}".format(current_line_index)) 
            
            # Verifica se a linha atual é o alvo e ataca se for um alvo agendado
            check_and_attack(current_line_index)
            
    except KeyboardInterrupt:
        print("\nPrograma interrompido pelo utilizador.")
        raise
    except Exception as e:
        print("Erro durante a rotacao e ataque: {}".format(e)) 
    finally:
        tank_pair.off()