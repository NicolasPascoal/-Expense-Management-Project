# Roadmap Estratégico — De Ferramenta Interna a SaaS Comercial para Construtoras

**Autor:** CTO (visão de produto/engenharia)
**Premissa deste documento:** cada item aqui foi filtrado por uma pergunta única — *"isso aumenta a chance de vender e reter uma construtora como cliente pagante?"*. Itens de baixo impacto comercial (polimento de código, reorganização de pastas, ajustes cosméticos) foram propositalmente **excluídos**, mesmo que estivessem listados como dívida técnica no diagnóstico anterior. Alguns deles reaparecem aqui **somente quando são pré-requisito inevitável** de algo que vende (ex.: ORM/migrations não vende sozinho, mas sem ele não dá para construir com segurança as features que vendem).

---

## Como ler este documento

- **Épico**: uma capacidade de negócio completa (não uma tela).
- **Fase**: agrupamento temporal — o que precisa existir antes de vender para o primeiro cliente externo, o que diferencia no mercado, o que permite vender contratos maiores.
- Cada **tarefa** traz: Prioridade, Dependências, Impacto no Negócio, Impacto Técnico, Dificuldade, Estimativa, Riscos, Critérios de Aceite.
- **Prioridade**: P0 (bloqueia o lançamento comercial), P1 (necessário para o primeiro ciclo de vendas sério), P2 (diferencial competitivo/expansão), P3 (necessário só para contas enterprise grandes).
- **Estimativa**: em dias úteis de um time pequeno (2-3 devs), não em horas individuais — é uma ordem de grandeza para planejamento, não um compromisso de sprint.

---

## Tese comercial (por que esta ordem de prioridades)

Hoje o sistema é, na prática, **uma ferramenta de uso interno de uma única obra/empresa**, sem separação real entre "empresas diferentes usando o mesmo sistema" (multi-tenancy). Isso significa que, literalmente, **não é possível vender para um segundo cliente hoje sem risco grave**: qualquer usuário autenticado de qualquer "construtora" enxergaria dados de todas as outras. Por isso, a Fase 0 deste roadmap não é sobre "melhorar", é sobre **tornar o produto vendável para mais de um cliente sem vazar dados entre eles** — isso é pré-requisito lógico de tudo o mais, incluindo cobrança (não dá para cobrar por "obra" ou por "empresa" se o sistema não sabe o que é uma empresa).

Depois disso, o roadmap segue a lógica: **(1) conseguir cobrar** → **(2) ter a feature que realmente resolve a dor do comprador** (controle financeiro de obra: orçado vs. realizado, fluxo de caixa, comprovantes) → **(3) reduzir atrito de adoção em campo** (mobile, fotos, notificações) → **(4) vencer objeções de contas maiores** (segurança, auditoria, SSO, white-label).

---

# FASE 0 — Fundação Comercial (bloqueia qualquer venda para um segundo cliente)

> Nada nesta fase é "feature vendável" isoladamente. É o que torna possível vender **com segurança** para mais de uma construtora ao mesmo tempo. Sem isso, o produto não é um SaaS — é uma instância única mal disfarçada.

## Épico 1 — Multi-tenancy (isolamento entre construtoras)

### Tarefa 1.1 — Modelar entidade "Empresa/Tenant" e vincular usuários e projetos a ela
- **Prioridade:** P0
- **Dependências:** Nenhuma (ponto de partida do roadmap)
- **Impacto no negócio:** Sem isso, literalmente não existe um segundo cliente possível — é o pré-requisito absoluto para transformar "o sistema da Obra Itanhaém" em um produto multi-cliente. Toda venda futura depende disto.
- **Impacto técnico:** Introduz uma nova tabela `empresas` (tenant) e uma coluna `empresa_id` em `usuarios` e `projetos`. Esta é a mudança de schema mais invasiva de todo o roadmap — toca praticamente todas as tabelas transitivamente (via `projeto_id`).
- **Dificuldade:** Alta
- **Estimativa:** 5-8 dias
- **Riscos:** Migração de dados existentes (a obra atual precisa virar o "tenant 1"); qualquer query esquecida sem filtro de tenant vira um vazamento de dados entre clientes — o maior risco de reputação possível para um SaaS B2B financeiro.
- **Critérios de aceite:**
  - [ ] Toda tabela que hoje depende de `projeto_id` tem rastreabilidade até um `empresa_id` (direta ou via join)
  - [ ] Usuário só pode pertencer a uma empresa (ou N:N, se decidido suportar consultorias — a decidir com produto)
  - [ ] Dado legado da "Obra Itanhaém" migrado para uma empresa seed sem perda de histórico

### Tarefa 1.2 — Middleware/decorator de isolamento por tenant em toda a API
- **Prioridade:** P0
- **Dependências:** Tarefa 1.1
- **Impacto no negócio:** É a garantia técnica de que "Construtora A nunca vê dado de Construtora B" — a condição mínima de confiança para qualquer cliente pagante assinar contrato.
- **Impacto técnico:** Substitui o modelo atual (`@token_required` genérico) por um modelo que injeta `empresa_id` do token em toda query, e recusa qualquer acesso a um recurso de `empresa_id` diferente do usuário autenticado — inclusive para admins (um admin de uma construtora não deveria ver dados de outra).
- **Dificuldade:** Alta
- **Estimativa:** 5-7 dias
- **Riscos:** É fácil esquecer um endpoint (histórico do projeto já mostra inconsistência entre módulos — ver diagnóstico anterior); requer testes automatizados dedicados (ver Tarefa 3.4) para não depender de revisão manual.
- **Critérios de aceite:**
  - [ ] Todo endpoint que lê/escreve um recurso de projeto/lançamento/categoria/conta/tarefa/requisição valida `empresa_id` do recurso contra `empresa_id` do token
  - [ ] Existe um teste automatizado que tenta acessar cross-tenant para cada endpoint e espera `403`/`404`
  - [ ] Nenhum endpoint de listagem retorna dados de outra empresa mesmo sem filtro explícito no request

