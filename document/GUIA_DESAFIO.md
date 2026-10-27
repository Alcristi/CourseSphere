# Guia de trabalho — desafio AppSec & SRE no CourseSphere

Este guia transforma o enunciado em atividades de até 30 minutos. A intenção é que **você investigue, tome as decisões e construa a entrega**. Nenhum achado é considerado verdadeiro até você produzir evidência. Os exemplos do enunciado são hipóteses de investigação, não uma lista de respostas.

## Como usar cada bloco

Reserve até 30 minutos: aproximadamente 5 para entender a pergunta, 20 para executar e 5 para registrar o resultado. Se uma atividade não terminar, registre onde parou e continue em outro bloco de 30 minutos. Não force uma conclusão sem evidência.

Para cada decisão, escreva em suas notas:

1. **O que observei?** Arquivo, comportamento ou evidência.
2. **Por que isso importa?** Qual propriedade de segurança ou confiabilidade está em jogo?
3. **Que alternativas considerei?** Quais custos e limitações cada uma tem?
4. **Por que escolhi esta?** Qual causa ou risco ela trata?
5. **Como sei que funciona?** Teste, saída observada e seus limites.

Faça os testes apenas no ambiente que você controla, com contas e dados de teste. Não registre tokens, senhas, chaves ou dados pessoais nas evidências. Marque uma atividade somente quando o resultado indicado estiver registrado.

## 1. Entender o enunciado e a aplicação

- [x] **01 — Traduzir a entrega em uma lista de verificação**
  **Objetivo:** distinguir o que é obrigatório, recomendado e opcional.
  **Faça:** releia o PDF e anote quantidades mínimas, artefatos e critérios de avaliação.
  **Pergunte:** o que precisa estar funcionando e o que precisa apenas estar documentado?
  **Concluído quando:** sua lista permitir conferir a entrega sem depender da memória. Consulte `document/CHECKLIST_ENTREGA.md`, conferido com o PDF original.

- [x] **02 — Definir o ponto de partida**
  **Objetivo:** saber qual versão está sendo analisada e preservar seu trabalho.
  **Faça:** consulte o estado do Git, anote o commit inicial e identifique arquivos locais não versionados ou alterados. Escolha uma forma de trabalhar que preserve esses arquivos.
  **Pergunte:** outra pessoa conseguiria voltar à mesma versão para reproduzir os achados?
  **Concluído quando:** a revisão inicial e o estado de trabalho estiverem anotados. Consulte `document/PONTO_DE_PARTIDA.md`.

- [x] **03 — Preparar o ambiente de análise**
  **Objetivo:** separar dados e serviços de teste dos dados reais.
  **Faça:** leia o README e os exemplos de configuração; liste dependências, credenciais necessárias e serviços externos. Prepare configurações de teste sem inserir segredos no Git.
  **Pergunte:** quais partes podem ser exercitadas localmente e quais dependem de serviços externos?
  **Concluído quando:** houver um mapa das dependências e das limitações do ambiente. Consulte `document/AMBIENTE_ANALISE.md` e os modelos `backend/analysis.env.example` e `frontend/analysis.env.example`.

- [x] **04 — Iniciar e observar o backend**
  **Objetivo:** entender como a API é iniciada e como uma requisição chega a uma rota.
  **Faça:** siga as instruções existentes, registre o resultado da inicialização e teste uma rota disponível. Se faltar uma dependência, registre o bloqueio e investigue uma alternativa de teste isolado.
  **Pergunte:** uma falha de inicialização é defeito do código, configuração ausente ou serviço indisponível?
  **Concluído quando:** você tiver uma resposta observada ou um bloqueio reproduzível.

- [x] **05 — Iniciar e observar o frontend**
  **Objetivo:** acompanhar uma ação do usuário até a chamada de API.
  **Faça:** inicie a interface, abra as ferramentas de desenvolvedor do navegador e observe uma interação.
  **Pergunte:** qual origem faz a chamada, para qual endereço e com quais dados?
  **Concluído quando:** você tiver desenhado esse caminho sem copiar credenciais.

- [x] **06 — Desenhar a arquitetura atual**
  **Objetivo:** reconhecer os componentes e as fronteiras de confiança.
  **Faça:** desenhe navegador, API, bancos e serviços externos; identifique o sentido das chamadas. Consulte `document/ARCHITECTURE.md` e confirme o que puder no código.
  **Pergunte:** quais informações atravessam cada fronteira e quem controla cada entrada?
  **Concluído quando:** o diagrama indicar componentes, dados principais e pontos ainda desconhecidos.

