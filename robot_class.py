# Configurações Base do robot
ROBOT_MAX_HEALTH = 750              # Vida máxima do robot
ROBOT_MAX_ENERGY = 500              # Energia máxima do robot
ENERGY_RECOVERY_PERCENT = 0.5       # Ganho de energia por turno (50% da energia atual)


# Ataques Disponíveis
# Define o dano infligido e o custo de energia para cada tipo de ataque físico.
ROBOT_ATTACKS = {
    "crane" : {             # Ataque de grua
        "damage": 200, 
        "cost": 300
        },
    "touch" : {             # Ataque de toque
        "damage": 100, 
        "cost": 150
        },
    "sound" : {             # Ataque som
        "damage": 50, 
        "cost": 50
        }
}

# Tipos de Cura Disponíveis
# Define a quantidade de vida recuperada e o custo de energia necessário.
ROBOT_HEALS = {
    "heal1": {
        "health_recovered": 100, 
        "cost": 200
        },
    "heal2": {
        "health_recovered": 200, 
        "cost": 300
        },
    "heal3": {
        "health_recovered": 400, 
        "cost": 400
        }
}


class Robot:

    def __init__(self):
        # Inicializa o estado do robot com os valores máximos e limpa os registos de turno.
        self.current_health = ROBOT_MAX_HEALTH
        self.energy = ROBOT_MAX_ENERGY
        self.max_health = ROBOT_MAX_HEALTH
        self.heal_used_this_turn = False
        self.slots_attacked_this_turn = set()

    # Rotina de início de turno
    # Recupera energia baseado na energia atual 
    # Verifica se não vai ultrapassar a energia máxima
    # Reseta os registos de cura e ataques do turno
    def start_new_turn(self):
        recovered_energy = self.energy * ENERGY_RECOVERY_PERCENT
        self.energy += recovered_energy
        
        if self.energy > ROBOT_MAX_ENERGY:
            self.energy = ROBOT_MAX_ENERGY

        self.heal_used_this_turn = False
        self.slots_attacked_this_turn.clear()


    # Ataca um inimigo num slot específico
    # Valida o tipo de ataque, o slot, se o alvo existe e se há energia suficiente.
    # Retorna True se o ataque for bem-sucedido, False caso contrário
    def attack_slot(self, attack_type, slot_id, enemies):

        # Verifica se o tipo de ataque é válido (crane, touch ou sound)
        if attack_type not in ROBOT_ATTACKS:
            print("Erro: O Ataque '{}' nao existe.".format(attack_type))
            return False

        # Verifica se o slot é válido (entre 1 e 6)
        if not (1 <= slot_id <= 6):
            print("Erro: O Slot {} nao existe.".format(slot_id))
            return False

        # Verifica se o slot já foi atacado neste turno
        if slot_id in self.slots_attacked_this_turn:
            print("Erro: O Slot {} ja foi atacado neste turno.".format(slot_id))
            return False

        # Verifica se existe algum inimigo no slot
        target_enemy = enemies[slot_id - 1]
        if target_enemy is None:
            print("Erro: O Slot {} esta vazio.".format(slot_id))
            return False

        # Obtém os dados do ataque (dano e custo)
        attack = ROBOT_ATTACKS[attack_type]
        cost = attack["cost"]
        damage = attack["damage"]

        # Verifica se o robot tem energia suficiente para fazer o ataque
        if self.energy < cost:
            print("Erro: O Robot nao tem energia suficiente para fazer o Ataque '{}'. Tem um custo de {} e o Robot so tem {} de energia.".format(attack_type, cost, self.energy))
            return False

        # Realiza o ataque  
        # Reduz a energia do robot
        # Dá dano no inimigo 
        self.energy -= cost
        target_enemy.receive_damage(damage)

        # Adiciona o slot à lista de slots atacados no turno para evitar ataques múltiplos no mesmo slot
        self.slots_attacked_this_turn.add(slot_id)
        return True



    # Cura o robot
    # Verifica se já houve cura no turno, se o tipo é válido e se há energia.
    # Retorna True se a cura for bem-sucedida, False caso contrário
    def heal(self, heal_type):

        # Verifica se o robot já se curou neste turno
        if self.heal_used_this_turn:
            print("Erro: O Robot ja se curou neste turno.")
            return False

        # Verifica se o tipo de cura é válido (heal1, heal2 ou heal3)
        if heal_type not in ROBOT_HEALS:
            print("Erro: A Cura '{}' nao existe.".format(heal_type))
            return False

        # Obtém os dados da cura (vida recuperada e custo)    
        heal_action = ROBOT_HEALS[heal_type]
        cost = heal_action["cost"]
        health_recovered = heal_action["health_recovered"]

        # Verifica se o robot tem energia suficiente para fazer a cura
        if self.energy < cost:
            print("Erro: O Robot nao tem energia suficiente para fazer a Cura '{}'. Tem um custo de {} e o Robot so tem {} de energia.".format(heal_type, cost, self.energy))
            return False
            
        # Realiza a cura
        # Reduz a energia do robot
        # Aumenta a vida atual do robot, sem ultrapassar a vida máxima
        self.energy -= cost
        self.current_health += health_recovered
        if self.current_health > self.max_health:
            self.current_health = self.max_health
            
        # Regista que já foi usada uma cura neste turno
        self.heal_used_this_turn = True
        
        return True


    # Recebe dano dos inimigos e atualiza a vida do robot
    # Retorna True se o robot morrer (vida menor ou igual a 0), False esteja vivo
    def receive_damage(self, damage):
        self.current_health -= damage
        if self.current_health < 0:
            self.current_health = 0
        
        print("O Robot sofreu {} de dano! Vida restante: {:.0f}/{}".format(
            damage, self.current_health, self.max_health
        ))
        
        return self.current_health == 0


    # Verifica se o robot ainda está vivo
    # Retorna True se estiver vivo, False caso contrário
    def is_alive(self):
        return self.current_health > 0