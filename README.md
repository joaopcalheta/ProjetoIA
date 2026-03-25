# Defender-Bot - Projeto de Inteligência Artificial

## Objetivo do Projeto

O **Defender-Bot** é um sistema de inteligência artificial desenvolvido para atuar como um robô de defesa em um cenário de combate simulado. O objetivo principal é programar um robô que, em um ambiente de 13 turnos, consiga reconhecer forças inimigas, planear ataques e curas estratégicas, e sobreviver ao ataque combinado de diferentes unidades inimigas (tanques, artilharia e infantaria). O projeto visa aplicar conceitos de heurísticas, tomada de decisão e controlo de ações em tempo real, usando técnicas de IA para otimizar a sobrevivência do robô.

## Áreas Tocadas

Este projeto envolve várias áreas de inteligência artificial e programação, incluindo:

- **Reconhecimento de ambiente:** usando sensores para identificar inimigos e as suas posições.
- **Heurísticas de decisão:** implementação de estratégias para decidir quando atacar, curar ou reconhecer inimigos, visando maximizar a sobrevivência.
- **Controlo de ações:** gestão de ataques, curas e reconhecimento, respeitando restrições de energia e uma única ação por slot/turno.
- **Programação de robôs:** controlo do hardware do EV3, usando Python (ev3dev2) para movimentação, ataque e reconhecimento.

## Como Executar

O projeto foi desenvolvido em Python, utilizando a plataforma EV3 com o sistema ev3dev2. Para executar:

1. Certifique-se de que o hardware EV3 está configurado corretamente com o sistema ev3dev2.
2. Conecte os sensores e motores conforme necessário.
3. Transfira o código para o EV3.
4. Execute o arquivo `main.py` com Python 3 no EV3:
   
```bash
python3 main.py
```

O programa inicia o ciclo de reconhecimento, ataque, cura e decisão, turno a turno, até ao fim do jogo ou interrupção manual.

## Detalhes do Projeto

- **Reconhecimento:** o robô usa sensores de cor, ultrassônico e giroscópio para identificar inimigos e as suas posições.
- **Ataques:** três tipos de ataques com diferentes custos e impactos:
  - Grua (200 uv, custo 300 en)
  - Toque (100 uv, custo 150 en)
  - Som (50 uv, custo 50 en)
- **Curas:** três níveis de cura, com diferentes recuperações e custos:
  - Cura 1 (100 uv, 200 en)
  - Cura 2 (200 uv, 300 en)
  - Cura 3 (400 uv, 400 en)
- **Heurísticas:** desenvolvidas para ajudar o robô a avaliar o potencial de dano de cada inimigo, tendo em conta a sua força, vida atual e tipo. É calculado a ameaça de cada inimigo com base no dano que pode causar, considerando a sua força e a percentagem de vida restante. Assim, o robô consegue priorizar os inimigos mais perigosos. Quando o robô vai realizar um ataque, a heurística estima o dano que seria causado e compara-o com a ameaça atual do inimigo. Também calcula a eficiência do ataque, avaliando o dano que seria evitado em relação ao custo energético do ataque. Além disso, a heurística atribui bónus para ataques a inimigos mais perigosos, como artilharia e tanques, e por eliminar inimigos, enquanto penaliza ataques que causam dano excessivo (overkill). O objetivo é garantir que o robô ataque as maiores ameaças de forma eficiente, sem desperdiçar energia desnecessária e garantindo a sua sobrevivência. Assim, a prioridade de ataque é ajustada de forma dinâmica, dependendo da ameaça real de cada inimigo.

## Avaliação e Nota

Este projeto recebeu uma nota final de **17,5 valores** na disciplina de Inteligência Artificial, na Universidade da Madeira, sob orientação do professor Eduardo Fermé.

## Considerações Finais

Este trabalho demonstra a integração de sensores, controlo de hardware, lógica de decisão baseada em heurísticas e estratégias de IA para um cenário de combate simulado. O código está organizado em módulos que representam classes de inimigos, o robô, ataques e lógica de jogo.
