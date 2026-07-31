# STATUS.md

Estado vivo da transformação em SaaS. **Toda sessão que concluir (total ou parcialmente) uma tarefa do roadmap deve atualizar este arquivo antes de encerrar** — é assim que a próxima sessão (ou você) sabe o que já existe sem precisar reler todo o código para descobrir.

Este arquivo espelha os épicos/tarefas de `docs/Roadmap-SaaS-Construtoras.md`. Não duplique o detalhamento de cada tarefa aqui (prioridade, riscos, critérios de aceite) — isso continua vivendo só no roadmap. Aqui só o **status**.

Legenda: `[ ]` Não iniciado · `[~]` Em andamento · `[x]` Concluído · `[!]` Bloqueado

---

## Como atualizar este arquivo

Ao terminar (ou pausar) uma tarefa:
1. Marque o checkbox correspondente.
2. Preencha `Data` e, se houver, `Commit/PR`.
3. Se ficou parcial, descreva em `Observações` exatamente o que falta — a próxima sessão não tem acesso à sua memória de conversa, só a este arquivo e ao código.
4. Se bloqueado (`[!]`), descreva o bloqueio em `Observações` (ex.: "aguardando decisão de gateway de pagamento — ver docs/adr/002-gateway-pagamento.md").

---

## Fase 0 — Fundação Comercial

### Épico 1 — Multi-tenancy
| Tarefa | Status | Data | Commit/PR | Observações |
|---|---|---|---|---|
| 1.1 — Entidade Empresa/Tenant | [x] | 2026-07-14 | | Tabela `empresas` criada (`modelEmpresas.py`) com empresa seed ("Obra Itanhaém", id=1); `usuarios.empresa_id` e `projetos.empresa_id` (`NOT NULL REFERENCES empresas`) adicionados; criação de usuário/projeto grava `empresa_id` a partir de `g.user`; login/JWT passam a incluir `empresa_id`. `back/migrate_add_empresas.py` executado contra o banco de dev local (`expense_management`) — todos os usuários e projetos existentes foram vinculados a `empresa_id=1` sem perda de dado (verificado por query direta). Suíte pytest inicial (`back/tests/`, ADR-001) rodando contra banco de teste dedicado (`expense_management_test`) — 4/4 testes passando, sem qualquer escrita no banco de dev (confirmado). **Trade-off aceito**: `username` continua `UNIQUE` global (não composto por empresa) — revisitar na Tarefa 5.1 (cadastro público). **Ainda não coberto** (fora do escopo desta tarefa): isolamento de leitura entre empresas (nenhuma query filtra por `empresa_id` ainda) é a Tarefa 1.2; `migrate_to_v2.py` (script legado, não chamado pela aplicação) ficou desatualizado — quebraria se executado do zero |
| 1.2 — Middleware de isolamento por tenant | [x] | 2026-07-17 | | Implementado **sem** um decorator genérico: um decorator único não é viável de forma limpa porque cada tabela chega em `empresa_id` por um caminho diferente (`projetos`/`usuarios` direto; `categorias`/`contas`/`lancamentos_v2` via join com `projetos`; `tarefas`/`requisicoes_materiais` via join com `usuarios`) — decisão registrada no plano aprovado desta tarefa. Toda listagem (`GET /lancamentos`, `/categorias`, `/contas`, `/projetos`, `/tarefas` [admin], `/requisicoes` [admin], `/usuarios`) agora filtra por `empresa_id` do token. Todo `GET`/`PUT`/`DELETE` por id e toda criação que referencia `projeto_id`/`prestador_id` valida posse antes de agir, retornando `404` (recurso de outra empresa) ou `400` (criação apontando para `projeto_id`/`prestador_id` de outra empresa) — nunca vazando a existência do recurso alheio. Dois helpers reutilizáveis em `back/app/utils/tenant.py` (`projeto_pertence_a_empresa`, `usuario_pertence_a_empresa`). 15 testes novos em `back/tests/test_tenant_isolation.py` (cross-tenant por módulo), suíte completa (19/19) passando contra `expense_management_test`. **Não coberto** (fora do escopo desta tarefa): unificação de `@token_required`/`@admin_required` é a Tarefa 1.3; `username` continua único globalmente (trade-off já registrado na Tarefa 1.1) |
| 1.3 — Autorização por role considerando tenant | [x] | 2026-07-20 | | Decorators unificados: `_autenticar()` é o ponto único de decode em `auth_middleware.py`; `admin_required` agora é composição sobre ele (mesmo contrato de `g.user` por construção). De passagem, dentro do escopo: removido `except Exception: str(e)` que vazava detalhe interno na resposta 401, e `split(" ")[1]` que estourava 500 com header `Bearer ` malformado. Matriz de permissão papel × rota documentada em `docs/Authorization.md` (seção 6) e testada em `back/tests/test_autorizacao.py` (13 testes: mecanismo + matriz admin/prestador/user). Suíte completa 47/47. **Fora do escopo** (registrado no plano aprovado): papéis expandidos e regra própria para `role='user'` são o Épico 6 |

