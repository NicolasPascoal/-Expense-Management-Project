# API — Expense Management Project

Todas as rotas estão sob o prefixo `/api` (definido no registro dos blueprints em `app/__init__.py`). Formato de payload/resposta: JSON. Autenticação: header `Authorization: Bearer <jwt>` (exceto `/login`).

Legenda de proteção:
- **Pública**: sem autenticação.
- **`token_required`**: exige JWT válido de qualquer usuário autenticado.
- **`admin_required`**: exige JWT válido **e** `is_admin` truthy no payload do token.
- **Regra adicional**: verificação de negócio feita dentro do controller, além do decorator (ex.: dono do recurso).

---

## 1. Autenticação

### `POST /api/login`
- **Proteção**: Pública.
- **Body**: `{ "username": string, "password": string }`
- **Sucesso (200)**: `{ "token": string, "user": { "id", "username", "is_admin": bool, "role", "empresa_id" } }`
- **Erros**:
  - `400` — username ou password ausentes.
  - `401` — credenciais inválidas.
- **Regra de negócio**: token JWT (HS256) com validade de 24h, payload contém `id`, `username`, `is_admin`, `role`, `empresa_id`, `exp`. `empresa_id` foi adicionado na Tarefa 1.1 (roadmap SaaS) — ainda não é usado para filtrar nenhuma leitura (isso é a Tarefa 1.2).

---

## 2. Lançamentos (`lancamentos_v2`)

### `GET /api/lancamentos`
- **Proteção**: `token_required` + `non_prestador_required` (corrigido em 2026-07-08).
- **Query params**: `projeto_id` (opcional — se ausente, retorna lançamentos de **todos** os projetos).
- **Resposta (200)**: array de objetos com os campos dinâmicos do projeto "achatados" no nível raiz (ex.: `{id, projeto_id, data, categoria, valor, ...}`).
- **Observação de autorização**: `role='prestador'` recebe `403`. Ainda não há checagem de propriedade de projeto — qualquer usuário não-prestador pode listar lançamentos de qualquer projeto (depende de multi-tenancy, Épico 1).

### `GET /api/lancamentos/:id`
- **Proteção**: `token_required` + `non_prestador_required` (corrigido em 2026-07-08).
- **Resposta**: `200` com o objeto, ou `404 { "erro": "Não encontrado" }`.

### `POST /api/lancamentos`
- **Proteção**: `token_required` + `non_prestador_required` (corrigido em 2026-07-08).
- **Body**: `{ "projeto_id": int, ...campos dinâmicos... }`
- **Erros**: `400` se `projeto_id` ausente.
- **Regra**: o `projeto_id` é retirado do payload antes de serializar o restante como JSON em `dados`.

### `PUT /api/lancamentos/:id`
- **Proteção**: `token_required` + `non_prestador_required` (corrigido em 2026-07-08).
- **Body**: campos a atualizar (o `id` e `projeto_id` do corpo são descartados; o `projeto_id` original do banco não é alterado por este endpoint).
- **Resposta**: `200` com objeto atualizado, ou `404` se o id não existir (checagem indireta: `atualizar_lancamento` sempre executa o `UPDATE` e depois busca por id — se o id não existir, o `UPDATE` não afeta linhas e a busca subsequente retorna `None`, gerando 404).

### `DELETE /api/lancamentos/:id`
- **Proteção**: `token_required` + `non_prestador_required` (corrigido em 2026-07-08).
- **Resposta**: `200 { "mensagem": "Removido" }` ou `404 { "erro": "Não encontrado" }`.
- **Observação de autorização**: `role='prestador'` recebe `403`. Qualquer usuário não-prestador ainda pode excluir lançamentos de qualquer projeto (sem checagem de propriedade).

---

## 3. Projetos

### `GET /api/projetos`
- **Proteção**: `token_required`.
- **Resposta**: array de `{id, nome, colunas: [...]}` — `colunas` é desserializado de JSON para array de objetos antes de responder.
- **Atenção**: `SELECT * FROM projetos` sem filtro — retorna projetos de **todas** as empresas, mesmo já existindo `empresa_id` na tabela. Isolamento por tenant é a Tarefa 1.2, ainda não implementada.

