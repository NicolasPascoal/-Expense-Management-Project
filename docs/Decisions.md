# Decisions.md — Registro de Decisões de Arquitetura (ADR-lite)

Este arquivo existe para que uma decisão, uma vez tomada, **não seja re-decidida por acidente** por uma sessão futura que não tinha esse contexto. Toda decisão relevante de arquitetura, fornecedor ou stack que afete mais de uma tarefa do roadmap deve ser registrada aqui — decidida ou pendente.

Formato: cada entrada tem `Status` (`Decidido` / `Pendente`), `Contexto`, `Decisão` (ou opções em aberto), e `Consequências`.

---

## ADR-001 — Stack de testes automatizados

- **Status:** Decidido
- **Contexto:** O projeto não tem nenhum teste automatizado (ver `docs/TechDebt.md`). O roadmap (Tarefa 3.3) e o `CLAUDE.md` exigem testes ao mexer em autorização, multi-tenancy e cálculo financeiro. Sem uma escolha travada, cada sessão poderia introduzir uma stack de teste diferente.
- **Decisão:**
  - **Backend**: `pytest` + `pytest-postgresql` (ou um banco Postgres de teste dedicado via Docker) para testes de integração reais contra o banco — dado que a lógica de negócio hoje é SQL direto/ORM, mockar o banco esconderia justamente os bugs de isolamento entre tenants que mais importam aqui. Cada teste roda em uma transação com rollback ao final (evita necessidade de recriar o schema a cada teste).
  - **Frontend**: `Vitest` + `React Testing Library`, introduzido **quando** a arquitetura alvo (hooks por domínio) começar a ser adotada — não faz sentido escrever testes de unidade contra o "God Hook" atual antes de ele ser desmembrado, pois o teste ficaria acoplado a uma estrutura que vai mudar.
- **Consequências:** Testes de backend exigem um Postgres disponível no ambiente de CI (não apenas mocks) — o pipeline de CI (Tarefa 3.4) precisa subir um container de banco de teste. Testes de frontend só começam a aparecer organicamente conforme a Fase 2 avança.

---

## ADR-002 — Gateway de pagamento (assinatura recorrente)

- **Status:** **Pendente — decisão do usuário/produto**
- **Contexto:** Bloqueia as Tarefas 4.1, 4.2, 4.3 e 4.4 do roadmap (todo o Épico 4 — Cobrança e Planos). Sem essa decisão, a Fase 1 (MVP Comercial) não pode ser iniciada de forma completa.
- **Opções em aberto** (não decidir por conta própria — cada uma tem trade-off comercial, não só técnico):
  - **Stripe** — melhor DX e documentação, mas cobertura de PIX/boleto no Brasil é mais limitada/recente; forte se houver ambição de expansão internacional.
  - **Pagar.me** ou **Iugu** — nativos do mercado brasileiro, suporte maduro a PIX/boleto/cartão, mais alinhados ao perfil de construtoras de pequeno/médio porte que preferem boleto/PIX a cartão recorrente.
  - **Asaas** — forte em cobrança recorrente + emissão de nota fiscal integrada (relevante para a Tarefa 4.4).
- **O que decidir:** público-alvo inicial (nacional vs. internacional), meios de pagamento obrigatórios no lançamento (PIX/boleto são prováveis não-negociáveis para o segmento de construção civil brasileira), e se emissão de NF-e/NFS-e integrada é necessária já no MVP ou pode vir depois.
- **Ação:** Quando decidido, atualizar esta entrada para `Status: Decidido`, preencher `Decisão`, e desbloquear as tarefas correspondentes em `STATUS.md`.

---

## ADR-003 — Provedor de e-mail transacional

- **Status:** **Pendente — decisão do usuário/produto**
- **Contexto:** Bloqueia a Tarefa 5.2 (convite de usuários) e a Tarefa 8.3 (notificações) do roadmap.
- **Opções em aberto:**
  - **SendGrid** — amplamente usado, free tier existe, boa entregabilidade.
  - **Amazon SES** — mais barato em volume, exige mais configuração inicial (DKIM/SPF, sandbox de produção).
  - **Resend** — mais recente, DX simples, boa opção se o time preferir setup rápido a menor custo em escala.
- **O que decidir:** volume esperado de e-mails (convites + notificações de aprovação de requisição/tarefa), e se já existe um domínio verificado disponível para configurar DKIM/SPF.
- **Ação:** Quando decidido, atualizar esta entrada e desbloquear as tarefas correspondentes em `STATUS.md`.

---

## ADR-004 — Storage de anexos (recibos, notas fiscais, fotos de requisição)

- **Status:** **Pendente — decisão do usuário/produto**
- **Contexto:** Bloqueia a Tarefa 7.3 (anexos em lançamentos) e a Tarefa 8.1 (foto em requisição de material) do roadmap.
- **Opções em aberto:**
  - **AWS S3** — padrão de mercado, mais opções de configuração (lifecycle, classes de armazenamento para reduzir custo de arquivos antigos).
  - **Cloudflare R2** — compatível com API S3, sem custo de egress (relevante se o volume de download de comprovantes for alto).
  - **Storage do próprio provedor de hospedagem** (se a decisão de infraestrutura de deploy ainda não estiver travada) — pode simplificar operação inicial ao custo de portabilidade futura.
- **O que decidir:** onde o backend será hospedado em produção (isso pode tornar uma opção de storage naturalmente mais barata/integrada que outra), e limite de tamanho/formato de arquivo aceito por plano (afeta também a Tarefa 4.2 — limites de plano).
- **Ação:** Quando decidido, atualizar esta entrada e desbloquear as tarefas correspondentes em `STATUS.md`.

---

## Como adicionar uma nova entrada

Ao tomar (ou precisar registrar a necessidade de) uma decisão que afete mais de uma tarefa do roadmap ou que um agente futuro poderia "reinventar" sem esse contexto:

```markdown
## ADR-00X — Título curto da decisão

- **Status:** Decidido | Pendente
- **Contexto:** por que essa decisão precisa existir, o que ela bloqueia
- **Decisão:** o que foi decidido (ou as opções em aberto, se pendente)
- **Consequências:** o que essa decisão implica para código/infra/custo
```
