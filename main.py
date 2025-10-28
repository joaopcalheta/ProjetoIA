#!/usr/bin/env python3

from time import sleep, time
from ev3dev2.motor import (SpeedPercent, MoveTank, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C)
from ev3dev2.sensor.lego import UltrasonicSensor
from ev3dev2.sensor import INPUT_1


# Inicializa o MoveTank (motores de locomoção) usando OUTPUT_B e OUTPUT_C
# Esta variável é global para ser acedida por múltiplas funções (se necessário)
# e no bloco 'finally' para garantir que pára.
tank_pair = MoveTank(OUTPUT_B, OUTPUT_C)


def spin_and_scan(sensor, motor_a, duration_seconds=20, speed=50, motor_a_speed=75):
    """
    Gira os motores B & C (tank_pair) durante um determinado tempo.
    Enquanto gira, verifica o sensor ultrassónico.
    Se a distância < 40cm, ativa o motor_a.
    Caso contrário, o motor_a é parado.

    :param sensor: O objeto UltrasonicSensor inicializado.
    :param motor_a: O objeto MediumMotor (ou LargeMotor) inicializado.
    :param duration_seconds: Duração total (em segundos) da operação.
    :param speed: Velocidade (percentagem) para os motores do tank_pair.
    :param motor_a_speed: Velocidade (percentagem) para o motor_a quando ativado.

    """
    print("A girar motores e a fazer scan por {} segundos...".format(duration_seconds))

    # Obtém o tempo atual para marcar o início
    start_time = time()

    # Inicia a rotação dos motores (um para a frente, um para trás)
    tank_pair.on(left_speed=SpeedPercent(speed * -1), right_speed=SpeedPercent(speed))

    # Inicia um ciclo (loop) que corre durante o tempo desejado
    try:
        while (time() - start_time) < duration_seconds:
            
            # Verifica a distância do sensor
            distance_cm = sensor.distance_centimeters
            print("Distância: {:.1f} cm".format(distance_cm))

            # Se a distância for < 40cm, ativa o motor A
            if distance_cm < 40:
                print("!!! Objeto detetado! Distância: {:.1f} cm. A ativar motor A.".format(distance_cm))
                motor_a.on(SpeedPercent(motor_a_speed)) # Ativa o motor A à velocidade definida
            
            # Se nenhum objeto for detetado (ou estiver > 40cm), pára o motor A
            else:
                motor_a.off() # Pára o motor A

            # Espera um curto período de tempo
            sleep(0.1)  # Verifica 10 vezes por segundo

    except Exception as e:
        print("Ocorreu um erro durante o ciclo: {}".format(e))
    finally:
        # Pára todos os motores depois do ciclo terminar (ou se ocorrer um erro)
        tank_pair.off()
        motor_a.off()
        print("Todos os motores pararam.")






# O bloco "if __name__ == '__main__':" é o ponto de entrada principal do script
# O código aqui dentro só é executado quando o ficheiro é corrido diretamente
if __name__ == "__main__":
    us_sensor = None # Variável para o sensor
    motor_a = None   # Variável para o motor A
    try:
        # Inicializa o sensor na porta INPUT_1
        us_sensor = UltrasonicSensor(INPUT_1)
        print("Sensor ultrassónico ligado.")

        # Inicializa o Motor A (Médio)
        motor_a = MediumMotor(OUTPUT_A)  # <-- Alterado para MediumMotor
        print("Motor A (Médio) ligado.")

        # Chama a função principal
        spin_and_scan(sensor=us_sensor,
                      motor_a=motor_a,
                      duration_seconds=10, # <-- Duração total
                      speed=20,            # <-- Velocidade de rotação
                      motor_a_speed=50)    # <-- Velocidade do motor A

    except Exception as e:
        print("Ocorreu um erro na inicialização ou execução: {}".format(e))
        print("A garantir que todos os motores estão parados.")
        # Garante que todos os motores param mesmo que ocorra um erro na inicialização
        tank_pair.off()
        if motor_a:        # Verifica se motor_a chegou a ser inicializado
            motor_a.off()