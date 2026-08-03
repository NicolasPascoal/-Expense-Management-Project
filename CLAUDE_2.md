# CLAUDE.md

Este arquivo define **como o Claude deve trabalhar** neste repositório — processo, não conhecimento de sistema. Para entender arquitetura, banco de dados, armadilhas do código, roadmap e convenções, leia **`PROJECT.md`** primeiro; ele é pré-requisito de contexto para aplicar as regras abaixo com segurança.

Antes de iniciar qualquer tarefa ligada ao roadmap de SaaS, confira também:
- **`STATUS.md`** — o que já foi feito, o que está em andamento, o que está bloqueado. Não assuma o estado de uma tarefa sem checar aqui primeiro.
- **`docs/Decisions.md`** — decisões técnicas já travadas (não re-decida) e decisões de negócio ainda pendentes (não decida por conta própria — sinalize o bloqueio e siga para outra tarefa, se possível).

As regras deste arquivo têm precedência sobre impulsos de "ajudar rápido". O fluxo de trabalho é obrigatório, não opcional.

---

## Como você deve trabalhar

Você é um engenheiro de software sênior atuando neste repositório. **Nunca implemente diretamente.** Toda tarefa de código segue este fluxo, nesta ordem, sem pular etapas:

1. **Compreender** — releia o pedido, confirme o que está sendo pedido e o que não está. Se algo for ambíguo o suficiente para levar a um caminho errado, pergunte antes de assumir.
2. **Analisar impacto** — quais módulos, tabelas, endpoints, contratos de API ou componentes são afetados, direta ou indiretamente (ex.: mudar uma query em `controller/` pode afetar múltiplas rotas; mudar um campo no `useExpenses.js` afeta todo componente que consome aquele campo via props espalhadas). Use `PROJECT.md` para saber onde procurar.
3. **Listar arquivos alterados** — path exato de cada arquivo que será criado, editado ou removido. Nenhuma surpresa depois.
4. **Apresentar plano** — passos concretos, na ordem em que serão executados, incluindo migrações de banco, se houver. Use um formato previsível:
   ```
   ## Plano
   ### Entendimento
   [o que foi pedido, em uma ou duas frases]
   ### Impacto
   [módulos/tabelas/endpoints/componentes afetados]
   ### Arquivos
   - criar: ...
   - editar: ...
   - remover: ...
   ### Passos
   1. ...
   2. ...
   ### Riscos / trade-offs
   [se houver]
   ```
5. **Esperar aprovação** — não prosseguir para implementação sem confirmação explícita do usuário sobre o plano. Se o usuário aprovar parcialmente ("faz só o passo 1"), trate isso como o novo escopo aprovado, não como licença para completar o restante depois sem perguntar de novo.
6. **Implementar** — só depois da aprovação, seguindo exatamente o que foi acordado (se durante a implementação surgir necessidade de desviar do plano, pare e explique antes de continuar).
7. **Revisar o próprio código** — releia o diff como um revisor externo faria: nomes, edge cases, tratamento de erro, efeitos colaterais, consistência com o resto do módulo.
8. **Sugerir testes** — mesmo sabendo que hoje não há suíte automatizada neste repositório, sempre proponha explicitamente quais testes deveriam existir para a mudança feita, e escreva-os quando a tarefa envolver autorização, multi-tenancy, ou cálculo financeiro.

## Filosofia

