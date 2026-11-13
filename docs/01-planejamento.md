# Etapa 1 — Planejamento

## Tema

**Stokei**: sistema web de controle de estoque para pequenos negócios.

## Problema

Pequenos negócios (mercadinhos, lojas, cantinas) costumam controlar o estoque em caderno ou planilha. Isso causa três problemas:

- **Registros perdidos.** Entradas e saídas não são anotadas ou são anotadas erradas, e o saldo real não bate com o registrado.
- **Falta de produto descoberta tarde.** O dono só percebe que um item acabou quando o cliente pede.
- **Falta de visão do todo.** Não se sabe quanto dinheiro está parado em mercadoria nem quais produtos estão críticos.

Além disso, a planilha fica num único computador: se ele quebrar, os dados se perdem, e não dá para consultar o estoque fora da loja.

## Objetivos

1. Centralizar o cadastro de produtos e as movimentações num sistema acessível pela internet, de qualquer dispositivo.
2. Garantir a consistência do estoque: o sistema não permite saída maior que o saldo disponível.
3. Avisar automaticamente quando um produto fica abaixo do estoque mínimo.
4. Gerar um resumo do estoque (quantidade de itens, valor total e produtos críticos) sem cálculo manual.
5. Manter um histórico das movimentações para consulta e auditoria.

## Funcionalidades

| # | Funcionalidade | Descrição |
|---|---|---|
| F1 | Cadastro de produtos | Código, nome, categoria, quantidade inicial, estoque mínimo e preço unitário. O código não pode se repetir |
| F2 | Busca de produtos | Filtro por nome, código ou categoria |
| F3 | Entradas e saídas | Registro de movimentações. Saída maior que o saldo é recusada |
| F4 | Alerta de estoque baixo | Produto abaixo do mínimo aparece destacado |
| F5 | Dashboard | Total de produtos, total de itens, valor do estoque e itens abaixo do mínimo |
| F6 | Histórico | Lista das últimas movimentações com data, tipo, quantidade e saldo após a operação |

## Serviços de nuvem e justificativa

Arquitetura planejada no **Google Cloud** (ver "Restrições" para o motivo de não usar o Azure). A última coluna mostra o equivalente no Azure, para relacionar com o enunciado.

| Serviço | Uso no projeto | Justificativa | Equivalente Azure |
|---|---|---|---|
| **Projeto do Google Cloud** | Agrupa todos os recursos, permissões e faturamento | Cumpre o papel do Resource Group exigido no R1. Centraliza permissões e custos e permite apagar tudo de uma vez ao final | Resource Group |
| **Firestore** | Armazena os produtos e o histórico de movimentações | Banco NoSQL gerenciado, sem servidor para administrar, com cota gratuita diária. Suporta transações, o que garante saldo correto mesmo com operações simultâneas (R2) | Table Storage / Cosmos DB |
| **Cloud Run functions** | API HTTP e regras de negócio: validação, controle de saldo, alertas, relatório e busca | Serverless: só executa (e só cobra) quando recebe requisições, escala automaticamente e a cota gratuita mensal cobre o projeto (R3) | Azure Functions |
| **Cloud Storage** | Hospeda a interface web (HTML, CSS e JS) | Serve a página direto do bucket, sem servidor web, com custo praticamente zero | Blob Storage (site estático) |

Integração entre os serviços (R5): a função lê e grava no Firestore a cada operação feita pela interface. Ela se autentica por uma conta de serviço com permissão apenas no Firestore, sem senha ou chave no código.

## Por que usar nuvem

- **Acesso de qualquer lugar.** O dono consulta o estoque pelo celular, fora da loja.
- **Dados seguros.** Os dados não dependem de um computador local que pode quebrar ou ser perdido.
- **Custo proporcional ao uso.** Um negócio pequeno paga quase nada, e o sistema cresce se o negócio crescer.
- **Sem manutenção de servidor.** Atualizações, disponibilidade e backup da infraestrutura ficam com o provedor.

## Restrições encontradas

- **Assinatura acadêmica do Azure.** O acesso fornecido pela instituição é restrito aos estudantes de Medicina.
- **Cadastro próprio no Azure.** O cadastro exigiu o CCM (Cadastro de Contribuintes Mobiliários), uma inscrição municipal de empresa que os integrantes, pessoas físicas, não possuem.
- **AWS.** O professor autorizou verbalmente a AWS como alternativa, mas o grupo também não conseguiu criar uma conta nela.

Sem conta disponível no Azure nem na AWS, a solução foi planejada no **Google Cloud**, que oferece os mesmos tipos de serviço (armazenamento gerenciado e processamento serverless) e um período de teste gratuito.