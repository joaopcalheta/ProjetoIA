from robot_class import ROBOT_ATTACKS, ROBOT_HEALS, Robot
# Lógica de cura e de ataque do robot por turno
def robot_turn_logic(robot, enemies_list):

    # LÓGICA DE CURA
    
    # Vai tentar curar se tiver a vida menor que 500
    if robot.current_health < 500 and not robot.heal_used_this_turn:
        
        # Tenta usar a cura mais forte primeiro
        for heal_type in ["heal3", "heal2", "heal1"]:
            heal_info = ROBOT_HEALS[heal_type]
            if robot.energy >= heal_info["cost"]:
                if robot.heal(heal_type):
                    print("O Robot usou a Cura '{}' (Custo {}EN) e recuperou {} de vida. Vida atual: {:.0f}. Energia restante: {:.0f}.".format(
                        heal_type, heal_info["cost"], heal_info["health_recovered"], robot.current_health, robot.energy
                    ))
                    break


    # LÓGICA DE ATAQUE

    # Vai tentar atacar se tiver mais de 200 de energia
    if robot.energy > 200:
        
        # Encontra o inimigo vivo mais forte que ainda não foi atacado neste turno
        best_target = None
        best_target_strength = -1
        best_target_id = -1
        for i, enemy in enumerate(enemies_list):
            slot_id = i + 1
            if enemy and enemy.is_alive() and slot_id not in robot.slots_attacked_this_turn:
                if enemy.force > best_target_strength:
                    best_target = enemy
                    best_target_strength = enemy.force
                    best_target_id = slot_id

        # Ataca o alvo escolhido
        if best_target:
            print("Robot escolheu como alvo o Slot {} ({}).".format(best_target_id, best_target.type))

            attack_to_use = None
            
            # Se o inimigo for fraco, usa um ataque mais barato para o eliminar
            if best_target.current_health <= ROBOT_ATTACKS["sound"]["damage"] and robot.energy >= ROBOT_ATTACKS["sound"]["cost"]:
                attack_to_use = "sound"
            elif best_target.current_health <= ROBOT_ATTACKS["touch"]["damage"] and robot.energy >= ROBOT_ATTACKS["touch"]["cost"]:
                attack_to_use = "touch"
            
            # Se não, usa o ataque mais forte que puder pagar, mas mantendo uma reserva de 100 de energia
            elif robot.energy - ROBOT_ATTACKS["crane"]["cost"] > 100:
                attack_to_use = "crane"
            elif robot.energy - ROBOT_ATTACKS["touch"]["cost"] > 100:
                attack_to_use = "touch"
            elif robot.energy - ROBOT_ATTACKS["sound"]["cost"] > 100:
                attack_to_use = "sound"

            if attack_to_use:
                robot.attack_slot(attack_type=attack_to_use, slot_id=best_target_id, enemies=enemies_list)
                print("O Robot usou o Ataque '{}' (Custo {}EN) no Inimigo {} do Slot {}, deu {} de dano. Energia restante: {:.0f}.".format(
                        attack_to_use, ROBOT_ATTACKS[attack_to_use]["cost"], best_target.type, best_target_id, ROBOT_ATTACKS[attack_to_use]["damage"] ,robot.energy
                    ))
            else:
                print("O Robot encontrou um alvo, mas decidiu nao atacar. Ficaria com Energia inferior a 100 se atacasse com o Ataque mais barato.") # O 'ã' em 'nao' foi removido para evitar erros de codificacao.
        else:
            print("O Robot nao encontrou alvos validos. Ou ja atacou todos os inimigos neste turno, ou ainda nao existem inimigos ou ja estao todos mortos.") # O 'ã' em 'nao' foi removido para evitar erros de codificacao.

    else:
        print("O Robot esta a conservar energia porque esta abaixo de 200 (Energia atual: {:.0f}EN) e nao vai atacar.".format(robot.energy))