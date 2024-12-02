from maspy import *
from random import choice 

"""
Controlador: Controla o cruzamento para a travessia dos carros
VA: Carros querem atingir um destino e precisam cruzar o cruzamento
Ambiente(Cruzamento): Contem informações da posição dos carros nas ruas e suas intenções de destino

carros_na_rua: Armazena as fila de carros em uma determinada rua(A,B,C ou D)
carro_na_rua: Armazena o carro em uma rua que tem sua rota
carro_cruzamento: Armazena os carros atualmente no cruzamento

RUAS: Constante com as ruas disponíveis.
PRIORIDADES: Prioridades que carros podem assumir: Comum para carros de passeio, Urgencia para carros a caminho da trabalho,
        Transporte, para o transporte coletivo de passageiros, Emergencia para veículos de socorro.    i
"""


"""
entrar_na_rua tem que criar
rua_destino que guarda a direção que o agt pretende seguir Perception("rua_destino", (agt, rua_destino))

Ativada o plano de manter_cruzamento o controlador deve esperar alguns segundos e depois buscar nas suas crenças a versão atualizada da carros_vruzamento
ele deve criar uma ordem de travessia com base nos detalhes de direção e quantidade de carros em cada rua. (ruas com mais carros devem ter prioridade)
carros que seguem em linha reta tem mais prioridade
resto é resto
enviar proposta para cada carro askOneReply
"""


RUAS = [
    "rua_A",
    "rua_B",
    "rua_C",
    "rua_D",
]

PRIORIDADES = ["transporte", "urgente", "comum", "emergencia"]

class Cruzamento(Environment):
    def __init__(self, env_name):
        super().__init__(env_name)
        self.create(Percept("carros_cruzamento", ({})))
        
        for RUA in RUAS: 
            self.create(Percept("carros_na_rua", (RUA,[])))
        
    def entrar_na_rua(self, agt, nome_rua, rua_destino, prioridade, preferencia):
        fila_rua = self.get(Percept("carros_na_rua", (nome_rua, "Lista" ))) 
        carros_cruzamento = self.get(Percept("carros_cruzamento", "Dicionario" ))
        
        if fila_rua and carros_cruzamento:
            
            fila_rua.args[1].append(agt)
            self.change(fila_rua, fila_rua.args)
            self.print(f"{agt} entrou na rua {fila_rua.args[0]}: {fila_rua.args[1]}")

            if nome_rua not in carros_cruzamento.args:
                carros_cruzamento.args[nome_rua] = agt
                self.change(carros_cruzamento, carros_cruzamento.args)
                self.print(f"O {agt} entrou no cruzamento da rua {nome_rua}: {carros_cruzamento.args}")
            
            self.create(Percept("rua_destino", (agt, rua_destino, prioridade, preferencia)))
            self.print(f"O {agt} está indo em direção a rua {rua_destino}")

        else:
            self.print(f"Erro: Estrada {nome_rua} não existe ou percepts estão inconsistentes!")
    
    def liberar_carros(self, agt, carros_cruzando):
        carros_cruzamento = self.get(Percept("carros_cruzamento", "Dicionario" ))

        if not carros_cruzamento or not carros_cruzando or not carros_cruzamento.args:
            self.print("Não há carros no cruzamento para serem liberados")
            return

        for carro in carros_cruzando:
            if carro in carros_cruzamento.args.values():
                ruas = [rua for rua, agt in carros_cruzamento.args.items() if agt == carro]
                for rua in ruas:
                    del carros_cruzamento.args[rua]
                self.print(f"{agt} liberou o carro {carro} do cruzamento na {ruas}.")
            
            ruas = self.get(Percept("carros_na_rua", ("Rua","Lista")), all= True)
            for rua in ruas:
                if carro in rua.args[1]:
                    rua.args[1].remove(carro)
                    self.print(f"O {carro} saiu da rua {rua.args[0]}.")
                    self.change(rua, rua.args)

        self.print("Carros liberados, chamando proximos da fila...")

        for RUA in RUAS:
            fila_rua = self.get(Percept("carros_na_rua", (RUA, "Lista")))

            if fila_rua.args[1]:
                if RUA not in carros_cruzamento.args:
                    carros_cruzamento.args[RUA] = fila_rua.args[1][0]
                    self.change(carros_cruzamento, carros_cruzamento.args)
                    self.print(f"O {fila_rua.args[1][0]} entrou no cruzamento da rua {RUA}: {carros_cruzamento.args}")
            else:
                self.print(f"Ninguem na {RUA} para entrar no cruzamento")

        self.change(carros_cruzamento, carros_cruzamento.args)

    def adicionar_ordem(self, src, ordem_carros):
        atual = self.get(Percept("ordem_carros", "Lista"))
        if atual:
            self.change(atual, (ordem_carros))
        else:
            self.create(Percept("ordem_carros", (ordem_carros)))

    