### Tarefa 1.3 — Reescrever autorização por role considerando o tenant (fechar a lacuna hoje existente em lançamentos/categorias/contas)
- **Prioridade:** P0
- **Dependências:** Tarefas 1.1, 1.2
- **Impacto no negócio:** Hoje qualquer usuário autenticado (mesmo "prestador") pode alterar dados financeiros via chamada direta à API — isso é inaceitável para um produto comercial que lida com dinheiro de terceiros; um único incidente de auditoria de segurança pode inviabilizar a venda para qualquer construtora de porte médio/grande.
- **Impacto técnico:** Unifica os dois decorators existentes (`token_required`/`admin_required`) em um único mecanismo consistente que sempre popula o contexto do usuário (papel + tenant) e aplica a regra de role em todos os módulos, não só em Tarefas.
- **Dificuldade:** Média
- **Estimativa:** 3-5 dias
- **Riscos:** Pode quebrar fluxos hoje "funcionais por acidente" (ex.: telas que dependiam implicitamente de o backend não checar nada); precisa de comunicação com o time de produto sobre qual papel pode fazer o quê antes de travar.
- **Critérios de aceite:**
  - [ ] `prestador` não consegue criar/editar/excluir lançamentos, categorias ou contas via API, mesmo com token válido
  - [ ] Toda rota tem uma matriz de permissão testável e documentada

## Épico 2 — Segurança e Confiança (pré-requisito de venda B2B financeira)

### Tarefa 2.1 — Rotacionar e remover segredos do histórico do Git; adotar gestor de segredos
- **Prioridade:** P0
- **Dependências:** Nenhuma (pode e deve ser feito em paralelo ao Épico 1)
- **Impacto no negócio:** Qualquer cliente enterprise (ou seu jurídico/segurança) que audite o repositório antes de assinar contrato encontra uma chave JWT e senha de banco expostas — isso é motivo de reprovação imediata em qualquer due diligence de segurança, além do risco real de takeover do sistema hoje.
- **Impacto técnico:** Reescrita de histórico do Git (ou início de um repositório limpo), migração de configuração para um cofre de segredos (Vault, AWS Secrets Manager, ou no mínimo variáveis de ambiente injetadas via pipeline de deploy, nunca versionadas).
- **Dificuldade:** Baixa (execução) / Média (coordenação, já que invalida tokens/acessos existentes)
- **Estimativa:** 1-2 dias
- **Riscos:** Janela de indisponibilidade breve ao trocar `JWT_SECRET_KEY` (todos os tokens ativos são invalidados); precisa de comunicação para usuários atuais fazerem login novamente.
- **Critérios de aceite:**
  - [ ] `.env` não existe mais em nenhum commit acessível (histórico reescrito ou repositório recriado)
  - [ ] Segredos de produção são diferentes dos usados em qualquer ambiente de desenvolvimento/repositório
  - [ ] Processo de rotação de segredo documentado e testado uma vez

### Tarefa 2.2 — Rate limiting e proteção de força bruta no login
- **Prioridade:** P0
- **Dependências:** Nenhuma
- **Impacto no negócio:** Item de checklist padrão em qualquer questionário de segurança de fornecedor (vendor security assessment) que uma construtora de médio/grande porte vai aplicar antes de comprar — sua ausência é um "não" automático em processos de compra mais maduros.
- **Impacto técnico:** Middleware de rate limiting (ex.: Flask-Limiter) por IP e por conta, com backoff progressivo.
- **Dificuldade:** Baixa
- **Estimativa:** 1-2 dias
- **Riscos:** Baixo; atenção para não bloquear acidentalmente uso legítimo de equipes atrás do mesmo IP (NAT de obra/escritório compartilhado).
- **Critérios de aceite:**
  - [x] Após N tentativas falhas em um intervalo, requisições adicionais são bloqueadas temporariamente
  - [x] Testado manualmente com script de tentativas repetidas

### Tarefa 2.3 — Padronizar tratamento de erro (parar de vazar detalhes internos) e logging estruturado
- **Prioridade:** P1
- **Dependências:** Nenhuma
- **Impacto no negócio:** Suporte a clientes fica inviável sem logs estruturados e correlacionáveis (não dá para operar um SaaS pago sem conseguir investigar um chamado de suporte); vazamento de erro interno na resposta HTTP é outro item reprovado em auditorias de segurança.
- **Impacto técnico:** Handler de erro global do Flask, biblioteca de logging estruturado (ex.: `structlog`) com correlação por request-id e por tenant.
- **Dificuldade:** Média
- **Estimativa:** 3-4 dias
- **Riscos:** Baixo, mas exige disciplina para não reintroduzir `except Exception: return str(e)` em código novo.
- **Critérios de aceite:**
  - [ ] Nenhuma resposta de erro da API expõe stack trace, nome de tabela/coluna ou mensagem crua de driver de banco
  - [ ] Todo erro 500 é logado com `request_id`, `empresa_id`, `usuario_id` e stack trace completo apenas no log interno

### Tarefa 2.4 — Conformidade básica com LGPD (registro de tratamento, política de privacidade, exportação/exclusão de dados por tenant)
- **Prioridade:** P1
- **Dependências:** Tarefa 1.1 (precisa existir o conceito de tenant para "exportar/excluir os dados de uma empresa")
- **Impacto no negócio:** O sistema processa dados financeiros e pessoais (nomes de prestadores, valores pagos) de terceiros — vender para empresas brasileiras sem uma postura mínima de conformidade com a LGPD é um risco jurídico direto para o cliente comprador, e cada vez mais aparece como cláusula contratual obrigatória (DPA — Data Processing Agreement).
- **Impacto técnico:** Endpoint/processo de exportação completa dos dados de uma empresa; processo de exclusão sob solicitação; documento de política de privacidade e termos de uso publicados.
- **Dificuldade:** Média
- **Estimativa:** 4-6 dias (parte jurídica em paralelo com parte técnica)
- **Riscos:** Parte jurídica (redação de política/termos) não é competência de engenharia — precisa de apoio jurídico externo; sem isso, o prazo real pode estourar.
- **Critérios de aceite:**
  - [ ] Existe um mecanismo (mesmo que manual/operacional no início) de exportar todos os dados de uma empresa em formato legível
  - [ ] Existe um processo documentado de exclusão de dados de uma empresa encerrada
  - [ ] Política de privacidade e termos de uso publicados e vinculados ao fluxo de cadastro

## Épico 3 — Fundação Técnica para Construir Rápido e Seguro

> Estes itens não vendem por si só, mas sem eles cada feature comercial das fases seguintes (Épicos 4-9) fica mais lenta e mais arriscada de construir. Incluídos aqui **apenas** porque são pré-requisito direto de itens que vendem — não porque "o código ficaria mais bonito".