- [x] **07 — Inventariar rotas e operações**
  **Objetivo:** definir a superfície que será examinada.
  **Faça:** liste método, rota, entrada, autenticação esperada e efeito sobre dados. Verifique também se a aplicação cobre autenticação, consumo de API e CRUD de cursos/aulas, como pedido no enunciado.
  **Pergunte:** existe diferença entre o que a interface permite e o que a API aceita diretamente? Se faltar uma capacidade exigida, qual é o menor caminho coerente para incluí-la ou explicar a limitação?
  **Concluído quando:** houver uma tabela de operações e uma decisão registrada sobre eventuais lacunas.

- [x] **08 — Acompanhar autenticação e autorização**
  **Objetivo:** diferenciar identidade de permissão.
  **Faça:** siga o fluxo de uma ação autenticada do navegador até o acesso ao dado. Identifique onde a identidade é verificada e como o recurso é associado a ela.
  **Pergunte:** “quem é o usuário?” e “o que ele pode fazer?” são respondidas em pontos diferentes?
  **Concluído quando:** você conseguir explicar o fluxo com suas próprias palavras.

## 2. Investigar possíveis vulnerabilidades

Nestas atividades, procure comportamentos reais na versão escolhida. **Não conte uma hipótese, um aviso de ferramenta ou uma recomendação genérica como vulnerabilidade comprovada.** Cubra pelo menos duas categorias do enunciado.

- [x] **09 — Formular hipóteses de acesso**
  **Objetivo:** investigar acesso indevido entre usuários.
  **Faça:** escolha recursos que pertençam a usuários e desenhe testes com duas contas de teste, incluindo leitura, alteração e exclusão quando existirem.
  **Pergunte:** de onde vem a identidade usada para selecionar o recurso? O que deveria acontecer ao usar o identificador de outra conta?
  **Concluído quando:** houver cenários e resultados esperados, sem alterar dados de terceiros.

- [x] **10 — Investigar autenticação e sessão**
  **Objetivo:** entender a validade e o transporte das credenciais.
  **Faça:** examine como a aplicação recebe e valida credenciais e teste casos ausente, inválido e expirado em ambiente de teste.
  **Pergunte:** o componente que valida a identidade é o mesmo que recebe a entrada? Onde a credencial pode aparecer?
  **Concluído quando:** você tiver uma tabela de casos, resultados e evidências.

- [x] **11 — Investigar entrada e consultas**
  **Objetivo:** verificar como dados controlados pelo usuário chegam à persistência e a serviços externos.
  **Faça:** siga pelo menos dois campos desde a requisição até seu uso; teste formatos inesperados e limites em dados descartáveis.
  **Pergunte:** quais valores podem alterar a estrutura de uma consulta e quais são tratados apenas como dados?
  **Concluído quando:** você puder apontar onde cada entrada é validada e usada.

- [x] **12 — Investigar saída e dados sensíveis**
  **Objetivo:** entender o que respostas, logs e interface expõem.
  **Faça:** examine respostas de sucesso e erro, armazenamento no navegador e renderização de conteúdo controlado pelo usuário.
  **Pergunte:** uma mensagem interna ou conteúdo de outro usuário chega a um lugar onde não deveria? Em que condições?
  **Concluído quando:** houver exemplos seguros de respostas e uma lista de hipóteses verificáveis.

- [x] **13 — Investigar configuração de segurança**
  **Objetivo:** revisar como navegador, servidor e ambiente interagem.
  **Faça:** inspecione configuração de execução, políticas HTTP e origens aceitas; compare o comportamento observado com a intenção da aplicação.
  **Pergunte:** que proteção cada configuração oferece? Qual pré-condição seria necessária para um abuso?
  **Concluído quando:** você tiver comandos de verificação e respostas registradas.

- [x] **14 — Executar análise de dependências ou SAST**
  **Objetivo:** usar uma ferramenta para ampliar a revisão manual.
  **Faça:** escolha uma ferramenta adequada à stack, execute-a e salve a saída ou registre o motivo de bloqueio.
  **Pergunte:** o aviso afeta dependência de produção ou de desenvolvimento? A versão está instalada? A funcionalidade vulnerável é alcançável?
  **Concluído quando:** o resultado puder ser reproduzido e os alertas não forem tratados automaticamente como exploração comprovada.

