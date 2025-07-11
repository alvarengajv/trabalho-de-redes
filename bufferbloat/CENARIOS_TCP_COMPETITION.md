# Cenários de Competição TCP Implementados

## ✅ OS 3 CENÁRIOS SOLICITADOS:

### 1. **Um fluxo TCP Reno competindo contra um fluxo TCP BBR**

- **Comando:** `--scenario reno_vs_bbr`
- **Topologia:** h1(Reno) + h2(BBR) → h3(servidor)
- **Descrição:** Competição básica 1x1 entre os dois algoritmos

### 2. **Dois fluxos TCP Reno competindo contra dois fluxos TCP BBR**

- **Comando:** `--scenario dual_reno_vs_dual_bbr`
- **Topologia:** h1(Reno) + h2(Reno) + h3(BBR) + h4(BBR) → h5(servidor)
- **Descrição:** Competição balanceada 2x2 entre os algoritmos

### 3. **Dois fluxos TCP Reno competindo contra um fluxo TCP BBR**

- **Comando:** `--scenario dual_reno_vs_bbr`
- **Topologia:** h1(Reno) + h2(Reno) + h3(BBR) → h4(servidor)
- **Descrição:** Competição desbalanceada 2x1 (vantagem numérica para Reno)

## 🚀 EXEMPLO DE USO:

```bash
# Cenário 1: 1 Reno vs 1 BBR
python bufferbloat_competition.py --competition --scenario reno_vs_bbr \
    --bw-net 10 --delay 10 --time 30 --maxq 100 --dir reno_vs_bbr_results

# Cenário 2: 2 Reno vs 2 BBR
python bufferbloat_competition.py --competition --scenario dual_reno_vs_dual_bbr \
    --bw-net 10 --delay 10 --time 30 --maxq 100 --dir dual_reno_vs_dual_bbr_results

# Cenário 3: 2 Reno vs 1 BBR
python bufferbloat_competition.py --competition --scenario dual_reno_vs_bbr \
    --bw-net 10 --delay 10 --time 30 --maxq 100 --dir dual_reno_vs_bbr_results
```

## 📈 ANÁLISE AUTOMÁTICA INCLUÍDA:

- **Vazão (throughput)** por fluxo individual
- **Identificação do "vencedor"** baseado na vazão
- **Índice de Justiça** (Jain's Fairness Index)
- **Interpretação automática** dos resultados
- **Utilização do link** e eficiência geral
- **Comparação entre algoritmos** com insights técnicos

