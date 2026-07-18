# Authentication — Expense Management Project

## 1. Mecanismo escolhido: JWT stateless (PyJWT + HS256)

O sistema usa **JSON Web Tokens** assinados com o algoritmo simétrico **HS256**, emitidos pelo próprio backend Flask (não há integração com provedor externo de identidade — sem OAuth2, sem SSO, sem Auth0/Keycloak/Cognito).

**Por que essa escolha faz sentido aqui**: para uma aplicação de uso interno, com um número pequeno e conhecido de usuários (administradores da obra + prestadores de serviço), implementar autenticação própria com JWT é a solução mais simples e direta — evita a complexidade e o custo de integrar um provedor de identidade externo, e o modelo stateless (o servidor não guarda sessão em memória/banco) simplifica a escalabilidade horizontal do backend (qualquer instância do Gunicorn pode validar o token sozinha, sem precisar consultar um armazenamento de sessão compartilhado).

## 2. Fluxo de autenticação

```
1. Cliente envia POST /api/login { username, password }
2. auth_controller.login_usuario():
   a. Busca o usuário por username
   b. Compara a senha informada com o hash armazenado (werkzeug.check_password_hash)
   c. Se válido, monta o payload do JWT:
        { id, username, is_admin, role, empresa_id, exp: now + 24h }
   d. Assina com JWT_SECRET_KEY (HS256) e retorna { token, user }
3. Cliente armazena token e user em sessionStorage (não em cookie, não em localStorage)
4. Toda chamada subsequente inclui header: Authorization: Bearer <token>
5. auth_middleware.token_required (ou admin_required) decodifica e valida o token a cada requisição
```

## 3. Estrutura do token (payload)

```json
{
  "id": 1,
  "username": "admin",
  "is_admin": 1,
  "role": "admin",
  "empresa_id": 1,
  "exp": 1751980800
}
```

**`empresa_id`** foi adicionado na Tarefa 1.1 do roadmap SaaS (multi-tenancy). Hoje ele só identifica a que empresa o usuário pertence — nenhuma rota ainda valida esse campo para restringir acesso a dados de outra empresa (isso é a Tarefa 1.2, ainda não implementada). `admin_required` também passou a popular `g.user` com o payload completo (antes só validava `is_admin` e descartava o payload), para que rotas administrativas consigam ler `g.user['empresa_id']`.

**Motivo de incluir `is_admin` e `role` diretamente no payload do token** (em vez de apenas o `id` e consultar o banco a cada requisição): evita uma query adicional ao banco de dados em toda requisição autenticada só para saber o papel do usuário — o middleware decodifica o JWT (operação criptográfica local, sem I/O) e já tem a informação de autorização disponível. O trade-off dessa decisão é que, se o papel de um usuário for alterado (ex.: promovido a admin, ou rebaixado), **essa mudança só terá efeito no próximo login** — o token antigo, ainda válido por até 24h, continua carregando o papel antigo até expirar. Não há revogação de token nem verificação em tempo real contra o banco a cada requisição.

## 4. Armazenamento do token no cliente

- Guardado em **`sessionStorage`** do navegador (não `localStorage`, não cookie).
- **Motivo provável dessa escolha**: `sessionStorage` é automaticamente limpo ao fechar a aba/janela do navegador, reduzindo a janela de exposição do token comparado a `localStorage` (que persiste indefinidamente até ser limpo manualmente). Isso é uma escolha mais conservadora de segurança do que o padrão mais comum (`localStorage`), mas ainda **não é o ideal do ponto de vista de segurança contra XSS** — ambos (`sessionStorage` e `localStorage`) são acessíveis via JavaScript, então qualquer script malicioso injetado na página (XSS) pode ler o token. A alternativa mais segura (cookie `httpOnly` + `Secure` + `SameSite`) não é usada aqui, provavelmente porque exigiria configurar o backend para setar cookies e lidar com CSRF, adicionando complexidade que o time optou por não introduzir nesta fase.

## 5. Expiração e renovação

- Validade fixa de **24 horas**, definida na emissão (`datetime.utcnow() + timedelta(hours=24)`).
- **Não há refresh token** nem endpoint de renovação — quando o token expira, o middleware retorna `401 { "erro": "Token expirado!" }`, e o frontend trata isso via handler global de `401` (limpa `sessionStorage`, dispara evento `auth-error`, força novo login).
- **Consequência prática**: um usuário que deixa a aba aberta e ativa por mais de 24 horas seguidas precisará fazer login novamente, independente de estar ativamente usando o sistema (o token não é renovado silenciosamente em segundo plano).

## 6. Timeout de inatividade (mecanismo adicional, client-side apenas)

Além da expiração do JWT, o frontend implementa seu próprio controle de inatividade:

```js
const TIMEOUT_MS = 15 * 60 * 1000; // 15 minutos
// reseta o timer a cada mousedown, mousemove, keypress, scroll, touchstart
// ao expirar: chama logout() e exibe alert("Sessão expirada por inatividade...")
```

**Motivo**: um requisito comum em aplicações financeiras/administrativas é encerrar a sessão de um usuário que "esqueceu" a aba aberta, mesmo que o token JWT ainda seja tecnicamente válido por até 24h. Como o JWT é stateless e o backend não tem como "empurrar" um logout para o cliente, essa é uma medida **exclusivamente client-side**: ela desloga a UI (remove token do `sessionStorage`, volta para tela de login), mas **o token em si continua válido no backend** até sua expiração natural — se alguém copiar o valor do token antes do timeout de inatividade disparar (via inspeção do `sessionStorage`, por exemplo), ele continua utilizável diretamente contra a API até as 24h expirarem, independentemente do timeout de UI.

## 7. Hash de senha

- Biblioteca: `werkzeug.security` (`generate_password_hash` / `check_password_hash`), que por padrão do Werkzeug usa **PBKDF2 com SHA-256** e salt aleatório por senha.
- **Motivo**: é a solução de hashing "pronta" já disponível como dependência transitiva do próprio Flask (Werkzeug é a base do Flask), evitando adicionar uma dependência extra (ex.: `bcrypt`, `argon2`) só para esse propósito. É uma escolha adequada e segura (PBKDF2 é um algoritmo de hashing de senha reconhecido), embora `bcrypt`/`argon2` sejam geralmente considerados mais resistentes a ataques de hardware especializado (GPU/ASIC) que o PBKDF2 puro, a depender dos parâmetros de custo usados.

## 8. Pontos sem tratamento (apenas documentados aqui — não corrigidos nesta etapa)

- Não há política de complexidade/tamanho mínimo de senha em nenhuma camada (backend nem frontend).
- Não há *rate limiting* no endpoint `/login` — nenhuma proteção contra tentativas de força bruta (nem por IP, nem por usuário, nem CAPTCHA).
- Não há mecanismo de "esqueci minha senha" / recuperação de conta — a única forma de resetar uma senha é um administrador excluir e recriar o usuário, ou rodar um script manual (`create_admin.py`) diretamente no servidor.
- Não há autenticação multifator (MFA/2FA).
- Não há registro de tentativas de login (bem-sucedidas ou falhas) — nenhum log de auditoria de acesso.
- A variável `JWT_SECRET_KEY`, usada para assinar e validar todos os tokens, está commitada em texto plano no arquivo `back/.env`, versionado no Git (ver `Security.md` para o detalhamento do risco).