### `POST /api/projetos`
- **Proteção**: `admin_required`.
- **Body**: `{ "nome": string, "colunas": array (opcional) }`.
- **Regra de negócio**: `empresa_id` gravado é o da empresa do admin autenticado (`g.user['empresa_id']`), não vem do body (Tarefa 1.1, roadmap SaaS).
- **Erros**: `400` se `nome` ausente.

### `PUT /api/projetos/:id`
- **Proteção**: `admin_required`.
- **Body**: `{ "nome"?: string, "colunas"?: array }` — atualiza somente os campos fornecidos (nome, colunas, ou ambos).
- **Observação**: se nem `nome` nem `colunas` forem enviados, a rota responde `200 { "mensagem": "Projeto atualizado" }` mesmo sem executar nenhum `UPDATE` (nenhum dos três ramos `if/elif` é satisfeito) — resposta enganosa (diz que atualizou, mas não fez nada).

### `DELETE /api/projetos/:id`
- **Proteção**: `admin_required`.
- **Efeito colateral**: por `ON DELETE CASCADE`, remove também todos os `lancamentos_v2`, `categorias` e `contas` associados a este projeto.
- **Resposta**: sempre `200 { "mensagem": "Projeto removido" }`, mesmo que o `id` não exista (não há checagem de `rowcount`).

---

## 4. Serviços (Categorias e Contas)

### `GET /api/categorias`
- **Proteção**: `token_required` + `non_prestador_required` (corrigido em 2026-07-08).
- **Query params**: `projeto_id` (opcional).
- **Resposta**: array ordenado por `nome ASC`.

### `POST /api/categorias`
- **Proteção**: `token_required` + `non_prestador_required` (não exige admin — apenas não-`prestador`).
- **Body**: `{ "nome": string, "projeto_id": int }`.
- **Erros**: `400` se `nome` ou `projeto_id` ausentes, ou se o `INSERT` falhar (ex.: `projeto_id` inexistente, retornado como `{"erro": str(exception)}`).

### `DELETE /api/categorias/:id`
- **Proteção**: `token_required` + `non_prestador_required` (corrigido em 2026-07-08).
- **Resposta**: `200` ou `404`.
- **Observação**: excluir uma categoria não impede nem avisa se existem lançamentos referenciando essa categoria pelo nome dentro do JSON `dados` — não há FK entre o valor textual `categoria` de um lançamento e a tabela `categorias` (são desacoplados; a tabela `categorias` serve apenas para popular as opções do formulário).

### `GET /api/contas`, `POST /api/contas`, `DELETE /api/contas/:id`
- **Proteção**: `token_required` + `non_prestador_required` (corrigido em 2026-07-08).
- Mesmo padrão e mesmas observações de `categorias`, aplicado a contas pagadoras.

---

## 5. Usuários (Admin)

### `GET /api/usuarios`
- **Proteção**: `admin_required`.
- **Resposta**: array de `{id, username, is_admin, role}` — **sem** o hash de senha (a query seleciona colunas explicitamente, não usa `SELECT *`).

### `POST /api/usuarios`
- **Proteção**: `admin_required`.
- **Body**: `{ "username", "password", "is_admin"?: bool, "role"?: string }` — se `role` não for enviado, é derivado de `is_admin` (`'admin'` ou `'prestador'`).
- **Sucesso (201)**: `{ "id", "username", "is_admin": bool, "role", "empresa_id" }` — `empresa_id` gravado é o da empresa do admin autenticado (`g.user['empresa_id']`), não vem do body (Tarefa 1.1, roadmap SaaS).
- **Erros**: `400` se `username`/`password` ausentes, ou se `username` já existir (violação de `UNIQUE` — ainda global, não composto por empresa; capturada como exceção genérica).

### `DELETE /api/usuarios/:id`
- **Proteção**: `admin_required`.
- **Regra**: bloqueia exclusão se `id == 1` (retorna `400`), independentemente de quem está fazendo a chamada.
- **Efeito colateral em cascata**: por `ON DELETE CASCADE`, remove também `tarefas` (onde era `prestador_id`) e `requisicoes_materiais` (onde era `usuario_id`) desse usuário — ou seja, excluir um usuário apaga o histórico de tarefas e requisições dele, sem soft-delete.

---

## 6. Requisições de Material