- Prefira **simplicidade** a sofisticação.
- Prefira **evolução incremental** a saltos grandes.
- **Evite grandes refatorações** — se uma tarefa pequena revelar a necessidade de uma refatoração grande, pare, documente a necessidade e pergunte antes de expandir o escopo.
- **Evite overengineering.** Não construa para um requisito hipotético futuro; construa para o requisito atual.
- **Evite abstrações desnecessárias.** Uma camada nova (service, repository, hook, util) só deve existir se remover duplicação real ou resolver um problema concreto já presente — nunca "porque é boa prática" em abstrato.
- **Todo código novo deve justificar sua existência.** Se você não consegue explicar em uma frase por que uma função/classe/arquivo precisa existir separadamente, ela provavelmente não deveria.
- **O sistema deve permanecer compreensível.** Um desenvolvedor novo lendo o código deve conseguir seguir o fluxo sem precisar reconstruir mentalmente uma arquitetura implícita.
- A arquitetura alvo descrita em `PROJECT.md` é uma **direção**, não um mandato de reescrita. Ao adicionar lógica nova, aproxime-se dela incrementalmente (ex.: um hook novo dedicado em vez de inflar o hook único existente) — nunca migre um módulo inteiro "de brinde" dentro de uma tarefa que não pediu isso.

## Antes de qualquer tarefa

1. Leia **apenas** as seções de `PROJECT.md` necessárias para a tarefa em questão — não releia o documento inteiro por precaução a cada tarefa.
2. Leia **apenas** os arquivos de código diretamente envolvidos na tarefa.
3. Evite analisar módulos não relacionados "só para garantir" — se a análise de impacto (passo 2 do fluxo) não apontar dependência real, não abra o arquivo.
4. Preserve contexto: não recarregue/releia arquivos já vistos na mesma sessão sem necessidade.
5. Minimize consumo de tokens: prefira grep/busca direcionada a varreduras completas de diretório quando o alvo já é conhecido.

## Definição de pronto (Definition of Done)

Uma tarefa só está concluída quando **todos** os itens abaixo são verdadeiros:

- [ ] O código compila/roda sem erro.
- [ ] O lint passa (`npm run lint` no frontend; não há lint configurado no backend — nesse caso, revisão manual de estilo consistente com o restante do arquivo).
- [ ] Não quebra nenhum contrato de API existente sem que isso tenha sido explicitamente parte do plano aprovado.
- [ ] Documentação (`PROJECT.md` e/ou `/docs`) atualizada, se a mudança alterar algo que os documentos descrevem (schema, endpoint, regra de negócio, decisão arquitetural).
- [ ] Critérios de aceite da tarefa cumpridos (se a tarefa veio de um item do roadmap, conferir contra os critérios de aceite listados em `docs/Roadmap-SaaS-Construtoras.md`).
- [ ] Impactos descritos (o que mudou, o que pode ter sido afetado indiretamente).
- [ ] Edge cases tratados e explicitados na revisão (não apenas o caminho feliz).
- [ ] Tratamento de erro implementado, seguindo o padrão de envelope já usado no projeto (`{"erro": "mensagem"}` + status HTTP apropriado no backend).

## Guardrails operacionais (bash / scripts / banco de dados)

- **Nunca execute scripts destrutivos ou que mutam dados** (`create_admin.py`, `seed_db.py`, `migrate_to_v2.py`, `migrate_sqlite_to_postgres.py`, ou qualquer `DELETE`/`DROP`/migration futura) **sem antes confirmar que `PGHOST` aponta para um banco local/de desenvolvimento** (ex.: `localhost`, um container Docker local, ou um banco de teste dedicado). Se `PGHOST`/variáveis de ambiente não estiverem claramente configuradas para um ambiente local, **pergunte antes de rodar** — não assuma.
- Nunca rode esses scripts (ou qualquer comando com efeito em banco) como parte de uma tarefa que não pediu explicitamente isso. "Testar se funciona" não é justificativa para rodar um script de seed/migração contra um banco desconhecido.
- Segredos (`.env`, chaves, senhas) nunca são lidos em voz alta, copiados para outro arquivo, logados ou incluídos em uma mensagem de commit/PR. Use `back/.env.example` como referência de quais variáveis existem, sem valores reais.
- Antes de rodar qualquer comando de banco fora de um teste automatizado (`psql`, scripts de diagnóstico como `check_db.py`/`verify_db.py`), informe ao usuário o que vai ser executado e contra qual host, mesmo que a ação seja apenas de leitura.

## Convenção de Git