### Épico 2 — Segurança e Confiança
| Tarefa | Status | Data | Commit/PR | Observações |
|---|---|---|---|---|
| 2.1 — Rotacionar/remover segredos do Git | [x] | 2026-07-30 | | `.env` destrackeado, fallbacks hardcoded removidos de `docker-compose.yml`, credenciais fixas removidas de `create_admin.py`. **2026-07-30**: `JWT_SECRET_KEY` e senha do Postgres (usuário `postgres`, banco local `expense_management`) rotacionados — valores antigos (vazados no histórico do Git) agora inválidos; nada estava em produção no momento, então não houve impacto em usuários ativos. **Decisão pendente, não bloqueante**: reescrever ou não o histórico do Git para remover os valores antigos por completo (ver `docs/Security.md`, item 1.1) — como os valores já foram rotacionados, isso deixou de ser urgente e é só limpeza opcional |
| 2.2 — Rate limiting no login | [x] | 2026-07-30 | | Flask-Limiter adicionado (`app/extensions.py`, storage em memória — só serve para um único processo backend, ver comentário no arquivo). `POST /api/login` limitado por IP (10/min) e por conta via `username` do corpo (5/min; 20/hora) — decorators empilhados em `auth_routes.py`. Testado manualmente com scripts de tentativas repetidas: 401 dentro do limite, 429 ao estourar, tanto por conta quanto por IP. Suíte completa 47/47 continua passando |
| 2.3 — Tratamento de erro padronizado + logging estruturado | [x] | 2026-07-30 | | `app/logging_config.py`: logging padrão da stdlib com formatter JSON em stdout (sem nova dependência tipo `structlog`). `app/__init__.py`: `request_id` (UUID4, aceita `X-Request-Id` de entrada, devolvido no header e no corpo de erro), log de toda requisição concluída, e dois `@app.errorhandler` globais — `HTTPException` (400/401/403/404/429...) loga em WARNING e normaliza pra JSON (antes retornava HTML padrão do Flask nos erros não tratados manualmente); `Exception` genérica loga stack trace completo (`exc_info`) + `request_id`/`empresa_id`/`usuario_id` internamente e devolve só `{"erro": "Erro interno do servidor", "request_id": ...}` ao cliente — nunca stack trace/nome de tabela/coluna/mensagem de driver. Removidos os 5 pontos que vazavam `str(e)` na resposta (`usuarios_controller.criar_usuario`, `servicos_controller.criar_categoria`/`criar_conta`, `tarefas_controller.criar_tarefa`/`atualizar_tarefa`) — viraram `try/finally` (deixa propagar pro handler global) exceto `criar_usuario`, que trata `UniqueViolation` (username duplicado) como 400 de validação, não 500. De passagem: corrigido bug de conexão do pool não sendo fechada em todo caminho de retorno em `atualizar_tarefa`, e um bug real de encoding (log gravava cp850 no Windows em vez de UTF-8, corrompendo acentos) pego durante teste manual. `print()` de `db.py`/`auditoria.py`/`main.py` viraram log estruturado. Testado manualmente: rota inexistente agora retorna JSON 404 (antes HTML), username duplicado retorna 400 limpo, erro genuíno (tipo inválido) retorna 500 genérico sem vazar detalhe — log interno confirmado com stack trace completo e request_id correlacionado. Suíte 47/47 passando |
| 2.4 — Conformidade LGPD básica | [ ] | | | Depende de 1.1; parte jurídica fora do escopo de engenharia |

