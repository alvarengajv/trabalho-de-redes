from mininet.topo import Topo
from mininet.node import CPULimitedHost, Controller
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

# Parâmetros para cenários de competição TCP
parser.add_argument('--competition',
                    action='store_true',
                    help="Enable TCP competition scenarios")

parser.add_argument('--scenario',
                    type=str,
                    choices=['reno_vs_bbr', 'dual_reno_vs_dual_bbr', 'dual_reno_vs_bbr', 'reno_vs_cubic'],
                    default='reno_vs_bbr',
                    help="""Competition scenario to run:
                    - reno_vs_bbr: 1 Reno vs 1 BBR
                    - dual_reno_vs_dual_bbr: 2 Reno vs 2 BBR  
                    - dual_reno_vs_bbr: 2 Reno vs 1 BBR
                    - reno_vs_cubic: 1 Reno vs 1 Cubic""")

# Parâmetros do experimento
args = parser.parse_args()


class CompTopo(Topo):
    "Topologia para experimentos de competição TCP."

    def build(self, n=4):
        # Criação de hosts baseada no cenário de competição
        hosts = []
        if args.competition:
            # Para cenários de competição, criar múltiplos hosts
            for i in range(1, n+1):
                host = self.addHost(f'h{i}')
                hosts.append(host)

        # Criação do switch s0 para clientes, e s1 para o server
        # As interfaces serão s0-eth1, s0-eth2, s0-eth3, s0-eth4, etc.
        switch_cliente = self.addSwitch('s0')
        switch_server = self.addSwitch('s1')

        delay_ms = f"{args.delay}ms"

        # Configuração dos links com características específicas:
        if args.competition:
            # Múltiplos clientes conectados ao switch s0
            for i, host in enumerate(hosts[:-1], 1):
                # Clientes: alta largura de banda (sem gargalo)
                self.addLink(host, switch_cliente, bw=args.bw_host, delay=delay_ms)
            
            # Link entre o servidor e o switch s1  
            self.addLink(hosts[-1], switch_server, bw=args.bw_host, delay=delay_ms)

            # Link entre os dois switchs, é o gargalo
            self.addLink(switch_cliente, switch_server, bw=args.bw_net, delay=delay_ms, max_queue_size=args.maxq)


def start_iperf_competition(net):
    """Inicia fluxos TCP competindo com diferentes algoritmos de congestionamento"""
    print("=== CENÁRIO DE COMPETIÇÃO TCP ===")
    print(f"Cenário: {args.scenario}")
    
    # Determina os algoritmos a serem usados baseado no cenário
    if args.scenario == 'reno_vs_bbr':
        # Cenário 1: 1 fluxo Reno vs 1 fluxo BBR (competição básica)
        flows = [('h1', 'reno'), ('h2', 'bbr')]
        server_host = 'h3'
    elif args.scenario == 'dual_reno_vs_dual_bbr':
        # Cenário 2: 2 fluxos Reno vs 2 fluxos BBR (competição balanceada)
        flows = [('h1', 'reno'), ('h2', 'reno'), ('h3', 'bbr'), ('h4', 'bbr')]
        server_host = 'h5'
    elif args.scenario == 'dual_reno_vs_bbr':
        # Cenário 3: 2 fluxos Reno vs 1 fluxo BBR (competição desbalanceada)
        flows = [('h1', 'reno'), ('h2', 'reno'), ('h3', 'bbr')]
        server_host = 'h4'
    elif args.scenario == 'reno_vs_cubic':
        # Cenário 4: 1 fluxo Reno vs 1 fluxo Cubic
        flows = [('h1', 'reno'), ('h2', 'Cubic')]
        server_host = 'h3'
    
    # Inicia servidor iperf no host de destino
    server = net.get(server_host)
    print(f"Iniciando servidor iperf em {server_host}...")
    server_proc = server.popen("iperf -s -w 16m -p 5001")
    sleep(1)
    
    # Inicia clientes com diferentes algoritmos TCP
    clients = []
    for i, (host_name, tcp_algo) in enumerate(flows):
        client = net.get(host_name)
        print(f"Iniciando cliente {host_name} com TCP {tcp_algo.upper()}...")
        
        # Configura algoritmo TCP no host cliente
        client.cmd(f"sysctl -w net.ipv4.tcp_congestion_control={tcp_algo}")
        
        # Inicia iperf client com porta específica e logging
        port = 5001
        log_file = f"{args.dir}/iperf_{host_name}_{tcp_algo}.txt"
        client_proc = client.popen(f"iperf -c {server.IP()} -p {port} --time {2*args.time} -i 5 > {log_file}", shell=True)
        clients.append((host_name, tcp_algo, client_proc))
        
        # Pequeno delay entre inícios para evitar sincronização
        sleep(0.5)
    
    return server_proc, clients


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


