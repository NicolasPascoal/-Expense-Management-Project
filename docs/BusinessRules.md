# Business Rules — Expense Management Project

Este documento consolida as regras de negócio identificadas no código (backend e frontend), organizadas por módulo. Regras marcadas como **(implícita)** foram deduzidas do comportamento do código, não de um comentário explícito ou especificação — quando havia dúvida real sobre a intenção, isso foi registrado em vez de assumido (ver seção final "Regras Ambíguas").

## 1. Autenticação e Sessão

- Login exige `username` e `password`; senha é validada por hash (Werkzeug), nunca comparada em texto plano.
- Token JWT tem validade de **24 horas** a partir da emissão (`exp`).
- **(implícita, frontend)** Sessão é encerrada automaticamente após **15 minutos de inatividade** do usuário (sem interação de mouse/teclado/scroll/touch), mesmo que o token JWT ainda seja válido no backend — esta é uma regra puramente de UX/client-side; o token continua tecnicamente utilizável em outra aba/dispositivo até expirar.
- Ao receber `401` de qualquer chamada de API, o frontend limpa a sessão local e força o retorno à tela de login (evento global `auth-error`).

## 2. Usuários e Papéis

- Existem, na prática, dois papéis com comportamento diferenciado: `admin` (`is_admin=1`) e `prestador` (`role='prestador'`, `is_admin=0`).
- O usuário de `id=1` é **meta-protegido**: não pode ser excluído, nem pelo próprio admin — essa regra é aplicada tanto no backend (`deletar_usuario`) quanto redundantemente no frontend (`AdminTab.jsx` bloqueia o clique antes mesmo de chamar a API).
- Apenas administradores podem criar, listar e remover usuários.
- **(implícita)** Ao criar um usuário pela tela de Admin, se o checkbox "Admin" não estiver marcado, o sistema oferece um segundo checkbox "Prestador" — se também desmarcado, o `role` enviado é `'user'`. Este terceiro valor **não tem nenhuma regra de negócio associada** em nenhuma rota do backend (ver seção "Regras Ambíguas").

## 3. Projetos (Obras)

- Todo lançamento pertence a exatamly um projeto (`projeto_id` obrigatório).
- Cada projeto define seu próprio schema de campos (`colunas`) — um array de definições `{name, label, type, options?}` usado para renderizar dinamicamente o formulário de lançamento e para orientar a exportação/importação de CSV.
- Existe sempre um projeto seed padrão (`Obra Itanhaém`, id fixo 1) criado automaticamente na primeira inicialização do banco.
- Apenas administradores podem criar, editar ou excluir projetos.
- **Excluir um projeto exclui em cascata** todos os seus lançamentos, categorias e contas (não há confirmação adicional ou soft-delete no backend — a confirmação existe apenas como modal no frontend, `ConfirmModal`/`DeleteModal`).

## 4. Lançamentos (Despesas)

- Um lançamento é composto por um `projeto_id` fixo (definido na criação, não alterável via `PUT`) e um conjunto de campos dinâmicos conforme `projetos.colunas`.
- **(implícita, frontend)** Se o schema do projeto ativo incluir um campo chamado `data`, ele é obrigatório no formulário (única validação de campo obrigatório aplicada no cliente); nenhuma outra obrigatoriedade de campo é verificada, nem no cliente nem no servidor.
- **(implícita, frontend)** Se os campos `quantidade` e `unitario` forem preenchidos, o campo `valor` é recalculado automaticamente como `quantidade × unitario`, sobrescrevendo qualquer valor manual digitado anteriormente pelo usuário assim que um desses dois campos for alterado novamente.
- **(corrigido em 2026-07-08)** Qualquer usuário autenticado não-`prestador` pode criar, editar e excluir lançamentos de **qualquer** projeto via API — não há checagem de propriedade de projeto (isso depende de multi-tenancy, ainda não implementado). Usuários com `role='prestador'` agora recebem `403` em qualquer chamada a `/lancamentos*` (ver `Authorization.md`).

## 5. Categorias e Contas

- Escopadas por projeto — cada obra tem seu próprio conjunto de categorias/contas.
- Qualquer usuário autenticado (não apenas admin) pode criar/excluir categorias e contas.
- **(implícita)** Excluir uma categoria ou conta não verifica nem impede que lançamentos existentes ainda referenciem esse nome dentro do seu JSON `dados` — o vínculo é apenas por nome de string, sem integridade referencial real entre `categorias`/`contas` e o conteúdo de `lancamentos_v2.dados`.

## 6. Requisições de Material

- Qualquer usuário autenticado pode criar uma requisição, associada automaticamente ao seu próprio `usuario_id` (não é possível criar uma requisição em nome de outro usuário via este endpoint).
- Uma requisição nasce sempre com `status = 'Pendente'`.
- Usuários não-admin só visualizam suas próprias requisições; admins visualizam todas, com o nome do solicitante.
- Somente administradores podem alterar o `status` de uma requisição — não há validação de quais transições de status são permitidas (ex.: nada impede voltar de `'Comprado'` para `'Pendente'`).
- **Não implementado (confirmado pelo roadmap do autor)**: gerar lançamento financeiro automático ao aprovar uma requisição; anexar foto ao pedido; vincular a requisição a um projeto/obra específico.