### Tarefa 3.1 — Introduzir ORM (SQLAlchemy) e migrations versionadas (Alembic)
- **Prioridade:** P0
- **Dependências:** Ideal fazer junto com a Tarefa 1.1 (mudança de schema de multi-tenancy é a oportunidade natural de já nascer com migrations versionadas, em vez de mais um script avulso)
- **Impacto no negócio:** Toda feature comercial das fases seguintes (orçamento, parcelamento, anexos, auditoria) exige alterações de schema. Sem migrations versionadas, cada alteração é um script manual de risco alto — isso deixa o time de engenharia lento demais para competir no ritmo de um mercado SaaS, e aumenta o risco de indisponibilidade em produção a cada release.
- **Impacto técnico:** Reescrita da camada de acesso a dados (`controller/` e `database/model*.py`) para usar SQLAlchemy; eliminação da camada de compatibilidade SQLite→Postgres (`db.py`), que deixa de ser necessária.
- **Dificuldade:** Alta
- **Estimativa:** 8-12 dias
- **Riscos:** Maior refatoração técnica do roadmap — risco de regressão em todos os módulos existentes; deve ser acompanhada de testes automatizados (Tarefa 3.3) para ser segura.
- **Critérios de aceite:**
  - [ ] Toda query SQL manual foi substituída por modelos ORM
  - [ ] Toda alteração de schema, a partir desta tarefa, é feita via migration versionada e reversível
  - [ ] A camada de compatibilidade SQLite (`db.py`) é removida

### Tarefa 3.2 — Migrar campos dinâmicos de `TEXT` para `JSONB`
- **Prioridade:** P1
- **Dependências:** Tarefa 3.1
- **Impacto no negócio:** Habilita relatórios e filtros mais ricos (ex.: "todos os lançamentos acima de X em qualquer obra") sem depender de trazer todos os dados para o cliente processar — pré-requisito técnico direto da feature comercial de relatórios/dashboards avançados (Épico 7).
- **Impacto técnico:** Alteração de tipo de coluna + reescrita das agregações hoje feitas no frontend para acontecerem via SQL (`->>`, índices GIN).
- **Dificuldade:** Média
- **Estimativa:** 3-5 dias
- **Riscos:** Baixo, é uma migração de dado direta (JSON válido em ambos os formatos), mas exige reescrever consultas de agregação.
- **Critérios de aceite:**
  - [ ] Consultas de totais por categoria/conta passam a ser feitas via SQL, não mais no frontend
  - [ ] Tempo de resposta do dashboard não degrada com o aumento do volume de lançamentos

### Tarefa 3.3 — Suíte de testes automatizados (foco em autorização multi-tenant e regras financeiras)
- **Prioridade:** P0
- **Dependências:** Idealmente em paralelo com Tarefas 1.2 e 3.1
- **Impacto no negócio:** É o que permite vender e evoluir o produto **sem quebrar a promessa de isolamento entre clientes a cada deploy** — para um SaaS B2B financeiro, "nunca vazar dado de um cliente para outro" é a promessa mais cara de quebrar (contratualmente e reputacionalmente).
- **Impacto técnico:** Suíte de testes de integração no backend (pytest), priorizando: isolamento multi-tenant, regras de autorização por papel, cálculos financeiros. Não é necessário cobertura 100% — é necessário cobertura dos pontos que, se quebrarem, geram incidente comercial grave.
- **Dificuldade:** Média
- **Estimativa:** 5-8 dias (fundação inicial; depois é trabalho contínuo por feature)
- **Riscos:** Pressão de prazo comercial tende a fazer esta tarefa ser cortada — deve ser tratada como não-negociável dado o modelo de negócio (dinheiro de terceiros).
- **Critérios de aceite:**
  - [ ] Existe teste automatizado cobrindo tentativa de acesso cross-tenant para cada entidade principal
  - [ ] Existe teste automatizado cobrindo cada regra de autorização por papel
  - [ ] Pipeline de CI (Tarefa 3.4) roda esta suíte a cada mudança de código

### Tarefa 3.4 — Pipeline de CI/CD
- **Prioridade:** P1
- **Dependências:** Tarefa 3.3 (para ter o que rodar)
- **Impacto no negócio:** Permite entregar features comerciais em ritmo de mercado sem depender de validação manual — velocidade de entrega é, ela mesma, um argumento de venda ("evoluímos rápido com base no seu feedback").
- **Impacto técnico:** Pipeline (GitHub Actions ou equivalente) rodando lint, testes e build a cada PR; deploy automatizado para ambiente de staging.
- **Dificuldade:** Baixa
- **Estimativa:** 2-3 dias
- **Riscos:** Baixo.
- **Critérios de aceite:**
  - [ ] Todo PR roda testes e lint automaticamente antes de poder ser mesclado
  - [ ] Deploy para staging acontece automaticamente após merge na branch principal

---

# FASE 1 — MVP Comercial (o que faz o produto ser vendável e cobrável pela primeira vez)

## Épico 4 — Cobrança e Planos (sem isso não existe "comercial" em SaaS)

### Tarefa 4.1 — Integração com gateway de pagamento (assinatura recorrente)
- **Prioridade:** P0
- **Dependências:** Épico 1 (multi-tenancy) completo
- **Impacto no negócio:** É literalmente o mecanismo pelo qual a empresa passa a faturar — sem isso, não há como "vender" no sentido comercial, apenas prover acesso gratuito e cobrar manualmente por fora (o que não escala e não é um SaaS de fato).
- **Impacto técnico:** Integração com gateway (Stripe para cartão internacional, ou Pagar.me/Iugu/Asaas para boleto/PIX no Brasil — decisão de produto: público-alvo brasileiro provavelmente exige PIX/boleto como opção). Webhooks de confirmação de pagamento, inadimplência e cancelamento.
- **Dificuldade:** Alta
- **Estimativa:** 8-10 dias
- **Riscos:** Escolha errada de gateway pode limitar meios de pagamento relevantes no setor de construção civil (empresas menores frequentemente preferem boleto/PIX a cartão); webhooks mal tratados geram inconsistência entre "pagou" e "acesso liberado".
- **Critérios de aceite:**
  - [ ] Uma empresa consegue assinar um plano pago e ter acesso liberado automaticamente após confirmação de pagamento
  - [ ] Inadimplência suspende o acesso de forma previsível (com período de tolerância definido pelo produto)
  - [ ] Cancelamento é auto-serviço, sem necessidade de suporte manual

