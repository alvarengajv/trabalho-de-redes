import matplotlib.pyplot as plt
import re

#Extrai os thoughputs dos arquivos iperf gerados pela competição
def parse_throughput(file_path):
    throughput_data = []
    bandwidth_re = re.compile(r'([\d\.]+)\s*(M|K)bits/sec')

    with open(file_path, 'r') as f:
        lines = f.readlines()

    # Exclui a última linha que é o sumário.
    if lines:
        lines = lines[:-1]

    for line in lines:
        if not line.startswith('[') or 'sec' not in line:
            continue
        if line.startswith('[ ID]'):
            continue

        match = bandwidth_re.findall(line)
        if not match:
            continue

        value_str, prefix = match[-1]
        value = float(value_str)

        mbps = value if prefix == 'M' else value / 1000.0
        throughput_data.append(mbps)

    return throughput_data

reno_c = 'iperf_h1_reno.txt'
bbr_c = 'iperf_h2_bbr.txt'

throughput_1 = parse_throughput(reno_c)
throughput_2 = parse_throughput(bbr_c)

min_length = min(len(throughput_1), len(throughput_2))
throughput_1 = throughput_1[:min_length]
throughput_2 = throughput_2[:min_length]

max_throughput = 10

plt.figure(figsize=(8, 6))

for i in range(len(throughput_1) - 1):
    x0, y0 = throughput_1[i], throughput_2[i]
    dx = throughput_1[i + 1] - x0
    dy = throughput_2[i + 1] - y0
    plt.arrow(x0, y0, dx, dy, head_width=0.3, head_length=0.3, fc='red', ec='red', length_includes_head=True)

x_vals = [0, max_throughput]
y_vals = [max_throughput, 0]

plt.plot(x_vals, y_vals, '--', label=f"Full bandwidth utilization line", color='black')
plt.arrow(x = 0, y = 0, dx=max_throughput, dy=max_throughput,head_width=0.3, head_length=0.3, color='black', label=f"Equal bandwidth share")

plt.xlabel("Connection 1 Throughput (Mbps) (Reno)")
plt.ylabel("Connection 2 Throughput (Mbps) (BBR)")

plt.legend()

plt.grid(True)
plt.show()

plt.savefig('throughput_plot.svg')