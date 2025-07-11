#!/bin/bash

# Script para testar os 3 cenários de competição TCP Reno vs BBR solicitados
# 
# Este script executa os cenários específicos de competição e analisa os resultados
# Demonstra quem "sai ganhando" entre TCP Reno e TCP BBR nas situações solicitadas

echo "=== OS 3 CENÁRIOS DE COMPETIÇÃO TCP RENO vs BBR ==="

# Cria diretório para resultados
mkdir -p competition_results

# Configurações da rede para teste
BW_NET=10    # 10 Mbps - largura de banda do gargalo
DELAY=20     # 20ms de delay
MAXQ=100     # Buffer de 100 pacotes
TIME=30      # 30 segundos de experimento

echo "Configurações da rede:"
echo "- Largura de banda do gargalo: ${BW_NET} Mbps"
echo "- Delay: ${DELAY} ms"
echo "- Tamanho do buffer: ${MAXQ} pacotes"
echo "- Duração: ${TIME} segundos"
echo ""

# Cenário 1: TCP Reno vs TCP BBR (competição direta)
echo "🥊 CENÁRIO 1: 1 TCP Reno vs 1 TCP BBR"
echo "Descrição: Um fluxo TCP Reno competindo contra um fluxo TCP BBR"
echo "Quem vai dominar o link?"
echo ""

python bufferbloat_competition.py \
    --competition \
    --scenario reno_vs_bbr \
    --bw-net ${BW_NET} \
    --delay ${DELAY} \
    --maxq ${MAXQ} \
    --time ${TIME} \
    --dir competition_results/scenario1_reno_vs_bbr

echo ""
echo "Aguardando 5 segundos antes do próximo cenário..."
sleep 5

# Cenário 2: Dois fluxos TCP Reno vs Dois fluxos TCP BBR
echo "⚔️ CENÁRIO 2: 2 TCP Reno vs 2 TCP BBR"
echo "Descrição: Dois fluxos TCP Reno competindo contra dois fluxos TCP BBR"
echo "Competição balanceada - quem domina quando há igualdade numérica?"
echo ""

python bufferbloat_competition.py \
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
echo "🎯 CENÁRIO 3: 2 TCP Reno vs 1 TCP BBR"
echo "Descrição: Dois fluxos TCP Reno competindo contra um fluxo TCP BBR"
echo "Vantagem numérica para Reno - consegue superar o BBR?"
echo ""

python bufferbloat_competition.py \
    --competition \
    --scenario dual_reno_vs_bbr \
    --bw-net ${BW_NET} \
    --delay ${DELAY} \
    --maxq ${MAXQ} \
    --time ${TIME} \
    --dir competition_results/scenario3_dual_reno_vs_bbr

echo ""
echo "=== TODOS OS 3 CENÁRIOS CONCLUÍDOS ==="
echo ""
echo "📊 RESUMO DOS RESULTADOS:"
echo ""
echo "Verifique os arquivos de log em competition_results/ para análise detalhada:"
echo "- scenario1_reno_vs_bbr/: 1 Reno vs 1 BBR (competição direta)"
echo "- scenario2_dual_reno_vs_dual_bbr/: 2 Reno vs 2 BBR (competição balanceada)"
echo "- scenario3_dual_reno_vs_bbr/: 2 Reno vs 1 BBR (vantagem numérica Reno)"
echo ""
echo "💡 INTERPRETAÇÃO ESPERADA:"
echo ""
echo "🏆 TCP BBR geralmente vence em:"
echo "   • Redes com alto RTT (> 10ms)"
echo "   • Links com alta largura de banda"
echo "   • Cenários com buffers grandes"
echo "   • Situações de competição com TCP Reno"
echo ""
echo "🏆 TCP Reno pode vencer em:"
echo "   • Redes com baixo RTT (< 5ms)"
echo "   • Links congestionados"
echo "   • Buffers pequenos"
echo "   • Quando tem vantagem numérica (mais fluxos)"
echo ""
echo "📈 Métricas analisadas automaticamente:"
echo "   • Vazão (throughput) - quem consegue mais largura de banda"
echo "   • Justiça (fairness) - como dividem o link"
echo "   • Utilização do link - eficiência geral"
echo "   • Identificação do 'vencedor' por cenário"
echo ""
echo "Execute o script novamente com diferentes parâmetros (delay, largura de banda,"
echo "tamanho do buffer) para explorar diferentes condições de rede!"
