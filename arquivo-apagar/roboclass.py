ROBOT_INITIAL_HEALTH = 750
ROBOT_MAX_ENERGY = 500
ENERGY_RECOVERY_PERCENT = 0.5


BOT_ATTACKS = {

    "crane" : {"damage": 200, "cost": 300},
    "touch" : {"damage": 100, "cost": 150},
    "sound" : {"damage": 50, "cost": 50}
}


BOT_HEALS = {
    "heal_1": {"health": 100, "cost": 200},
    "heal_2": {"health": 200, "cost": 300},
    "heal_3": {"health": 400, "cost": 400}
}


#------------------------------------------CLASS DEFENDER_BOT-----------------------------------------------------------------------------------

class DefenderBot:
    def __init__(self):

        self.health = ROBOT_INITIAL_HEALTH
        self.energy = ROBOT_MAX_ENERGY
        self.max_health = ROBOT_INITIAL_HEALTH

        self.heal_used_this_turn = False
        self.slots_attacked_this_turn = set() # stores the number of the slot attacked in the turn

    def start_new_turn(self):

        
        #Recovers energy
        recovered_energy = self.energy * ENERGY_RECOVERY_PERCENT
        self.energy += recovered_energy
        
        #Limit energy to the maximum
        if self.energy > ROBOT_MAX_ENERGY:
            self.energy = ROBOT_MAX_ENERGY
            

        #Reset turn action limiters
        self.heal_used_this_turn = False
        #self.slots_attacked_this_turn.clear()



    def attack_slot(self, attack_type, target_slot):
        #Check if the attack type exists
        if attack_type not in BOT_ATTACKS:
            print("Error: Unknown attack type.")
            return False

        #Check rule: One attack per Slot
        if target_slot.id in self.slots_attacked_this_turn:
            print("Error: Slot has already been attacked this turn.")
            return False

        #Get attack data
        attack = BOT_ATTACKS[attack_type]
        cost = attack["cost"]
        damage = attack["damage"]

        #Check if there is enough energy
        if self.energy < cost:
            print("Bot does not have enough energy")
            return False
            
        #Perform the attack
        self.energy -= cost
        
        # (Here, the 'target_slot.enemy' would receive the damage. Ex: target_slot.enemy.take_damage(damage))
        # Let's simulate:
        target_slot.enemy.health -= damage
        
        if(target_slot.enemy.is_alive()):
            print("O inimigo {} morreu.".format(target_slot.enemy.type))

        

        #Mark slot as attacked
        self.slots_attacked_this_turn.add(target_slot.id)
        return True
    



    def heal(self, heal_type):
        #Check if it has already healed this turn
        if self.heal_used_this_turn:
            print("Error: Can only use one heal per turn.")
            return False

        #Check if the heal type exists
        if heal_type not in BOT_HEALS:
            print("Error: Unknown heal type.")
            return False
            
        heal_action = BOT_HEALS[heal_type]
        cost = heal_action["cost"]
        health_recovered = heal_action["health"]

        #Check if there is enough energy
        if self.energy < cost:
            print("Bot tried to use '{}' (cost {}) but only has {:.0f} energy.".format(heal_type, cost, self.energy))
            return False
            
        #Perform the heal
        self.energy -= cost
        self.health += health_recovered
        
        #Limit health to the maximum
        if self.health > self.max_health:
            self.health = self.max_health
            

        #Mark heal as used
        self.heal_used_this_turn = True
        
        return True