### Tarefa 4.2 — Modelagem de planos e limites (nº de obras, usuários, armazenamento)
- **Prioridade:** P0
- **Dependências:** Tarefa 1.1 (tenant), Tarefa 4.1
- **Impacto no negócio:** Define a régua de monetização — sem planos diferenciados, não há como capturar tanto o pequeno construtor (1 obra) quanto a construtora média (múltiplas obras simultâneas), que são segmentos de preço muito diferentes.
- **Impacto técnico:** Tabela de planos + limites, checagem de limite em pontos de criação (nova obra, novo usuário, upload de anexo).
- **Dificuldade:** Média
- **Estimativa:** 4-6 dias
- **Riscos:** Decisão de precificação é de produto/comercial, não só técnica — atraso aqui pode travar a tarefa; a engenharia deve validar a estrutura de dados de forma flexível o suficiente para o time comercial iterar em preço sem nova migration a cada mudança de plano.
- **Critérios de aceite:**
  - [ ] Uma empresa no plano gratuito/trial não consegue ultrapassar os limites definidos (ex.: criar uma segunda obra)
  - [ ] Alterar o plano de uma empresa (upgrade/downgrade) reflete os novos limites imediatamente

### Tarefa 4.3 — Trial self-service e fluxo de upgrade
- **Prioridade:** P1
- **Dependências:** Tarefas 4.1, 4.2, 5.1 (onboarding)
- **Impacto no negócio:** Reduz o atrito de vendas — permite que uma construtora comece a usar sozinha, sem depender de um vendedor/onboarding manual, o que é essencial para um modelo de aquisição eficiente (PLG — product-led growth) e reduz o custo de aquisição de cliente.
- **Impacto técnico:** Período de trial com contagem regressiva, bloqueio suave ao expirar (acesso de leitura, sem criar novos dados) até conversão em plano pago.
- **Dificuldade:** Média
- **Estimativa:** 3-4 dias
- **Riscos:** Se o bloqueio ao fim do trial for muito agressivo (perde acesso total), gera atrito e churn antes mesmo de converter — desenho de UX importa tanto quanto a implementação técnica aqui.
- **Critérios de aceite:**
  - [ ] Uma empresa nova começa automaticamente em trial, sem intervenção manual
  - [ ] Ao expirar o trial sem conversão, o acesso é degradado (não apagado) e há um caminho claro de upgrade dentro do próprio produto

### Tarefa 4.4 — Emissão de nota fiscal/fatura
- **Prioridade:** P2
- **Dependências:** Tarefa 4.1
- **Impacto no negócio:** Empresas (pessoa jurídica) frequentemente exigem nota fiscal para efetivar o pagamento internamente (departamento financeiro/contábil do cliente) — sua ausência pode travar a conversão de trial em pago mesmo com o cliente satisfeito com o produto.
- **Impacto técnico:** Integração com emissor de NF-e/NFS-e (via o próprio gateway de pagamento escolhido, que frequentemente já oferece isso, ou um serviço dedicado).
- **Dificuldade:** Média
- **Estimativa:** 3-5 dias
- **Riscos:** Regras fiscais variam por município (NFS-e é municipal no Brasil) — pode exigir apoio contábil especializado.
- **Critérios de aceite:**
  - [ ] Toda cobrança bem-sucedida gera uma nota fiscal acessível pelo cliente

## Épico 5 — Onboarding e Autosserviço

### Tarefa 5.1 — Cadastro público de nova construtora (signup)
- **Prioridade:** P0
- **Dependências:** Tarefa 1.1
- **Impacto no negócio:** Hoje só um admin de sistema pode criar um novo usuário/projeto manualmente no banco — isso não escala como aquisição comercial. Um formulário público de cadastro é o que permite qualquer construtora começar a usar o produto sem depender de um humano da equipe interna.
- **Impacto técnico:** Tela pública de cadastro, criação automática de: empresa (tenant), primeiro usuário admin daquela empresa, projeto/obra inicial.
- **Dificuldade:** Média
- **Estimativa:** 4-5 dias
- **Riscos:** Superfície nova de ataque (cadastro público) — precisa de validação de e-mail, proteção contra bots (captcha), e reaproveitar o rate limiting da Tarefa 2.2.
- **Critérios de aceite:**
  - [ ] Uma pessoa consegue criar uma conta nova de construtora sem intervenção manual da equipe
  - [ ] E-mail é validado antes da conta ser totalmente ativada

### Tarefa 5.2 — Convite de usuários por e-mail com papel pré-definido
- **Prioridade:** P1
- **Dependências:** Tarefa 5.1, Épico 6 (papéis)
- **Impacto no negócio:** Reduz drasticamente o atrito de adoção em equipe — hoje só um admin pode criar usuário manualmente digitando usuário/senha; convite por e-mail é o padrão esperado em qualquer SaaS B2B moderno e acelera a expansão de uso dentro de um cliente já pago (mais usuários = maior valor percebido = menor churn).
- **Impacto técnico:** Envio de e-mail transacional (ex.: SendGrid/SES), link de convite com token de expiração, tela de definição de senha pelo convidado.
- **Dificuldade:** Média
- **Estimativa:** 3-4 dias
- **Riscos:** Depende de infraestrutura de e-mail transacional confiável (deliverability); baixo risco técnico isolado.
- **Critérios de aceite:**
  - [ ] Um admin consegue convidar um novo usuário por e-mail, definindo o papel antecipadamente
  - [ ] O convite expira após um prazo definido e pode ser reenviado

### Tarefa 5.3 — Onboarding guiado (wizard de primeira obra)
- **Prioridade:** P2
- **Dependências:** Tarefa 5.1
- **Impacto no negócio:** Reduz o tempo até o primeiro valor percebido ("time to value") — quanto antes uma construtora cadastra sua primeira obra e vê o dashboard populado, maior a chance de conversão de trial em pago.
- **Impacto técnico:** Fluxo guiado (poucos passos) para criar a primeira obra, definir categorias/contas iniciais (aproveitando os templates já existentes no seed atual) e convidar a primeira pessoa da equipe.
- **Dificuldade:** Baixa
- **Estimativa:** 2-3 dias
- **Riscos:** Baixo — principalmente trabalho de UX/frontend.
- **Critérios de aceite:**
  - [ ] Uma nova conta consegue, em menos de 5 minutos, ter uma obra criada com categorias/contas padrão prontas para uso

