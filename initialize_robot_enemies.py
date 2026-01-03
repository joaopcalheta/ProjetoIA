import random
from time import sleep, time
from ev3dev2.motor import (SpeedPercent, MoveTank, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C)
from ev3dev2.sensor.lego import ColorSensor, UltrasonicSensor, GyroSensor
from ev3dev2.sensor import INPUT_1, INPUT_2, INPUT_4

from tools import print_initial_setup, roll_digital_dice, clamp_speed
from enemy_class import ENEMY_STATS, Enemy
from robot_class import ROBOT_ATTACKS, ROBOT_HEALS, Robot
from robot_attacks import touch_attack, sound_attack, crane_attack
from game_logic import check_game_status, handle_game_over
from robot_movement_logic import search_enemies
from robot_heal_attack_logic import robot_turn_logic
from enemy_attack_logic import enemy_attack_phase


# Instancia o objeto principal do Robot.
# Cria a entidade do jogador com os atributos iniciais de vida e energia definidos na classe Robot.
def initialize_robot():
    robot = Robot()
    print("Robot inicializado com {:.0f}HP e {:.0f}EN.".format(robot.current_health, robot.energy))
    return robot



# Converte uma lista de cores (detetadas pelos sensores) em instâncias da classe Enemy.
# Mapeia as cores lidas pelo sensor de cor para tipos específicos de unidades inimigas.
# Faz o ajuste de "Yellow" para "Brown" devido à limitação do sensor.
def initialize_enemies_by_color(color_list, current_turn):
    enemy_object_list = []

    for i, color in enumerate(color_list):
        if color == "Empty":
            enemy_object_list.append(None) 

        else:
            found_type = None
            color_found = color
            if color_found == "Yellow":
                color_found = "Brown"

            for type, stats in ENEMY_STATS.items():
                if stats['color'] == color_found:
                    found_type = type
                    break
            
            if found_type:
                new_enemy = Enemy(found_type, current_turn, i+1)
                enemy_object_list.append(new_enemy)
                print("Slot {}: Criado inimigo '{}' (Cor: {})".format(i+1, found_type, color_found))
            else:
                print("Slot {}: Inimigo ignorado (Cor desconhecida: '{}').".format(i+1, color_found))
                enemy_object_list.append(None)

    return enemy_object_list

