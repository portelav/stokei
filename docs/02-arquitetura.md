# Etapa 2 — Arquitetura da solução

## Diagrama

![Arquitetura do Stokei](arquitetura.png)

O diagrama também está em `arquitetura.svg` (editável) e `arquitetura.png` (para colar no relatório ou no Google Docs).

## Componentes

| Componente | Serviço | O que faz |
|---|---|---|
| Site e API | **Cloud Run** (serviço `stokei`, um contêiner com Python 3.12) | Entrega as quatro páginas do site (Dashboard, Produtos, Movimentações e Histórico), o CSS e os scripts. No mesmo endereço, recebe as requisições da API, valida os dados e aplica as regras (saldo não pode ficar negativo, código único, alerta de mínimo, busca, relatório), respondendo em JSON |
| Imagem do contêiner | **Cloud Build + Artifact Registry** | No deploy, o Cloud Build monta a imagem a partir do `Dockerfile` e o Artifact Registry a guarda; o Cloud Run roda essa imagem |
| Banco de dados | **Firestore** (modo nativo) | Armazena os produtos (coleção `produtos`) e o histórico (coleção `movimentacoes`) |
| Identidade do serviço | **IAM, conta de serviço** `stokei-api` | Identidade com que o serviço roda. Tem apenas o papel *Cloud Datastore User*, ou seja, só pode ler e gravar no Firestore |
| Gestão | **Cloud Logging / Monitoring, Faturamento** | Logs de cada execução, métricas (requisições, latência, erros), consumo e orçamento com alertas |
| Agrupamento | **Projeto do Google Cloud** | Contém todos os recursos, permissões e o faturamento (papel equivalente ao Resource Group do Azure) |

## Comunicação entre os componentes

| # | De → Para | Protocolo | Conteúdo |
|---|---|---|---|
| ① | Navegador ↔ Cloud Run | HTTPS. O navegador baixa as páginas, o CSS e os scripts e, no mesmo endereço, chama a API com `fetch` e JSON. O CORS fica restrito a esse endereço | Páginas do site, requisições da API e respostas |
| ② | Cloud Run ↔ Firestore | Biblioteca cliente do Google (gRPC sobre TLS), autenticada pela conta de serviço | Leitura e gravação de documentos, em transação |
| — | Cloud Run → Cloud Logging | Automático | Logs e métricas de cada execução |
| — | Cloud Build → Artifact Registry → Cloud Run | Só no deploy | A imagem montada pelo `Dockerfile` é guardada e publicada |

Toda a comunicação é criptografada (HTTPS/TLS). O navegador nunca fala direto com o banco: todo acesso aos dados passa pelo serviço, que valida as regras.

### Rotas da API

| Método | Rota | Função |
|---|---|---|
| GET | `/produtos?busca=` | Lista produtos (busca por nome, código ou categoria) e indica quais estão em alerta |
| POST | `/produtos` | Cadastra produto (recusa código repetido) |
| DELETE | `/produtos/{id}` | Remove produto |
| POST | `/movimentacao` | Registra entrada ou saída |
| GET | `/movimentacoes?produto_id=` | Histórico (últimas 50) |
| GET | `/relatorio` | Dados do dashboard |

### Fluxo de uma movimentação (exemplo: saída de estoque)

```mermaid
sequenceDiagram
    actor U as Usuário (navegador)
    participant F as Cloud Run (stokei)
    participant DB as Firestore

    U->>F: POST /movimentacao {id, tipo: "saida", quantidade: 3}
    F->>F: valida tipo e quantidade
    F->>DB: inicia transação e lê o produto
    alt produto não existe
        F-->>U: 404 Produto não encontrado
    else saída maior que o saldo
        F-->>U: 400 Estoque insuficiente
    else ok
        F->>DB: atualiza o saldo do produto
        F->>DB: grava o registro no histórico
        DB-->>F: confirma a transação
        F-->>U: 200 produto atualizado (com flag de alerta)
    end
    U->>F: GET /produtos, /relatorio, /movimentacoes
    F->>DB: consultas
    F-->>U: tela atualizada (alerta destacado, se abaixo do mínimo)
```

A atualização do saldo e a gravação no histórico acontecem na **mesma transação**. Se uma das duas falhar, nenhuma é gravada. Se duas saídas chegarem ao mesmo tempo, o Firestore garante que uma seja processada depois da outra, já com o saldo atualizado. Assim o estoque nunca fica errado nem negativo.

### Modelo de dados (Firestore)

**Coleção `produtos`** (um documento por produto, ID gerado automaticamente):

