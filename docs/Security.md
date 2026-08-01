# Security — Expense Management Project

> Este documento apenas **relata** os achados de segurança identificados na análise do código. Nenhuma correção foi aplicada nesta etapa, conforme solicitado.

## 1. Classificação por severidade

### 🔴 Crítico

#### 1.1 Segredos reais commitados no controle de versão — ✅ segredos rotacionados em 2026-07-30
O arquivo `back/.env` estava rastreado pelo Git (confirmado via `git ls-files`), apesar de existir um `.gitignore` que lista `.env` como arquivo a ignorar. O conteúdo desse arquivo inclui:
- A senha real do usuário do PostgreSQL (`PGPASSWORD`).
- A chave real usada para assinar todos os tokens JWT (`JWT_SECRET_KEY`).

Além disso, `docker-compose.yml` também tinha esses dois valores reais hardcoded como *fallback* (`PGPASSWORD:-K33ps@f&` e `JWT_SECRET_KEY:-chave_super_secreta_padrao`) — um segundo ponto de vazamento independente do `.env`.

**Por que isso é crítico**: qualquer pessoa com acesso ao histórico do repositório (se o repositório for ou já tiver sido público, ou se algum colaborador tiver clonado antes de uma eventual limpeza) tem acesso à chave que assina os tokens de autenticação — o que permite **forjar um token JWT válido como administrador**, sem precisar de nenhuma senha, e ter acesso total à aplicação. Também tem acesso à senha do banco, permitindo conexão direta caso a porta do Postgres esteja acessível.

**Detalhe técnico relevante**: como o `.gitignore` já listava `.env` corretamente, o arquivo provavelmente foi adicionado ao Git **antes** da entrada correspondente ser incluída no `.gitignore`, ou foi adicionado forçadamente (`git add -f`) em algum momento. De qualquer forma, apagar o arquivo do commit mais recente não é suficiente — o segredo permanece acessível no histórico de commits até que este seja reescrito.

**Mitigação aplicada em 2026-07-08** (ver `STATUS.md`, Tarefa 2.1): `back/.env`/`front/.env` foram removidos do rastreamento (`git rm --cached`, arquivos preservados localmente) e os fallbacks hardcoded do `docker-compose.yml` foram substituídos por `${VAR:?erro}` (falha explícita se não configurado via `.env`).

**Rotação aplicada em 2026-07-30**: `JWT_SECRET_KEY` e a senha do usuário `postgres` foram trocados por novos valores gerados aleatoriamente (`ALTER ROLE` no Postgres local + atualização de `back/.env`). Não havia produção rodando no momento, então não houve impacto em usuários ativos. Os valores antigos, mesmo continuando visíveis no histórico do Git, **não são mais válidos** — não assinam tokens aceitos pela aplicação nem autenticam no banco. Decisão ainda em aberto, mas não mais urgente: reescrever ou não o histórico do Git para remover os valores antigos por completo (limpeza, não correção de vulnerabilidade ativa).

#### 1.2 Credenciais de administrador hardcoded em script versionado — ✅ corrigido em 2026-07-08
`back/create_admin.py` continha, em texto plano no código-fonte, um usuário/senha fixos (`nicolas`/`nicolas12`). Qualquer pessoa que lesse o repositório tinha conhecimento de um login administrativo válido, caso o script já tivesse sido executado contra o banco de produção.

**Correção aplicada**: o script agora lê `ADMIN_USERNAME`/`ADMIN_PASSWORD` de variável de ambiente e falha com mensagem clara se ausentes, em vez de usar valores fixos. **Se o script `nicolas`/`nicolas12` já foi executado contra o banco de produção em algum momento**, esse usuário existe hoje com essa senha — precisa ser tratado como o item 1.1 (senha trocada ou usuário removido), independentemente da correção no código-fonte.

#### 1.3 Senha de administrador seed previsível
`app/database/modelUsuarios.py` cria automaticamente, na primeira inicialização de um banco vazio, um usuário `admin` com senha `admin` (hash aplicado, mas a senha original é trivial). Se uma nova instância do sistema for provisionada e essa senha não for trocada imediatamente, existe uma conta administrativa com credencial obviamente adivinhável.

**Risco aceito conscientemente na stack de dev/staging (Umbrel/Portainer, `docker-compose.dev.yml`, 2026-07-30)**: mantido `admin`/`admin` de propósito — ambiente só acessível via VPN, uso restrito a duas pessoas conhecidas (usuário e familiar), sem dados reais de produção. Não há endpoint de troca de senha pela própria UI hoje (`usuarios_routes.py` só tem GET/POST/DELETE); a única forma de trocar é rodando `create_admin.py` no console do container. **Revisitar antes de**: expor esse ambiente fora da VPN, colocar dados reais nele, ou promovê-lo a produção de fato.

