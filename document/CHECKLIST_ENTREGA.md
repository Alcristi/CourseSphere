# Checklist da entrega — Desafio AppSec & SRE

Fonte: PDF **Desafio Técnico — AppSec & SRE (Segurança e Confiabilidade)**, 3 páginas. Marque um item somente com artefato e evidência.

## Condição de escopo

- [x] A aplicação cobre **autenticação, CRUD de cursos/aulas e consumo de API**. Rails + React é sugestão; outra stack equivalente é aceita se cobrir esses fluxos.
- [x] Versão/commit analisado e fluxos testados estão identificados no relatório.

**Estado final:** Flask + React cobre autenticação, consumo de API e CRUD de cursos próprios em `/my/courses`; catálogo público em `/courses` permanece somente leitura. O CRUD foi verificado inicialmente com mocks e depois com duas contas descartáveis no Firebase configurado, por autorização explícita; houve limpeza dos dados e contas após o ensaio.

## Obrigatório — precisa funcionar e ter prova observada

| Item | Mínimo para marcar |
| --- | --- |
| - [x] Análise | Análise manual alinhada à OWASP Top 10; **5 vulnerabilidades reais e distintas**, em **2 ou mais categorias** entre controle de acesso, injeção, XSS, dados sensíveis, autenticação/sessão, configuração de segurança e dependências vulneráveis. Para cada achado: descrição, severidade (CVSS ou Alta/Média/Baixa), passos de reprodução e impacto potencial no negócio. Hipótese ou alerta isolado não é achado comprovado. |
| - [x] Correções | **3 ou mais** achados corrigidos no código. Para cada correção: causa raiz, explicação de como a solução a resolve, reprodução/teste antes e depois, verificação do fluxo legítimo e commit com mensagem clara. |
| - [x] Hardening | **2 ou mais** melhorias adicionais à função original, implementadas e verificadas. Exemplos: limite de requisições, headers HTTP, validação de entrada, CSRF, hashing e expiração de sessão. Registre a ameaça tratada e o resultado. |
| - [x] Logs | Logging estruturado para **requisições, erros e eventos de autenticação**; exemplos reais sanitizados. |
| - [x] Saúde e métricas | Métricas básicas de saúde e performance **expostas e testadas**, por `/health` e `/metrics` compatível com Prometheus **ou equivalente**. Mostre resposta/coleta real e explique o significado dos sinais. |
| - [x] Containers | **Dockerfile para backend e frontend**; imagens construídas, serviços iniciados e comandos reproduzíveis. |
| - [x] Balanceamento | `docker-compose` com balanceador simples à frente de **pelo menos 2 instâncias do backend**. Prints ou logs mostram requisições atendidas por **instâncias diferentes**; iniciar duas instâncias não demonstra distribuição. |

## Obrigatório — precisa estar definido ou documentado

| Item | Mínimo para marcar |
| --- | --- |
| - [x] SLIs/SLOs | **Pelo menos 2 SLIs relevantes** e **1 SLO proposto para cada SLI**. Registre fórmula, população de eventos, janela e meta. O PDF pede definição/proposta, não comprovação de cumprimento histórico. |
| - [x] Dashboard | **Descrição** de como os dados seriam visualizados, por exemplo no Grafana. Dashboard em execução é opcional. |
| - [x] Relatório | **Markdown ou PDF** com escopo, metodologia, achados e severidades, evidências (prints, logs ou requisições/respostas), recomendações priorizadas, causa raiz e solução das correções. Compreensível para equipe técnica e gestão, incluindo risco de negócio. |
| - [x] Confiabilidade | Seção do relatório com SLIs/SLOs, principais riscos de disponibilidade da arquitetura e recomendações de resiliência. |
| - [x] README | Como rodar a aplicação, reproduzir os achados, quais ferramentas foram usadas e como executá-las. Se houver ambiente Docker, comandos para subir e acessar. |
| - [ ] Entrega | **Repositório público no GitHub** com código analisado e corrigido, relatório técnico e README. Sem segredos ou dados reais nas evidências. Prazo: o definido no edital; o PDF não traz data. |

## Recomendado

- [x] Apoiar a análise manual com ferramentas **sempre que possível** (exemplos: ZAP, Burp Community, Brakeman, `npm audit`, Semgrep), registrando comando, versão, resultado e limites.
- [x] Configurar **ao menos uma ferramenta SAST ou SCA** no repositório e anexar o resultado. O PDF classifica este bloco como **recomendado**.

## Diferenciais opcionais

Todos contam pontos extras; nenhum substitui os mínimos.

- [x] Threat modeling estruturado, como STRIDE, com diagrama de fluxo de dados.
- [x] Ambiente de testes isolado via Docker/Compose.
- [x] SAST/SCA automatizado em pipeline de CI.
- [x] Testes automatizados dos cenários de autorização corrigidos.
- [ ] Kubernetes/k3s/minikube com probes de readiness/liveness.
- [ ] Deploy real em nuvem com rede privada, privilégio mínimo e gestão de segredos.
- [x] Tratamento de falhas entre serviços: timeout, retry e circuit breaker.
- [x] Dashboard funcional conectado a métricas reais.

## Critérios de avaliação

| Prioridade | O que a banca avaliará |
| --- | --- |
| **Alta** | Achados reais e severidade correta; reprodução clara; correções da causa raiz sem quebrar funções existentes. |
| **Média** | Relatório claro, inclusive confiabilidade; recomendações bem priorizadas; qualidade do hardening além do mínimo; coerência do balanceamento proposto ou implementado. |
| **Baixa** | SAST/SCA e evidências; organização dos commits; qualidade dos logs e métricas. Prioridade baixa não dispensa os requisitos mínimos dessas áreas. |

## Conferência final em uma passagem

- [x] Contagens: **5** achados, **2** categorias, **3** correções, **2** medidas de hardening, **2** SLIs com **2** SLOs, **2** instâncias de backend.
- [x] Há prova observada dos itens que precisam **funcionar**: fluxos da aplicação, correções, hardening, logs, saúde/métricas, containers e distribuição de requisições.
- [x] Relatório e README cobrem os itens que precisam **estar documentados**: método, reprodução, severidade e impacto, causa raiz, SLIs/SLOs, dashboard descritivo, riscos de disponibilidade, resiliência e comandos.
- [x] Código, relatório, README, evidências e histórico estão coerentes e permitem reprodução pela banca; a reprodução da versão inicial usa o commit-base e a sonda versionada na branch de entrega.
