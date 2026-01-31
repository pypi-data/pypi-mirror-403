# mtcli-volume

Plugin do **mtcli** para cálculo e visualização de **Volume Profile** diretamente no terminal, com foco em:

- Precisão técnica (distribuição High–Low)
- Leitura profissional de mercado
- Total acessibilidade (screen reader friendly)
- Integração com MetaTrader 5

---

## Principais recursos

- **Volume Profile por faixa High–Low**
  - O volume de cada candle é distribuído uniformemente entre todas as faixas de preço tocadas entre o **LOW** e o **HIGH**
  - Modelo mais próximo do Volume Profile clássico (VAP)

- **Estatísticas de Market Profile**
  - POC (Point of Control)
  - Área de Valor (70%)
  - HVNs e LVNs com critérios profissionais

- ⚙️ **Critérios avançados para HVN/LVN**
  - Baseado na média (multiplicadores)
  - Baseado em percentis (ex: 80% / 20%)

- **100% acessível**
  - Saída textual linear
  - Compatível com NVDA, JAWS e leitores de tela
  - Sem dependência de cores ou gráficos visuais

- **Arquitetura MVC**
  - Model: cálculos e dados
  - Controller: fluxo de negócio
  - View: apresentação no terminal
  - CLI: interface de linha de comando

---

## Instalação

Via PyPI:

```bash
pip install mtcli-volume
````

Ou com Poetry:

```bash
poetry add mtcli-volume
```

> ⚠️ Requer MetaTrader 5 instalado e configurado corretamente no sistema.

---

## Uso básico

Após a instalação, o comando é registrado automaticamente no `mtcli`:

```bash
mt vp
```

Exemplo completo:

```bash
mt vp \
  --symbol WING26 \
  --period m1 \
  --limit 500 \
  --range 100 \
  --volume tick \
  --hvn-criterio media \
  --verbose
```

---

## 🔧 Opções disponíveis

| Opção               | Descrição                                    |
| ------------------- | -------------------------------------------- |
| `--symbol`, `-s`    | Símbolo do ativo (ex: WIN, WDO, PETR4)       |
| `--period`, `-p`    | Timeframe (m1, m5, m15, h1, etc.)            |
| `--limit`, `-l`     | Quantidade de candles analisados             |
| `--range`, `-r`     | Tamanho da faixa de preço                    |
| `--volume`, `-v`    | Tipo de volume (`tick` ou `real`)            |
| `--inicio`, `-i`    | Data/hora inicial (`YYYY-MM-DD HH:MM`)       |
| `--fim`, `-f`       | Data/hora final (`YYYY-MM-DD HH:MM`)         |
| `--timezone`, `-tz` | Fuso horário para exibição                   |
| `--hvn-criterio`    | Critério de HVN/LVN (`media` ou `percentil`) |
| `--verbose`, `-vv`  | Exibe informações detalhadas                 |

---

## Metodologia de cálculo

### Volume Profile

* Cada candle contribui volume para **todas as faixas de preço** entre seu `low` e `high`
* O volume é distribuído **uniformemente**
* Evita o viés de concentrar volume apenas no preço de fechamento

### HVN / LVN

Critérios disponíveis:

* **Média**

  * HVN: volume ≥ média × multiplicador
  * LVN: volume ≤ média × multiplicador

* **Percentil**

  * HVN: acima do percentil superior (ex: 80%)
  * LVN: abaixo do percentil inferior (ex: 20%)

---

## Acessibilidade

Este plugin foi projetado para uso total com leitores de tela:

* Tabelas em texto puro
* Distribuição expressa em percentuais
* Estatísticas narráveis
* Sem gráficos ASCII ruidosos

Funciona corretamente com:

* NVDA
* JAWS
* VoiceOver (terminal)

---

## Arquitetura

```text
mtcli_volume/
├── cli.py         # Interface de linha de comando
├── controller.py  # Orquestração do fluxo
├── model.py       # Cálculos e acesso ao MT5
├── view.py        # Apresentação acessível
├── conf.py        # Configurações padrão
└── plugin.py      # Registro no mtcli
```

---

## Exemplo de saída

```text
Volume Profile — WING26

Preço           | Volume        | Distribuição
-------------------------------------------------------
186300.00       | 18.250        | 72.4% do máximo
186200.00       | 25.190        | 100.0% do máximo
186100.00       | 14.880        | 59.1% do máximo

Estatísticas
POC             : 186200.00
Área de Valor   : 185900.00 → 186300.00
HVNs            : 186200.00, 186100.00
LVNs            : 185700.00
```

---

## Testes

O plugin foi projetado para facilitar testes unitários do cálculo no `model.py`,
permitindo validação independente do MetaTrader 5.

---

## Contribuição

Pull requests são bem-vindos, especialmente para:

* Novos critérios de HVN/LVN
* Value Area expandida a partir do POC
* Modo TPO
* Integração com VWAP e Footprint

---

## Licença

GPL License