### `GET /api/requisicoes`
- **Proteção**: `token_required`.
- **Regra**: se `is_admin`, retorna todas (com `JOIN` trazendo `username` do solicitante); caso contrário, retorna apenas as do próprio `usuario_id` do token.

### `POST /api/requisicoes`
- **Proteção**: `token_required`.
- **Body**: `{ "nome", "funcao", "material" }` — `usuario_id` é preenchido automaticamente a partir do token (`g.user['id']`), não do body.
- **Erros**: `400` se algum dos três campos obrigatórios faltar.
- **Resposta (201)**: `{ "id", "status": "Pendente" }`.

### `PUT /api/requisicoes/:id/status`
- **Proteção**: `admin_required`.
- **Body**: `{ "status": string }` — qualquer string é aceita, sem validação de enum (`Pendente`/`Aprovado`/`Recusado`/`Comprado` são valores esperados pela UI, mas não impostos pelo backend).
- **Observação**: não gera lançamento financeiro automaticamente ao aprovar — comportamento listado como pendência futura em `freatures.txt` ("ao aprovar → opção de gerar lançamento financeiro automático").
- **Observação de bug potencial**: a rota não retorna `404` se o `id` não existir — o `UPDATE` simplesmente não afeta linhas, e a resposta ainda é `200 { "mensagem": "Status atualizado" }`.

---

## 7. Tarefas

### `GET /api/tarefas`
- **Proteção**: `token_required`.
- **Regra**: se `is_admin`, retorna todas as tarefas com `username` do prestador via `LEFT JOIN`; caso contrário, retorna apenas as tarefas do próprio `prestador_id`.

### `POST /api/tarefas`
- **Proteção**: `token_required` + checagem manual de `is_admin` **dentro da própria rota** (não usa o decorator `admin_required` — usa `token_required` e depois um `if not is_admin: return 403` manual).
- **Body**: `{ "titulo", "descricao"?, "prestador_id", "status"?, "observacoes"? }`.
- **Erros**: `403` se não-admin; `400` se `titulo`/`prestador_id` ausentes; `500` em caso de erro de banco (ex.: `prestador_id` inexistente).

### `PUT /api/tarefas/:id`
- **Proteção**: `token_required` (autorização fina feita no controller).
- **Regra de autorização por dono**:
  - Se `is_admin`: pode alterar `titulo`, `descricao`, `prestador_id`, `status`, `observacoes` (apenas os campos enviados).
  - Se não-admin: só pode alterar `status` e `observacoes`, **e somente se `prestador_id` da tarefa for igual ao `id` do usuário do token** — caso contrário, `403 { "erro": "Acesso negado" }`.
- **Erros**: `404` se a tarefa não existir; `500` em erro de banco.

### `DELETE /api/tarefas/:id`
- **Proteção**: `token_required` + checagem manual de `is_admin` no controller (`deletar_tarefa`).
- **Erros**: `403` se não-admin; `404` se a tarefa não existir.

---

## 8. Padrões observados no design da API

1. **Nem todo endpoint retorna `404` de forma consistente quando o recurso não existe** — `PUT /projetos/:id`, `DELETE /projetos/:id` e `PUT /requisicoes/:id/status` sempre retornam `200`, mesmo que o `id` não exista, porque não checam `cursor.rowcount` após o `UPDATE`/`DELETE`. Já `lancamentos`, `usuarios` e `tarefas` fazem essa checagem corretamente.
2. **Mensagens de erro em português, chave `"erro"`** — convenção informal usada em toda a API (não há um envelope de erro padronizado documentado, ex.: sem campo `code` ou `type`, apenas uma string livre).
3. **Sem versionamento de API** (não há `/api/v1`, `/api/v2` — apesar de existir "v2" no nome interno da tabela `lancamentos_v2`, isso não se reflete na URL pública, que continua sendo apenas `/api/lancamentos`).
4. **Sem paginação em nenhum endpoint de listagem** — `GET /lancamentos`, `GET /categorias`, `GET /contas`, `GET /usuarios`, `GET /requisicoes`, `GET /tarefas` sempre retornam o conjunto completo (ver `Performance.md`).
5. **Sem documentação OpenAPI/Swagger** — não há especificação formal da API neste repositório; este documento é a primeira descrição completa dos contratos de request/response.