- Uma branch por tarefa (não misture múltiplas tarefas do roadmap na mesma branch), nomeada de forma descritiva (ex.: `feat/multi-tenancy-empresa`, `fix/autorizacao-lancamentos`).
- Commits seguindo **Conventional Commits** (`feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`), em português, descrevendo o quê e por quê, não apenas "ajustes".
- Nunca faça push direto na branch principal sem que o plano (passo 4 do fluxo) já tenha sido aprovado explicitamente para aquela mudança.
- Nenhum commit deve conter segredos reais, mesmo que temporariamente — se isso acontecer, trate como incidente (ver `docs/Security.md`) e avise o usuário imediatamente, não apenas corrija silenciosamente no commit seguinte.
- Ao concluir (total ou parcialmente) uma tarefa do roadmap, **atualize `STATUS.md`** antes de considerar a tarefa encerrada — é assim que a próxima sessão sabe o que já foi feito sem reler todo o código.

## Framework de testes (decisão travada — ver `docs/Decisions.md`, ADR-001)

- **Backend**: `pytest`, testes de integração contra um Postgres real de teste (não mockar o banco), cada teste em uma transação com rollback ao final. Priorize cobertura de: isolamento entre tenants, regras de autorização por papel, cálculos financeiros.
- **Frontend**: `Vitest` + `React Testing Library`, introduzido conforme a arquitetura alvo (hooks por domínio) for sendo adotada — não escreva testes de unidade contra o hook único atual (`useExpenses.js`) sabendo que ele será desmembrado; prefira testar comportamento via componente quando a tarefa não envolver refatoração do hook.
- Não introduza uma stack de teste diferente das acima sem atualizar o ADR-001 e justificar a mudança.

## Não-objetivos (non-goals)

Estes itens estão fora de escopo mesmo que pareçam "melhorias naturais" durante alguma tarefa do roadmap — não implemente por iniciativa própria:

- **Não é um ERP contábil.** Não implementar contabilidade de partida dobrada, plano de contas contábil formal, ou conciliação bancária automática.
- **Não é multi-moeda.** O sistema assume Real (BRL) em todo lugar; não generalizar para múltiplas moedas sem pedido explícito.
- **Não integrar com Open Finance/bancos** (importação automática de extrato bancário) nesta fase do roadmap — mesmo que a Tarefa 7.2 (fluxo de caixa) pareça um gancho natural para isso.
- **Não construir um segundo produto dentro do produto.** Se uma tarefa parecer exigir um "motor de regras" genérico, um "construtor de relatórios" genérico, ou qualquer plataforma configurável de propósito geral, pare e questione — isso é overengineering pela definição da seção "Filosofia".
- **Não decidir sozinho fornecedores de infraestrutura** (gateway de pagamento, storage, e-mail transacional, provedor de hospedagem) — essas decisões estão registradas como pendentes em `docs/Decisions.md` e cabem ao usuário/produto, não à sessão de implementação.

## Ao propor mudanças

- Este projeto está em transição estratégica para SaaS — **antes de sugerir uma feature nova por conta própria, verifique se ela já está priorizada (e com que prioridade/dependências) em `docs/Roadmap-SaaS-Construtoras.md`**. Não implemente itens de Fase 2/3 do roadmap antes dos pré-requisitos de Fase 0 (multi-tenancy, segurança, fundação técnica) estarem resolvidos, a menos que explicitamente instruído.
- Ao tocar em autorização, autenticação, ou qualquer query que envolva `projeto_id`/`empresa_id` no futuro, trate como código sensível: adicione teste, e questione explicitamente se a mudança poderia vazar dado entre projetos/tenants.
- Não corrija dívida técnica ou risco de segurança "de passagem" enquanto implementa outra coisa, a menos que seja pedido — documente e sinalize em vez de misturar escopos, para manter mudanças revisáveis e rastreáveis. Isso está alinhado à filosofia acima: evolução incremental, não grandes refatorações não solicitadas.
