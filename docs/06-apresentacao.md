# Etapa 6 — Apresentação final

O professor pediu que o grupo **mostre o sistema funcionando na sala** e que os integrantes **assinem os nomes**. Não há apresentação longa com divisão de falas. O importante é a demonstração mostrar a aplicação usando a nuvem de verdade: gravação no Firestore e processamento na função.

## Antes da aula

- [ ] Site publicado e abrindo pela URL pública (`https://storage.googleapis.com/<ID-do-projeto>-stokei-web/index.html`).
- [ ] Dados de exemplo cadastrados (tabela em `05-testes.md`), com pelo menos um produto abaixo do mínimo.
- [ ] Duas abas abertas: o site e o console do Firestore, na aba *Dados*.
- [ ] Uma chamada ao site alguns minutos antes, para "acordar" a função e evitar a espera do primeiro acesso (*cold start*).
- [ ] Vídeo curto da demonstração gravado, como reserva.
- [ ] Folha para as assinaturas.

## Roteiro da demonstração (cerca de 5 minutos)

1. **Acesso pela internet.** Mostrar a URL pública na barra do navegador. Se der, abrir também no celular de alguém.
2. **Dashboard.** Mostrar os indicadores e a lista "Repor estoque".
3. **Cadastro (gravação).** Em *Produtos*, cadastrar código "LEI-01", "Leite integral 1L", categoria "Laticínios", quantidade 3, mínimo 6, preço 5,49. O produto aparece com o selo **"Abaixo do mínimo"** e a faixa amarela e azul: o alerta foi calculado pela função.
4. **Prova de que está na nuvem.** Na aba do Firestore, atualizar e mostrar o documento novo na coleção `produtos`.
5. **Processamento.** Em *Movimentações*, registrar uma **entrada de 5** no Leite. O saldo vai para 8 e o Leite sai da lista "Repor estoque" do Dashboard.
6. **Entrada inválida.** Tentar uma **saída de 100**: aparece "Estoque insuficiente" e o saldo não muda. Tentar cadastrar outro produto com o código "lei-01": o cadastro é recusado.
7. **Histórico.** Mostrar as movimentações em *Histórico* e o documento na coleção `movimentacoes` do Firestore.
8. **Bastidores (opcional).** No console, abrir **Cloud Run → stokei-api → Registros** e mostrar os logs das operações que acabaram de ser feitas.

**Plano B:** se a internet ou a nuvem falharem na hora, mostrar o vídeo gravado e os prints de `03-configuracao.md`. Não demonstrar o modo local como se fosse a nuvem.

## Perguntas prováveis

**Por que não usaram o Azure, se o enunciado pede?**
A assinatura da instituição é só para Medicina, e o cadastro próprio exigiu CCM, que é inscrição de empresa. A AWS, liberada pelo professor, também não deu certo. O Google Cloud oferece os mesmos tipos de serviço: o Firestore equivale ao Table Storage/Cosmos DB, o Cloud Run functions ao Azure Functions e o projeto ao Resource Group.

**Onde está o "processamento na nuvem"?**
Na função `stokei-api`. Ela valida os dados, calcula o saldo, impede saldo negativo, calcula o alerta de mínimo, faz a busca e gera o relatório do Dashboard. O navegador só exibe o resultado.

**Como a função acessa o banco sem senha?**
Ela roda com a conta de serviço `stokei-api`, que tem só o papel *Cloud Datastore User*. O Google fornece a credencial automaticamente no ambiente da função; não há chave no código nem no repositório.

**E se duas pessoas derem saída no mesmo produto ao mesmo tempo?**
A movimentação roda numa transação do Firestore. Uma operação acontece depois da outra, já com o saldo atualizado, então o estoque não fica negativo.

**Por que serverless e não uma máquina virtual?**
A VM ficaria ligada 24h, cobrando, e exigiria manter o sistema operacional. A função só roda quando chamada, escala sozinha e cabe na cota gratuita.

**Quanto custa?**
No uso do projeto, praticamente zero: fica dentro das cotas gratuitas. Para um pequeno negócio real, a estimativa é de poucos reais por mês. Ver seção 8 do relatório.

**O que é IaaS, PaaS e SaaS no projeto?**
- PaaS é o modelo principal: a função, o Firestore e o Cloud Storage. O grupo entrega só código, dados e arquivos; o Google cuida da infraestrutura.
- SaaS: o console e o monitoramento, e o próprio Stokei para o dono do negócio.
- IaaS não foi usado: seria uma máquina virtual, descartada por custo e manutenção.

**O que vocês melhorariam?**
Login, edição de produto, paginação do histórico e relatório calculado com menos leituras no banco.
