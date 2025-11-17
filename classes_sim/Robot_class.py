import random

ROBOT_VIDA_INICIAL = 750
ROBOT_ENERGIA_INICIAL=500
ROBOT_ENERGIA_MAX = 500
RECUPERACAO_ENERGIA_PERCENT = 0.5


ATAQUES_BOT = {

    "grua" : {"dano": 200, "custo": 300},
    "toque" : {"dano": 100, "custo": 150},
    "som" :   {"dano": 50, "custo": 50}
}


CURAS_BOT = {
    "cura_1": {"vida": 100, "custo": 200},
    "cura_2": {"vida": 200, "custo": 300},
    "cura_3": {"vida": 400, "custo": 400}
}


#------------------------------------------CLASS DEFENDER_BOT-----------------------------------------------------------------------------------

class DenfenderBot:
    def __init__(self):

        self.vida = ROBOT_VIDA_INICIAL
        self.energia = ROBOT_ENERGIA_INICIAL
        self.max_vida = ROBOT_VIDA_INICIAL

        self.cura_usada_neste_turno = False
        self.slots_atacados_neste_turno = set() #guardae o numero de slot atacado no turno

    def iniciar_novo_turno(self):

        
        #Recupera a  energia
        energia_recuperada = self.energia * RECUPERACAO_ENERGIA_PERCENT
        self.energia += energia_recuperada
        
        #Limitar energia ao máximo 
        if self.energia > ROBOT_ENERGIA_MAX:
            self.energia = ROBOT_ENERGIA_MAX
            

        #Resetar limitadores de ação do turno
        self.cura_usada_neste_turno = False
        self.slots_atacados_neste_turno.clear()



    def atacar_slot(self, tipo_ataque, alvo_slot):
        #Verifica se o tipo de ataque existe
        if tipo_ataque not in ATAQUES_BOT:
            print("Erro: Tipo de ataque  desconhecido.")
            return False

        #Verifica regra: Um ataque por Slot
        if alvo_slot.id in self.slots_atacados_neste_turno:
            print("Erro: Slot  já foi atacado neste turno.")
            return False

        #Obtem dados do ataque
        ataque = ATAQUES_BOT[tipo_ataque]
        custo = ataque["custo"]
        dano = ataque["dano"]

        #Verifica se tem energia suficiente
        if self.energia < custo:
            print("Bot não tem energia sufeciente")
            return False
            
        #Realizar o ataque
        self.energia -= custo
        
        # (Aqui, o 'alvo_slot.inimigo' receberia o dano. Ex: alvo_slot.inimigo.receber_dano(dano))
        # Vamos simular:
        alvo_slot.inimigo.vida -= dano 
        

        #Marcar slot como atacado
        self.slots_atacados_neste_turno.add(alvo_slot.id) 
        return True
    



    def curar(self, tipo_cura):
        #Verifica se já se curou neste turno
        if self.cura_usada_neste_turno:
            print("Erro: Só pode usar uma cura por turno.")
            return False

        #Verifica se o tipo de cura existe
        if tipo_cura not in CURAS_BOT:
            print("Erro: Tipo de cura desconhecido.")
            return False
            
        cura = CURAS_BOT[tipo_cura]
        custo = cura["custo"]
        vida_recuperada = cura["vida"]

        #Verifica se tem energia suficiente 
        if self.energia < custo:
            print(f"Bot tentou usar '{tipo_cura}' (custo {custo}) mas só tem {self.energia:.0f} de energia.")
            return False
            
        #Realiza a cura
        self.energia -= custo
        self.vida += vida_recuperada
        
        #Limita a vida ao máximo
        if self.vida > self.max_vida:
            self.vida = self.max_vida
            

        #Marca cura como usada
        self.cura_usada_neste_turno = True 
        
        return True