---

# FASE 2 — Diferenciação Competitiva (o que faz a construtora escolher este produto e não uma planilha)

> Esta é a fase que entrega o **valor central** que uma construtora paga para ter: controle financeiro de obra de verdade. Sem essa fase, o produto compete apenas em preço contra uma planilha Excel — com ela, compete em valor.

## Épico 6 — RBAC Granular e Controle por Obra

### Tarefa 6.1 — Papéis expandidos (gestor de obra, financeiro, pedreiro) com permissões por ação
- **Prioridade:** P1
- **Dependências:** Épico 1 (multi-tenancy), Tarefa 1.3
- **Impacto no negócio:** Construtoras de porte médio/grande têm estrutura organizacional real (o dono não é quem lança despesa; o financeiro não é quem aprova compra em campo) — vender "admin vs. prestador" apenas é insuficiente para esse comprador; a granularidade de papéis é frequentemente citada como critério de decisão em ferramentas de gestão B2B.
- **Impacto técnico:** Extensão do modelo de autorização (já unificado na Tarefa 1.3) para suportar múltiplos papéis configuráveis por ação, não apenas dois papéis fixos.
- **Dificuldade:** Alta
- **Estimativa:** 6-8 dias
- **Riscos:** Se mal desenhado, complexidade de permissões pode confundir o próprio usuário final (que é, tipicamente, pouco afeito a sistemas complexos) — exige validação de UX junto com construtoras piloto.
- **Critérios de aceite:**
  - [ ] É possível criar um usuário com papel "financeiro" que vê e edita lançamentos, mas não gerencia usuários
  - [ ] É possível criar um usuário com papel "gestor de obra" que aprova requisições e gerencia tarefas, mas não vê lançamentos de outras obras que não gerencia

### Tarefa 6.2 — Controle de acesso por obra (usuário vinculado a obras específicas dentro da mesma empresa)
- **Prioridade:** P1
- **Dependências:** Tarefa 6.1
- **Impacto no negócio:** Construtoras com múltiplas obras simultâneas frequentemente não querem que o gestor da Obra A veja os números financeiros da Obra B (times diferentes, sigilo interno entre unidades de negócio) — recurso citado com frequência como requisito por compradores com mais de uma obra ativa.
- **Impacto técnico:** Tabela de associação usuário↔projeto com papel específico por vínculo (o mesmo usuário pode ser "gestor" na Obra A e não ter acesso nenhum à Obra B).
- **Dificuldade:** Média
- **Estimativa:** 4-5 dias
- **Riscos:** Baixo, é uma extensão natural do modelo de tenant já existente.
- **Critérios de aceite:**
  - [ ] Um usuário sem vínculo a uma obra específica não a vê em sua lista de projetos, mesmo pertencendo à mesma empresa

### Tarefa 6.3 — Log de auditoria (quem fez o quê, quando)
- **Prioridade:** P1
- **Dependências:** Épico 1
- **Impacto no negócio:** Em contexto financeiro, "quem editou este lançamento e quando" é frequentemente um requisito não-negociável de compradores com processos de controle interno mais maduros (e um forte argumento de venda contra planilhas, que não têm rastreabilidade nenhuma).
- **Impacto técnico:** Tabela de auditoria registrando criação/edição/exclusão de lançamentos, requisições e tarefas, com usuário, timestamp e diff do que mudou.
- **Dificuldade:** Média
- **Estimativa:** 4-6 dias
- **Riscos:** Volume de dados de auditoria cresce continuamente — precisa de estratégia de retenção/arquivamento desde o início.
- **Critérios de aceite:**
  - [ ] Toda alteração em um lançamento fica registrada com autor e timestamp, visível em uma tela de histórico
  - [ ] Exclusões não removem o registro de auditoria mesmo que o dado original seja apagado

## Épico 7 — Controle Financeiro de Obra (o motivo real de compra)

### Tarefa 7.1 — Orçado vs. Realizado por obra e por categoria
- **Prioridade:** P0
- **Dependências:** Épico 1, Tarefa 3.2 (JSONB, para agregação eficiente)
- **Impacto no negócio:** Esta é, provavelmente, **a funcionalidade de maior impacto comercial de todo o roadmap** — é a dor central de qualquer construtora ("a obra está estourando o orçamento? em qual categoria?"). É o tipo de tela que se mostra em uma demonstração de vendas e fecha contrato.
- **Impacto técnico:** Nova entidade de orçamento (valor planejado por categoria/obra), comparação em tempo real contra o realizado (soma de lançamentos), com alerta visual de estouro.
- **Dificuldade:** Média
- **Estimativa:** 5-7 dias
- **Riscos:** Depende de dados de orçamento serem inseridos pelo cliente com disciplina — se o produto não tornar isso fácil (ex.: importação de planilha de orçamento existente), a adoção da feature pode ser baixa mesmo estando disponível.
- **Critérios de aceite:**
  - [ ] É possível definir um valor orçado por categoria em uma obra
  - [ ] O dashboard mostra, em tempo real, o percentual consumido do orçamento por categoria
  - [ ] Existe um alerta visual quando uma categoria ultrapassa o orçado

### Tarefa 7.2 — Fluxo de caixa (entradas + saídas, saldo por obra e geral)
- **Prioridade:** P1
- **Dependências:** Épico 1
- **Impacto no negócio:** O sistema atual só rastreia despesas (saídas) — sem entradas (aportes de sócios, financiamento, recebimentos), não há visão de saldo de caixa real, que é a pergunta mais básica de qualquer responsável financeiro de obra ("quanto ainda tenho disponível?").
- **Impacto técnico:** Nova entidade de "entrada" (aporte/recebimento), cálculo de saldo (entradas − saídas) por obra e consolidado.
- **Dificuldade:** Média
- **Estimativa:** 4-6 dias
- **Riscos:** Baixo tecnicamente; risco de escopo (pode ser confundido com um módulo contábil completo — deve ficar limitado a controle de caixa simples, não contabilidade formal).
- **Critérios de aceite:**
  - [ ] É possível registrar uma entrada de caixa vinculada a uma obra
  - [ ] O dashboard mostra saldo atual por obra e saldo consolidado de todas as obras da empresa

