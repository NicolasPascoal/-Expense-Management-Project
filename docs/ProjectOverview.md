# Project Overview — Expense Management Project

## 1. O que é o sistema

O **Expense Management Project** é uma aplicação web para **gestão financeira de obras de construção civil**. Ele permite que uma empresa (ou grupo de sócios/familiares que financiam uma obra) controle:

- **Lançamentos financeiros** (despesas): o que foi comprado, quando, de quem, por qual forma de pagamento e com qual conta pagadora.
- **Múltiplos projetos/obras** simultaneamente, cada um com seu próprio conjunto de categorias, contas e — de forma notável — seu próprio **schema de campos** (ver `Entities.md`, seção "Colunas Dinâmicas").
- **Requisições de material** feitas por prestadores de serviço em campo (pedreiros, etc.), com fluxo de aprovação por um administrador.
- **Tarefas** atribuídas a prestadores, com acompanhamento de status.
- **Controle de acesso** com dois papéis efetivamente implementados: administrador (`is_admin=1`) e prestador (`role='prestador'`).

O nome do projeto seed padrão (`Obra Itanhaém`) e os nomes de contas seed (`FF Alves Construtora`, `Victor Praça Pascoal`, `Vanderlei Almeida Simões`, `SPE Luiz Pascoal`) indicam fortemente que este é um sistema **construído para um caso de uso real e específico** (uma obra/empreendimento familiar/societário), não um produto genérico de mercado desde a concepção — embora a arquitetura de "projeto com colunas dinâmicas" já demonstre uma tentativa de generalização para múltiplas obras.

## 2. Motivação de negócio (inferida do código e do roadmap)

O arquivo `front/freatures.txt`, presente no repositório, funciona como um roadmap informal escrito pelo próprio mantenedor. Ele revela a intenção declarada de evolução do produto:

- Introduzir um sistema de **permissões mais granular** (admin, gestor de obra, financeiro, pedreiro) — hoje só existem `admin` e `prestador` de fato implementados.
- Criar um **fluxo próprio para "pedreiro"**: pedidos de material com foto, aprovação/recusa, geração automática de lançamento financeiro ao aprovar — hoje o módulo de requisições existe, mas **sem geração automática de lançamento** e **sem upload de foto**.
- Migrar definitivamente para PostgreSQL com **JSONB**, ORM (SQLAlchemy) e migrations (Alembic) — a migração para Postgres **já foi feita**, mas ainda usando `TEXT` no lugar de `JSONB`, sem ORM e sem ferramenta de migrations (ver `Database.md` e `TechDebt.md`).
- Evoluir o módulo financeiro: fluxo de caixa, orçado vs. realizado, parcelamento, anexos de recibo, auditoria de edição — **nenhum desses itens está implementado** no estado atual do código.
- Reforçar segurança: controle de acesso por obra, permissões por ação, log de auditoria completo — **nenhum desses itens está implementado**.

Esse documento (`freatures.txt`) é importante porque estabelece que boas partes das lacunas encontradas nesta documentação **já são conhecidas pelo autor como trabalho futuro**, e não "descobertas" desta análise. Isso deve ser levado em conta ao priorizar qualquer evolução.

## 3. Personas / Papéis de usuário

| Papel | Como é identificado no sistema | O que pode fazer (conforme UI) |
|---|---|---|
| **Administrador** | `is_admin = 1` (e `role = 'admin'`) | Acesso total: todas as abas, CRUD de projetos, categorias, contas, lançamentos, usuários, tarefas (criar/editar/excluir) e aprovação de requisições. |
| **Prestador** | `role = 'prestador'`, `is_admin = 0` | Acesso restrito a duas abas: **Tarefas** (ver e atualizar apenas as suas, status/observações) e **Materiais/Requisições** (criar pedido, ver apenas os seus próprios). |
| **"user" (não tratado)** | `role = 'user'` — possível de ser criado pela tela de Admin, mas sem tratamento explícito em nenhuma rota do backend nem no front | Efetivamente se comporta como "não-prestador" na maioria das checagens de UI (`role !== 'prestador'`), ou seja, hoje herda acidentalmente o comportamento de um usuário comum/administrativo sem ser admin. Ver `Authorization.md` para detalhamento do risco. |

