# Cria diretório para resultados
mkdir -p competition_results

# Configurações da rede para teste
BW_NET=10    # 10 Mbps - largura de banda do gargalo
DELAY=20     # 20ms de delay
MAXQ=100     # Buffer de 100 pacotes
TIME=60      # 30 segundos de experimento

# Cenário 1: TCP Reno vs TCP BBR (competição direta)
echo "CENÁRIO 1: 1 TCP Reno vs 1 TCP BBR"

# CORREÇÃO: Alterado de 'python' para 'python3'
python3 bufferbloat_competition.py \
    --competition \
    --scenario reno_vs_bbr \
    --bw-net ${BW_NET} \
    --delay ${DELAY} \
    --maxq ${MAXQ} \
    --time ${TIME} \
    --dir competition_results/scenario1_reno_vs_bbr

echo ""
sleep 5

# Cenário 2: Dois fluxos TCP Reno vs Dois fluxos TCP BBR
echo "CENÁRIO 2: 2 TCP Reno vs 2 TCP BBR"

python3 bufferbloat_competition.py \
    --competition \
    --scenario dual_reno_vs_dual_bbr \
    --bw-net ${BW_NET} \
    --delay ${DELAY} \
    --maxq ${MAXQ} \
    --time ${TIME} \
    --dir competition_results/scenario2_dual_reno_vs_dual_bbr

echo ""
sleep 5

# Cenário 3: Dois fluxos TCP Reno vs Um fluxo TCP BBR
echo "CENÁRIO 3: 2 TCP Reno vs 1 TCP BBR"

python3 bufferbloat_competition.py \
    --competition \
    --scenario dual_reno_vs_bbr \
    --bw-net ${BW_NET} \
    --delay ${DELAY} \
    --maxq ${MAXQ} \
    --time ${TIME} \
    --dir competition_results/scenario3_dual_reno_vs_bbr

echo ""
sleep 5

# Cenário 4: Um fluxo TCP Reno vs Um fluxo TCP Cubic
echo "CENÁRIO 4: 1 TCP Reno vs 1 TCP Cubic"

python3 bufferbloat_competition.py \
    --competition \
    --scenario reno_vs_cubic \
    --bw-net ${BW_NET} \
    --delay ${DELAY} \
    --maxq ${MAXQ} \
    --time ${TIME} \
    --dir competition_results/scenario4_reno_vs_cubic

echo ""
