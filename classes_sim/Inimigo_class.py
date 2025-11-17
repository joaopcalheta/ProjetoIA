INIMIGO_STATS = {
    "Tanque": {
        "forca": 200,
        "num_ataques": 2,
        "vida_max": 200,
    },
    "Artilharia": {
        "forca": 500,
        "num_ataques": 1,
        "vida_max": 50,
    },
    "Infanteria": {
        "forca": 100,
        "num_ataques": 3,
        "vida_max": 100,
    }
}

# ---------------------------------------------------------------------------
# CLASSE DO INIMIGO
# ---------------------------------------------------------------------------

class Inimigo:
    def __init__(self, tipo, turno_inicial):
        if tipo not in INIMIGO_STATS:
            raise ValueError(f"Tipo de inimigo desconhecido: {tipo}")

        #Guarda o tipo
        self.tipo = tipo
        
        #Carrega os atributos base do dicionário global
        stats = INIMIGO_STATS[tipo]
        self.forca = stats["forca"]
        self.num_ataques = stats["num_ataques"]
        self.vida_max = stats["vida_max"]
        
        #Atributos de estado 
        self.vida = self.vida_max  
        self.turno_inicial = turno_inicial
        
        #'posicionado' controla se o inimigo já gastou seu turno para  entrar no slot
        self.posicionado = False 

    def esta_vivo(self):
        return self.vida > 0

    def pode_atacar(self):
        return self.esta_vivo() and self.posicionado

    def receber_dano(self, quantidade_dano):
        if not self.esta_vivo():
            print(f"{self.tipo} já estava destruído.")
            return

        self.vida -= quantidade_dano
        
        if self.vida <= 0:
            self.vida = 0
            print(f"!!! {self.tipo} foi destruído!")
        else:
            print(f"{self.tipo} recebeu {quantidade_dano} de dano. Vida restante: {self.vida}/{self.vida_max}")

    def calcular_dano_total_do_turno(self):
        if not self.pode_atacar():
            return 0

        #Calcula a percentagem de vida
        percent_vida = self.vida / self.vida_max
        
        #Calcula o dano de um único ataque
        dano_por_ataque = self.forca * percent_vida
        
        #Multiplica pelo número de ataques
        dano_total = dano_por_ataque * self.num_ataques
        #Retorna como inteiro
        return int(dano_total) 

    def __repr__(self):
        estado = "Posicionado" if self.posicionado else "Aguardando"
        if not self.esta_vivo():
            estado = "Destruído"  
        return f"<{self.tipo} | Vida: {self.vida}/{self.vida_max} | Turno: {self.turno_inicial} | Estado: {estado}>"