class VA(Agent):
    def __init__(self, agt_name):
        super().__init__(agt_name)
        self.add(Goal("seguir_destino"))
        self._criar_crencas()
    
    @pl(gain, Goal("seguir_destino"))
    def informar_rota(self, src):
        rua_atual = self.get(Belief("rua", "Nome"))
        rua_destino = self.get(Belief("direcao", "Rua"))
        prioridade = self.get(Belief("prioridade", "Valor"))
        preferencia = self.get(Belief("preferencia", "Valor"))

        if rua_atual and rua_destino and prioridade: 
            self.entrar_na_rua(rua_atual.args, rua_destino.args, prioridade.args, preferencia.args)
    
    @pl(gain,Goal("ordem_carros", ("Controlador", "Lista", "Dicionario", "Contra")))
    def avaliar_proposta(self, src, args):
        preferencia = self.get(Belief("preferencia","Valor"))

        controlador = args[0]
        proposta_ordem = args[1]
        respostas = args[2]
        contra_proposta = args[3]

        if not proposta_ordem or not preferencia:
            self.print("Informações insuficientes para negociacao")
            return

        posicao_agente = proposta_ordem.index(f"{self.str_name}")

        if posicao_agente <= preferencia.args:
            self.print(f"{self.str_name} aceitou a proposta de travessia na posição {posicao_agente}.")
            resposta = 1 
        else:
            self.print(f"{self.str_name} rejeitou a proposta de travessia.")
            resposta = 0 

        respostas[self.str_name] = resposta
        if posicao_agente == len(proposta_ordem) - 1:
            self.print(f"Enviando pacote de respostas para o {controlador}...")
            self.send(controlador, achieve, Goal("respostas", (respostas, contra_proposta)))
        else:
            self.print(f"Enviando pacote de respostas para o {proposta_ordem[posicao_agente + 1]}...")
            self.send(proposta_ordem[posicao_agente + 1], achieve, Goal("ordem_carros", (controlador, proposta_ordem, respostas, contra_proposta)))
 
    def _criar_crencas(self):
        rua_escolhida = choice(RUAS)
        direcao = choice([RUA for RUA in RUAS if RUA is not rua_escolhida])
        prioridade = choice(PRIORIDADES)
        preferencia = choice(list(range(4)))
        
        self.add(Belief("rua", (rua_escolhida)))
        self.add(Belief("direcao", (direcao)))
        self.add(Belief("prioridade", (prioridade)))
        self.add(Belief("preferencia", preferencia))

        self.print(f"Crenças criadas, Rua: {rua_escolhida}, Direcao: {direcao}, Prioridade: {prioridade}, Preferencia: {preferencia}")
        