### Tarefa 7.3 — Anexos de recibos/notas fiscais em lançamentos
- **Prioridade:** P1
- **Dependências:** Épico 1
- **Impacto no negócio:** Comprovação documental de despesa é frequentemente exigida por sócios/investidores de uma obra e por processos de auditoria contábil — é um diferencial claro contra qualquer alternativa baseada em planilha, e reduz disputas ("cadê o comprovante desse gasto?").
- **Impacto técnico:** Upload de arquivo/imagem vinculado a um lançamento, armazenamento em object storage (S3 ou equivalente, não no banco), geração de URL assinada para visualização.
- **Dificuldade:** Média
- **Estimativa:** 4-5 dias
- **Riscos:** Custo de armazenamento cresce com o uso — deve estar refletido nos limites de plano (Tarefa 4.2); necessário definir política de tamanho/formato de arquivo aceito.
- **Critérios de aceite:**
  - [ ] É possível anexar uma ou mais imagens/PDFs a um lançamento
  - [ ] O anexo é visualizável posteriormente por qualquer usuário com acesso ao lançamento

### Tarefa 7.4 — Parcelamento de pagamentos
- **Prioridade:** P2
- **Dependências:** Tarefa 7.1
- **Impacto no negócio:** Compras grandes de material/serviço em obra são frequentemente parceladas — sem esse recurso, o usuário precisa lançar manualmente cada parcela como um lançamento separado sem vínculo entre elas, perdendo a visão de "quanto ainda falta pagar deste fornecedor".
- **Impacto técnico:** Relação 1:N entre um lançamento "pai" (compra) e suas parcelas, com status individual (pendente/pago/atrasado) por parcela.
- **Dificuldade:** Média
- **Estimativa:** 4-6 dias
- **Riscos:** Baixo, mas precisa de cuidado em como isso interage com o cálculo de orçado vs. realizado (a parcela ainda não paga conta como "comprometido" ou só quando efetivamente paga? — decisão de produto a validar com clientes piloto).
- **Critérios de aceite:**
  - [ ] É possível dividir um lançamento em N parcelas com datas e status individuais
  - [ ] O relatório de fluxo de caixa reflete corretamente parcelas futuras como compromisso, não como gasto já realizado

### Tarefa 7.5 — Geração automática de lançamento a partir de requisição de material aprovada
- **Prioridade:** P2
- **Dependências:** Épico 1, Tarefa 7.1
- **Impacto no negócio:** Elimina retrabalho (hoje o gestor aprova o pedido e depois precisa lançar manualmente a despesa em outro lugar) — é um argumento forte de eficiência operacional em vendas ("aprovou, já virou lançamento, sem digitar duas vezes").
- **Impacto técnico:** Ao mudar o status de uma requisição para "Aprovado"/"Comprado", oferecer (ou automatizar, conforme decisão de produto) a criação de um lançamento vinculado, pré-preenchido com os dados da requisição.
- **Dificuldade:** Baixa/Média
- **Estimativa:** 2-3 dias
- **Riscos:** Baixo, mas requer decidir se a criação é automática ou uma sugestão que o gestor confirma (recomenda-se a segunda opção, para não gerar lançamentos com valores ainda não confirmados de compra).
- **Critérios de aceite:**
  - [ ] Ao aprovar uma requisição, o gestor tem a opção de gerar um lançamento já vinculado, sem redigitar as informações

### Tarefa 7.6 — Relatórios exportáveis (PDF) e comparação entre obras
- **Prioridade:** P1
- **Dependências:** Tarefa 3.2, Tarefa 7.1
- **Impacto no negócio:** Relatório em PDF é frequentemente o que o comprador (dono da construtora) precisa levar para uma reunião com sócios/investidores/banco — a ausência disso mantém o cliente dependente de exportar CSV e montar o relatório em outra ferramenta, reduzindo a percepção de "produto completo".
- **Impacto técnico:** Geração de PDF server-side (ex.: WeasyPrint/ReportLab) com resumo financeiro por obra e comparação lado a lado entre obras da mesma empresa.
- **Dificuldade:** Média
- **Estimativa:** 4-6 dias
- **Riscos:** Baixo tecnicamente; risco de escopo (pode virar um pedido infinito de "mais um formato de relatório" — deve ter um conjunto inicial fechado e validado com clientes piloto antes de expandir).
- **Critérios de aceite:**
  - [ ] É possível exportar um relatório em PDF com totais por categoria/conta de uma obra
  - [ ] É possível comparar, lado a lado, o total gasto entre duas ou mais obras da mesma empresa

## Épico 8 — Usabilidade em Campo (adoção pela ponta operacional)

### Tarefa 8.1 — Upload de foto na requisição de material
- **Prioridade:** P1
- **Dependências:** Tarefa 7.3 (reaproveita a mesma infraestrutura de upload)
- **Impacto no negócio:** Já é um item explicitamente esperado pelo próprio roadmap original do produto ("criar pedido com item, quantidade, observação, foto") — reduz ambiguidade do pedido (uma foto do material desejado evita compra errada) e é um recurso visivelmente "moderno" em demonstração comercial.
- **Impacto técnico:** Reaproveita o object storage já implementado na Tarefa 7.3, aplicado ao formulário de requisição.
- **Dificuldade:** Baixa
- **Estimativa:** 2 dias
- **Riscos:** Baixo.
- **Critérios de aceite:**
  - [ ] Um prestador consegue anexar uma foto ao criar um pedido de material pelo celular

### Tarefa 8.2 — Progressive Web App (PWA) para uso em campo
- **Prioridade:** P1
- **Dependências:** Nenhuma direta (pode ser feito em paralelo)
- **Impacto no negócio:** O usuário final de campo (pedreiro/prestador) usa celular, muitas vezes com conectividade instável na obra — uma experiência instalável, com ícone na tela inicial e funcionamento básico offline, aumenta drasticamente a adoção real por essa persona, que é quem gera os dados de origem (requisições, atualizações de tarefa) que o comprador (dono/gestor) quer ver.
- **Impacto técnico:** Service worker, manifest, cache de assets estáticos e fila local de ações para sincronizar quando a conexão voltar (ao menos para criação de requisição/atualização de tarefa).
- **Dificuldade:** Média
- **Estimativa:** 5-7 dias
- **Riscos:** Sincronização offline mal feita pode gerar duplicidade de dados ao reconectar — escopo inicial deve ser conservador (cache + fila simples), não uma solução offline-first completa.
- **Critérios de aceite:**
  - [ ] O aplicativo pode ser "instalado" na tela inicial do celular
  - [ ] Uma requisição criada com conexão instável é enviada automaticamente assim que a conexão for restabelecida, sem duplicar

