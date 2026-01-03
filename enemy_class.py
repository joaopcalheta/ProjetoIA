# Configuração dos atributos dos inimigos
# Tipos de inimigos: Tank, Artillery, Infantry baseado na cor detetada pelo sensor de cor do robot
ENEMY_STATS = {
    "Tank": {
        "color": "Green",
        "force": 200,
        "num_attacks_available": 2,
        "max_health": 200,
    },
    "Artillery": {
        "color": "Brown",
        "force": 500,
        "num_attacks_available": 1,
        "max_health": 50,
    },
    "Infantry": {
        "color": "Blue",
        "force": 100,
        "num_attacks_available": 3,
        "max_health": 100,
    }
}

class Enemy:

    # Inicializa uma nova unidade baseada no tipo detetado, turno de spawn e posição no tabuleiro (1-6).
    def __init__(self, type, spawn_turn, position):
        
        if type not in ENEMY_STATS:
            raise ValueError("Erro: O Inimigo '{}' nao existe.".format(type))
            
        stats = ENEMY_STATS[type]

        # Atribuição de atributos baseados no tipo de inimigo.
        self.type = type
        self.color = stats['color']
        self.force = stats['force']
        self.num_attacks_available = stats['num_attacks_available']
        self.max_health = stats['max_health']
        self.spawn_turn = spawn_turn
        self.current_health = self.max_health
        self.position = position


    # Processa o dano recebido após um ataque do robot.
    # Atualiza a vida e retorna True se a unidade for morta.
    def receive_damage(self, damage):
        self.current_health -= damage
        if self.current_health <= 0:
            self.current_health = 0
        return self.current_health == 0


    # Verifica se o inimigo ainda está vivo
    # Retorna True se estiver vivo, False caso contrário
    def is_alive(self):
        return self.current_health > 0

    # Define a representação textual do objeto no terminal.
    def __str__(self):
        status = "VIVO" if self.is_alive() else "MORTO"
        
        return "[Tipo: {} | Cor: {} | Vida: {}/{} | Forca: {} | Ataques disponiveis: {} | Status: {}]".format(
            self.type, 
            self.color, 
            self.current_health, 
            self.max_health, 
            self.force,
            self.num_attacks_available, 
            status
        )