from ev3dev2.sound import Sound
import os
import random

# Simula o lançamento de um dado digital 
# Retorna um valor entre 1 e 6
# Vai ser usado em print_initial_setup para determinar o tipo de unidade e o turno inicial
def roll_digital_dice():
    return random.randint(1, 6)



# Gera e imprime a tabela de configuração inicial do jogo.
# Determina aleatoriamente para cada um dos 6 slots, o tipo de inimigo e o turno em que aparecerá.
# Os tipos são definidos pelo numero do dado: Tanque (1-2), Artilharia (3-4) e Infantaria (5-6).
def print_initial_setup():
    print("=" * 60)
    print("{:<10} | {:<18} | {:<20}".format("Posicao", "Tipo de atacante", "Turno inicial (1-6)"))
    print("=" * 60)
    
    for i in range(1, 7):
        dice_type = roll_digital_dice()
        dice_turn = roll_digital_dice()
    
        if dice_type <= 2:
            unit = "Tanque (Verde)"
        elif dice_type <= 4:
            unit = "Artilharia (Amarelo)"
        else:
            unit = "Infantaria (Azul)"
    
        print("Slot{:<4} | {:<18} | {:<20}".format(i, unit, dice_turn))
    
    print("=" * 60)



# Garante que a velocidade do motor está entre -100 e 100
def clamp_speed(speed):
    if speed > 100:
        return 100
    if speed < -100:
        return -100
    return speed



# Toca musica de fundo em loop até o evento de paragem ser ativado
# Usado para tocar musica enquanto o robo faz o reconhecimento do ambiente
def background_music_loop(stop_event):
    speaker = Sound()
    
    SOUND_FILE = 'search_song.wav'

    while not stop_event.is_set():
        try:
            speaker.play_file(SOUND_FILE, volume=100)
        except Exception as e:
            print("Erro: Nao foi possivel encontrar o ficheiro de musica 'search_song.wav': {}".format(e))
            return



# Usado para tocar um som especifico
# win.wav quando o jogador vence
# defeat.wav quando o jogador perde
# enemy_down.wav quando um inimigo é derrotado
def playSound(sound):
    speaker = Sound()
    speaker.play_file(sound, volume=100)
