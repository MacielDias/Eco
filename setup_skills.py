import subprocess
import os
import shutil

SKILLS_DIR = os.path.expanduser("~/.agents/skills")

# Skills clonadas de repositórios (escrita acadêmica / formatação — conteúdo neutro).
# Se algum repo não existir, o clone apenas avisa e segue.
SKILLS_CLONE = [
    ("https://github.com/gustavobraga-byte/scientific-agent-skills.git", "redacao-cientifica"),
    ("https://github.com/gustavobraga-byte/UFV-ABNT.git", "ufv-abnt"),
]

# Skills econômicas geradas localmente (não dependem de repositório externo).
# Cada SKILL.md descreve QUANDO e COMO usar a fonte/lib, sem impor conclusões.

SKILL_BCB = """\
---
name: bcb-sgs
description: Séries temporais do Banco Central do Brasil via Sistema Gerenciador de Séries Temporais (SGS). Use para SELIC, câmbio, crédito, agregados monetários, IPCA e expectativas de mercado.
---

# Banco Central — SGS (`python-bcb`)

## Quando usar
Qualquer série macro/financeira oficial do Banco Central: taxa SELIC, câmbio
R$/US$, operações de crédito, base monetária, expectativas (Focus), etc.

## Como usar
A biblioteca `python-bcb` lê o SGS por código de série. Você precisa do código
correto da série; consulte https://www3.bcb.gov.br/sgspub/ quando não souber.

```python
from bcb import sgs

# Exemplos de códigos (confirme antes de usar):
#   432  = Meta SELIC (% a.a.)
#   1    = Câmbio R$/US$ (compra, diário)
#   433  = IPCA (var. % mensal)
df = sgs.get({'selic': 432, 'cambio': 1}, start='2010-01-01')
print(df.tail())
```

Para expectativas do boletim Focus:
```python
from bcb import Expectativas
em = Expectativas()
ep = em.get_endpoint('ExpectativasMercadoAnuais')
```

## Boas práticas (anti-viés)
- Sempre informe o **código da série**, o **período** e a **data de extração**:
  séries são revisadas; um número sem data não é replicável.
- Não interprete nível e variação como a mesma coisa. Declare a transformação
  (nível, log, primeira diferença, var. %) que você aplicou.
- Não afirme tendência a partir de poucos pontos; mostre a série e o horizonte.
"""

SKILL_IPEA = """\
---
name: ipeadata
description: Indicadores socioeconômicos e regionais do IPEADATA — mercado de trabalho, renda, pobreza, desigualdade, séries macro e regionais. Use ipeadatapy.
---

# IPEADATA (`ipeadatapy`)

## Quando usar
Indicadores agregados e regionais já compilados pelo IPEA: desemprego, renda,
Gini, pobreza, séries fiscais e monetárias, recortes por UF/município.

## Como usar
```python
import ipeadatapy as ip

# Buscar o código da série pelo nome:
ip.search_series('desemprego')

# Baixar uma série pelo código encontrado:
df = ip.timeseries('CODIGO_DA_SERIE')
print(df.tail())
```

## Boas práticas (anti-viés)
- IPEADATA agrega fontes primárias (IBGE, BCB, etc.). Cite a **fonte primária**
  além do IPEADATA.
- Verifique a unidade e a base de comparação (índices: ano-base; valores:
  nominal vs. real/deflacionado). Não compare nominal com real.
"""

SKILL_SIDRA = """\
---
name: sidra-ibge
description: Tabelas agregadas do IBGE via API SIDRA — PIB, PNAD Contínua, IPCA/INPC, POF, Censo, produção agrícola/industrial. Use sidrapy.
---

# IBGE — SIDRA (`sidrapy`)

## Quando usar
Agregados oficiais do IBGE: PIB e Contas Nacionais, PNAD Contínua (ocupação,
rendimento), inflação (IPCA/INPC), POF, Censo, PAM/PIM.

## Como usar
```python
import sidrapy

# Cada tabela tem um código; variáveis, períodos e níveis territoriais
# são parâmetros. Consulte https://sidra.ibge.gov.br para os códigos.
data = sidrapy.get_table(
    table_code='1737',        # ex.: IPCA
    territorial_level='1',    # 1 = Brasil
    ibge_territorial_code='all',
    period='last'
)
```

## Boas práticas (anti-viés)
- Declare **tabela, variável, período e nível territorial** usados.
- PNAD Contínua é amostral: respeite os **pesos amostrais** e relate o erro/CV
  quando disponível. Não trate estimativas amostrais como contagens exatas.
- Mudanças metodológicas (ex.: PNAD vs. PNAD Contínua) quebram comparabilidade:
  sinalize quando emendar séries de pesquisas diferentes.
"""

