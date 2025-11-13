#!/usr/bin/env python3

from time import sleep, time
from ev3dev2.motor import (SpeedPercent, MoveTank, OUTPUT_B, OUTPUT_C)
from ev3dev2.sensor.lego import ColorSensor, UltrasonicSensor, GyroSensor
from ev3dev2.sensor import INPUT_1, INPUT_2, INPUT_4

# Define constantes para facilitar a leitura
OBSTACLE_STOP_DISTANCE_CM = 10
OBJECT_SEARCH_DISTANCE_CM = 45
LINE_COLOR_NAME = 'Red'
SPIN_SEARCH_SPEED = 15
SEARCH_TIME_LEFT_S = 0.3
SEARCH_TIME_RIGHT_S = 3.0


def _follow_straight_on_line(tank_pair, gyro, base_speed, kp, target_angle):
    """
    Aplica a correção do giroscópio para manter o robô a andar em frente.
    Esta é a lógica de seguimento de linha (Proporcional).
    """
    current_angle = gyro.angle
    correction = current_angle - target_angle
    turn_power = kp * correction
    
    left_speed = base_speed + turn_power
    right_speed = base_speed - turn_power
    
    tank_pair.on(SpeedPercent(left_speed), SpeedPercent(right_speed))


def _perform_search_spin(tank_pair, color_sensor, us_sensor, duration_s, left_speed, right_speed):
    """
    Gira numa direção específica por um tempo_s, procurando a linha ou um obstáculo.
    Retorna 'FOUND_LINE', 'FOUND_OBSTACLE', ou 'NOT_FOUND'.
    """
    tank_pair.on(SpeedPercent(left_speed), SpeedPercent(right_speed))
    start_search_time = time()
    
    while (time() - start_search_time) < duration_s:
        if color_sensor.color_name == LINE_COLOR_NAME:
            return 'FOUND_LINE'
        if us_sensor.distance_centimeters <= OBSTACLE_STOP_DISTANCE_CM:
            return 'FOUND_OBSTACLE'
        sleep(0.01)
        
    return 'NOT_FOUND'


def _search_for_lost_line(tank_pair, color_sensor, us_sensor, gyro):
    """
    Executa a lógica de "sweep" (varredura) para reencontrar a linha.
    Para o robô, procura à esquerda e depois à direita.
    Retorna 'FOUND_LINE', 'FOUND_OBSTACLE', ou 'NOT_FOUND'.
    """
    tank_pair.off()
    print("...Perdi o 'Red'. A procurar (Sweep Esquerda)...")

    # 3. PROCURA ESQUERDA
    search_result = _perform_search_spin(
        tank_pair, color_sensor, us_sensor,
        duration_s=SEARCH_TIME_LEFT_S,
        left_speed=SPIN_SEARCH_SPEED,
        right_speed=-SPIN_SEARCH_SPEED
    )
    
    if search_result == 'FOUND_LINE':
        print("... 'Red' reencontrado (Esq). A zerar Gyro e continuar.")
        gyro.reset()
        return 'FOUND_LINE'
    
    if search_result == 'FOUND_OBSTACLE':
        print("...Objeto detetado durante a procura (Esq).")
        return 'FOUND_OBSTACLE'

    # 4. PROCURA DIREITA
    print("...Nao encontrou (Esq). A procurar (Sweep Direita)...")
    search_result = _perform_search_spin(
        tank_pair, color_sensor, us_sensor,
        duration_s=SEARCH_TIME_RIGHT_S,
        left_speed=-SPIN_SEARCH_SPEED,
        right_speed=SPIN_SEARCH_SPEED
    )

    if search_result == 'FOUND_LINE':
        print("... 'Red' reencontrado (Dir). A zerar Gyro e continuar.")
        gyro.reset()
        return 'FOUND_LINE'
        
    if search_result == 'FOUND_OBSTACLE':
        print("...Objeto detetado durante a procura (Dir).")
        return 'FOUND_OBSTACLE'

    # 5. FALHOU A PROCURA
    print("!!! PROCURA FALHOU. Linha perdida. A parar.")
    return 'NOT_FOUND'


def follow_line_until_obstacle(tank_pair, gyro, color_sensor, us_sensor, base_speed, kp):
    """
    Função principal de seguimento de linha.
    Segue a linha usando o giroscópio e ativa a procura se a perder.
    Para se o sensor US detetar algo a < OBSTACLE_STOP_DISTANCE_CM.
    """
    # MUDANÇA AQUI: Trocado f-string por .format()
    print("A iniciar seguimento (Modo: Gyro + Sweep) a {}%...".format(base_speed))
    print("KP (Ganho): {}".format(kp))
    
    gyro.reset()
    target_angle = 0
    
    while us_sensor.distance_centimeters > OBSTACLE_STOP_DISTANCE_CM:
        
        if color_sensor.color_name == LINE_COLOR_NAME:
            # 1. ESTÁ NA LINHA
            _follow_straight_on_line(tank_pair, gyro, base_speed, kp, target_angle)
        
        else:
            # 2. PERDEU A LINHA
            search_status = _search_for_lost_line(tank_pair, color_sensor, us_sensor, gyro)
            
            if search_status == 'FOUND_LINE':
                target_angle = 0  # O Gyro foi resetado na função de procura
                continue
            else:
                # 'FOUND_OBSTACLE' ou 'NOT_FOUND'
                break  # Sai do loop principal de seguimento

        sleep(0.01)

    # --- PARAGEM ---
    tank_pair.off()
    
    if us_sensor.distance_centimeters <= OBSTACLE_STOP_DISTANCE_CM:
        # MUDANÇA AQUI: Trocado f-string por .format()
        print("!!! Objeto a < {}cm detetado. A parar.".format(OBSTACLE_STOP_DISTANCE_CM))
    else:
        print("!!! Seguimento terminado (linha perdida).")
        
    if color_sensor.color_name != LINE_COLOR_NAME:
        print("...Parou fora da linha vermelha.")
    else:
        print("...Parou em cima da linha vermelha.")