## 7. Tarefas

- Somente administradores podem criar tarefas, e toda tarefa deve ter `titulo` e `prestador_id` definidos (o prestador responsável é obrigatório desde a criação).
- Uma tarefa nasce sempre com `status = 'Pendente'` (a menos que explicitamente enviado outro valor no corpo da requisição de criação — o backend aceita um `status` customizado no `POST`, o que é inconsistente com o comportamento de "requisições", que sempre força `'Pendente'` independentemente do body).
- **Regra de propriedade**: um prestador só pode ver e editar as tarefas onde ele é o `prestador_id`; um administrador vê e edita todas.
- Um prestador só pode alterar `status` e `observacoes` de suas próprias tarefas — não pode alterar `titulo`, `descricao` ou reatribuir a tarefa a outro prestador.
- Somente administradores podem excluir tarefas.

## 8. Importação/Exportação de CSV (regra exclusivamente de frontend)

- **Exportação**: gera um CSV com `;` como separador, colunas conforme `projetoAtivo.colunas`, valores monetários formatados em `pt-BR`/`BRL`, com BOM UTF-8 (`\uFEFF`) para compatibilidade com Excel.
- **Importação**:
  - Detecta automaticamente o separador (`;` ou `,`) olhando a primeira linha do arquivo.
  - Se não houver projeto ativo no momento da importação, **cria automaticamente um novo projeto** cujo nome é derivado do nome do arquivo, e cujo schema de colunas é derivado dos cabeçalhos do CSV (normalizados: minúsculas, sem acento, sem caracteres especiais).
  - Faz correspondência de cada coluna do CSV com uma coluna do projeto **por nome ou por label** (case-insensitive); se não encontrar correspondência, usa a posição (índice) como fallback.
  - **(implícita)** Ignora linhas totalmente vazias (sem nenhum valor não-vazio em nenhuma coluna).
  - **Efeito colateral automático**: se um valor de `categoria` ou `conta` encontrado no CSV não existir ainda no cadastro do projeto, uma nova categoria/conta é **criada automaticamente no banco**, sem confirmação prévia do usuário — apenas um aviso, ao final da importação, informando quantas foram criadas.
  - Cada linha do CSV gera **uma requisição HTTP individual** (`POST /lancamentos`) — não há requisição em lote nem transação atômica; se uma linha falhar (ex.: erro de rede), as linhas anteriores já importadas **permanecem no banco** (sem rollback).

## 9. Regras de Autorização Resumidas (cross-reference para `Authorization.md`)

| Ação | Quem pode |
|---|---|
| Login | Qualquer pessoa com credenciais válidas |
| CRUD de lançamentos/categorias/contas | Qualquer usuário autenticado com `role != 'prestador'` (corrigido em 2026-07-08) |
| CRUD de projetos | Somente admin |
| CRUD de usuários | Somente admin |
| Criar requisição | Qualquer usuário autenticado (para si mesmo) |
| Ver requisições | Admin vê todas; demais veem só as próprias |
| Alterar status de requisição | Somente admin |
| Criar/excluir tarefa | Somente admin |
| Ver/editar tarefa | Admin vê e edita todas; prestador vê e edita (parcialmente) só as suas |

## 10. Regras Ambíguas / Pontos que exigem confirmação de negócio

Estes pontos **não foram assumidos** — estão listados aqui como itens a esclarecer antes de qualquer alteração futura:

1. **Papel `role = 'user'`**: existe na UI de criação de usuário, mas não tem nenhuma regra de autorização própria no backend nem tratamento diferenciado no frontend além de "não é prestador". Não está claro se é um papel intencionalmente reservado para uso futuro (ex.: "financeiro", conforme roadmap) ou um resíduo de uma versão anterior da tela.
2. **Transições de status de requisições e tarefas**: o backend aceita qualquer string de status sem validar uma máquina de estados (ex.: nada impede pular de "Pendente" direto para "Comprado" sem passar por "Aprovado", ou voltar um status já avançado para um anterior). Não está claro se isso é intencional (flexibilidade) ou uma lacuna de validação a ser corrigida.
3. **`POST /tarefas` aceita um `status` customizado no corpo**, diferente de `POST /requisicoes`, que sempre força `'Pendente'` independentemente do que for enviado. Não está claro se essa assimetria é intencional.
4. **Criação automática de categorias/contas durante import de CSV**: não há confirmação explícita do usuário antes de gravar novas categorias/contas no banco — não está claro se esse comportamento "silencioso" é desejado ou se deveria exigir uma etapa de revisão antes de persistir.
