# Guide d'Observabilité - Agent Framework

Ce guide couvre l'architecture d'observabilité de l'Agent Framework.

## Table des Matières

1. [Vue d'Ensemble](#vue-densemble)
2. [Architecture par Défaut : Deux Chemins de Métriques](#architecture-par-défaut--deux-chemins-de-métriques)
3. [Dashboards Kibana (Direct ES)](#dashboards-kibana-direct-es)
4. [Dashboards Grafana (OTel)](#dashboards-grafana-otel)
5. [Configuration](#configuration)
6. [Métriques Disponibles](#métriques-disponibles)
7. [Architecture Alternative : Elastic APM Native](#architecture-alternative--elastic-apm-native)
8. [Architecture Alternative : Stack OTel Complet](#architecture-alternative--stack-otel-complet)
9. [Déploiement Production](#déploiement-production)
10. [Troubleshooting](#troubleshooting)

---

## Vue d'Ensemble

L'Agent Framework propose **deux chemins de métriques indépendants** qui peuvent fonctionner en parallèle :

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              AGENT FRAMEWORK                                    │
│                                                                                 │
│                        ObservabilityManager                                     │
│                               │                                                 │
│              ┌────────────────┴────────────────┐                               │
│              │                                 │                                │
│              ▼                                 ▼                                │
│   ┌──────────────────────┐       ┌──────────────────────┐                      │
│   │   CHEMIN 1 : OTel    │       │  CHEMIN 2 : Direct   │                      │
│   │   (Traces + Metrics) │       │  ES (Métriques)      │                      │
│   │                      │       │                      │                      │
│   │   OTEL_ENABLED=true  │       │  METRICS_ES_LOGGING  │                      │
│   │                      │       │  _ENABLED=true       │                      │
│   └──────────┬───────────┘       └──────────┬───────────┘                      │
│              │                               │                                  │
└──────────────┼───────────────────────────────┼──────────────────────────────────┘
               │                               │
               │ OTLP (gRPC)                   │ HTTP (bulk API)
               │                               │
               ▼                               ▼
┌──────────────────────────┐     ┌────────────────────────────────────────────────┐
│    OTel Collector        │     │              Elasticsearch                     │
│    (Port 4317)           │     │              (Port 9200)                       │
│                          │     │                                                │
│  Exporte vers:           │     │  Indices:                                      │
│  • Prometheus (metrics)  │     │  • agent-metrics-llm-{date}                    │
│  • Jaeger (traces)       │     │  • agent-metrics-api-{date}                    │
│  • ES (logs)             │     │                                                │
└──────────┬───────────────┘     └─────────────────────┬──────────────────────────┘
           │                                           │
     ┌─────┴─────┐                                     │
     │           │                                     │
     ▼           ▼                                     ▼
┌─────────┐ ┌─────────┐                         ┌───────────┐
│ Jaeger  │ │Prometheus│                         │  Kibana   │
│ Traces  │ │ Metrics  │                         │  (5601)   │
└─────────┘ └────┬────┘                          │           │
                 │                               │  TSVB     │
                 ▼                               │  Dashboard│
          ┌───────────┐                          └───────────┘
          │  Grafana  │                                ▲
          │  (3000)   │                                │
          │           │                    Créé via Admin Panel
          │  PromQL   │                    (Saved Objects API)
          └───────────┘
```

### Quel Chemin Utiliser ?

| Besoin | Chemin Recommandé | Pourquoi |
|--------|-------------------|----------|
| **Dashboard Kibana simple** | Direct ES | Pas besoin d'OTel Collector |
| **Alerting temps-réel** | OTel → Prometheus | PromQL optimisé pour alertes |
| **Traces distribuées** | OTel → Jaeger | Visualisation des spans |
| **Analyse détaillée LLM** | Direct ES → Kibana | Documents individuels, recherche |
| **Production complète** | Les deux | Complémentaires |

### Configuration Rapide

```bash
# .env - Configuration minimale pour Kibana (recommandé pour démarrer)
ELASTICSEARCH_ENABLED=true
ELASTICSEARCH_URL=http://localhost:9200
METRICS_ES_LOGGING_ENABLED=true

# Optionnel : Ajouter OTel pour traces et alerting
OTEL_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
```

---

## Architecture par Défaut : Deux Chemins de Métriques

### Comparaison des Deux Chemins

| Aspect | Chemin OTel (Prometheus) | Chemin Direct ES |
|--------|--------------------------|------------------|
| **Activation** | `OTEL_ENABLED=true` | `METRICS_ES_LOGGING_ENABLED=true` |
| **Prérequis** | OTel Collector + Prometheus | Elasticsearch seul |
| **Format** | Métriques agrégées (counters, histograms) | Documents JSON détaillés |
| **Stockage** | Prometheus (time-series optimisé) | Elasticsearch (documents) |
| **Visualisation** | Grafana | Kibana |
| **Requêtes** | PromQL | KQL / Lucene |
| **Granularité** | Agrégée par intervalle | Par événement individuel |
| **Use case** | Alerting temps-réel, SRE | Analyse détaillée, debugging |

### Données Capturées (identiques sur les deux chemins)

**Métriques LLM** : Tokens (input/output/thinking), durée, TTFT, modèle, tool calls

**Métriques API** : Durée totale, endpoint, méthode HTTP, session ID, status code

---

## Composants du Stack

### 1. OpenTelemetry Collector

**Rôle** : Hub central de télémétrie - reçoit, traite et exporte les données.

**Ports** :
- `4317` : OTLP gRPC (réception)
- `4318` : OTLP HTTP (réception)
- `8889` : Prometheus exporter (métriques)
- `13133` : Health check
- `55679` : zPages (debug)

**Configuration** (`observability/otel-collector-config.yaml`) :

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 5s
    send_batch_size: 1000
  memory_limiter:
    limit_mib: 512

exporters:
  prometheus:
    endpoint: 0.0.0.0:8889
    namespace: agent_framework
  otlp/jaeger:
    endpoint: jaeger:4317
  elasticsearch:
    endpoints: ["http://elasticsearch:9200"]
    logs_index: otel-logs

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [otlp/jaeger]
    metrics:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [prometheus]
    logs:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [elasticsearch]
```

### 2. Prometheus

**Rôle** : Stockage et requêtage des métriques time-series.

**Port** : `9090`

**Configuration** (`observability/prometheus.yml`) :

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'otel-collector'
    static_configs:
      - targets: ['otel-collector:8889']
```

### 3. Jaeger

**Rôle** : Backend de tracing distribué - visualisation des traces.

---

## Configuration

### Variables d'Environnement Complètes

```bash
# === Chemin Direct ES (Kibana) ===
ELASTICSEARCH_ENABLED=true
ELASTICSEARCH_URL=http://localhost:9200
METRICS_ES_LOGGING_ENABLED=true

# === Chemin OTel (Grafana) ===
OTEL_ENABLED=true
OTEL_SERVICE_NAME=agent_framework
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
```

---

## Métriques Disponibles

### Index Elasticsearch (Direct ES)

**`agent-metrics-llm-*`** (un document par appel LLM) :
| Champ | Type | Description |
|-------|------|-------------|
| `@timestamp` | date | Horodatage |
| `input_tokens` | integer | Tokens d'entrée |
| `output_tokens` | integer | Tokens de sortie |
| `thinking_tokens` | integer | Tokens thinking |
| `duration_ms` | float | Durée appel LLM |
| `time_to_first_token_ms` | float | TTFT (streaming) |
| `model_name` | keyword | Modèle |
| `session_id` | keyword | Session |
| `tool_call_count` | integer | Appels d'outils |

**`agent-metrics-api-*`** (un document par requête API) :
| Champ | Type | Description |
|-------|------|-------------|
| `@timestamp` | date | Horodatage |
| `endpoint` | keyword | Endpoint (ex: `/message`) |
| `total_api_duration_ms` | float | Durée totale |
| `llm_call_count` | integer | Nombre d'appels LLM |
| `session_id` | keyword | Session |
| `is_streaming` | boolean | Streaming activé |

### Métriques Prometheus (OTel)

| Métrique | Type |
|----------|------|
| `agent_framework_llm_tokens_input_total` | Counter |
| `agent_framework_llm_tokens_output_total` | Counter |
| `agent_framework_llm_request_duration_milliseconds` | Histogram |
| `agent_framework_http_request_duration_milliseconds` | Histogram |

---

## Architecture Alternative : Elastic APM Native

Si vous utilisez déjà Elastic Stack, vous pouvez envoyer les données OTel directement à APM Server (sans OTel Collector).

```
Agent Framework ──OTLP──► APM Server (8200) ──► Elasticsearch ──► Kibana APM UI
```

### Configuration

```bash
OTEL_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:8200
```

### Avantages

- ML/AIOps intégré (anomaly detection, correlations)
- Service Map automatique
- Moins de composants à maintenir

### Inconvénients

- Vendor lock-in Elastic
- Licence payante pour fonctionnalités avancées

---

## Architecture Alternative : Stack OTel Complet

Pour une observabilité complète avec traces, métriques et logs :

```bash
docker compose -f docker-compose.observability.yml up -d
```

Composants : OTel Collector + Prometheus + Jaeger + Grafana + Elasticsearch

---

## Déploiement Production

### Considérations

- **HA** : OTel Collector 2-3 replicas, Prometheus avec Thanos
- **Rétention** : Traces 7-14j, Métriques 15-30j, Logs 30-90j
- **Sécurité** : TLS entre composants, auth Grafana (LDAP/OAuth)

---

## Troubleshooting

| Problème | Solution |
|----------|----------|
| Pas de données Kibana | Vérifier `METRICS_ES_LOGGING_ENABLED=true` |
| Pas de métriques Grafana | Vérifier OTel Collector + Prometheus |
| Index ES non créés | Les templates sont créés au premier appel LLM |

### Vérifications

```bash
# Indices ES
curl -s "http://localhost:9200/_cat/indices/agent-metrics-*?v"

# OTel Collector health
curl http://localhost:13133

# Prometheus metrics
curl http://localhost:8889/metrics | grep agent_framework
```