SKILL_BDD = """\
---
name: basedosdados
description: Acesso unificado (BigQuery) a microdados e bases tratadas do Brasil — IBGE, RAIS, CAGED, TSE, Censo Escolar, DataSUS e mais — via pacote basedosdados.
---

# Base dos Dados (`basedosdados`)

## Quando usar
Quando precisar de **microdados** ou de bases já tratadas e padronizadas:
RAIS/CAGED (vínculos de emprego), TSE (eleições, candidatos, financiamento),
Censo Escolar/INEP, IBGE, DataSUS. É a rota mais robusta para painéis grandes.

## Como usar
Requer um `billing_project_id` de um projeto Google Cloud (a consulta roda no
BigQuery). O usuário precisa fornecer/autorizar isso.

```python
import basedosdados as bd

df = bd.read_sql(
    query='''
        SELECT ano, sigla_uf, COUNT(*) AS vinculos
        FROM `basedosdados.br_me_rais.microdados_vinculos`
        WHERE ano = 2021
        GROUP BY ano, sigla_uf
    ''',
    billing_project_id='SEU_PROJETO_GCP'
)
```

## Boas práticas (anti-viés)
- Microdados são grandes: filtre no SQL (ano, UF) antes de baixar; não puxe a
  tabela inteira.
- Documente a **query exata** — ela é a definição reproduzível da amostra.
- Em dados de pessoas/vínculos, não tente reidentificar indivíduos e respeite
  os termos de uso da fonte.
- Cuidado com a definição de cada variável na fonte (ex.: vínculo ativo em
  31/12 vs. fluxo no ano): a escolha muda o resultado e deve ser declarada.
"""

SKILL_COMPARACAO = """\
---
name: comparacao-modelos
description: Protocolo para testar várias famílias de modelos (econometria, machine learning, redes neurais), reportar o resultado de TODAS e apontar a melhor com justificativa — sem viés de seleção. Use quando a pergunta admitir mais de uma abordagem.
---

# Comparação e Seleção de Modelos

## Quando usar
Quando há mais de uma forma defensável de modelar o problema e o usuário quer
ver "todos os modelos e qual foi melhor". NÃO use isso para escolher uma
especificação CAUSAL pela métrica de previsão (ver Passo 0).

## Passo 0 — Classifique o objetivo (define o critério de "melhor")
- **Inferência/causal** → "melhor" = identificação mais defensável e robusta.
  Ajuste preditivo NÃO decide. ML entra como ferramenta (double ML, causal
  forest), não como concorrente num ranking de R²/AUC.
- **Previsão** → "melhor" = desempenho fora da amostra na métrica definida a priori.
- **Descrição** → "melhor" = adequação ao padrão + interpretabilidade.

## Protocolo de bake-off preditivo (objetivo = previsão)
1. Métrica definida ANTES: regressão → RMSE/MAE; classificação → AUC-PR/F1 se
   desbalanceado, acurácia só se equilibrado. Justifique.
2. Baseline ingênuo obrigatório (média / última obs. / classe majoritária).
3. Mesmo split, mesmas features, mesmo pré-processamento para todos.
   Série temporal → split temporal (sem embaralhar). Corte → k-fold/holdout.
   Sem vazamento: hiperparâmetros só na validação; teste tocado uma única vez.
4. Candidatos conforme o problema: linear/regularizado, ensemble de árvores,
   rede neural (se dados/estrutura justificarem). Não rode tudo por reflexo.
5. Reporte a métrica COM dispersão (desvio entre folds / IC).

## Esqueleto reprodutível (corte transversal, classificação)
```python
import numpy as np
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

SEED = 42
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)

modelos = {
    "baseline":  DummyClassifier(strategy="most_frequent"),
    "logit":     make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)),
    "rf":        RandomForestClassifier(n_estimators=300, random_state=SEED),
}
# opcionais se instalados:
try:
    from lightgbm import LGBMClassifier
    modelos["lgbm"] = LGBMClassifier(random_state=SEED)
except ImportError:
    pass

metrica = "average_precision"  # AUC-PR; troque conforme o balanceamento
resultados = {}
for nome, mdl in modelos.items():
    s = cross_val_score(mdl, X, y, cv=cv, scoring=metrica)
    resultados[nome] = (s.mean(), s.std())

for nome, (m, sd) in sorted(resultados.items(), key=lambda kv: kv[1][0], reverse=True):
    print(f"{nome:10s}  {metrica}={m:.3f} ± {sd:.3f}")
```

Para **rede neural** (tabular), use Keras/PyTorch com early stopping em conjunto
de validação; reporte na MESMA métrica e split dos demais. Para séries, use
split temporal e considere LSTM/alternativas — sempre contra um baseline.

## Apontar o vencedor (anti-viés de seleção)
- Tabela com TODOS os modelos e métrica (com dispersão).
- Declare o vencedor E a margem. Se a vantagem sobre um modelo mais simples
  estiver dentro do ruído (ICs sobrepostos), diga e prefira o mais simples
  (parcimônia/interpretabilidade). Não promova o complexo por vantagem irrelevante.
- Justifique o "porquê" pelo problema (não linearidade, n amostral, custo,
  interpretabilidade) — não "porque deu o maior número".
- Relate modelos que falharam/não convergiram: é resultado.
- Cheque overfitting (teste << treino) e vazamento.

## Reprodutibilidade
Fixe a semente, registre versões das libs, salve o script da comparação inteira.
"""

