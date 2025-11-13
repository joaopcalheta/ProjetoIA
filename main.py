#!/usr/bin/env python3

from time import sleep, time # <-- MUDANCA AQUI: Adicionado 'time'
from ev3dev2.motor import (SpeedPercent, MoveTank, OUTPUT_B, OUTPUT_C)
from ev3dev2.sensor.lego import ColorSensor, UltrasonicSensor, GyroSensor
from ev3dev2.sensor import INPUT_1, INPUT_2, INPUT_4

# Inicializa o MoveTank (motores B e C)
tank_pair = MoveTank(OUTPUT_B, OUTPUT_C)

# --- FUNCAO MODIFICADA (LOGICA DE "SWEEP" / VARREDURA) ---
def follow_line_with_gyro(gyro, color_sensor, us_sensor, tank_pair, base_speed, kp):
    """
    Funcao MODIFICADA para seguir linha com "sweep" (varredura).
    1. Tenta andar a direito (usando o Gyro) ENQUANTO ve 'Red'.
    2. Se perder o 'Red', PARA de avancar.
    3. GIRA 1.5s para a Esquerda (procura).
    4. Se nao encontrar, GIRA 3.0s para a Direita (procura).
    5. Se encontrar, zera o Gyro e continua.
    6. PARA APENAS se o sensor ultrassonico detetar algo a < 10cm.
    """
    print("A iniciar seguimento (Modo: Gyro + Sweep)...")
    print("KP (Ganho): {}".format(kp))
    
    gyro.reset()
    target_angle = 0
    
    # Loop principal: continua ENQUANTO esta a mais de 10cm
    while us_sensor.distance_centimeters > 10:
        
        if color_sensor.color_name == 'Red':
            # --- 1. ESTA NA LINHA ---
            # Usa o Gyro para andar a direito (logica original)
            current_angle = gyro.angle
            correction = current_angle - target_angle
            turn_power = kp * correction
            
            left_speed = base_speed + turn_power
            right_speed = base_speed - turn_power
            
            tank_pair.on(SpeedPercent(left_speed), SpeedPercent(right_speed))
            
        else:
            # --- 2. PERDEU A LINHA ---
            # Para de avancar e inicia a "varredura"
            tank_pair.off()
            print("...Perdi o 'Red'. A procurar (Sweep Esquerda)...")
            
            spin_search_speed = 15 # Velocidade de giro da procura
            found_line = False
            
            # --- 3. PROCURA ESQUERDA (1.5 segundos) ---
            # (Gira para a Esquerda)
            tank_pair.on(SpeedPercent(spin_search_speed), SpeedPercent(-spin_search_speed))
            
            start_search_time = time()
            while (time() - start_search_time) < 0.5:
                if color_sensor.color_name == 'Red':
                    found_line = True
                    break
                if us_sensor.distance_centimeters <= 10:
                    break # Objeto perto, para tudo
                sleep(0.01)
                
            # Se encontrou a linha
            if found_line:
                print("... 'Red' reencontrado (Esq). A zerar Gyro e continuar.")
                gyro.reset()
                target_angle = 0
                continue # Volta ao inicio do 'while > 10'
                
            # Se viu o objeto
            if us_sensor.distance_centimeters <= 10:
                print("...Objeto detetado durante a procura (Esq).")
                break # Sai do 'while > 10' e termina a funcao

            # --- 4. PROCURA DIREITA (3.0 segundos) ---
            # Nao encontrou a Esquerda, procura a Direita
            print("...Nao encontrou (Esq). A procurar (Sweep Direita)...")
            
            # Gira para a Direita o dobro do tempo (para cobrir o centro e o lado dir)
            tank_pair.on(SpeedPercent(-spin_search_speed), SpeedPercent(spin_search_speed))
            
            start_search_time = time()
            while (time() - start_search_time) < 3.0: # 1.5s (Volta) + 1.5s (Procura Dir)
                if color_sensor.color_name == 'Red':
                    found_line = True
                    break
                if us_sensor.distance_centimeters <= 10:
                    break # Objeto perto, para tudo
                sleep(0.01)

            # Se encontrou a linha
            if found_line:
                print("... 'Red' reencontrado (Dir). A zerar Gyro e continuar.")
                gyro.reset()
                target_angle = 0
                continue # Volta ao inicio do 'while > 10'

            # Se viu o objeto
            if us_sensor.distance_centimeters <= 10:
                print("...Objeto detetado durante a procura (Dir).")
                break # Sai do 'while > 10' e termina a funcao
                
            # --- 5. FALHOU A PROCURA ---
            # Se chegou aqui, nao encontrou nem a Esq nem a Dir
            print("!!! PROCURA FALHOU. Linha perdida. A parar.")
            break # Sai do 'while > 10' e termina a funcao

        sleep(0.01) # Sleep principal do loop

    # --- PARAGEM ---
    tank_pair.off()
    
    if us_sensor.distance_centimeters <= 10:
        print("!!! Objeto a < 10cm detetado. A parar.")
    else:
        print("!!! Seguimento terminado.")
        
    if color_sensor.color_name != 'Red':
        print("...Parou fora da linha vermelha.")
    else:
        print("...Parou em cima da linha vermelha.")


