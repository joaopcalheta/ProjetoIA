from time import sleep, time
from ev3dev2.motor import (SpeedPercent, MoveTank, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C)
from ev3dev2.sensor.lego import ColorSensor
from ev3dev2.sound import Sound

from config import LINE_COLOR_NAME

# Executa o Ataque de Som.
# Utiliza o altifalante interno do brick EV3 para emitir um sinal sonoro (beep).
def sound_attack():
    speaker = Sound()
    speaker.beep()

# Executa o Ataque de Toque.
# Simula um impacto físico fazendo o robot recuar brevemente e avançar com velocidade contra o alvo.
def touch_attack(tank_pair):
    tank_pair.on_for_rotations(SpeedPercent(-55), SpeedPercent(-55), 0.2)
    sleep(0.2)
    tank_pair.on_for_rotations(SpeedPercent(55), SpeedPercent(55), 0.2)

# Executa o Ataque de Grua.
# O robot roda 180º para usar a grua para atacar o inimigo 
# Ativa o motor da arma e regressa à orientação original.
def crane_attack(tank_pair, weapon_motor, color_sensor):
    
    # Fica de costas para o inimigo (-180º)
    tank_pair.on_for_rotations(SpeedPercent(30), SpeedPercent(30), 0.5)
    tank_pair.on(SpeedPercent(20), SpeedPercent(-20))
    sleep(1.0)
    while color_sensor.color_name != LINE_COLOR_NAME:
        sleep(0.01)
    tank_pair.off()
    tank_pair.on_for_rotations(SpeedPercent(20), SpeedPercent(20), 0.5)

    # Ativa o ataque (mexe o motor)
    weapon_motor.on_for_seconds(SpeedPercent(70), seconds=2)

    # Volta à posição inicial (+180º)
    tank_pair.on_for_rotations(SpeedPercent(-20), SpeedPercent(-20), 0.5)
    tank_pair.on(SpeedPercent(-20), SpeedPercent(20))
    sleep(1.0)
    while color_sensor.color_name != LINE_COLOR_NAME:
        sleep(0.01)
    tank_pair.off()
    tank_pair.on_for_rotations(SpeedPercent(-20), SpeedPercent(-20), 0.5)