---
sidebar_position: 3
---

# Análise Financeira

Esta seção apresenta uma estimativa de custos para o desenvolvimento e operação do Sistema Inteligente para Recomendação Agronômica, uma aplicação web responsável por processar inventários agrícolas, executar pipelines de tratamento de dados (Bronze → Silver → Gold) e gerar recomendações agronômicas automatizadas.

A análise considera dois cenários distintos:

- **Protótipo Acadêmico (MVP)**: desenvolvido para validação funcional da arquitetura, regras agronômicas e interface web.
- **Proposta em Escala Empresarial**: preparada para múltiplos clientes, alta disponibilidade, processamento concorrente e operação contínua.

---

# Protótipo

A versão de protótipo foi desenvolvida com foco na validação técnica da solução, permitindo testar o pipeline de processamento, as regras agronômicas, o dashboard web e a experiência do usuário.

Nessa etapa foram consideradas apenas infraestruturas mínimas necessárias para hospedar a aplicação e realizar testes de uso.

## Infraestrutura do protótipo

### Tabela de custos do protótipo

| Quantidade | Componente | Descrição | Preço estimado mensal |
|---|---|---|---:|
| 1 | Servidor de Aplicação | Hospedagem Backend Python/FastAPI (VPS básico) | R$ 150,00 |
| 1 | Banco de Dados PostgreSQL | Armazenamento dos resultados e histórico (instância gerenciada básica) | R$ 120,00 |
| 1 | Storage de Arquivos | Armazenamento dos CSVs enviados | R$ 50,00 |
| 1 | Hospedagem Front-End | Aplicação React (plano gratuito — Vercel/Netlify) | R$ 0,00 |
| 1 | Serviço de Logs | Monitoramento básico (plano gratuito — Logtail/Papertrail) | R$ 50,00 |
| 1 | Domínio Web | Registro anual proporcionalizado mensalmente (~R$ 80/ano) | R$ 7,00 |

### Estimativa total da infraestrutura do protótipo

| Item | Valor |
|---|---:|
| Infraestrutura mensal | R$ 377,00 |
| Duração estimada do projeto | 2 meses |
| Total infraestrutura | R$ 754,00 |

---

## Mão de obra do protótipo

Para desenvolvimento do MVP considera-se uma equipe equivalente à utilizada durante o projeto acadêmico, composta por 4 desenvolvedores juniores durante 2 meses.

As atividades contemplam:

- Desenvolvimento do pipeline Bronze, Silver e Gold
- Implementação das regras agronômicas
- Construção do dashboard React
- Testes automatizados
- Integração entre front-end e back-end

### Equipe

| Cargo | Quantidade |
|---|---:|
| Desenvolvedor Júnior | 4 |

### Salários estimados

> Referência de mercado: salários médios para desenvolvedores na região de São Paulo (2025), conforme pesquisas de remuneração como Glassdoor, LinkedIn Salary e CAGED/MTE.

| Cargo | Salário mensal | Quantidade | Custo mensal |
|---|---:|---:|---:|
| Desenvolvedor Júnior | R$ 3.800,00 | 4 | R$ 15.200,00 |

### Cálculo

```text
Custo mensal total = 4 × R$ 3.800,00
                   = R$ 15.200,00

Custo total (2 meses)
                   = R$ 15.200,00 × 2
                   = R$ 30.400,00
```

Preço mão de obra do protótipo: **R$ 30.400,00**

---

## Estimativa total do protótipo

| Item | Valor |
|---|---:|
| Infraestrutura | R$ 754,00 |
| Mão de obra | R$ 30.400,00 |
| Total estimado do protótipo | R$ 31.154,00 |

---

# Proposta em Escala Empresarial

Para uma operação real voltada ao mercado agrícola, a solução precisa suportar:

- Múltiplos clientes simultâneos
- Upload de grandes inventários
- Processamento concorrente
- Histórico permanente
- Alta disponibilidade
- Escalabilidade horizontal
- Monitoramento contínuo

Nesse cenário, a arquitetura evolui para uma estrutura baseada em microsserviços e processamento distribuído.

---

## Infraestrutura empresarial

### Componentes da arquitetura

A arquitetura industrial considera:

- Front-end React
- API REST
- Banco de dados PostgreSQL gerenciado
- Fila de processamento (RabbitMQ)
- Workers dedicados
- Armazenamento em nuvem
- Monitoramento centralizado
- Balanceamento de carga
- Containers Docker
- Orquestração Kubernetes

### Tabela de custos da infraestrutura

| Quantidade | Serviço | Descrição | Preço mensal estimado |
|---|---|---|---:|
| 2 | Servidores de Aplicação | API Backend em alta disponibilidade | R$ 1.200,00 |
| 3 | Workers de Processamento | Execução paralela da pipeline | R$ 1.800,00 |
| 1 | Banco PostgreSQL Gerenciado | Persistência dos dados | R$ 800,00 |
| 1 | RabbitMQ | Gerenciamento de filas | R$ 300,00 |
| 1 | Object Storage | Armazenamento de CSVs e relatórios | R$ 250,00 |
| 1 | Kubernetes Gerenciado | Orquestração dos containers (control plane + nodes mínimos) | R$ 3.500,00 |
| 1 | Monitoramento e Logs | Observabilidade da plataforma (ex.: Datadog, Grafana Cloud) | R$ 800,00 |
| 1 | CDN e Balanceador de Carga | Distribuição e disponibilidade | R$ 350,00 |
| 1 | Hospedagem Front-End | Aplicação React | R$ 150,00 |
| 1 | Domínio + Certificados SSL | Segurança e acesso web | R$ 50,00 |