- [x] **15 — Selecionar candidatos a achados**
  **Objetivo:** evitar duplicações e conclusões frágeis.
  **Faça:** agrupe hipóteses por causa, separe problemas comprováveis de riscos condicionais e escolha candidatos de pelo menos duas categorias.
  **Pergunte:** dois sintomas têm a mesma causa? O resultado depende de uma configuração que você ainda não verificou?
  **Concluído quando:** cada candidato tiver uma pergunta de teste clara.

- [x] **16 — Comprovar e registrar o achado 1**
  **Faça:** registre pré-condições, passos, entrada sem segredos, resposta observada, impacto e evidência.
  **Pergunte:** outra pessoa conseguiria repetir e distinguir o resultado esperado do observado?
  **Concluído quando:** existir evidência reproduzível e classificação justificada.

- [x] **17 — Comprovar e registrar o achado 2**
  **Faça:** repita o processo com outro candidato e mantenha a evidência independente.
  **Pergunte:** qual ativo e qual usuário seriam afetados?
  **Concluído quando:** descrição, reprodução, impacto e severidade estiverem registrados.

- [x] **18 — Comprovar e registrar o achado 3**
  **Faça:** execute o teste e registre o comportamento da versão analisada.
  **Pergunte:** o problema é reproduzível ou depende de hipótese ainda não confirmada?
  **Concluído quando:** evidência e limitações estiverem claras.

- [x] **19 — Comprovar e registrar o achado 4**
  **Faça:** execute o teste e relacione a evidência ao ponto do código.
  **Pergunte:** o que um agente precisaria controlar para alcançar esse comportamento?
  **Concluído quando:** pré-condições e impacto estiverem demonstrados ou delimitados.

- [x] **20 — Comprovar e registrar o achado 5**
  **Faça:** complete o quinto registro e confira a diversidade de categorias.
  **Pergunte:** cada item descreve uma falha distinta e real?
  **Concluído quando:** houver pelo menos cinco achados sustentados por evidência em pelo menos duas categorias. Se ainda não houver, volte às atividades 09–14 em novos blocos.

- [x] **21 — Priorizar os achados**
  **Objetivo:** decidir o que corrigir primeiro.
  **Faça:** atribua Alta/Média/Baixa ou CVSS e justifique com probabilidade, pré-condições, impacto e exposição. Escolha pelo menos três para corrigir.
  **Pergunte:** um problema grave no papel é realmente alcançável neste contexto? Qual correção reduz mais risco primeiro?
  **Concluído quando:** houver uma ordem de correção explicável para gestão e equipe técnica.

## 3. Corrigir pelo menos três problemas

Para cada correção, use dois blocos. Se precisar de mais tempo, repita o segundo bloco. Preserve um teste que falhe antes e passe depois sempre que for viável.

- [x] **22 — Correção 1: entender e planejar**
  **Faça:** identifique a causa raiz, o limite de confiança e duas opções de correção. Escreva o comportamento esperado e um teste de regressão.
  **Pergunte:** a opção escolhida elimina a causa ou apenas esconde o sintoma?
  **Concluído quando:** o plano e o teste forem claros.

- [x] **23 — Correção 1: construir e verificar**
  **Faça:** implemente a menor mudança coerente, execute o teste e repita a reprodução do achado.
  **Pergunte:** a funcionalidade legítima continua funcionando? Há outro caminho que chega à mesma operação?
  **Concluído quando:** você tiver evidências de antes/depois e limitações registradas.

- [x] **24 — Correção 2: entender e planejar**
  **Faça:** descreva causa raiz, alternativas, comportamento esperado e teste.
  **Pergunte:** qual camada deve assumir essa responsabilidade e por quê?
  **Concluído quando:** outra pessoa conseguir revisar a decisão antes de ler a implementação.

- [x] **25 — Correção 2: construir e verificar**
  **Faça:** implemente e execute o cenário de abuso e o cenário legítimo.
  **Pergunte:** o teste prova a propriedade desejada ou apenas repete detalhes da implementação?
  **Concluído quando:** o resultado e o impacto sobre o fluxo normal estiverem documentados.

