# Performance — Expense Management Project

> Documento de observação apenas — nenhuma otimização foi aplicada nesta etapa.

## 1. Ausência de paginação nas listagens

Nenhum endpoint `GET` de listagem (`/lancamentos`, `/categorias`, `/contas`, `/usuarios`, `/requisicoes`, `/tarefas`) implementa paginação, `limit`/`offset`, ou cursores. Toda listagem retorna o **conjunto completo** de registros da tabela (ou do projeto filtrado, no caso de lançamentos).

**Impacto esperado**: para o volume atual de dados (uma obra residencial/comercial de porte médio, algumas centenas a poucos milhares de lançamentos), isso não é um problema perceptível. Se o número de projetos ou o volume histórico de lançamentos por projeto crescer significativamente (múltiplos anos de obra, múltiplas obras simultâneas), o tempo de resposta do endpoint e o payload JSON trafegado crescem linearmente sem limite, e o processamento client-side (ver seção 2) se torna o gargalo dominante.

## 2. Agregações calculadas inteiramente no frontend

Devido ao modelo de dados EAV (`lancamentos_v2.dados` como JSON em `TEXT`, sem `JSONB`/índices — ver `Database.md`), não é possível fazer `SUM`/`GROUP BY` diretamente no SQL sobre os campos dinâmicos. Como consequência, `useExpenses.js` faz toda a agregação **depois** de trazer todos os registros para o navegador:

```js
const porCategoria = useMemo(() => {
  const m = {};
  dados.forEach(d => { ... m[cat] = (m[cat]||0) + parseVal(d.valor); });
  return Object.entries(m).sort((a,b)=>b[1]-a[1]);
}, [dados]);
```

Isso acontece para: total geral, total por categoria, total por conta, e filtro de busca textual (`Object.values(d).some(...)` — itera **todos os campos de todos os registros** a cada tecla digitada na busca, sem debounce).

**Impacto esperado**: aceitável para centenas de registros; torna-se perceptivelmente lento (bloqueio da thread principal do navegador, já que `Array.forEach`/`Object.values` são síncronos) na casa de muitos milhares de registros, especialmente em dispositivos móveis mais fracos (a UI é usada, presumivelmente, também em campo por prestadores/gestores de obra via celular).

## 3. Re-fetch completo em vez de atualização incremental

Sempre que uma mutação ocorre (criar/editar/excluir categoria, conta, requisição, tarefa), o padrão do código é chamar novamente a função `fetch*` correspondente, que busca **toda a coleção de novo**, em vez de atualizar apenas o item afetado no estado local:

```js
const addCategoria = async (nome) => {
  await api.createCategoria(nome, projetoAtivo.id);
  fetchServicos(); // refaz GET /categorias E GET /contas inteiros
};
```

(Uma exceção notável é o CRUD de **lançamentos**, que atualiza o array local diretamente via `setDados` após criar/editar, sem re-fetch completo.)

**Impacto esperado**: número de requisições HTTP maior que o estritamente necessário, e reprocessamento de dados que não mudaram — impacto pequeno no volume atual de categorias/contas/tarefas (dezenas de itens), mas é um padrão que se repetiria em qualquer novo módulo construído seguindo o mesmo estilo.

## 4. Importação de CSV: uma requisição HTTP por linha, sequencial

```js
for (let i = 1; i < parsedRows.length; i++) {
  ...
  await api.createLancamento({ ...payload, projeto_id: targetProjeto.id });
}
```

Cada linha do arquivo CSV gera uma chamada `POST /lancamentos` individual, **aguardada sequencialmente** (não em paralelo, não em lote/batch).

**Impacto esperado**: para um arquivo de importação com centenas ou milhares de linhas, o tempo total de importação escala linearmente com o número de linhas × latência de rede por requisição — uma importação de, por exemplo, 2.000 linhas a ~50-100ms por requisição levaria de 1,5 a 3+ minutos, com a aba do navegador ocupada processando o `FileReader` e aguardando cada resposta. Não há indicador de progresso incremental durante a importação (apenas um `alert()` final com a contagem).

## 5. Pool de conexões e concorrência no backend

- `SimpleConnectionPool(1, 20)` por processo Gunicorn; com `-w 4` (4 workers), o teto teórico é 80 conexões simultâneas ao Postgres.
- Cada chamada a uma função de controller abre e fecha (devolve ao pool) uma conexão — não há uma conexão única compartilhada durante todo o ciclo de vida de uma requisição HTTP que faça múltiplas operações de banco; se um endpoint fizesse duas chamadas de acesso a dados internamente, cada uma pegaria (e devolveria) uma conexão do pool separadamente, em vez de reusar a mesma conexão para as duas operações dentro da mesma transação lógica.

**Impacto esperado**: para o volume de usuários simultâneos esperado (equipe pequena de obra), 80 conexões é uma margem confortável. Não há indícios, no código analisado, de uma situação real de esgotamento do pool — mas o padrão de "uma conexão por chamada de função" ao invés de "uma conexão por requisição HTTP" é uma fonte de overhead desnecessário que se agravaria em cenários de maior concorrência.

## 6. Sem cache HTTP nem cache de aplicação

- Nenhuma resposta da API define headers de cache (`Cache-Control`, `ETag`).
- Não há cache de aplicação (Redis, memcached) nem cache em memória do processo Flask para nenhuma consulta (ex.: lista de categorias/contas, que muda com pouca frequência, é buscada do banco em toda troca de projeto ativo).
- No frontend, não há biblioteca de data-fetching com cache (React Query/SWR) — toda navegação que dispara um `useEffect` de fetch refaz a chamada de rede, mesmo que os dados não tenham mudado desde a última busca.

**Impacto esperado**: tráfego de rede e carga no banco maiores que o necessário para dados que mudam pouco (categorias, contas, lista de projetos), mas dentro do esperado para o volume de uso atual (poucos usuários, uso não simultâneo intenso).

## 7. Renderização no frontend

- Não há virtualização de listas (ex.: `react-window`/`react-virtualized`) na tabela de lançamentos (`LancamentosTab.jsx`) — todos os registros filtrados são renderizados no DOM de uma vez.
- Poucos usos de `useMemo`/`useCallback` no hook principal — a maioria das funções (`fetchDados`, `addCategoria`, etc.) é recriada a cada render de `useExpenses()`, o que pode gerar re-renders adicionais em componentes filhos que dependam dessas funções como props (efeito atenuado pelo fato de React não usar `React.memo` em nenhum componente do projeto, então todos os filhos já re-renderizam a cada mudança de estado do hook pai de qualquer forma).

**Impacto esperado**: para o volume de registros/linhas atual, provavelmente imperceptível; torna-se relevante caso o número de lançamentos por projeto cresça para a casa de milhares de linhas renderizadas simultaneamente na tabela.

## 8. Resumo de escalabilidade

O desenho atual (sem paginação, sem cache, com agregação client-side, com uma requisição por operação) é **adequado ao porte atual do sistema**: uso interno, poucos usuários simultâneos, volume de dados de uma ou poucas obras. Os pontos listados aqui não são bugs — são decisões implícitas de simplicidade que funcionam bem na escala atual, mas que se tornariam gargalos reais caso o sistema crescesse em qualquer uma destas direções: (a) muito mais lançamentos por projeto, (b) muitos projetos simultâneos, (c) muitos usuários simultâneos, ou (d) importações de CSV com arquivos muito maiores do que os observados até aqui.
