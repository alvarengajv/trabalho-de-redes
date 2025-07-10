from mininet.topo import Topo
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.log import lg, info
from mininet.util import dumpNodeConnections
from mininet.cli import CLI

from subprocess import Popen, PIPE
from time import sleep, time
from multiprocessing import Process
from argparse import ArgumentParser

from monitor import monitor_qlen

import sys
import os
import math

parser = ArgumentParser(description="Bufferbloat tests")
parser.add_argument('--bw-host', '-B',
                    type=float,
                    help="Bandwidth of host links (Mb/s)",
                    default=1000)

parser.add_argument('--bw-net', '-b',
                    type=float,
                    help="Bandwidth of bottleneck (network) link (Mb/s)",
                    required=True)

parser.add_argument('--delay',
                    type=float,
                    help="Link propagation delay (ms)",
                    required=True)

parser.add_argument('--dir', '-d',
                    help="Directory to store outputs",
                    required=True)

parser.add_argument('--time', '-t',
                    help="Duration (sec) to run the experiment",
                    type=int,
                    default=10)

parser.add_argument('--maxq',
                    type=int,
                    help="Max buffer size of network interface in packets",
                    default=100)

# Configuração do algoritmo de controle de congestionamento TCP
# Por padrão usa 'reno' para demonstrar o comportamento clássico do TCP
# CUBIC é o padrão do Linux e tem comportamento diferente (sem dente de serra)
parser.add_argument('--cong',
                    help="Congestion control algorithm to use",
                    default="reno")

# Parâmetros do experimento
args = parser.parse_args()


class BBTopo(Topo):
    "Topologia simples para experimento de bufferbloat."

    def build(self, n=2):
        # Criação dos dois hosts: h1 (cliente) e h2 (servidor)
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')

        # Criação do switch central s0
        # As interfaces serão s0-eth1 (para h1) e s0-eth2 (para h2)
        switch = self.addSwitch('s0')

        # Configuração dos links com características específicas:
        # h1 <-> switch: alta largura de banda (sem gargalo)
        # switch <-> h2: largura de banda limitada (gargalo) com buffer configurável
        self.addLink(h1, switch, bw=args.bw_host, delay=args.delay)
        self.addLink(switch, h2, bw=args.bw_net, delay=args.delay, max_queue_size=args.maxq)


def start_iperf(net):
    h1 = net.get('h1')
    h2 = net.get('h2')
    print("Iniciando servidor iperf...")
    # Parâmetro -w 16m garante que o fluxo TCP não seja limitado pela janela do receptor
    # Isso assegura que o buffer do roteador seja preenchido durante o teste
    server = h2.popen("iperf -s -w 16m")

    # Inicia cliente iperf em h1 conectando ao servidor h2
    # Fluxo TCP de longa duração (2x o tempo do experimento) para saturar o link
    client = h1.popen('iperf -c ' + str(h2.IP()) + ' --time ' + str(2*args.time))


def start_qmon(iface, interval_sec=0.1, outfile="buffer.txt"):
    monitor = Process(target=monitor_qlen,
                      args=(iface, interval_sec, outfile))
    monitor.start()
    return monitor


def start_ping(net):
    # Inicia sequência de pings de h1 para h2 para medir RTT
    # Ping a cada 0.1 segundos (-i 0.1) para capturar variações de latência
    # Saída redirecionada para arquivo ping.txt para análise posterior
    h1 = net.get('h1')
    h2 = net.get('h2')
    h1.popen("ping -i 0.1 " + str(h2.IP()) + " > " + args.dir + "/ping.txt", shell=True)


def start_webserver(net):
    h1 = net.get('h1')
    proc = h1.popen("python http/webserver.py", shell=True)
    sleep(1)
    return [proc]


def fetch_pages(net):
    h2 = net.get('h2')
    h1 = net.get('h1')
    result = 0
    for i in range(3):
        # Executa curl para medir tempo de download da página web
        proc = h2.popen("curl -o /dev/null -s -w %{time_total} " + str(h1.IP()) + "/http/index.html", shell=True, text=True, stdout=PIPE)
        output = proc.stdout.readline()
        print(output)
        result += float(output)
    return result


def bufferbloat():
    if not os.path.exists(args.dir):
        os.makedirs(args.dir)
    os.system("sysctl -w net.ipv4.tcp_congestion_control=%s" % args.cong)
    topo = BBTopo()
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink)
    net.start()
    # Exibe a topologia e como os nós estão interconectados
    dumpNodeConnections(net.hosts)
    # Teste básico de conectividade entre todos os hosts
    net.pingAll()

    # Inicia monitoramento do tamanho da fila do switch
    # Monitora interface s0-eth2 (link gargalo entre switch e h2)
    # A numeração das interfaces começa em 1: eth1 para h1, eth2 para h2
    qmon = start_qmon(iface='s0-eth2',
                      outfile='%s/buffer.txt' % (args.dir))

    # Inicia todos os processos necessários para o experimento:
    # - iperf: gera tráfego TCP de fundo para saturar o link
    # - ping: mede latência continuamente 
    # - webserver: serve páginas web para teste de responsividade
    start_iperf(net)
    start_ping(net)
    start_webserver(net)

    # Medição do tempo de transferência de páginas web
    # Testa o impacto do bufferbloat na responsividade de aplicações web
    # Usa curl para medir tempo total de download da página
    times = []

    start_time = time()
    while True:
        # Executa 3 medições por iteração e calcula média
        times.append(fetch_pages(net))
        sleep(5)
        now = time()
        delta = now - start_time
        if delta > args.time:
            break
        print("%.1fs restantes..." % (args.time - delta))

    # Cálculo de estatísticas dos tempos de busca das páginas web
    # Média aritmética e desvio padrão para avaliar impacto do bufferbloat
    # Buffers maiores tendem a aumentar latência e variabilidade dos tempos
    tempo_medio_busca = sum(times) / len(times)
    print("Tempo médio de busca da página web quando q = " + str(args.maxq) + ": " + str(tempo_medio_busca))
    desvio_padrao = (sum([((x - tempo_medio_busca) ** 2) for x in times]) / len(times)) ** 0.5
    print("Desvio padrão quando q = " + str(args.maxq) + ": " + str(desvio_padrao))

    # CLI desabilitada para execução automática
    # Descomente a linha abaixo para debug interativo dos hosts h1 e h2
    # CLI(net)

    # Finalização do experimento: para monitoramento e limpa recursos
    qmon.terminate()
    net.stop()
    # Mata processos do webserver que podem continuar rodando após o experimento
    # Necessário para evitar conflitos em execuções subsequentes
    Popen("pgrep -f webserver.py | xargs kill -9", shell=True).wait()

if __name__ == "__main__":
    bufferbloat()