- [x] **26 — Correção 3: entender e planejar**
  **Faça:** investigue a causa, compare opções e defina o teste.
  **Pergunte:** a mudança depende de outra configuração ou de um serviço externo?
  **Concluído quando:** os pressupostos estiverem explícitos.

- [x] **27 — Correção 3: construir e verificar**
  **Faça:** implemente, teste o caso que reproduzia o problema e uma operação válida.
  **Pergunte:** o que ainda não foi possível testar?
  **Concluído quando:** houver evidência de correção e uma limitação honesta, se existir.

- [x] **28 — Organizar os commits das correções**
  **Objetivo:** tornar o histórico revisável.
  **Faça:** revise o diff, verifique arquivos e segredos e organize commits com mensagens que expliquem a mudança.
  **Pergunte:** cada commit tem um propósito compreensível? Inclui arquivos de outra atividade por acidente?
  **Concluído quando:** o histórico e os testes associados puderem ser apresentados à banca.

## 4. Fazer pelo menos duas melhorias de hardening

Hardening reduz exposição além da função original da aplicação. Exemplos citados no enunciado incluem limite de requisições, headers, validação, proteção CSRF e gestão de sessão. Escolha medidas adequadas à arquitetura real; não use uma medida apenas para cumprir contagem.

- [x] **29 — Escolher a melhoria 1**
  **Faça:** identifique a ameaça, a camada de aplicação e alternativas. Defina um teste e o impacto em usuários legítimos.
  **Pergunte:** qual é o limite desta proteção? Que configuração ela exige em produção?
  **Concluído quando:** a decisão estiver fundamentada.

- [x] **30 — Construir e validar a melhoria 1**
  **Faça:** implemente e teste um caso permitido e um caso bloqueado.
  **Pergunte:** como observar falhas ou efeitos colaterais?
  **Concluído quando:** o resultado estiver reproduzível.

- [x] **31 — Escolher a melhoria 2**
  **Faça:** repita a análise para uma proteção distinta.
  **Pergunte:** ela protege uma fronteira diferente ou apenas duplica a primeira?
  **Concluído quando:** ameaça, escolha e teste estiverem anotados.

- [x] **32 — Construir e validar a melhoria 2**
  **Faça:** implemente, teste e registre os efeitos na aplicação.
  **Pergunte:** a proteção funciona em todas as instâncias e também em falhas?
  **Concluído quando:** a evidência estiver pronta para o relatório.

## 5. Observabilidade e confiabilidade

- [x] **33 — Planejar logs estruturados**
  **Objetivo:** decidir quais eventos ajudam a investigar uma operação.
  **Faça:** proponha campos para requisições, erros e autenticação, uma forma de correlação e uma lista do que não deve ser registrado.
  **Pergunte:** um operador consegue associar um erro à requisição sem ver credenciais ou dados pessoais?
  **Concluído quando:** houver exemplos fictícios e política de dados dos logs.

- [x] **34 — Instrumentar e verificar os logs**
  **Faça:** registre os eventos escolhidos em formato estruturado e provoque sucesso e erro controlados.
  **Pergunte:** os registros são legíveis por máquina? Existem eventos duplicados ou informações sensíveis?
  **Concluído quando:** você tiver exemplos reais sanitizados para o relatório.

- [x] **35 — Definir e implementar saúde**
  **Objetivo:** distinguir processo vivo de capacidade de atender tráfego.
  **Faça:** escolha o significado do endpoint de saúde e teste condições normal e de falha pertinentes.
  **Pergunte:** uma resposta positiva significa que todas as dependências estão prontas? O que o balanceador deve fazer diante de falha?
  **Concluído quando:** o contrato e seus limites estiverem documentados e testados.

- [x] **36 — Expor métricas básicas**
  **Objetivo:** medir volume, erro e desempenho ao longo do tempo.
  **Faça:** escolha métricas e rótulos, exponha um endpoint compatível com Prometheus ou equivalente e gere tráfego de teste.
  **Pergunte:** os rótulos podem crescer sem limite? Como coletar métricas de múltiplas instâncias?
  **Concluído quando:** uma coleta mostrar valores coerentes e a exposição estiver controlada.