## 4. Módulos funcionais (visão de produto)

1. **Login / Sessão** — autenticação via usuário/senha, sessão de 24h (JWT) com logout automático por inatividade de 15 minutos no front.
2. **Dashboard** — visão consolidada de totais por categoria e por conta, calculada no frontend a partir de todos os lançamentos do projeto ativo.
3. **Lançamentos** — CRUD de despesas do projeto ativo, com filtros (categoria, conta, forma de pagamento, busca textual) e exportação/importação via CSV.
4. **Materiais (Requisições)** — prestadores pedem material; administradores aprovam/alteram status.
5. **Tarefas** — administradores atribuem tarefas a prestadores; prestadores atualizam status/observações das suas.
6. **Por Conta / Serviços** — telas de gestão de "contas pagadoras" e "categorias" por projeto.
7. **Admin** — gestão de usuários (criar, listar, remover acesso).
8. **Seletor de Projeto** — troca entre obras/projetos cadastrados; cada projeto tem seu próprio schema de colunas, categorias e contas.

## 5. Stack tecnológica (resumo)

| Camada | Tecnologia | Ver detalhes em |
|---|---|---|
| Backend | Python 3.11, Flask 3, psycopg2, PyJWT, Werkzeug | `Architecture.md`, `Dependencies.md` |
| Banco de dados | PostgreSQL 15 (Docker) | `Database.md` |
| Frontend | React 19, Vite, Recharts, lucide-react | `Architecture.md`, `Dependencies.md` |
| Servidor de produção | Gunicorn (Linux/Docker) ou Waitress (Windows) | `DevelopmentFlow.md` |
| Proxy/estático | Nginx (frontend containerizado) | `Architecture.md` |
| Orquestração | Docker Compose (3 serviços) | `DevelopmentFlow.md` |

## 6. Estado geral do projeto (nesta análise)

- Aplicação **funcional e em uso** (evidenciado pelos dados seed reais e nomenclatura específica de obra/contas).
- Arquitetura simples, de 2 camadas no backend, sem testes automatizados.
- Migração de SQLite para Postgres **em transição**, ainda carregando uma camada de compatibilidade (ver `Database.md`).
- Roadmap de produto e de infraestrutura já mapeado pelo próprio autor, mas ainda não executado em boa parte.
- Existem problemas de segurança relevantes (segredos versionados em Git, autorização incompleta) documentados em `Security.md` e `Authorization.md` — **apenas documentados nesta etapa, sem correção**, conforme solicitado.

## 7. Como este conjunto de documentos está organizado

| Documento | Foco |
|---|---|
| `ProjectOverview.md` | Este documento — visão de produto e negócio |
| `Architecture.md` | Padrões arquiteturais, camadas, decisões e motivos |
| `FolderStructure.md` | Estrutura de diretórios e propósito de cada parte |
| `Database.md` | Motor de banco, estratégia de conexão, criação de schema, seeds, scripts de migração |
| `Entities.md` | Modelo de dados, tabelas, relacionamentos, ERD |
| `API.md` | Inventário completo de endpoints REST |
| `BusinessRules.md` | Regras de negócio por módulo |
| `Authentication.md` | Mecanismo de login, JWT, sessão |
| `Authorization.md` | RBAC, decorators, regras de acesso por dono de recurso |
| `Features.md` | Inventário de features implementadas vs. roadmap |
| `Dependencies.md` | Dependências de backend e frontend, e motivo de cada uma |
| `Security.md` | Riscos de segurança identificados |
| `Performance.md` | Gargalos de performance e escalabilidade |
| `TechDebt.md` | Dívida técnica identificada |
| `DevelopmentFlow.md` | Como rodar o projeto localmente e em produção |