def bufferbloat():
    if not os.path.exists(args.dir):
        os.makedirs(args.dir)
    
    # Determina topologia baseada no modo
    if args.competition:
        if args.scenario == 'dual_reno_vs_dual_bbr':
            # 2 Reno + 2 BBR + 1 servidor = 5 hosts
            num_hosts = 5
        elif args.scenario == 'dual_reno_vs_bbr':
            # 2 Reno + 1 BBR + 1 servidor = 4 hosts
            num_hosts = 4
        else:
            # Para reno_vs_bbr e reno_vs_cubic: 3 hosts (2 clientes + 1 servidor)
            num_hosts = 3
        topo = CompTopo(n=num_hosts)
    
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink, controller=Controller)
    net.start()
    
    # Exibe a topologia e como os nós estão interconectados
    dumpNodeConnections(net.hosts)
    # Teste básico de conectividade entre todos os hosts
    net.pingAll()

    # Inicia monitoramento do tamanho da fila do switch
    # Para competição, monitora a interface do servidor (última interface)
    if args.competition:
        interface = 's1-eth2'  # Interface do servidor (h5)
    
    qmon = start_qmon(iface=interface, outfile='%s/buffer.txt' % (args.dir))

    if args.competition:
        # Modo competição: inicia fluxos TCP competindo
        print(f"\n=== INICIANDO CENÁRIO DE COMPETIÇÃO: {args.scenario.upper()} ===")
        server_proc, clients = start_iperf_competition(net)
        
        # Inicia ping apenas do primeiro cliente para o servidor
        if args.scenario == 'dual_reno_vs_dual_bbr':
            server_host = 'h5'
        elif args.scenario == 'dual_reno_vs_bbr':
            server_host = 'h4'
        else:
            server_host = 'h3'
        
        h1 = net.get('h1')
        server = net.get(server_host)
        print(f"Iniciando monitoramento de latência de h1 para {server_host}...")
        h1.popen(f"ping -i 0.1 {server.IP()} > {args.dir}/ping_competition.txt", shell=True)
        
        # Aguarda experimento terminar
        print(f"\nExperimento rodando por {args.time} segundos...")
        sleep(args.time + 2)  # +2 segundos para garantir que todos os fluxos terminem
        
        # Finaliza processos
        print("Finalizando fluxos TCP...")
        server_proc.terminate()
        for host_name, tcp_algo, client_proc in clients:
            try:
                client_proc.terminate()
            except:
                pass

    # CLI desabilitada para execução automática
    # CLI(net)

    # Finalização do experimento
    qmon.terminate()
    net.stop()
    
    # Limpeza de processos
    if not args.competition:
        Popen("pgrep -f webserver.py | xargs kill -9", shell=True).wait()

def analyze_tcp_competition():
    """Analisa os resultados da competição TCP e determina o 'vencedor'"""
    
    import glob
    import re
    
    # Busca arquivos de log do iperf
    log_files = glob.glob(f"{args.dir}/iperf_*.txt")
    
    results = {}
    
    for log_file in log_files:
        # Extrai informações do nome do arquivo
        match = re.search(r'iperf_h(\d+)_(\w+)\.txt', log_file)
        if not match:
            continue
            
        host_num = match.group(1)
        tcp_algo = match.group(2)
        
        try:
            with open(log_file, 'r') as f:
                content = f.read()
                
            # Busca pela linha de resumo final do iperf
            # Formato típico: "[  3]  0.0-10.0 sec   113 MBytes  94.9 Mbits/sec"
            summary_match = re.search(r'\[\s*\d+\]\s+[\d\.-]+\s+sec\s+([\d\.]+)\s+(\w+Bytes)\s+([\d\.]+)\s+(\w+bits/sec)', content)
            
            if summary_match:
                throughput_value = float(summary_match.group(3))
                throughput_unit = summary_match.group(4)
                
                # Converte para Mbits/sec se necessário
                if 'Gbits' in throughput_unit:
                    throughput_mbps = throughput_value * 1000
                elif 'Kbits' in throughput_unit:
                    throughput_mbps = throughput_value / 1000
                else:
                    throughput_mbps = throughput_value
                    
                results[f"h{host_num}_{tcp_algo}"] = {
                    'throughput_mbps': throughput_mbps,
                    'host': f"h{host_num}",
                    'tcp_algo': tcp_algo.upper()
                }
                
        except Exception as e:
            print(f"Erro ao analisar {log_file}: {e}")
    
    if not results:
        print("Nenhum resultado encontrado nos arquivos de log.")
        return
    
    # Exibe resultados detalhados
    print("\nResultados por fluxo:")
    print("-" * 50)
    total_throughput = 0
    
    for flow_id, data in sorted(results.items()):
        print(f"{data['host']} (TCP {data['tcp_algo']}): {data['throughput_mbps']:.2f} Mbits/sec")
        total_throughput += data['throughput_mbps']
    
    print("-" * 50)
    print(f"Vazão total: {total_throughput:.2f} Mbits/sec")
    print(f"Utilização do link ({args.bw_net} Mbits/sec): {(total_throughput/args.bw_net)*100:.1f}%")
    
    # Determina o "vencedor" baseado na vazão
    if len(results) >= 2:
        sorted_results = sorted(results.items(), key=lambda x: x[1]['throughput_mbps'], reverse=True)
        winner = sorted_results[0]
        
        # Análise de fairness (justiça)
        throughputs = [data['throughput_mbps'] for data in results.values()]
        fairness_index = calculate_fairness_index(throughputs)
        print(f"\nÍndice de Justiça (Jain's Fairness Index): {fairness_index:.3f}")
        print("(1.0 = perfeitamente justo, menor = mais injusto)")


def calculate_fairness_index(throughputs):
    """Calcula o Índice de Justiça de Jain"""
    if not throughputs:
        return 0
    
    n = len(throughputs)
    sum_x = sum(throughputs)
    sum_x_squared = sum(x*x for x in throughputs)
    
    if sum_x_squared == 0:
        return 1.0
    
    return (sum_x * sum_x) / (n * sum_x_squared)

if __name__ == "__main__":
    bufferbloat()
    if args.competition:
        analyze_tcp_competition()
