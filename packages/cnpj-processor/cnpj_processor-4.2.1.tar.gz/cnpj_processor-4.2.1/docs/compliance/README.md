# 📋 Guia de Compliance - Monitoramento e Validação CNPJ

## 🎯 Visão Geral

Este diretório contém todos os recursos necessários para implementar **monitoramento, testes e validação de compliance** no processador de dados CNPJ.

## 📊 Componentes de Compliance

### 1. **Relatório de Compliance** (`relatorio-compliance-cnpj.md`)
Documento completo que demonstra como o sistema atende aos requisitos de:
- ✅ Monitoramento do processo de atualização
- ✅ Testes e automação
- ✅ Verificação e validação de dados

### 2. **Script de Monitoramento** (`compliance_monitor.py`)
Ferramenta executável para monitoramento e validação em tempo real.

### 3. **Sistema de Validação** (`src/Entity/validation/`)
Componentes de validação multi-camadas para garantir integridade dos dados.

## 🚀 Como Usar

### **Instalação e Preparação**

1. **Verificar dependências**:
```bash
pip install -r requirements.txt
```

2. **Configurar ambiente**:
```bash
copy .env.local.example .env.local
# Editar .env.local com suas configurações
```

### **Execução de Monitoramento**

#### **Health Check Rápido**
```bash
python compliance_monitor.py --mode health-check
```

#### **Validação de Dados**
```bash
python compliance_monitor.py --mode validation --sample-size 5000
```

#### **Relatório Completo de Compliance**
```bash
python compliance_monitor.py --mode full --output compliance_$(date +%Y%m%d).json
```

#### **Verificação Diária Automática**
```bash
# Adicionar ao crontab (executa diariamente às 2h)
0 2 * * * cd /path/to/cnpj && python compliance_monitor.py --mode full --output reports/compliance_$(date +\%Y\%m\%d).json
```

## 📈 Dashboard de Monitoramento

### **Métricas em Tempo Real**

O sistema fornece as seguintes métricas:

| Métrica | Descrição | Limite | Status |
|---------|-----------|---------|--------|
| **CPU Usage** | Uso de processador | <90% | ✅ Monitorado |
| **Memory Usage** | Uso de memória RAM | <90% | ✅ Monitorado |
| **Disk Space** | Espaço em disco | >10GB livre | ✅ Monitorado |
| **Validation Rate** | Taxa de validação | >95% | ✅ 99.03% |
| **Processing Time** | Tempo de processamento | <60min | ✅ 30-45min |

### **Visualização de Progresso**

Durante o processamento, o sistema exibe:
- Barras de progresso por módulo
- ETA (tempo estimado restante)
- Taxa de sucesso por arquivo
- Workers ativos e recursos utilizados

```
📊 EMPRESA: [45/50] ████████████████▌ 90.0% | ETA: 2.3min | Workers: 4/6
📊 ESTABELECIMENTO: [38/50] ███████████████▍ 76.0% | ETA: 4.1min | Workers: 5/6
```

## 🔍 Verificação de Dados

### **Tipos de Validação**

#### **1. Validação de CNPJ/CPF**
- ✅ Algoritmo oficial de validação
- ✅ Verificação de dígitos verificadores
- ✅ Prevenção de números sequenciais

#### **2. Validação de Integridade**
- ✅ Relacionamentos entre entidades
- ✅ Consistência de dados
- ✅ Integridade referencial

#### **3. Validação de Formato**
- ✅ Tipos de dados corretos
- ✅ Formatos de data válidos
- ✅ Códigos de classificação válidos

### **Correção Automática**

O sistema corrige automaticamente:
- CNPJs com formatação incorreta
- Textos com espaços extras
- Datas em formatos alternativos
- CEPs com ou sem hífen

## 📊 Relatórios

### **Tipos de Relatórios**

#### **1. Relatório Diário**
```bash
# Executar validação diária
python compliance_monitor.py --mode full --output reports/daily_$(date +%Y%m%d).json
```

#### **2. Relatório Mensal**
```bash
# Agregar relatórios mensais
python scripts/generate_monthly_report.py
```

#### **3. Relatório de Auditoria**
```bash
# Gerar relatório para auditoria
python compliance_monitor.py --mode full --output audit/compliance_audit_$(date +%Y%m%d_%H%M%S).json
```

