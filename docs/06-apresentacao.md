# Etapa 6 — Apresentação final

**Tempo:** 10 a 15 minutos, com demonstração. **Todos os integrantes falam.**

## Roteiro (cerca de 13 minutos)

| Tempo | Quem | Parte | Conteúdo | Material |
|---|---|---|---|---|
| 0:00 | Integrante 1 | Abertura e problema | O que é o Stokei; o problema do pequeno negócio com caderno e planilha; objetivos | `01-planejamento.md` |
| 1:30 | Integrante 1 | Funcionalidades | F1 a F6, em uma frase cada | `01-planejamento.md` |
| 2:30 | Integrante 2 | Arquitetura | Diagrama: os 3 fluxos numerados (① site, ② API, ③ banco); conta de serviço; monitoramento | `arquitetura.png` |
| 4:30 | Integrante 2 | IaaS, PaaS e SaaS | Classificação de cada serviço; o Stokei como SaaS para o cliente; tabela "quem cuida de quê" | `02-arquitetura.md` |
| 5:30 | Integrante 3 | Configuração na nuvem | Prints do console: projeto, IAM, Firestore, função, bucket, orçamento. Explicar a troca de Azure para Google Cloud em 30 segundos | `03-configuracao.md` + prints |
| 7:00 | Integrante 4 | **Demonstração ao vivo** | Ver roteiro abaixo | site no ar + console |
| 10:30 | Integrante 5 | Testes | Os 5 testes (saída do `testar-api.sh`); 58 testes automatizados | `05-testes.md` |
| 11:30 | Integrante 5 | Segurança e custos | Sem credenciais no código, conta de serviço com papel mínimo, CORS, orçamento; estimativa de custo | relatório, seção 8 |
| 12:30 | Integrante 5 | Conclusão | Dificuldades (contas Azure/AWS), limitações e melhorias | relatório, seção 9 |
| 13:00 | Todos | Perguntas | | |

## Roteiro da demonstração (3 a 4 minutos)

**Antes de começar:**
- Deixe o site aberto numa aba e o console do Firestore (aba *Dados*) aberto em outra.
- Tenha 3 ou 4 produtos já cadastrados. Pelo menos um deve estar próximo do mínimo.
- Faça uma chamada uns minutos antes, para "acordar" a função e evitar o *cold start*.

**Passos:**

1. **Acesso pela internet.** Mostre a URL pública do site na barra do navegador. Se der, abra também no celular de alguém.
2. **Cadastro (gravação).** Cadastre código "LEI-01", "Leite integral 1L", categoria "Laticínios", quantidade 3, mínimo 6, preço 5,49. O produto aparece marcado como **"Abaixo do mínimo"**, com a faixa amarela e azul ao lado: o alerta foi calculado pela função.
3. **Prova de que está na nuvem.** Troque para a aba do Firestore, atualize e mostre o documento novo na coleção `produtos`.
4. **Processamento.** Registre uma **entrada de 5** no Leite. O saldo vai para 8 e o Leite sai da lista "Repor estoque" do Dashboard. Aponte os indicadores do Dashboard atualizados: total de itens e valor do estoque.
5. **Histórico.** Mostre a movimentação no histórico e, no Firestore, o documento na coleção `movimentacoes`.
6. **Entrada inválida.** Tente uma **saída de 100**. Aparece a mensagem "Estoque insuficiente" e o saldo não muda. Depois, tente cadastrar outro produto com o código "LEI-01". O cadastro é recusado por código repetido.
7. **Busca.** Digite "lat" na busca: o filtro funciona pela categoria.
8. **Bastidores.** No console, abra **Cloud Run → stokei-api → Registros** e mostre os logs das operações que acabaram de ser feitas.

**Plano B:** se a internet ou a nuvem falharem na hora, mostrem um vídeo gravado da demonstração (gravem antes!) e os prints do `03-configuracao.md`. Não demonstrem o modo local como se fosse a nuvem.

## Perguntas prováveis

**Por que não usaram o Azure, se o enunciado pede?**
A assinatura da instituição é só para Medicina, e o cadastro próprio exigiu CCM, que é inscrição de empresa. A AWS, liberada pelo professor, também não deu certo. O Google Cloud oferece os mesmos tipos de serviço: o Firestore equivale ao Table Storage/Cosmos DB, o Cloud Run functions ao Azure Functions e o projeto ao Resource Group.

**Onde está o "processamento na nuvem"?**
Na função `stokei-api`. Ela valida os dados, calcula o saldo, impede saldo negativo, calcula o alerta de mínimo, faz a busca e gera o relatório. O navegador só exibe o resultado.

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