### Épico 3 — Fundação Técnica
| Tarefa | Status | Data | Commit/PR | Observações |
|---|---|---|---|---|
| 3.1 — ORM (SQLAlchemy) + migrations (Alembic) | [ ] | | | Ideal iniciar junto com 1.1 |
| 3.2 — Migrar campos dinâmicos TEXT → JSONB | [ ] | | | Depende de 3.1 |
| 3.3 — Suíte de testes automatizados | [ ] | | | Ver docs/Decisions.md (ADR-001) para stack de teste |
| 3.4 — Pipeline de CI/CD | [ ] | | | Depende de 3.3 |

## Fase 1 — MVP Comercial

### Épico 4 — Cobrança e Planos
| Tarefa | Status | Data | Commit/PR | Observações |
|---|---|---|---|---|
| 4.1 — Gateway de pagamento | [!] | | | Bloqueado: decisão de fornecedor pendente — ver docs/adr/002-gateway-pagamento.md |
| 4.2 — Planos e limites | [ ] | | | Depende de 1.1, 4.1 |
| 4.3 — Trial self-service | [ ] | | | Depende de 4.1, 4.2, 5.1 |
| 4.4 — Emissão de nota fiscal | [ ] | | | Depende de 4.1 |

### Épico 5 — Onboarding e Autosserviço
| Tarefa | Status | Data | Commit/PR | Observações |
|---|---|---|---|---|
| 5.1 — Cadastro público de construtora | [ ] | | | Depende de 1.1 |
| 5.2 — Convite de usuários por e-mail | [!] | | | Bloqueado: provedor de e-mail pendente — ver docs/adr/003-provedor-email.md |
| 5.3 — Onboarding guiado | [ ] | | | Depende de 5.1 |

## Fase 2 — Diferenciação Competitiva

### Épico 6 — RBAC Granular e Controle por Obra
| Tarefa | Status | Data | Commit/PR | Observações |
|---|---|---|---|---|
| 6.1 — Papéis expandidos + permissões por ação | [ ] | | | Depende de 1.3 |
| 6.2 — Controle de acesso por obra | [ ] | | | Depende de 6.1 |
| 6.3 — Log de auditoria | [x] | 2026-07-20 | bd3f23b | Tabela `auditoria` + helper `log_auditoria` (falha silenciosa — auditoria nunca derruba a ação principal) chamado em criar/editar/excluir de lançamentos, requisições e tarefas; aba Timeline (admin-only, últimos 100 eventos). **Desvio registrado**: grava descrição curta, não diff before/after completo (critério do roadmap) — diff fica para quando houver demanda real. Exclusões preservam o log (`ON DELETE SET NULL` no usuário). 3 testes em `test_auditoria.py` |