def run_challenge(color_sensor, us_sensor, gyro, spin_speed=20, forward_speed=15):
    """
    Loop principal do desafio autonomo.
    (Sem alteracoes aqui)
    """
    
    KP_GAIN = 1.5 
    print("A iniciar desafio... (Giro: {}%, Avanco: {}%)".format(spin_speed, forward_speed))
    
    try:
        while True:
            # --- ESTADO 1: A PROCURAR A LINHA (GIRAR) ---
            print("--- ESTADO 1: A procurar linha vermelha...")
            tank_pair.on(left_speed=SpeedPercent(spin_speed * -1), right_speed=SpeedPercent(spin_speed))

            while color_sensor.color_name != 'Red':
                sleep(0.01) 
            
            # --- ESTADO 2: LINHA ENCONTRADA / VERIFICAR OBJETO ---
            tank_pair.off()
            print("!!! Linha vermelha detetada! Robo parado. !!!")
            print("--- ESTADO 2: A verificar distancia...")
            
            sleep(0.1) 
            distance_cm = us_sensor.distance_centimeters
            
            if distance_cm < 45:
                # Objeto ENCONTRADO.
                print(">>> Objeto detetado a {:.1f} cm.".format(distance_cm))
                
                # --- ESTADO 3: SEGUIR A LINHA ATE AO OBJETO ---
                print("--- ESTADO 3: A seguir linha/aproximar do objeto...")
                follow_line_with_gyro(
                    gyro=gyro, 
                    color_sensor=color_sensor,
                    us_sensor=us_sensor,
                    tank_pair=tank_pair, 
                    base_speed=forward_speed, # -20 (marcha-atras)
                    kp=KP_GAIN
                )
                
                print("Acao terminada. A voltar ao ESTADO 1.")
                
            else:
                # Caminho LIVRE.
                print(">>> Caminho livre (objeto a {:.1f} cm). A sair da linha atual...".format(distance_cm))
                
                # --- ESTADO 4: SAIR DA LINHA ATUAL ---
                tank_pair.on(left_speed=SpeedPercent(spin_speed * -1), right_speed=SpeedPercent(spin_speed))
                
                while color_sensor.color_name == 'Red':
                    sleep(0.01)
                
                print("...Fora da linha. A procurar a proxima (ESTADO 1).")
            
            sleep(1.0) # Pausa entre ciclos

    except KeyboardInterrupt:
        print("\nPrograma interrompido pelo utilizador.")
    except Exception as e:
        print("Ocorreu um erro durante o ciclo: {}".format(e))
    finally:
        tank_pair.off()
        print("Motores de locomocao parados.")


if __name__ == "__main__":
    color_sensor = None 
    us_sensor = None
    gyro_sensor = None
    try:
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

        # Chama a funcao principal
        run_challenge(color_sensor=color_sensor, 
                      us_sensor=us_sensor, 
                      gyro=gyro_sensor,
                      spin_speed=20,      
                      forward_speed=-20) # Manteve a velocidade negativa (marcha-atras)
    
    except Exception as e:
        print("Ocorreu um erro fatal na inicializacao: {}".format(e))
        print("Verifique se os sensores estao nas portas corretas (1, 2, e 4).")
        print("A garantir que todos os motores estao parados.")
        tank_pair.off()