### Estimativa total da infraestrutura empresarial

| Item | Valor |
|---|---:|
| Infraestrutura mensal | R$ 9.200,00 |
| Período considerado | 6 meses |
| Total infraestrutura | R$ 55.200,00 |

---

## Mão de obra da proposta empresarial

Para desenvolvimento da solução em escala comercial considera-se uma equipe multidisciplinar composta por profissionais de diferentes níveis de experiência.

### Composição da equipe

| Nível | Quantidade |
|---|---:|
| Desenvolvedor Sênior | 3 |
| Desenvolvedor Pleno | 6 |
| Desenvolvedor Júnior | 6 |

### Salários estimados

> Referência de mercado: salários médios para desenvolvedores na região de São Paulo (2025), conforme pesquisas de remuneração como Glassdoor, LinkedIn Salary e CAGED/MTE.

| Cargo | Salário mensal | Quantidade | Custo mensal |
|---|---:|---:|---:|
| Desenvolvedor Júnior | R$ 3.800,00 | 6 | R$ 22.800,00 |
| Desenvolvedor Pleno | R$ 8.000,00 | 6 | R$ 48.000,00 |
| Desenvolvedor Sênior | R$ 14.000,00 | 3 | R$ 42.000,00 |

### Cálculo

```text
Seniores: 3 × R$ 14.000,00
         = R$ 42.000,00

Plenos:   6 × R$ 8.000,00
         = R$ 48.000,00

Juniores: 6 × R$ 3.800,00
         = R$ 22.800,00

Custo mensal total
         = R$ 112.800,00

Custo total (6 meses)
         = R$ 112.800,00 × 6
         = R$ 676.800,00
```

Preço mão de obra da proposta empresarial: **R$ 676.800,00**

---

## Custos operacionais anuais após implantação

Após o desenvolvimento inicial, a plataforma passa a demandar apenas equipe reduzida para manutenção e evolução contínua.

### Equipe de sustentação

| Cargo | Quantidade |
|---|---:|
| Desenvolvedor Sênior | 1 |
| Desenvolvedor Pleno | 1 |
| Analista DevOps | 1 |

### Salários da equipe de sustentação

| Cargo | Salário mensal | Quantidade | Custo mensal |
|---|---:|---:|---:|
| Desenvolvedor Sênior | R$ 14.000,00 | 1 | R$ 14.000,00 |
| Desenvolvedor Pleno | R$ 8.000,00 | 1 | R$ 8.000,00 |
| Analista DevOps | R$ 10.000,00 | 1 | R$ 10.000,00 |
| **Total mensal** | | | **R$ 32.000,00** |

### Custos anuais

| Item | Valor |
|---|---:|
| Equipe de sustentação (12 meses) | R$ 384.000,00 |
| Infraestrutura (12 meses) | R$ 110.400,00 |
| Total operacional anual | R$ 494.400,00 |

---

# Justificativa Econômica

O maior custo da solução não está na infraestrutura, mas sim na construção das regras de negócio e na engenharia do sistema.

Isso ocorre porque:

- As regras agronômicas exigem conhecimento especializado;
- O pipeline Bronze → Silver → Gold precisa garantir consistência dos dados;
- A arquitetura deve suportar múltiplos usuários simultaneamente;
- Os testes automatizados precisam garantir confiabilidade das recomendações;
- A plataforma deve ser preparada para evolução futura sem reescrita completa.

Observa-se que, mesmo em escala empresarial, a infraestrutura representa cerca de 8% do investimento inicial, enquanto o principal custo está relacionado ao desenvolvimento e validação da solução.

---

## Estimativa total da proposta empresarial

| Item | Valor |
|---|---:|
| Infraestrutura (6 meses) | R$ 55.200,00 |
| Mão de obra (15 profissionais × 6 meses) | R$ 676.800,00 |
| Total estimado da proposta empresarial | R$ 732.000,00 |

---

# Resumo

| Cenário | Infraestrutura | Mão de obra | Total estimado |
|---|---:|---:|---:|
| Protótipo Acadêmico | R$ 754,00 | R$ 30.400,00 | R$ 31.154,00 |
| Escala Empresarial | R$ 55.200,00 | R$ 676.800,00 | R$ 732.000,00 |

---

## Conclusão

A análise financeira demonstra que a construção de uma plataforma inteligente de recomendação agronômica possui baixo custo de infraestrutura quando comparada ao investimento em engenharia de software e conhecimento de domínio.

A arquitetura proposta foi projetada para suportar:

- Pipeline resiliente Bronze → Silver → Gold;
- Processamento concorrente através de filas e workers;
- Escalabilidade horizontal;
- Modularização das regras agronômicas;
- Testes automatizados;
- Dashboard desacoplado;
- Evolução futura para microsserviços e processamento distribuído.

Essa abordagem garante que a solução possa iniciar como um MVP acadêmico e evoluir para uma plataforma corporativa capaz de atender grandes operações agrícolas sem necessidade de reconstrução completa da arquitetura.