- [x] **37 — Definir dois SLIs e dois SLOs**
  **Objetivo:** transformar medições em objetivos verificáveis.
  **Faça:** para cada SLI, defina evento bom, total, exclusões, janela e fórmula; proponha um SLO com meta e período.
  **Pergunte:** a métrica representa a experiência do usuário? O que acontece quando não há tráfego?
  **Concluído quando:** qualquer pessoa conseguir calcular o indicador e avaliar a meta.

- [x] **38 — Planejar o dashboard**
  **Objetivo:** tornar as medições úteis para operação.
  **Faça:** descreva painéis, filtros e alertas para os dois SLIs, erros, latência e instâncias. Um dashboard funcional é opcional.
  **Pergunte:** que ação alguém tomaria ao ver cada alerta? Como evitar alertas sem contexto?
  **Concluído quando:** o relatório descreva visualização e resposta esperada.

- [x] **39 — Analisar riscos de disponibilidade**
  **Faça:** identifique dependências externas, pontos únicos de falha, armazenamento e efeitos de lentidão ou indisponibilidade. Priorize recomendações de resiliência.
  **Pergunte:** qual funcionalidade para, qual pode degradar e como os dados seriam recuperados?
  **Concluído quando:** houver riscos, impactos e próximos passos proporcionais.

## 6. Containerização e balanceamento

- [x] **40 — Planejar os containers**
  **Objetivo:** entender o que precisa estar em cada imagem e o que deve vir do ambiente.
  **Faça:** desenhe imagens, portas, configuração, dados persistentes e segredos; escolha como iniciar cada serviço.
  **Pergunte:** quais arquivos não devem entrar na imagem? O que precisa sobreviver à recriação?
  **Concluído quando:** houver um desenho simples e justificativas.

- [x] **41 — Containerizar o backend**
  **Faça:** crie o Dockerfile, construa a imagem e teste uma rota de saúde.
  **Pergunte:** o processo usado para servir a API é adequado ao ambiente escolhido? Como o container recebe configuração?
  **Concluído quando:** outra pessoa puder construir e iniciar o backend pelos comandos registrados.

- [x] **42 — Containerizar o frontend**
  **Faça:** crie ou ajuste o Dockerfile, gere o build e verifique se a interface é servida.
  **Pergunte:** que valores são incorporados ao código enviado ao navegador? A interface consegue localizar a API no ambiente escolhido?
  **Concluído quando:** o build e o acesso à interface forem reproduzíveis.

- [x] **43 — Definir a orquestração**
  **Faça:** crie o Compose com frontend, pelo menos duas instâncias de backend e um serviço de balanceamento. Defina rede, configuração e persistência necessárias.
  **Pergunte:** quais serviços devem ser acessíveis de fora? Qual dependência precisa estar pronta antes de receber tráfego?
  **Concluído quando:** a configuração for validada e os serviços iniciarem.

- [x] **44 — Configurar o balanceador**
  **Faça:** encaminhe as requisições para as duas instâncias e teste frontend e API pelo endereço de entrada.
  **Pergunte:** o caminho da URL e os cabeçalhos chegam como a aplicação espera? O que acontece se uma instância falhar?
  **Concluído quando:** chamadas válidas funcionarem pelo ponto de entrada.

- [x] **45 — Demonstrar a distribuição**
  **Faça:** produza várias requisições e colete logs ou respostas que identifiquem a instância que atendeu cada uma. Guarde a evidência sanitizada.
  **Pergunte:** a evidência prova atendimento por duas instâncias distintas ou apenas que duas foram criadas?
  **Concluído quando:** o relatório apresentar saídas observadas de ambas e os comandos para reproduzi-las.

## 7. Relatório e entrega

- [x] **46 — Escrever o resumo para gestão**
  **Faça:** apresente escopo, riscos mais relevantes, impacto de negócio, prioridade e limitações sem depender de jargão.
  **Pergunte:** alguém sem conhecer o código entende o que pode acontecer e o que foi corrigido?
  **Concluído quando:** o resumo for consistente com as evidências técnicas.

- [x] **47 — Completar o relatório técnico**
  **Faça:** para cada achado, inclua descrição, severidade, pré-condições, reprodução, evidências, impacto, causa e situação da correção. Acrescente SLIs/SLOs, riscos de disponibilidade e recomendações.
  **Pergunte:** quais resultados foram observados e quais são propostas ou hipóteses?
  **Concluído quando:** a banca conseguir repetir os passos em ambiente de teste.