### Tarefa 8.3 — Notificações (e-mail e/ou push) de aprovação e mudança de status
- **Prioridade:** P2
- **Dependências:** Nenhuma direta
- **Impacto no negócio:** Reduz o tempo de resposta entre "pedido feito" e "pedido aprovado/comprado" — melhora a percepção de agilidade do produto e reduz a necessidade de o prestador ficar checando o app manualmente, o que aumenta a satisfação e retenção de uso.
- **Impacto técnico:** Envio de e-mail transacional em eventos-chave (requisição aprovada/recusada, tarefa atribuída, tarefa concluída); push notification via PWA como evolução posterior.
- **Dificuldade:** Baixa/Média
- **Estimativa:** 3-4 dias
- **Riscos:** Baixo — cuidado para não gerar excesso de notificações (fadiga de notificação reduz engajamento em vez de aumentar).
- **Critérios de aceite:**
  - [ ] Um prestador recebe uma notificação quando seu pedido de material muda de status
  - [ ] Um prestador recebe uma notificação quando uma nova tarefa é atribuída a ele

## Épico 10 — Funcionalidades Solicitadas (prioridade não decidida)

> Itens pedidos diretamente (fora do processo de priorização por impacto comercial que gerou o resto deste documento). Registrados aqui para não se perder, mas **sem prioridade P0-P3 atribuída** — cabe ao produto decidir quando/se entram na fila, na frente ou atrás do que já está priorizado acima.

### Tarefa 10.1 — Contas a Pagar (módulo dedicado)
- **Prioridade:** a definir
- **Dependências:** Épico 1
- **Impacto no negócio:** Cobre vencimento/pagamento/fornecedor/parcelamento/comprovante de forma estruturada, com calendário financeiro e alertas — hoje só existe fluxo de caixa simples (Tarefa 7.2).
- **Impacto técnico:** Nova entidade `conta_pagar` (fornecedor, valor, vencimento, status, parcelas, comprovante). Reaproveita storage de anexos (Tarefa 7.3, ainda bloqueada) para o comprovante.
- **Dificuldade:** Média
- **Riscos:** Sobreposição conceitual com Fluxo de Caixa (7.2) e Parcelamento (7.4) — definir fronteira exata entre os três antes de iniciar, para não duplicar modelo de dado.
- **Critérios de aceite:**
  - [ ] É possível cadastrar uma conta a pagar com fornecedor, valor e vencimento
  - [ ] Alerta visual para contas vencendo/vencidas

### Tarefa 10.2 — Controle de Materiais Compartilhados (equipamentos entre obras)
- **Prioridade:** a definir
- **Dependências:** Épico 1
- **Impacto no negócio:** Rastreia equipamentos (serra, betoneira, escada, furadeira) por quantidade total/disponível/em uso, obra atual, responsável e histórico de transferência entre obras.
- **Impacto técnico:** Nova entidade `equipamento` + `movimentacao_equipamento`.
- **Dificuldade:** Alta
- **Riscos:** ⚠️ Este item se aproxima de um módulo de inventário/ativos genérico — o `CLAUDE.md` deste repo tem regra explícita contra "construir um segundo produto dentro do produto". **Confirmar com produto que isso é realmente escopo do Gabaro antes de iniciar implementação.**
- **Critérios de aceite:**
  - [ ] Um equipamento pode ser transferido de uma obra para outra, com histórico registrado

### Tarefa 10.3 — Calendário Unificado
- **Prioridade:** a definir
- **Dependências:** Tarefa 10.1 (para ter vencimentos a mostrar)
- **Impacto no negócio:** Visão única de tarefas, entregas, compras, contas a pagar e reuniões, em modo diário/semanal/mensal.
- **Impacto técnico:** Agregação de eventos de múltiplas entidades já existentes (tarefas, requisições) + novas (contas a pagar).
- **Dificuldade:** Média
- **Riscos:** Fácil de subestimar — agregar fontes de dado heterogêneas num único calendário tende a crescer em escopo.
- **Critérios de aceite:**
  - [ ] Calendário mostra tarefas e contas a pagar num único lugar, filtrável por tipo

### Tarefa 10.4 — Dashboard Inteligente (consolidação)
- **Prioridade:** a definir
- **Dependências:** Tarefas 7.1, 7.2, 10.1 e Épico 8 (quanto mais dessas prontas, mais completo o painel)
- **Impacto no negócio:** Um único painel com total gasto, previsto, fluxo de caixa, orçado × realizado, obras em atraso, pedidos pendentes, contas vencendo, equipamentos em uso e saúde financeira — reduz a necessidade de navegar entre abas.
- **Impacto técnico:** Não é uma feature nova de dado, é composição do que as tarefas acima já expõem — só faz sentido depois que a maioria delas existir, senão vira painel com buracos.
- **Dificuldade:** Média
- **Riscos:** Se iniciada cedo demais (antes das dependências), rende um dashboard incompleto que precisa ser refeito depois.

### Tarefa 10.5 — Comentários em Tarefas e Pedidos
- **Prioridade:** a definir
- **Dependências:** Épico 1
- **Impacto no negócio:** Permite discussão contextual em uma tarefa/pedido sem depender de WhatsApp externo — reduz perda de contexto.
- **Impacto técnico:** Nova entidade `comentario` (entidade, entidade_id, usuario_id, texto, criado_em) — reaproveita o mesmo padrão de isolamento por tenant já usado em Auditoria (Tarefa 6.3).
- **Dificuldade:** Baixa
- **Riscos:** Baixo — é o item de menor escopo desta lista, candidato natural a entrar antes dos outros 4 se o produto decidir priorizar algo desta leva.
- **Critérios de aceite:**
  - [ ] É possível comentar em uma tarefa ou pedido de material e ver o histórico de comentários

---

# FASE 3 — Prontidão Enterprise (o que destrava contratos maiores)

> Estes itens raramente são decisivos para o primeiro cliente pequeno, mas são frequentemente **bloqueadores explícitos** em processos de compra de construtoras de maior porte (que têm departamento de TI/segurança próprio e exigem itens específicos em RFPs).

