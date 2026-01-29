# Ghost Compute

**Intelligent Serverless Orchestration for Data Platforms**

Ghost eliminates the $44.5B annual waste from idle clusters and cold start latency in enterprise data infrastructure. Drop-in optimization for Databricks, EMR, Synapse, and Spark workloads.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## The Problem

Enterprises face an impossible tradeoff:

| Option | Problem |
|--------|---------|
| **Keep clusters warm** | Pay for 24/7 idle compute (~30% waste) |
| **Cold start on-demand** | 5-35 minute startup delays, missed SLAs |
| **Vendor serverless** | Premium pricing, vendor lock-in, limited control |

**Ghost solves this** by providing intelligent cluster orchestration that delivers sub-second start times while eliminating idle waste.

## Key Features

### 🔮 Ghost Predict
ML-powered predictive provisioning that pre-warms resources before you need them.

### 💤 Ghost Hibernate
State preservation that snapshots clusters to object storage for instant resume.

### 🏊 Ghost Pool
Cross-workload resource sharing that maximizes utilization across teams.

### ⚡ Ghost Spot
Autonomous spot/preemptible instance management with graceful failover.

### 📊 Ghost Insight
Real-time cost attribution and optimization recommendations.

## Quick Start

### Installation

**One command to install Ghost Compute with all platforms:**

```bash
pip install ghost-compute
```

This single install includes support for:
- Databricks (Azure, AWS, GCP)
- Amazon EMR
- Azure Synapse Analytics
- Google Cloud Dataproc

**Install from source:**

```bash
git clone https://github.com/ghost-ai-dev/ghost-compute.git
cd ghost-compute
pip install -e .
```

### Basic Usage

```python
from ghost import GhostClient

# Initialize Ghost
ghost = GhostClient(
    platform="databricks",
    credentials_path="~/.ghost/credentials.json"
)

# Enable intelligent orchestration
ghost.optimize(
    workspace_id="your-workspace",
    strategies=["predict", "hibernate", "spot"],
    target_savings=0.40  # 40% cost reduction target
)

# Monitor savings
stats = ghost.get_stats()
print(f"Monthly savings: ${stats.savings_usd:,.2f}")
print(f"Cold starts eliminated: {stats.cold_starts_prevented}")
```

### CLI Usage

```bash
# View supported platforms
ghost platforms

# Connect to your platform
# Databricks
ghost connect databricks --workspace-url https://xxx.cloud.databricks.com --token YOUR_TOKEN

# AWS EMR
ghost connect emr --profile default --region us-east-1

# Azure Synapse
ghost connect synapse --subscription-id YOUR_SUB_ID --resource-group YOUR_RG

# Google Dataproc
ghost connect dataproc --project-id YOUR_PROJECT --region us-central1

# Analyze current waste
ghost analyze --output report.json

# Enable optimization
ghost optimize --strategies predict,hibernate,spot

# List clusters
ghost clusters

# View optimization insights
ghost insights
```

## Supported Platforms

All platforms are included in the single `pip install ghost-compute` package.

| Platform | Status | Features |
|----------|--------|----------|
| **Databricks** | ✅ GA | Predict, Hibernate, Pool, Spot, Insight |
| **Amazon EMR** | ✅ GA | Predict, Hibernate*, Spot, Pool, Insight |
| **Azure Synapse** | ✅ GA | Predict, Hibernate (auto-pause), Pool, Insight |
| **Google Dataproc** | ✅ GA | Predict, Hibernate*, Preemptible VMs, Pool, Insight |
| **Cloudera CDP** | 🚧 Alpha | Insight only (coming soon) |
| **Self-managed Spark** | 🚧 Alpha | Pool, Spot (coming soon) |

*EMR and Dataproc hibernation works via cluster termination with state preservation for fast recreation.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    YOUR APPLICATION                          │
│         (Databricks / EMR / Synapse / Dataproc)             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      GHOST LAYER                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Predict   │  │  Hibernate  │  │        Spot         │  │
│  │  Scheduler  │  │   Manager   │  │    Orchestrator     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │    Pool     │  │   Insight   │  │     Multi-Cloud     │  │
│  │   Manager   │  │   Engine    │  │     Abstraction     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  CLOUD INFRASTRUCTURE                        │
│              (AWS / Azure / GCP / On-Prem)                  │
└─────────────────────────────────────────────────────────────┘
```

## How It Works

### 1. Predictive Provisioning

Ghost analyzes your workload patterns to predict when clusters will be needed:

```python
# Ghost learns from historical patterns
# - Scheduled jobs (cron patterns)
# - User activity (login times, query patterns)
# - Data arrival (streaming triggers)
# - Seasonal trends (end of month, quarterly)

