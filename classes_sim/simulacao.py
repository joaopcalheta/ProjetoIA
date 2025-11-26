

import random
from Robot_class import DenfenderBot
from Slot_class import Slot
from Inimigo_class import INIMIGO_STATS 

def setup_jogo():
    """
    Cria os 6 slots e sorteia os inimigos.
    """
    print("--- A INICIAR O SETUP DO JOGO ---")
    lista_slots = [Slot(id=i+1) for i in range(6)]
    
    #Obtem a lista de tipos de inimigos
    tipos_inimigos_base = list(INIMIGO_STATS.keys()) 

    #Preenche os slots
    for slot in lista_slots:
        #Dado 1 (Tipo): 1-2 Tanque, 3-4 Art, 5-6 Inf
        dado_tipo = random.randint(1, 6)
        if dado_tipo <= 2:
            tipo = "Tanque"
        elif dado_tipo <= 4:
            tipo = "Artilharia"
        else:
            tipo = "Infanteria"
            
        #Dado 2 (Turno inicial)
        dado_turno = random.randint(1, 6)
        
        #Adiciona o inimigo ao slot
        slot.adicionar_inimigo(tipo, dado_turno)
        
    print("--- SETUP COMPLETO ---")
    return lista_slots

def run_game():
    """
    Função principal que corre o ciclo do jogo.
    """
    
    # Cria o Bot
    bot = DenfenderBot()
    
    # Cria os Slots e Inimigos
    slots = setup_jogo()
    
    # Inicia o ciclo de 13 turnos
    for turno in range(1, 14): # Vai de 1 a 13
        
        if turno % 2 == 0:
            # --- TURNO DO BOT (Par) ---
            print("\n=== TURNO {} (DEFENDER-BOT) ===".format(turno))
            bot.iniciar_novo_turno()
            #decisão do robot (deixado em branco como pediste)
            
        else:
            # --- TURNO DO ATACANTE (Ímpar) ---
            print("\n=== TURNO {} (ATACANTE) ===".format(turno))
            
            dano_total_neste_turno = 0
            
            # --- ESTA É A CORREÇÃO LÓGICA ---
            
            # LOOP 1: QUEM JÁ ESTAVA POSICIONADO, ATACA
            for s in slots:
                if s.esta_ocupado_e_vivo():
                    # Verifica se o inimigo está pronto para atacar
                    inimigo = s.get_inimigo_pronto_para_atacar()
                    if inimigo:
                        dano_do_inimigo = inimigo.calcular_dano_total_do_turno()
                        print("!!! {} (Slot {}) ataca o Bot com {} de dano!".format(inimigo.tipo, s.id, dano_do_inimigo))
                        dano_total_neste_turno += dano_do_inimigo
            
            # LOOP 2: QUEM CHEGA NESTE TURNO, POSICIONA-SE
            for s in slots:
                if s.esta_ocupado_e_vivo():
                    # Posiciona inimigos (se for o turno deles)
                    # Estes só atacarão no próximo turno ímpar (ex: Turno 5)
                    s.atualizar_estado_inimigo(turno)
            # --- FIM DA CORREÇÃO ---
            
            # Aplica o dano ao Bot
            if dano_total_neste_turno > 0:
                bot.vida -= dano_total_neste_turno
                print("Bot sofreu {} de dano. Vida restante: {}".format(dano_total_neste_turno, bot.vida))

        # Verifica se o jogo acabou (depois de qualquer turno)
        if bot.vida <= 0:
            print("\n--- FIM DE JOGO (no Turno {}): O Defender-Bot foi destruído! ---".format(turno))
            break
            
    if bot.vida > 0:
        print("\n--- FIM DE JOGO: O Defender-Bot sobreviveu! ---")

# (O resto do teu ficheiro `setup_jogo()` e `if __name__ == "__main__":` fica igual)
if __name__ == "__main__":
    run_game()