### Épico 7 — Controle Financeiro de Obra
| Tarefa | Status | Data | Commit/PR | Observações |
|---|---|---|---|---|
| 7.1 — Orçado vs. Realizado | [x] | 2026-07-18 | | Implementado **sem** esperar a Tarefa 3.2 (JSONB) — decisão registrada no plano aprovado: o "realizado" já era calculado 100% em JS a partir de `dados` (`useExpenses.js`/`porCategoria`), então a feature nova só precisou do lado "orçado". Nova tabela `orcamentos` (`projeto_id`, `categoria_id`, `valor_orcado`, `UNIQUE(projeto_id, categoria_id)`), CRUD em `orcamentos_controller.py`/`orcamentos_routes.py` com o mesmo padrão de isolamento por tenant da Tarefa 1.2 (leitura filtra por `empresa_id` via join, escrita valida posse de `projeto_id` e que `categoria_id` pertence a esse projeto). Campo "orçado" editável em `ServicosTab.jsx`; nova aba "Orçamento" (`OrcamentoTab.jsx`) com barras + alerta visual no estilo Prumo (`--ok`/`--blue`/`--bad` conforme percentual: <90%/90–100%/>100%), oculta para `prestador`. 7 testes novos em `back/tests/test_orcamentos.py`, suíte completa 26/26 passando. Verificado ponta a ponta no navegador contra o banco de dev (categoria "Alvenaria", orçado R$50k × realizado R$127k → 254%, flag de estouro exibida corretamente). **Não coberto**: se o volume de lançamentos crescer muito, a agregação client-side pode precisar migrar para SQL (gatilho natural pra fazer a Tarefa 3.2 depois, não antes) |
| 7.2 — Fluxo de caixa | [x] | 2026-07-20 | bd3f23b | Nova entidade `entradas` (aporte/recebimento) com isolamento por tenant; aba Fluxo de Caixa com saldo (entradas − saídas) da obra ativa, registro e exclusão de entrada. **Não coberto**: saldo consolidado entre obras — app nunca agrega múltiplos projetos; fica para quando for pedido. 5 testes em `test_entradas.py` |
| 7.3 — Anexos de recibos/notas | [!] | | | Bloqueado: storage de anexos pendente — ver docs/adr/004-storage-anexos.md |
| 7.4 — Parcelamento de pagamentos | [ ] | | | Depende de 7.1 |
| 7.5 — Lançamento automático a partir de requisição aprovada | [ ] | | | Depende de 1.1, 7.1 |
| 7.6 — Relatórios PDF e comparação entre obras | [ ] | | | Depende de 3.2, 7.1 |

### Épico 8 — Usabilidade em Campo
| Tarefa | Status | Data | Commit/PR | Observações |
|---|---|---|---|---|
| 8.1 — Upload de foto na requisição | [ ] | | | Depende de 7.3 (mesma infra de storage) |
| 8.2 — PWA | [ ] | | | |
| 8.3 — Notificações | [!] | | | Bloqueado: provedor de e-mail pendente — ver docs/adr/003-provedor-email.md |

## Fase 3 — Prontidão Enterprise
| Tarefa | Status | Data | Commit/PR | Observações |
|---|---|---|---|---|
| 9.1 — White-label | [ ] | | | Depende de 1.1 |
| 9.2 — SSO | [ ] | | | Só priorizar mediante conta enterprise concreta em negociação |
| 9.3 — Observabilidade e SLA | [ ] | | | Antecipar para logo após Fase 1, independente da numeração |
| 9.4 — Portabilidade de dados | [ ] | | | Depende de 2.4 |

---

## Decisões de negócio pendentes que bloqueiam tarefas acima

Ver `docs/Decisions.md` para o log completo. Resumo do que está travando tarefas hoje:

- **Gateway de pagamento** (bloqueia 4.1, 4.2, 4.3, 4.4) — pendente de decisão do usuário/produto.
- **Storage de anexos** (bloqueia 7.3, 8.1) — pendente de decisão do usuário/produto.
- **Provedor de e-mail transacional** (bloqueia 5.2, 8.3) — pendente de decisão do usuário/produto.

## Log de mudanças deste arquivo

| Data | O que mudou |
|---|---|
| — | Arquivo criado, roadmap ainda não iniciado — todas as tarefas em `[ ]` ou `[!]` conforme dependência de decisão de negócio |
| 2026-07-14 | Tarefa 1.1 (entidade Empresa/Tenant) concluída — schema, vínculo de `usuarios`/`projetos`, JWT com `empresa_id`, migração executada no banco de dev e suíte de testes inicial passando. Ver observações da tarefa |
| 2026-07-17 | Tarefa 1.2 (isolamento por tenant) concluída — todas as leituras/escritas de lançamentos, categorias, contas, projetos, tarefas, requisições e usuários agora filtram/validam por `empresa_id`. Ver observações da tarefa |
| 2026-07-18 | Tarefa 7.1 (Orçado vs. Realizado) concluída — feita direto no schema atual, sem esperar a Tarefa 3.2. Ver observações da tarefa |
| 2026-07-20 | Tarefas 7.2 (Fluxo de Caixa) e 6.3 (Timeline/Auditoria) concluídas em sessão anterior (commit bd3f23b); Tarefa 1.3 (autorização por role) concluída — decorators unificados, matriz testada. Épico 1 completo. Ver observações das tarefas |
