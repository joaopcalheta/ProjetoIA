#!/usr/bin/env python3

from time import sleep
from ev3dev2.sensor.lego import ColorSensor
from ev3dev2.sensor import INPUT_4

def main():
    """
    Função principal que inicializa o sensor e imprime a cor lida.
    """
    sensor_cor = None 

    try:
        # Inicializa o sensor de cor na Porta 4
        sensor_cor = ColorSensor(INPUT_4)
        
        # Define o modo para deteção de cor (necessário para .color_name)
        sensor_cor.mode = 'COL-COLOR'
        
        print("Sensor de Cor (Porta 4) inicializado.")
        print("A ler cores... Pressione Ctrl+C para parar.")
        
        # Loop infinito para ler e imprimir a cor
        while True:
            # Obtém o nome da cor atual
            cor_atual = sensor_cor.color_name
            
            # Imprime a cor detetada no terminal
            # O '\r' faz o cursor voltar ao início da linha,
            # para que a nova leitura substitua a antiga.
            print("Cor detetada: {}        ".format(cor_atual), end='\r')
            
            # Pequena pausa para não sobrecarregar o processador
            sleep(0.1) 

    except KeyboardInterrupt:
        # Captura a interrupção (Ctrl+C) para parar de forma limpa
        print("\nPrograma terminado pelo utilizador.")
    
    except Exception as e:
        # Captura outros erros (ex: sensor não está ligado)
        print("\nOcorreu um erro:")
        print(e)
        print("Verifique se o sensor de cor está ligado na Porta 4.")
    
    finally:
        # Mensagem final
        print("\nFim do programa.")

# Executa a função main quando o script é corrido
if __name__ == "__main__":
    main()