- [x] **48 — Preparar o README**
  **Faça:** documente pré-requisitos, configuração sem segredos, comandos para iniciar e testar, ferramentas, reprodução dos achados e execução do Compose.
  **Pergunte:** uma pessoa que acabou de clonar o repositório consegue avançar sem adivinhar etapas?
  **Concluído quando:** você revisar os comandos em uma instalação limpa ou registrar o que não conseguiu validar.

- [x] **49 — Preparar a verificação automatizada recomendada**
  **Faça:** configure ao menos uma ferramenta SAST ou SCA no repositório e anexe ou referencie o resultado da execução. Se fizer CI, documente quando roda e o que causa falha.
  **Pergunte:** a ferramenta analisa o que será entregue? Como um aviso será revisado?
  **Concluído quando:** comando, resultado e limitações estiverem disponíveis.

- [ ] **50 — Revisar a entrega como avaliador**
  **Faça:** confira o quadro abaixo, execute os comandos essenciais, revise o histórico e procure segredos ou dados de teste indevidos. Prepare o repositório público solicitado pelo edital quando estiver pronto para publicar.
  **Pergunte:** cada afirmação tem evidência? Há algo apresentado como concluído sem ter sido testado?
  **Concluído quando:** código, relatório, README, resultados e histórico estiverem coerentes.

## 8. Diferenciais opcionais

Faça estes blocos somente depois dos requisitos mínimos. Cada item pode ser dividido em novos blocos de 30 minutos.

- [x] **51 — Threat modeling:** escolha um fluxo, desenhe dados e fronteiras, aplique STRIDE e registre ameaças, controles e pressupostos.
- [x] **52 — Ambiente isolado:** avalie como tornar os testes descartáveis e como evitar acesso a dados ou serviços reais.
- [x] **53 — CI de segurança:** execute SAST/SCA e testes relevantes em push ou pull request; registre dependências e limitações.
- [x] **54 — Testes de autorização:** use dois usuários de teste para provar que operações sobre recursos de outra pessoa são negadas, quando essa operação existir.
- [ ] **55 — Kubernetes:** estude a diferença entre liveness e readiness e, se fizer sentido, prepare uma demonstração local com probes.
- [x] **56 — Nuvem:** desenhe rede privada, permissões mínimas e gestão de segredos; um deploy real depende de ambiente e acesso disponíveis.
- [x] **57 — Resiliência entre serviços:** escolha uma chamada externa e avalie timeout, retry seguro e circuit breaker, incluindo efeitos de falha.
- [x] **58 — Dashboard funcional:** conecte um coletor e um painel às métricas reais e valide consultas e alertas.

## Conferência dos requisitos do PDF

| Requisito | Onde trabalhar | Como saber que está atendido |
| --- | --- | --- |
| Análise: cinco vulnerabilidades reais, pelo menos duas categorias | 09–21 | Cinco registros independentes com reprodução, severidade, impacto e evidência |
| Pelo menos três correções e commits claros | 22–28 | Três causas tratadas, cenários antes/depois e histórico revisável |
| Duas melhorias de hardening | 29–32 | Duas medidas justificadas, implementadas e verificadas |
| Logs, saúde, métricas, dois SLIs/SLOs e dashboard descrito | 33–39 | Eventos e métricas observados; indicadores e metas com fórmulas e janelas |
| Dockerfiles, Compose, balanceador e duas instâncias | 40–45 | Serviços executando e evidência de atendimento pelas duas instâncias |
| Relatório técnico e de confiabilidade | 46–47 | Escopo, método, evidências, prioridade, impacto e recomendações |
| README e repositório para entrega | 48 e 50 | Instruções reproduzíveis, código e relatório organizados |
| SAST/SCA recomendado | 14 e 49 | Ferramenta configurada e resultado anexado ou referenciado |
| Diferenciais opcionais | 51–58 | Apenas os escolhidos, com evidência e limites explicitados |

## Modelo curto para suas anotações

Copie para cada atividade ou achado:

```text
Atividade / data:
Pergunta que estou tentando responder:
Contexto e arquivos/rotas examinados:
Passos executados e dados de teste:
Resultado observado:
Resultado esperado e justificativa:
Decisão, alternativas e motivo:
Evidência e como reproduzir:
Limitações / próxima ação:
```
