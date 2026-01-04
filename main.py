import os
from hardware import initialize_hardware
from tools import print_initial_setup
from game_logic import check_game_status, handle_game_over
from robot_heal_attack_logic import robot_turn_logic
from enemy_attack_logic import enemy_attack_phase
from initialize_robot_enemies import initialize_robot, initialize_enemies_by_color
from robot_movement_logic import search_enemies
from config import (OBSTACLE_STOP_DISTANCE_CM, OBJECT_SEARCH_DISTANCE_CM, LINE_COLOR_NAME, SPIN_SEARCH_SPEED, SEARCH_TIME_LEFT_S, SEARCH_TIME_RIGHT_S)

# Array global para armazenar os inimigos encontrados nas 6 posições disponiveis
enemies = [None] * 6      


# Loop principal do jogo que controla a progressão do jogo turno a turno
# Realiza o reconhecimento do ambiente até ao turno 6 (ultimo turno em que surgem novos inimigos)
# Recupera a energia do robot, reseta os ataques e curas usadas no turno anterior
# Realiza a fase de ataque dos inimigos no inicio de cada turno (inimigos que o robot não matou)
# Realiza a fase de ataque e cura do robot
# Verifica se o jogo já terminou no final dos ataques do robot e depois dos ataques dos inimigos
def run_game_loop(robot, tank_pair, medium_motor, color_sensor, us_sensor, gyro, spin_speed, forward_speed):
    
    current_turn = 1
    try:
        while True:
            print("\n=== TURNO {} ===".format(current_turn))
            if(current_turn != 1):
                robot.start_new_turn()
                print("ROBOT RECUPERA 50% DE ENERGIA E DA RESET NOS REGISTOS DE ATAQUES E CURAS DO TURNO ANTERIOR")
                print("Energia do Robot: {:.0f}EN".format(robot.energy))
                
                print("FASE DE ATAQUE DOS INIMIGOS")
                enemy_attack_phase(robot, enemies, current_turn)
                print("Vida do Robot: {:.0f}HP".format(robot.current_health))



            game_status = check_game_status(robot, enemies)
            if((current_turn > 6 and game_status == "victory") or game_status == "defeat"):
                handle_game_over(game_status)
                break
            
            input(">>> Pressiona ENTER para iniciar o reconhecimento do ambiente do turno {}".format(current_turn))

            if(current_turn <= 6):
                enemies_log = search_enemies(
                    tank_pair=tank_pair,
                    medium_motor=medium_motor, 
                    color_sensor=color_sensor, 
                    us_sensor=us_sensor, 
                    gyro=gyro,
                    spin_speed=spin_speed,
                    forward_speed=forward_speed,
                    enemies=enemies
                )

            print("\nResultado do Turno {}: {}".format(current_turn, enemies_log))
            new_enemies_list = initialize_enemies_by_color(enemies_log, current_turn)
            
            for i, new_enemy in enumerate(new_enemies_list):
                if enemies[i] is None and new_enemy is not None:
                    print("Novo inimigo adicionado na Posicao {}".format(i))
                    enemies[i] = new_enemy
            
            print("\n--- Campo de Batalha Atual (Turno {}) ---".format(current_turn))
            for i, enemy in enumerate(enemies):
                if enemy is None:
                    print("Posicao {}: Vazio".format(i+1))
                else:
                    print("Posicao {}: {}".format(i+1, enemy))

            print("FASE DE ATAQUE / CURA DO ROBOT")
            robot_turn_logic(
                tank_pair=tank_pair,
                medium_motor=medium_motor, 
                color_sensor=color_sensor, 
                gyro=gyro,
                us_sensor=us_sensor, 
                spin_speed=spin_speed,
                forward_speed=forward_speed,
                robot=robot, 
                enemies_list=enemies)
            
            print("\n--- Campo de Batalha Apos Ataques (Turno {}) ---".format(current_turn))
            for i, enemy in enumerate(enemies):
                if enemy is None:
                    print("Posicao {}: Vazio".format(i+1))
                else:
                    print("Posicao {}: {}".format(i+1, enemy))

            game_status = check_game_status(robot, enemies)
            if((current_turn > 6 and game_status == "victory") or game_status == "defeat"):
                handle_game_over(game_status)
                break
            
            current_turn += 1
            print("-" * 30)

    except KeyboardInterrupt:
        print("\nPrograma interrompido pelo utilizador.")
    except Exception as e:
        print("Erro: {}".format(e))
    finally:
        tank_pair.off()
        medium_motor.off()



# Inicializa o hardware do robot
# Imprime a tabela inicial de configuração do robot e inimigos
# Inicia o loop principal do jogo
def main():

    tank_pair, medium_motor, color_sensor, us_sensor, gyro_sensor = initialize_hardware()
    
    if tank_pair is not None:
        
        robot = initialize_robot()
        print_initial_setup() 
        
        run_game_loop(
            robot=robot,
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