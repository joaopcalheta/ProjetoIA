from ev3dev2.sound import Sound
import random

# Tocar ficheiro WAV
def play_wav(file_path, volume=100):
    try:
        speaker = Sound()
        speaker.set_volume(volume)
        speaker.play_file(file_path)
    except:
        pass


# Rola dado 
def roll_digital_dice():
    return random.randint(1, 6)


# Imprime a tabela do enunciado preenchida
def print_initial_setup():
    # O 'ç' em 'Posicao' foi removido para evitar erros de codificacao.
    print("=" * 60)
    print("{:<10} | {:<18} | {:<20}".format("Posicao", "Tipo de atacante", "Turno inicial (1-6)"))
    print("=" * 60)
    
    for i in range(1, 7):
        dice_type = roll_digital_dice()
        dice_turn = roll_digital_dice()
    
        if dice_type <= 2:
            unit = "Tanque"
        elif dice_type <= 4:
            unit = "Artilharia"
        else:
            unit = "Infantaria"
    
        print("Slot{:<4} | {:<18} | {:<20}".format(i, unit, dice_turn))
    
    print("=" * 60)


# Garante que a velocidade do motor está entre -100 e 100
def clamp_speed(speed):
    if speed > 100:
        return 100
    if speed < -100:
        return -100
    return speed