class Controlador(Agent):
    def __init__(self, agt_name):
        super().__init__(agt_name)  
        self.add(Goal("organizar_cruzamento"))
        
    @pl(gain, Goal("organizar_cruzamento"),)
    def organizar_ordem_travessia(self,src):
        self.wait(1)

        carros_cruzamento = self.get(Belief("carros_cruzamento", "Dicionario"))
        if not carros_cruzamento.args:
            self.print("Nenhum carro no cruzamento para organizar.")
            self.add(Goal("organizar_cruzamento"))
        else:
            pontuacao = {}
            for rua, carro in carros_cruzamento.args.items():
                rua_destino = self.get(Belief("rua_destino", (carro, "Destino", "Prioridade", "Preferencia")))
                if rua_destino:
                    pontuacao[carro] = self._pontos_travessia(rua, rua_destino.args[1], rua_destino.args[2])
            
            ordem_carros = sorted(pontuacao, key=pontuacao.get)
            self.print(f"Ordem dos carros foram processados: {ordem_carros}")
            self.adicionar_ordem(ordem_carros)

            self._recuperar_respostas(ordem_carros)

    @pl(gain, Goal("respostas", ("Dicionario", "Boolean")))
    def processar_respostas(self, src, args):

        ordem_carros = self.get(Belief("ordem_carros", "Lista")).args
        carros_cruzamento = self.get(Belief("carros_cruzamento", "Dicionario"))

        contra = args[1]
        respostas = args[0]

        preferencias = self._recuperar_preferencias(carros_cruzamento)

        if contra:
            self.print("Lidando com Contra-proposta...")
            for carro in [carro for carro, resposta in respostas.items() if not resposta]:
                self.print(f"O {carro} optou por aguardar uma próxima oportunidade...")
                ordem_carros.remove(carro)

            self.print("Liberando carros do cruzamento!")
            self.liberar_carros(ordem_carros)

            self.add(Goal("organizar_cruzamento"))
        else:
            self.print("Lidando com Proposta...")
            ordem_atual = ordem_carros
            for carro in [carro for carro, resposta in respostas.items() if not resposta]:
                i_carro = ordem_carros.index(carro)
                for pos in range(preferencias[carro], -1, -1):
                    carro_troca = ordem_carros[pos]
                    if preferencias[carro_troca] >= i_carro:
                        self.print(f"Trocando {carro_troca} com {carro}...")
                        ordem_carros[pos] = carro
                        ordem_carros[i_carro] = carro_troca
                        break
            self.print(f"Nova proposta gerada. Proposta anterior {ordem_atual} atual {ordem_carros}...")

            self._recuperar_respostas(ordem_carros, 1)

    def _recuperar_respostas(self, ordem_carros, contra = 0):
        self.print("Enviando proposta para os agentes...")
        self.send(ordem_carros[0], achieve, Goal("ordem_carros", (self.str_name, ordem_carros, {}, contra)),"CruzamentoChannel")

    def _recuperar_preferencias(self, carros_cruzamento):
        preferencias = {}
        for rua, carro in carros_cruzamento.args.items():
            rua_destino = self.get(Belief("rua_destino", (carro, "Destino", "Prioridade", "Preferencia")))
            if rua_destino:
                preferencias[carro] = rua_destino.args[3]
        return preferencias
                
    def _pontos_travessia(self, rua, destino, prioridade):
        l = list(range(0, len(RUAS)))
        i_rua = RUAS.index(rua)
        i_destino = RUAS.index(destino)
        i_prio = (PRIORIDADES[-1:] + PRIORIDADES[:-1]).index(prioridade)

        l_sft = l[-i_rua:] + l[:-i_rua]

        return l_sft[i_destino] + ((len(PRIORIDADES) - 1) - i_prio)
                
if __name__=="__main__":
    i1 = Cruzamento("i1")
    c1 = Controlador("c1") # conectar no ambiente
    agents = [VA("vA") for i in range(0, 10)]
    cruzamento_channel = Channel("CruzamentoChannel")

    Admin().connect_to(agents + [c1], cruzamento_channel) 
    Admin().connect_to(agents, i1)
    Admin().connect_to(c1, i1)
    Admin().start_system()  