def run_challenge(tank_pair, color_sensor, us_sensor, gyro, spin_speed, forward_speed):
    """
    Loop principal do desafio autônomo, gerindo os estados.
    """
    KP_GAIN = 1.5 
    # MUDANÇA AQUI: Trocado f-string por .format()
    print("A iniciar desafio... (Giro: {}%, Avanco: {}%)".format(spin_speed, forward_speed))
    
    try:
        while True:
            # --- ESTADO 1: A PROCURAR A LINHA (GIRAR) ---
            print("--- ESTADO 1: A procurar linha vermelha...")
            tank_pair.on(left_speed=SpeedPercent(spin_speed * -1), right_speed=SpeedPercent(spin_speed))

            while color_sensor.color_name != LINE_COLOR_NAME:
                sleep(0.01) 
            
            # --- ESTADO 2: LINHA ENCONTRADA / VERIFICAR OBJETO ---
            tank_pair.off()
            print("!!! Linha vermelha detetada! Robo parado. !!!")
            print("--- ESTADO 2: A verificar distancia...")
            
            sleep(0.1) 
            distance_cm = us_sensor.distance_centimeters
            
            if distance_cm < OBJECT_SEARCH_DISTANCE_CM:
                # Objeto ENCONTRADO.
                # MUDANÇA AQUI: Trocado f-string por .format()
                print(">>> Objeto detetado a {:.1f} cm.".format(distance_cm))
                
                # --- ESTADO 3: SEGUIR A LINHA ATE AO OBJETO ---
                print("--- ESTADO 3: A seguir linha/aproximar do objeto...")
                follow_line_until_obstacle(
                    tank_pair=tank_pair,
                    gyro=gyro, 
                    color_sensor=color_sensor,
                    us_sensor=us_sensor,
                    base_speed=forward_speed,
                    kp=KP_GAIN
                )
                
                print("Acao terminada. A voltar ao ESTADO 1.")
                
            else:
                # Caminho LIVRE.
                # MUDANÇA AQUI: Trocado f-string por .format()
                print(">>> Caminho livre (objeto a {:.1f} cm). A sair da linha atual...".format(distance_cm))
                
                # --- ESTADO 4: SAIR DA LINHA ATUAL ---
                tank_pair.on(left_speed=SpeedPercent(spin_speed * -1), right_speed=SpeedPercent(spin_speed))
                
                while color_sensor.color_name == LINE_COLOR_NAME:
                    sleep(0.01)
                
                print("...Fora da linha. A procurar a proxima (ESTADO 1).")
            
            sleep(1.0) # Pausa entre ciclos

    except KeyboardInterrupt:
        print("\nPrograma interrompido pelo utilizador.")
    except Exception as e:
        # MUDANÇA AQUI: Trocado f-string por .format()
        print("Ocorreu um erro durante o ciclo: {}".format(e))
    finally:
        tank_pair.off()
        print("Motores de locomocao parados.")


def initialize_hardware():
    """
    Inicializa todos os motores e sensores.
    Retorna os objetos (tank_pair, color_sensor, us_sensor, gyro_sensor)
    ou None se falhar.
    """
    try:
        # Motores (Portas B e C)
        tank_pair = MoveTank(OUTPUT_B, OUTPUT_C)
        print("Motores (B, C) OK.")

        # Sensor de Cor (Porta 4)
        color_sensor = ColorSensor(INPUT_4)
        color_sensor.mode = 'COL-COLOR'
        print("Sensor de cor (Porta 4) OK.")
        
        # Sensor Ultrassonico (Porta 1)
        us_sensor = UltrasonicSensor(INPUT_1)
        us_sensor.mode = 'US-DIST-CM'
        print("Sensor ultrassonico (Porta 1) OK.")
        
        # Sensor Giroscopio (Porta 2)
        gyro_sensor = GyroSensor(INPUT_2)
        gyro_sensor.mode = 'GYRO-ANG' 
        print("Sensor Giroscopio (Porta 2) OK. A calibrar...")
        sleep(2.0) # Nao mexer no robo!
        gyro_sensor.reset() 
        print("Giroscopio calibrado e zerado. Pronto.")
        
        return tank_pair, color_sensor, us_sensor, gyro_sensor

    except Exception as e:
        # MUDANÇA AQUI: Trocado f-string por .format()
        print("Ocorreu um erro fatal na inicializacao: {}".format(e))
        print("Verifique se os sensores estao nas portas corretas (1, 2, e 4) e motores (B, C).")
        return None, None, None, None


def main():
    """
    Ponto de entrada principal do programa.
    """
    tank_pair, color_sensor, us_sensor, gyro_sensor = initialize_hardware()
    
    if tank_pair is not None:
        # Chama a funcao principal
        run_challenge(
            tank_pair=tank_pair,
            color_sensor=color_sensor, 
            us_sensor=us_sensor, 
            gyro=gyro_sensor,
            spin_speed=20,
            forward_speed=-20  # Manteve a velocidade negativa (marcha-atrás)
        )
    else:
        print("Falha ao inicializar hardware. A sair.")


if __name__ == "__main__":
    main()