
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
            print(f"Setup: {tipo_inimigo} colocado no Slot {self.id} (posiciona-se no Turno {turno_inicial})")
        else:
            print(f"Erro: Slot {self.id} já está ocupado.")

    def esta_vazio(self):
        return self.inimigo is None or not self.inimigo.esta_vivo()

    def esta_ocupado_e_vivo(self):
        return self.inimigo is not None and self.inimigo.esta_vivo()

    def atualizar_estado_inimigo(self, turno_atual):
        if self.esta_ocupado_e_vivo() and not self.inimigo.posicionado:
            if turno_atual == self.inimigo.turno_inicial:
                self.inimigo.posicionado = True
                print(f"!!! ALERTA (Slot {self.id}): {self.inimigo.tipo} posicionou-se. Atacará no próximo turno!")

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
            print(f"Bot ataca Slot {self.id}...")
            self.inimigo.receber_dano(dano)
        else:
            print(f"Bot ataca Slot {self.id}, mas está vazio ou o inimigo já foi destruído.")

    def __repr__(self):
        if self.inimigo:
            return f"[Slot {self.id}: {self.inimigo}]"
        return f"[Slot {self.id}: Vazio]"