### Tarefa 9.1 — White-label (logo e cores da construtora no sistema)
- **Prioridade:** P2
- **Dependências:** Épico 1
- **Impacto no negócio:** Construtoras maiores valorizam a percepção de que a ferramenta é "delas", especialmente quando compartilham telas/relatórios com sócios e investidores externos — recurso frequentemente citado como diferencial em negociações de contratos anuais maiores.
- **Impacto técnico:** Configuração de logo/cores por tenant, aplicada ao layout e aos relatórios em PDF.
- **Dificuldade:** Baixa/Média
- **Estimativa:** 3-4 dias
- **Riscos:** Baixo.
- **Critérios de aceite:**
  - [ ] Uma empresa consegue configurar seu próprio logo, visível no cabeçalho da aplicação e nos relatórios exportados

### Tarefa 9.2 — Single Sign-On (SSO) via Google/Microsoft
- **Prioridade:** P3
- **Dependências:** Épico 1
- **Impacto no negócio:** Empresas maiores frequentemente exigem SSO corporativo por política interna de segurança (gestão centralizada de identidade) — sua ausência pode ser um bloqueador explícito em RFPs de contas grandes, mesmo que o produto atenda todo o resto.
- **Impacto técnico:** Integração OAuth2/OIDC com Google Workspace e Microsoft Entra ID (Azure AD), mantendo login por senha como alternativa para clientes menores.
- **Dificuldade:** Alta
- **Estimativa:** 6-8 dias
- **Riscos:** Baixo retorno para clientes pequenos/médios — deve ser priorizado apenas quando houver uma conta enterprise concreta em negociação que exija isso, não de forma especulativa.
- **Critérios de aceite:**
  - [ ] Um usuário consegue autenticar via conta Google/Microsoft corporativa, sem necessidade de senha própria do sistema

### Tarefa 9.3 — Observabilidade e SLA (monitoramento, alertas, backups automatizados testados)
- **Prioridade:** P1 (mais cedo do que a numeração de fase sugere, se houver qualquer cliente pagante)
- **Dependências:** Nenhuma técnica direta, mas faz mais sentido após a Fase 0/1 estarem em produção real
- **Impacto no negócio:** No momento em que existe o primeiro cliente pagante, uma indisponibilidade não comunicada ou uma perda de dados sem backup testado é o tipo de incidente que encerra o contrato imediatamente — é o item de menor "brilho" em uma demonstração de vendas, mas o de maior risco de perda de receita já conquistada se ausente.
- **Impacto técnico:** Monitoramento de uptime/erro (ex.: Sentry para erros de aplicação, uptime checks externos), backups automatizados do Postgres com teste periódico de restauração (não apenas "o backup existe", mas "o backup restaura corretamente").
- **Dificuldade:** Média
- **Estimativa:** 4-6 dias
- **Riscos:** É comum subestimar isso até o primeiro incidente real — deve ser tratado como obrigatório assim que houver o primeiro cliente pagante, independentemente de "fase".
- **Critérios de aceite:**
  - [ ] Existe alerta automático para erro 500 acima de um limiar e para indisponibilidade do serviço
  - [ ] Existe um backup automatizado diário, com teste de restauração comprovado ao menos uma vez por trimestre

### Tarefa 9.4 — Exportação/portabilidade completa de dados por empresa
- **Prioridade:** P2
- **Dependências:** Tarefa 2.4 (LGPD)
- **Impacto no negócio:** Paradoxalmente, facilitar a saída do cliente (exportar todos os seus dados a qualquer momento) é um argumento de **confiança** que facilita a entrada — construtoras maiores frequentemente perguntam "e se eu quiser sair, como fico com meus dados?" antes de assinar, e uma resposta fraca aqui pode custar a venda.
- **Impacto técnico:** Endpoint de exportação completa (JSON/CSV) de todos os dados de uma empresa, sob demanda.
- **Dificuldade:** Baixa/Média
- **Estimativa:** 2-3 dias
- **Riscos:** Baixo.
- **Critérios de aceite:**
  - [ ] Um admin de uma empresa consegue solicitar e receber uma exportação completa de todos os dados daquela empresa

---

## Visão consolidada — sequenciamento sugerido

```
FASE 0 (Fundação — bloqueia qualquer venda para 2º cliente)
├─ Épico 1 — Multi-tenancy               (P0, ~15-20 dias)
├─ Épico 2 — Segurança e Confiança        (P0/P1, ~9-12 dias, paralelo ao Épico 1)
└─ Épico 3 — Fundação Técnica              (P0/P1, ~18-28 dias, iniciar junto do Épico 1)

FASE 1 (MVP Comercial — primeiro cliente pagante)
├─ Épico 4 — Cobrança e Planos             (P0/P1/P2, ~18-25 dias)
└─ Épico 5 — Onboarding e Autosserviço     (P0/P1/P2, ~9-12 dias)

FASE 2 (Diferenciação — o motivo de escolher este produto)
├─ Épico 6 — RBAC Granular                 (P1, ~14-19 dias)
├─ Épico 7 — Controle Financeiro de Obra   (P0/P1/P2, ~23-33 dias)
├─ Épico 8 — Usabilidade em Campo          (P1/P2, ~10-13 dias)
└─ Épico 10 — Funcionalidades Solicitadas  (prioridade não decidida — ver seção própria)

FASE 3 (Enterprise — contratos maiores)
├─ Tarefa 9.1 — White-label                (P2)
├─ Tarefa 9.2 — SSO                        (P3, sob demanda de conta específica)
├─ Tarefa 9.3 — Observabilidade e SLA       (P1 — antecipar para logo após Fase 1)
└─ Tarefa 9.4 — Portabilidade de dados      (P2)
```

## Recomendação executiva final

Se houvesse orçamento/tempo para apenas **três coisas** antes de tentar vender para o primeiro cliente externo, seriam, nesta ordem: **(1)** Multi-tenancy com isolamento real (Épico 1) — sem isso não existe segundo cliente possível; **(2)** remoção dos segredos expostos e fechamento da lacuna de autorização em lançamentos (Tarefas 2.1 e 1.3) — sem isso, o primeiro incidente de segurança encerra a empresa antes de começar; **(3)** Orçado vs. Realizado (Tarefa 7.1) — é a funcionalidade que efetivamente justifica o preço de uma assinatura frente à alternativa gratuita (planilha). Tudo o mais neste roadmap aumenta a taxa de conversão e o tamanho do contrato, mas estes três itens são a diferença entre "ter um produto para vender" e "não ter".