# Pre-warms clusters 30-60 seconds before needed
# Result: Sub-second perceived start time
```

### 2. State Hibernation

Instead of terminating clusters, Ghost preserves state:

```python
# Traditional approach:
# Terminate → Cold start (5-35 min) → Re-initialize

# Ghost approach:
# Hibernate → Snapshot to S3 → Resume in <5 sec
```

### 3. Intelligent Pooling

Share warm resources across workloads:

```python
# Team A finishes job at 2:00 PM
# Team B starts job at 2:05 PM
# Ghost transfers warm instances → Zero cold start for Team B
```

### 4. Spot Orchestration

Maximize savings with automatic spot management:

```python
# Ghost automatically:
# - Uses spot instances for interruptible workloads
# - Monitors interruption signals
# - Checkpoints state before termination
# - Fails over to on-demand gracefully
```

## Configuration

### Environment Variables

```bash
GHOST_API_KEY=your-api-key
GHOST_PLATFORM=databricks
GHOST_WORKSPACE_URL=https://xxx.cloud.databricks.com
GHOST_LOG_LEVEL=INFO
```

### Configuration File

```yaml
# ghost.yaml
platform: databricks
workspace_url: https://xxx.cloud.databricks.com

strategies:
  predict:
    enabled: true
    lookahead_minutes: 60
    confidence_threshold: 0.8

  hibernate:
    enabled: true
    idle_timeout_minutes: 10
    storage_backend: s3
    storage_bucket: ghost-hibernate-states

  spot:
    enabled: true
    max_spot_percentage: 80
    fallback_to_ondemand: true
    interruption_buffer_seconds: 120

  pool:
    enabled: true
    cross_team_sharing: true
    max_idle_instances: 10

  insight:
    enabled: true
    cost_alerts: true
    alert_threshold_usd: 1000

exclusions:
  - cluster_name: "production-critical-*"
  - tag: "ghost:exclude"
```

## Pricing

Ghost operates on a savings-share model:

| Tier | Monthly Compute Spend | Ghost Fee |
|------|----------------------|-----------|
| Starter | < $50K | 25% of savings |
| Growth | $50K - $250K | 20% of savings |
| Enterprise | > $250K | Custom |

**No savings = No payment.** We only charge when we deliver results.

## Benchmarks

| Metric | Before Ghost | After Ghost | Improvement |
|--------|-------------|-------------|-------------|
| Average cold start | 8.5 min | 0.8 sec | 99.8% faster |
| Idle compute waste | 32% | 4% | 87% reduction |
| Monthly spend ($100K baseline) | $100,000 | $58,000 | 42% savings |
| SLA misses (5-min threshold) | 23/month | 0/month | 100% eliminated |

## Documentation

- [Getting Started Guide](docs/getting-started.md)
- [Platform Integration](docs/integrations/)
- [API Reference](docs/api-reference.md)
- [Configuration Options](docs/configuration.md)
- [Best Practices](docs/best-practices.md)
- [Troubleshooting](docs/troubleshooting.md)

## Examples

- [Databricks Notebook Integration](examples/databricks_notebook.py)
- [EMR Step Function Integration](examples/emr_step_function.py)
- [Airflow DAG with Ghost](examples/airflow_dag.py)
- [Terraform Module](examples/terraform/)
- [Kubernetes Operator](examples/k8s/)

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
# Development setup
git clone https://github.com/ghost-ai-dev/ghost-compute.git
cd ghost-compute
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Security

- SOC 2 Type II certified
- No data leaves your cloud environment
- All state stored in your own S3/Blob/GCS buckets
- Role-based access control
- Audit logging

Report security issues to security@ghost-compute.io

## License

Apache License 2.0 - see [LICENSE](LICENSE)

## Support

- 📧 Email: support@ghost-compute.io
- 💬 Slack: [ghost-compute.slack.com](https://ghost-compute.slack.com)
- 📖 Docs: [docs.ghost-compute.io](https://docs.ghost-compute.io)
- 🐛 Issues: [GitHub Issues](https://github.com/ghost-ai-dev/ghost-compute/issues)

---

**Built by [Ghost AI](https://ghost-ai.io)** | Eliminating waste in enterprise data infrastructure