| Campo | Tipo | Exemplo |
|---|---|---|
| `codigo` | texto (único, opcional) | "CAN-01" |
| `nome` | texto | "Caneta azul" |
| `categoria` | texto (opcional) | "Papelaria" |
| `quantidade` | inteiro | 12 |
| `minimo` | inteiro | 5 |
| `preco` | número | 2.50 |

**Coleção `movimentacoes`** (um documento por entrada ou saída):

| Campo | Tipo | Exemplo |
|---|---|---|
| `produto_id` | texto | "a1b2c3…" |
| `produto_nome` | texto | "Caneta azul" |
| `tipo` | texto | "saida" |
| `quantidade` | inteiro | 3 |
| `saldo` | inteiro | 9 (saldo após a operação) |
| `data` | data/hora | definida pelo servidor |

## Modelos de serviço: IaaS, PaaS e SaaS

**Definições:**

- **IaaS (Infraestrutura como Serviço).** O provedor entrega infraestrutura básica: máquinas virtuais, discos, redes, armazenamento. O cliente cuida do sistema operacional, do software e da aplicação.
- **PaaS (Plataforma como Serviço).** O provedor entrega uma plataforma pronta para executar código ou guardar dados. O cliente só cuida da aplicação e dos dados; servidor, sistema operacional e escala ficam com o provedor.
- **SaaS (Software como Serviço).** O provedor entrega um software pronto, usado pelo navegador. O cliente só usa.

**Classificação dos serviços do projeto:**

| Serviço | Modelo | Por quê |
|---|---|---|
| Cloud Run | **PaaS** (serverless, contêiner gerenciado) | O grupo entrega a imagem do contêiner (código Python e site, descritos no `Dockerfile`). O Google cuida dos servidores, da rede, do HTTPS, da escala e da disponibilidade, e cobra só enquanto atende requisições |
| Cloud Build e Artifact Registry | **PaaS** | Montam e guardam a imagem sem que o grupo precise de uma máquina de build |
| Firestore | **PaaS** (banco gerenciado) | O grupo define coleções e documentos. O Google cuida de instalação, replicação, backup da infraestrutura e escala |
| Console, Cloud Logging/Monitoring, Faturamento | **SaaS** | Ferramentas prontas, usadas pelo navegador, para administrar e acompanhar o projeto |
| **O próprio Stokei** | **SaaS** (do ponto de vista do cliente) | O dono do negócio usa o sistema pelo navegador, sem instalar nada e sem saber onde ele roda. É exatamente o modelo SaaS |

**Por que não há IaaS:** o modelo predominante é o PaaS. O IaaS só apareceria se o grupo usasse uma máquina virtual (Compute Engine) e instalasse o servidor por conta própria. Essa opção foi descartada (ver "Decisões de arquitetura"). Usar contêiner não transforma o projeto em IaaS: o grupo define o que roda dentro da imagem, mas não administra máquina, sistema operacional do servidor, rede nem escala.

**Responsabilidades (quem cuida de quê):**

| Camada | Se fosse IaaS (máquina virtual) | No Stokei (Cloud Run, PaaS) |
|---|---|---|
| Código e regras de negócio | grupo | grupo |
| Dados | grupo | grupo |
| Imagem do contêiner (Python e bibliotecas, no `Dockerfile`) | grupo | grupo |
| Servidor, sistema operacional da máquina e atualizações de segurança | grupo | **Google** |
| Servidor, escala e disponibilidade | grupo | **Google** |
| Hardware, rede e datacenter | Google | Google |

## Decisões de arquitetura

| Decisão | Alternativa descartada | Motivo |
|---|---|---|
| Contêiner serverless no Cloud Run (PaaS) | Máquina virtual com servidor web (IaaS) | A VM fica ligada e cobrando 24h, exige atualizar o sistema operacional e configurar o servidor. O Cloud Run só roda quando é chamado e cabe na cota gratuita |
| Firestore (NoSQL) | Cloud SQL (banco relacional) | O Cloud SQL não tem cota gratuita e cobra por hora ligado. O modelo de dados é simples (2 coleções) e o Firestore tem transações, que garantem a consistência do saldo |
| Site e API no mesmo contêiner | Site num bucket do Cloud Storage e API separada | Um deploy só e uma URL só. Como o site e a API ficam no mesmo endereço, não é preciso configurar o endereço da API no site nem liberar CORS para outra origem |
| Acesso ao banco só pelo serviço | Navegador acessando o banco direto | Concentra as regras de negócio e a validação num só lugar e não expõe credenciais no navegador |
| Região `southamerica-east1` (São Paulo) | Regiões nos EUA | Menor latência para usuários no Brasil |
