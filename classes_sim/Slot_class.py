
from Inimigo_class import Inimigo

# ---------------------------------------------------------------------------
# CLASSE DO SLOT 
# ---------------------------------------------------------------------------

class Slot:
    def __init__(self, id):
        self.id = id
        self.inimigo = None  

    def adicionar_inimigo(self, tipo_inimigo, turno_inicial):
        if self.inimigo is None:
            self.inimigo = Inimigo(tipo_inimigo, turno_inicial)
            print("Setup: {} colocado no Slot {} (posiciona-se no Turno {})".format(tipo_inimigo, self.id, turno_inicial))
        else:
            print("Erro: Slot {} já está ocupado.".format(self.id))

    def esta_vazio(self):
        return self.inimigo is None or not self.inimigo.esta_vivo()

    def esta_ocupado_e_vivo(self):
        return self.inimigo is not None and self.inimigo.esta_vivo()

    def atualizar_estado_inimigo(self, turno_atual):
        if self.esta_ocupado_e_vivo() and not self.inimigo.posicionado:
            if turno_atual == self.inimigo.turno_inicial:
                self.inimigo.posicionado = True
                print("!!! ALERTA (Slot {}): {} posicionou-se. Atacará no próximo turno!".format(self.id, self.inimigo.tipo))

    def get_inimigo_para_reconhecer(self):
        if self.esta_ocupado_e_vivo():
            return self.inimigo
        return None

    def get_inimigo_pronto_para_atacar(self):
        if self.esta_ocupado_e_vivo() and self.inimigo.pode_atacar():
            return self.inimigo
        return None

    def receber_ataque_do_bot(self, dano):
        if self.esta_ocupado_e_vivo():
            print("Bot ataca Slot {}...".format(self.id))
            self.inimigo.receber_dano(dano)
        else:
            print("Bot ataca Slot {}, mas está vazio ou o inimigo já foi destruído.".format(self.id))

    def __repr__(self):
        if self.inimigo:
            return "[Slot {}: {}]".format(self.id, self.inimigo)
        return "[Slot {}: Vazio]".format(self.id)