### **Formato dos Relatórios**

Os relatórios são gerados em JSON com estrutura:

```json
{
  "report_id": "compliance_20241201_143022",
  "generated_at": "2024-12-01T14:30:22Z",
  "compliance_status": "compliant",
  "health_check": {
    "system_status": "healthy",
    "resources": {
      "cpu_percent": 45.2,
      "memory_percent": 67.8,
      "disk_free_gb": 125.4
    }
  },
  "validation_results": {
    "empresa": {
      "total_rows": 1000000,
      "valid_rows": 990000,
      "success_rate": 99.0
    }
  }
}
```

## ⚙️ Configuração de Alertas

### **Alertas Configuráveis**

#### **1. Configuração de Thresholds**
Edite o arquivo `config.py`:

```python
# Configurações de compliance
COMPLIANCE_THRESHOLDS = {
    "cpu_max": 90,
    "memory_max": 90,
    "disk_min_gb": 10,
    "validation_min_rate": 95,
    "processing_max_minutes": 60
}
```

#### **2. Notificações por Email**
```bash
# Configurar SMTP para alertas
export SMTP_SERVER=smtp.company.com
export SMTP_USER=alerts@company.com
export SMTP_PASSWORD=your_password
export ALERT_EMAIL=admin@company.com
```

## 🔄 Automação

### **Pipeline Automatizado**

#### **1. Processamento Completo**
```bash
# Executar pipeline completo com validação
python main.py --step all --validate-after
```

#### **2. Validação Após Processamento**
```bash
# Processar e validar automaticamente
python main.py --step all && python compliance_monitor.py --mode validation
```

#### **3. Agendamento com Cron**
```bash
# /etc/cron.d/cnpj-compliance
# Executar processamento completo diariamente às 1h
0 1 * * * cd /opt/cnpj && python main.py --step all

# Executar validação às 2h
0 2 * * * cd /opt/cnpj && python compliance_monitor.py --mode full --output reports/$(date +\%Y\%m\%d).json

# Verificar health check a cada hora
0 * * * * cd /opt/cnpj && python compliance_monitor.py --mode health-check > /var/log/cnpj_health.log
```

## 🐛 Troubleshooting

### **Problemas Comuns**

#### **1. Falha na Validação**
```bash
# Verificar logs de validação
tail -f logs/validation.log

# Executar validação manual
python compliance_monitor.py --mode validation --sample-size 100
```

#### **2. Recursos Insuficientes**
```bash
# Verificar uso de recursos
python -c "from src.process.base.resource_monitor import ResourceMonitor; print(ResourceMonitor().get_system_resources_dict())"

# Ajustar concorrência
export MAX_WORKERS=4
export MAX_MEMORY_GB=8
```

#### **3. Erros de Integridade**
```bash
# Verificar relacionamentos entre entidades
python scripts/check_integrity.py

# Reprocessar dados com validação
python main.py --step process --validate-during
```

## 📚 Documentação Adicional

### **Arquivos Relevantes**

- `docs/compliance/relatorio-compliance-cnpj.md` - Relatório técnico completo
- `src/Entity/validation/README.md` - Documentação do sistema de validação
- `docs/production/best-practices.md` - Melhores práticas para produção
- `docs/performance/benchmarks.md` - Resultados de performance e benchmarks

### **Exemplos de Uso**

```bash
# Verificar exemplos completos
ls docs/examples/

# Executar exemplo básico
python docs/examples/basic-processing.py

# Executar teste rápido
python docs/examples/quick-test.py
```

## 🆘 Suporte

### **Obter Ajuda**

1. **Verificar logs**: `logs/` diretório
2. **Executar health check**: `python compliance_monitor.py --mode health-check`
3. **Consultar documentação**: Arquivos neste diretório
4. **Executar validação**: `python compliance_monitor.py --mode validation`

### **Contato**

Para questões de compliance ou suporte técnico:
- **Email**: compliance@company.com
- **Issue Tracker**: [GitHub Issues](https://github.com/company/cnpj-processor/issues)
- **Documentação**: [Wiki do Projeto](https://github.com/company/cnpj-processor/wiki)

---

**Última atualização**: 2024-12-01
**Versão**: 1.0.0
**Status**: ✅ Produção Ready