### 🟠 Alto

#### 2.1 Autorização incompleta em módulos financeiros — ⚠️ mitigação parcial em 2026-07-08
Como detalhado em `Authorization.md`, os endpoints de lançamentos, categorias e contas (`/api/lancamentos*`, `/api/categorias*`, `/api/contas*`) exigiam apenas um JWT válido (`@token_required`), sem checagem de `role` ou de propriedade do projeto. Qualquer usuário autenticado — inclusive um com `role='prestador'`, cuja UI é deliberadamente restrita — podia, via chamada direta à API (fora da interface web), ler, criar, editar e excluir lançamentos financeiros de **qualquer** projeto cadastrado no sistema.

**Mitigação aplicada em 2026-07-08**: novo decorator `non_prestador_required` (`app/utils/auth_middleware.py`) aplicado a todas as rotas de lançamentos/categorias/contas — `role='prestador'` agora recebe `403` em leitura e escrita nesses três módulos. **O que continua em aberto**: (a) não há checagem de propriedade de projeto — um admin (ou o papel ambíguo `role='user'`, ver `Authorization.md` e `BusinessRules.md`) ainda pode ler/escrever dados de qualquer projeto, já que multi-tenancy (Épico 1) ainda não existe; (b) essa é uma correção pontual do gap conhecido, não a Tarefa 1.3 completa do roadmap, que prevê autorização considerando tenant.

#### 2.2 Vazamento de detalhes internos em mensagens de erro — ✅ corrigido em 2026-07-30
Vários controllers capturavam exceções genéricas e devolviam a mensagem crua ao cliente:
```python
except Exception as e:
    return {"erro": str(e)}
```
Isso podia expor detalhes internos do banco de dados (nomes de tabelas/colunas, mensagens de erro do driver `psycopg2`, stack traces parciais) diretamente na resposta HTTP, informação que normalmente deveria ficar restrita a logs internos, não à resposta pública da API.

**Correção aplicada** (Tarefa 2.3, `STATUS.md`): os 5 pontos que faziam esse `except Exception as e: return {"erro": str(e)}` foram removidos. Um handler global (`@app.errorhandler(Exception)` em `app/__init__.py`) agora captura qualquer exceção não tratada, loga o stack trace completo internamente (com `request_id`/`empresa_id`/`usuario_id`) e devolve só `{"erro": "Erro interno do servidor", "request_id": ...}` ao cliente. O único caso que continua com tratamento específico é `username` duplicado em `criar_usuario` (`psycopg2.errors.UniqueViolation`), que retorna `400` com mensagem limpa por ser erro de validação esperado, não falha interna.

#### 2.3 Log de query com dados sensíveis potencialmente expostos
`app/database/db.py`, dentro de `PostgreSQLCursorWrapper.execute()`, faz:
```python
except Exception as e:
    print(f"\n[QUERY FAILED] {sql_pg} | Params: {params} | Error: {e}")
    raise e
```
Esse `print` vai para a saída padrão (stdout) do processo — em um ambiente de produção com Docker, isso normalmente é coletado pelo sistema de logs do container/orquestrador. Se algum parâmetro de uma query que falhar contiver dados sensíveis (ex.: uma senha em texto plano sendo inserida, antes do hash, em algum fluxo futuro; ou dados pessoais em campos de texto livre), esses valores ficam registrados em log de forma não controlada.

### 🟡 Médio

#### 3.1 CORS aberto por padrão na ausência de configuração
`app/__init__.py`:
```python
allowed_origins = os.getenv("CORS_ALLOWED_ORIGINS", "*")
if allowed_origins != "*":
    CORS(app, origins=origins_list)
else:
    CORS(app)  # sem restrição de origem
```
Se a variável `CORS_ALLOWED_ORIGINS` não for definida no ambiente, a API aceita requisições de **qualquer origem**. No `.env` real do projeto essa variável está corretamente configurada (`http://localhost:5173,http://localhost:3000`), mas o comportamento padrão do código, para quem clonar o projeto sem configurar isso, é permissivo.

#### 3.2 Ausência de rate limiting no endpoint de login — ✅ corrigido em 2026-07-30
`POST /api/login` não tinha nenhuma proteção contra tentativas repetidas (nem por IP, nem por conta, nem CAPTCHA, nem atraso progressivo) — um ataque de força bruta de senha contra uma conta específica não encontraria nenhuma barreira automática no nível da aplicação.