LOCAL_SKILLS = {
    "bcb-sgs": SKILL_BCB,
    "ipeadata": SKILL_IPEA,
    "sidra-ibge": SKILL_SIDRA,
    "basedosdados": SKILL_BDD,
    "comparacao-modelos": SKILL_COMPARACAO,
}

JOKES_SKILLS = [
    "📊 Instalando econometria: lembre-se, correlação não é causalidade.",
    "📈 Carregando dados: a série está sendo deflacionada da sua paciência.",
    "📊 Heterocedasticidade detectada na velocidade do download.",
    "📈 Estimando o tempo restante... erro-padrão muito alto.",
    "📊 Variável omitida: o tempo que isso ainda vai levar.",
    "📈 Teste de raiz unitária: seu download tem tendência estocástica.",
    "📊 Endogeneidade: sua impaciência afeta a percepção de lentidão.",
    "📈 Intervalo de confiança do término: [agora, nunca].",
    "📊 p-valor da sua paciência acabar: < 0.01.",
    "📈 Esse progresso não rejeita a hipótese nula de estar parado.",
]

_joke_index = 0

def next_joke():
    global _joke_index
    if _joke_index < len(JOKES_SKILLS):
        joke = JOKES_SKILLS[_joke_index]
        _joke_index += 1
        return joke
    return JOKES_SKILLS[-1]


def clone_skill(repo_url, dest_name):
    tmp = f"/tmp/skill_{dest_name}"
    if os.path.exists(tmp):
        shutil.rmtree(tmp)

    result = subprocess.run(
        ["git", "clone", "--depth", "1", repo_url, tmp],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"⚠️  Não foi possível clonar {repo_url} (seguindo sem ela).")
        return False
    print(f"✅ {dest_name} clonado.")
    return True


def write_local_skills():
    for name, content in LOCAL_SKILLS.items():
        dest = os.path.join(SKILLS_DIR, name)
        os.makedirs(dest, exist_ok=True)
        with open(os.path.join(dest, "SKILL.md"), "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ skill local '{name}' instalada.")


def install_skills():
    print(f"\n{next_joke()}")
    print("🔧 Instalando skills...")
    os.makedirs(SKILLS_DIR, exist_ok=True)

    # 1. Skills econômicas geradas localmente (núcleo do agente)
    print(f"\n{next_joke()}")
    print("📊 Gerando skills de dados econômicos brasileiros...")
    write_local_skills()

    # 2. Skills de escrita/formatação clonadas (opcionais)
    print(f"\n{next_joke()}")
    print("📚 Buscando skills de redação científica e ABNT...")
    for repo, name in SKILLS_CLONE:
        tmp = f"/tmp/skill_{name}"
        if clone_skill(repo, name):
            # 'scientific-agent-skills' guarda as skills numa subpasta 'skills'
            src = os.path.join(tmp, "skills") if os.path.isdir(os.path.join(tmp, "skills")) else tmp
            dest = os.path.join(SKILLS_DIR, name)
            if os.path.exists(dest):
                shutil.rmtree(dest)
            shutil.copytree(src, dest, dirs_exist_ok=True)
            print(f"✅ {name} instalada.")

    print(f"\n{next_joke()}")
    print("\n🎉 Todas as skills instaladas com sucesso!")


if __name__ == "__main__":
    install_skills()