**Correção aplicada**: Flask-Limiter (`back/app/extensions.py`) limita `/api/login` por IP (10/min) e por conta (5/min; 20/hora), verificado manualmente com scripts de tentativas repetidas (`STATUS.md`, Tarefa 2.2). Storage em memória — adequado para o único processo backend atual; precisa de um backend compartilhado (Redis) se o app rodar em múltiplas instâncias no futuro.

#### 3.3 `except:` genérico mascarando erros de programação
Em `utils/auth_middleware.py`, o decorator `admin_required` usa um bloco `except:` sem tipo especificado, que responde sempre "Token inválido!" mesmo quando o erro real é um bug de programação não relacionado à validação do token — isso dificulta o diagnóstico de problemas reais e pode ocultar comportamentos inesperados do sistema em produção.

#### 3.4 Sem HTTPS/TLS configurado no proxy do frontend
`front/nginx.conf` expõe a aplicação apenas na porta 80 (HTTP puro), sem qualquer configuração de TLS/HTTPS, HSTS, ou redirecionamento de HTTP para HTTPS. Presume-se que, se isso é servido publicamente, exista um proxy/balanceador externo (não presente neste repositório) fazendo a terminação TLS — mas isso não está documentado em lugar nenhum do projeto.

#### 3.5 Sem expiração/revogação de token além do tempo fixo
Como não há uma lista de tokens revogados (blacklist) nem verificação em tempo real contra o banco a cada requisição, um token roubado (por exemplo, via XSS, dado que fica em `sessionStorage` acessível a JavaScript) continua **totalmente válido** por até 24 horas, mesmo que o usuário faça logout manual na interface (o logout apenas limpa o armazenamento local do navegador — não invalida o token no lado do servidor).

#### 3.6 Cadastro público sem verificação de e-mail nem captcha — risco aceito conscientemente em 2026-08-01
`POST /api/signup` (Tarefa 5.1, `STATUS.md`) é uma rota pública, sem autenticação, que cria empresa + usuário admin + projeto ativados na hora. Só tem rate limiting (5/hora por IP, reaproveitado da Tarefa 2.2) como barreira contra abuso — sem verificação de e-mail nem captcha.

**Por que foi aceito**: verificação de e-mail depende de ADR-003 (provedor de e-mail transacional, pendente — ver `docs/Decisions.md`), decisão de fornecedor do usuário. Captcha também depende de fornecedor externo (reCAPTCHA/hCaptcha/Turnstile), não escolhido. Hoje o app não está exposto publicamente (roda local ou na VPN do Umbrel — ver `docs/Decisions.md`/memória de infra), então o risco prático de abuso automatizado é baixo.

**Revisitar antes de**: apontar um domínio público pra esse backend, ou se aparecer abuso real de cadastro (contas em massa). Nesse momento, considerar uma trava temporária (código de convite) até a ADR-003 e a escolha de captcha serem resolvidas.

## 2. Riscos relacionados a dados sensíveis de negócio

- Dados financeiros reais (valores, fornecedores, contas pagadoras com nomes de pessoas físicas reais) estão presentes nos seeds e no dataset `front/src/data/data.json` — qualquer pessoa com acesso ao repositório tem acesso a esse histórico financeiro caso o repositório contenha commits desses arquivos com dados reais (o `data.json` observado tem ~60KB de dados, indicando um volume real de lançamentos históricos).
- Requisições de material e tarefas armazenam nomes reais de prestadores de serviço — não há política de retenção/anonimização de dados de ex-colaboradores.

## 3. Itens que a própria equipe já identificou como pendência de segurança (roadmap)

O arquivo `front/freatures.txt` já lista, na seção "segurança", os seguintes itens como trabalho futuro conhecido:
- Controle de acesso por obra.
- Permissões por ação (não só por tipo de usuário).
- Log de ações (auditoria completa).

Isso indica que a lacuna de autorização granular (seção 2.1 deste documento) já é percebida pelo autor como uma limitação a ser endereçada, não uma descoberta nova — mas os itens de **segredos commitados no Git** (seção 1.1 e 1.2) não constam nesse roadmap e parecem não ter sido percebidos como um risco ativo até esta análise.

## 4. Escopo desta análise

Esta análise de segurança foi feita por **leitura estática do código-fonte** disponível no repositório. Não foi realizado (nem estava no escopo desta etapa):
- Pentest ou varredura de vulnerabilidades ativa contra uma instância em execução.
- Análise de configuração do ambiente de produção real (servidor, firewall, exposição de portas, backups) além do que está descrito em `docker-compose.yml`.
- Verificação se os segredos encontrados no Git ainda são os mesmos em uso em produção hoje (ponto já levantado como pergunta em aberto na análise inicial deste projeto).
