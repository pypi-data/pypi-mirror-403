"""Templates for brawny init command."""

import importlib.resources as resources

PYPROJECT_TEMPLATE = """\
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{project_name}"
version = "0.1.0"
description = "brawny keeper project"
requires-python = ">=3.10"
dependencies = ["brawny>=0.1.0"]

[tool.setuptools.packages.find]
where = ["."]
include = ["{package_name}*"]
"""

CONFIG_TEMPLATE = """\
# brawny configuration
# See: https://github.com/yearn/brawny#configuration

# Core settings
database_url: sqlite:///data/brawny.db
rpc:
  groups:
    primary:
      endpoints:
        - ${{RPC_URL}}
  defaults:
    read: primary
    broadcast: primary
chain_id: 1

# Keystore configuration
# Options: "file" (preferred) or "env" (least preferred)
keystore_type: file
keystore_path: ~/.brawny/keys

# SQLite requires worker_count: 1 (single runner only).
worker_count: 1

# Prometheus metrics port (default: 9091)
# metrics_port: 9091

# Telegram alerts (optional)
# telegram:
#   bot_token: ${{TELEGRAM_BOT_TOKEN}}
#   chats:
#     admin_alerts: "-1001234567890"
#     public_alerts: "-1009876543210"
#   admin: ["admin_alerts"]
#   public: ["public_alerts"]
#   default: ["public_alerts"]
#   rate_limits:
#     public: "1/min"
#   parse_mode: "Markdown"
#   health_cooldown_seconds: 1800

# HTTP (optional, for job code)
# http:
#   allowed_domains:
#     - "api.coingecko.com"
#     - "*.githubusercontent.com"
#   connect_timeout_seconds: 5
#   read_timeout_seconds: 10
#   max_retries: 2

# Debug-only settings (optional, default false)
# debug:
#   allow_console: false

# Advanced settings (optional)
# advanced:
#   poll_interval_seconds: 1.0
#   reorg_depth: 32
#   default_deadline_seconds: 3600
"""

ENV_EXAMPLE_TEMPLATE = """\
# RPC endpoint (required)
RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY

# Keystore password (file keystore mode)
# BRAWNY_KEYSTORE_PASSWORD_WORKER=your-password
# Then import the key:
# brawny accounts import --name worker --private-key 0x...

# Telegram alerts (optional)
# TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
"""

GITIGNORE_TEMPLATE = """\
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
.env
.venv
env/
venv/
ENV/

# brawny
data/
*.db
*.db-journal

# IDE
.idea/
.vscode/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
"""

INIT_JOBS_TEMPLATE = '"""Job definitions - auto-discovered from ./jobs."""\n'

AGENTS_TEMPLATE = resources.files("brawny").joinpath("assets/AGENTS.md").read_text(encoding="utf-8")

EXAMPLES_TEMPLATE = '''\
"""Example job patterns - NOT registered.

These are reference implementations. To use them:
1. Copy the class to a new file (e.g., my_job.py)
2. Add @job decorator
3. Customize the implementation

Delete this file when you no longer need it.
"""
from brawny import Job, Contract, trigger, kv

# Note: No @job decorator - these are templates only


class MonitorOnlyJob(Job):
    """Monitor-only job - alerts without transactions.

    Use cases:
    - Price deviation alerts
    - Health check monitoring
    - Threshold breach notifications

    Outcome:
    - Creates: Trigger only (no intent, no transaction)
    - Alerts: on_trigger only
    """

    job_id = "monitor_example"
    name = "Monitor Example"
    check_interval_blocks = 10

    def __init__(self, oracle_address: str, threshold_percent: float = 5.0):
        self.oracle_address = oracle_address
        self.threshold_percent = threshold_percent

    def check(self, ctx):
        """Check if condition is met.

        Returns:
            Trigger with tx_required=False, or None
        """
        oracle = Contract(self.oracle_address)
        price = oracle.latestAnswer() / 1e8

        last_price = kv.get("last_price")
        if last_price is not None:
            change_pct = abs(price - last_price) / last_price * 100
            if change_pct >= self.threshold_percent:
                kv.set("last_price", price)
                return trigger(
                    reason=f"Price changed {change_pct:.2f}%",
                    data={
                        "old_price": last_price,
                        "new_price": price,
                        "change_percent": change_pct,
                    },
                    tx_required=False,  # No transaction needed
                )

        kv.set("last_price", price)
        return None

    def on_trigger(self, ctx):
        """Send alert when monitor triggers."""
        data = ctx.trigger.data
        ctx.alert(
            f"Price alert: {data['old_price']:.2f} -> {data['new_price']:.2f}\\n"
            f"Change: {data['change_percent']:.2f}%"
        )
'''

# Monitoring stack templates
DOCKER_COMPOSE_MONITORING_TEMPLATE = """\
# Production-friendly Prometheus + Grafana stack for Brawny
# Usage: docker-compose -f monitoring/docker-compose.yml up -d
#
# Access:
#   Prometheus: http://localhost:9090
#   Grafana:    http://localhost:3000 (admin / admin)
#
# For production, set GF_ADMIN_PASSWORD in environment or .env

services:
  prometheus:
    image: prom/prometheus:v2.48.0
    container_name: brawny-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
    extra_hosts:
      - "host.docker.internal:host-gateway"
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost:9090/-/ready"]
      interval: 10s
      timeout: 3s
      retries: 3
    restart: unless-stopped

  grafana:
    image: grafana/grafana:10.2.3
    container_name: brawny-grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=${{GF_ADMIN_PASSWORD:-admin}}
      - GF_USERS_ALLOW_SIGN_UP=false
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost:3000/api/health"]
      interval: 10s
      timeout: 3s
      retries: 3
    restart: unless-stopped

volumes:
  prometheus_data:
  grafana_data:
"""

PROMETHEUS_CONFIG_TEMPLATE = """\
# Prometheus configuration for Brawny
#
# Default: scrapes metrics from Brawny on host at localhost:9091
#
# Troubleshooting:
#   macOS/Windows: host.docker.internal:9091 works out of the box
#   Linux: if target is down, replace with your host IP (e.g., 172.17.0.1:9091)
#          or run Brawny in the same Docker network

global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'brawny'
    static_configs:
      - targets: ['host.docker.internal:9091']
"""

GRAFANA_DATASOURCE_TEMPLATE = """\
# Auto-provision Prometheus datasource
# UID is stable so dashboards can reference it reliably
apiVersion: 1

datasources:
  - name: Prometheus
    uid: prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
"""

GRAFANA_DASHBOARDS_PROVIDER_TEMPLATE = """\
# Auto-provision dashboards from this directory
apiVersion: 1

providers:
  - name: 'brawny'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    editable: true
    options:
      path: /etc/grafana/provisioning/dashboards
"""

GRAFANA_DASHBOARD_TEMPLATE = """\
{
  "annotations": {
    "list": []
  },
  "editable": true,
  "fiscalYearStartMonth": 0,
  "graphTooltip": 0,
  "id": null,
  "links": [],
  "panels": [
    {
      "gridPos": {
        "h": 1,
        "w": 24,
        "x": 0,
        "y": 0
      },
      "id": 1,
      "title": "Status",
      "type": "row"
    },
    {
      "datasource": {
        "type": "prometheus",
        "uid": "prometheus"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "thresholds"
          },
          "mappings": [
            {
              "type": "value",
              "options": {
                "0": {
                  "text": "false"
                },
                "1": {
                  "text": "true"
                }
              }
            }
          ],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "red",
                "value": null
              },
              {
                "color": "green",
                "value": 1
              }
            ]
          },
          "unit": "short"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 4,
        "w": 4,
        "x": 0,
        "y": 1
      },
      "id": 2,
      "options": {
        "colorMode": "background",
        "graphMode": "none",
        "justifyMode": "auto",
        "orientation": "auto",
        "reduceOptions": {
          "calcs": [
            "lastNotNull"
          ],
          "fields": "",
          "values": false
        },
        "textMode": "auto"
      },
      "pluginVersion": "10.2.3",
      "targets": [
        {
          "datasource": {
            "type": "prometheus",
            "uid": "prometheus"
          },
          "expr": "max(up{job=\"brawny\"})",
          "refId": "A"
        }
      ],
      "title": "Brawny Up",
      "type": "stat"
    },
    {
      "datasource": {
        "type": "prometheus",
        "uid": "prometheus"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "thresholds"
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "yellow",
                "value": 120
              },
              {
                "color": "red",
                "value": 300
              }
            ]
          },
          "unit": "s"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 4,
        "w": 4,
        "x": 4,
        "y": 1
      },
      "id": 3,
      "options": {
        "colorMode": "background",
        "graphMode": "none",
        "justifyMode": "auto",
        "orientation": "auto",
        "reduceOptions": {
          "calcs": [
            "lastNotNull"
          ],
          "fields": "",
          "values": false
        },
        "textMode": "auto"
      },
      "pluginVersion": "10.2.3",
      "targets": [
        {
          "datasource": {
            "type": "prometheus",
            "uid": "prometheus"
          },
          "expr": "max(brawny_oldest_pending_intent_age_seconds)",
          "refId": "A"
        }
      ],
      "title": "Oldest Pending Intent",
      "type": "stat"
    },
    {
      "datasource": {
        "type": "prometheus",
        "uid": "prometheus"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "thresholds"
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "yellow",
                "value": 10
              },
              {
                "color": "red",
                "value": 50
              }
            ]
          },
          "unit": "short"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 4,
        "w": 4,
        "x": 8,
        "y": 1
      },
      "id": 4,
      "options": {
        "colorMode": "background",
        "graphMode": "none",
        "justifyMode": "auto",
        "orientation": "auto",
        "reduceOptions": {
          "calcs": [
            "lastNotNull"
          ],
          "fields": "",
          "values": false
        },
        "textMode": "auto"
      },
      "pluginVersion": "10.2.3",
      "targets": [
        {
          "datasource": {
            "type": "prometheus",
            "uid": "prometheus"
          },
          "expr": "sum(brawny_pending_intents) or vector(0)",
          "refId": "A"
        }
      ],
      "title": "Pending Intents",
      "type": "stat"
    },
    {
      "datasource": {
        "type": "prometheus",
        "uid": "prometheus"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "thresholds"
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              }
            ]
          },
          "unit": "short"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 4,
        "w": 4,
        "x": 16,
        "y": 1
      },
      "id": 6,
      "options": {
        "colorMode": "value",
        "graphMode": "area",
        "justifyMode": "auto",
        "orientation": "auto",
        "reduceOptions": {
          "calcs": [
            "lastNotNull"
          ],
          "fields": "",
          "values": false
        },
        "textMode": "auto"
      },
      "pluginVersion": "10.2.3",
      "targets": [
        {
          "datasource": {
            "type": "prometheus",
            "uid": "prometheus"
          },
          "expr": "sum(brawny_blocks_processed_total) or vector(0)",
          "refId": "A"
        }
      ],
      "title": "Blocks Processed",
      "type": "stat"
    },
    {
      "datasource": {
        "type": "prometheus",
        "uid": "prometheus"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "thresholds"
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              }
            ]
          },
          "unit": "short"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 4,
        "w": 4,
        "x": 20,
        "y": 1
      },
      "id": 7,
      "options": {
        "colorMode": "value",
        "graphMode": "area",
        "justifyMode": "auto",
        "orientation": "auto",
        "reduceOptions": {
          "calcs": [
            "lastNotNull"
          ],
          "fields": "",
          "values": false
        },
        "textMode": "auto"
      },
      "pluginVersion": "10.2.3",
      "targets": [
        {
          "datasource": {
            "type": "prometheus",
            "uid": "prometheus"
          },
          "expr": "sum(brawny_tx_confirmed_total) or vector(0)",
          "refId": "A"
        }
      ],
      "title": "TX Confirmed",
      "type": "stat"
    },
    {
      "gridPos": {
        "h": 1,
        "w": 24,
        "x": 0,
        "y": 5
      },
      "id": 10,
      "title": "Activity",
      "type": "row"
    },
    {
      "datasource": {
        "type": "prometheus",
        "uid": "prometheus"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisBorderShow": false,
            "axisCenteredZero": false,
            "axisColorMode": "text",
            "axisLabel": "",
            "axisPlacement": "auto",
            "barAlignment": 0,
            "drawStyle": "line",
            "fillOpacity": 10,
            "gradientMode": "none",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "insertNulls": false,
            "lineInterpolation": "linear",
            "lineWidth": 1,
            "pointSize": 5,
            "scaleDistribution": {
              "type": "linear"
            },
            "showPoints": "never",
            "spanNulls": false,
            "stacking": {
              "group": "A",
              "mode": "none"
            },
            "thresholdsStyle": {
              "mode": "line"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "yellow",
                "value": 120
              },
              {
                "color": "red",
                "value": 300
              }
            ]
          },
          "unit": "s"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 0,
        "y": 6
      },
      "id": 11,
      "options": {
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom",
          "showLegend": true
        },
        "tooltip": {
          "mode": "multi",
          "sort": "none"
        }
      },
      "pluginVersion": "10.2.3",
      "targets": [
        {
          "datasource": {
            "type": "prometheus",
            "uid": "prometheus"
          },
          "expr": "max(brawny_block_processing_lag_seconds)",
          "legendFormat": "seconds behind chain head",
          "refId": "A"
        }
      ],
      "title": "Block Processing Lag",
      "type": "timeseries"
    },
    {
      "datasource": {
        "type": "prometheus",
        "uid": "prometheus"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisBorderShow": false,
            "axisCenteredZero": false,
            "axisColorMode": "text",
            "axisLabel": "",
            "axisPlacement": "auto",
            "barAlignment": 0,
            "drawStyle": "line",
            "fillOpacity": 10,
            "gradientMode": "none",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "insertNulls": false,
            "lineInterpolation": "linear",
            "lineWidth": 1,
            "pointSize": 5,
            "scaleDistribution": {
              "type": "linear"
            },
            "showPoints": "never",
            "spanNulls": false,
            "stacking": {
              "group": "A",
              "mode": "none"
            },
            "thresholdsStyle": {
              "mode": "line"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "yellow",
                "value": 120
              },
              {
                "color": "red",
                "value": 300
              }
            ]
          },
          "unit": "s"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 12,
        "y": 6
      },
      "id": 12,
      "options": {
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom",
          "showLegend": true
        },
        "tooltip": {
          "mode": "multi",
          "sort": "none"
        }
      },
      "pluginVersion": "10.2.3",
      "targets": [
        {
          "datasource": {
            "type": "prometheus",
            "uid": "prometheus"
          },
          "expr": "time() - max(brawny_last_tx_confirmed_timestamp)",
          "legendFormat": "seconds since last TX",
          "refId": "B"
        },
        {
          "datasource": {
            "type": "prometheus",
            "uid": "prometheus"
          },
          "expr": "time() - max(brawny_last_intent_created_timestamp)",
          "legendFormat": "seconds since last intent",
          "refId": "C"
        }
      ],
      "title": "Activity Staleness",
      "type": "timeseries"
    },
    {
      "gridPos": {
        "h": 1,
        "w": 24,
        "x": 0,
        "y": 14
      },
      "id": 20,
      "title": "Transactions",
      "type": "row"
    },
    {
      "datasource": {
        "type": "prometheus",
        "uid": "prometheus"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisBorderShow": false,
            "axisCenteredZero": false,
            "axisColorMode": "text",
            "axisLabel": "",
            "axisPlacement": "auto",
            "barAlignment": 0,
            "drawStyle": "line",
            "fillOpacity": 10,
            "gradientMode": "none",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "insertNulls": false,
            "lineInterpolation": "linear",
            "lineWidth": 1,
            "pointSize": 5,
            "scaleDistribution": {
              "type": "linear"
            },
            "showPoints": "never",
            "spanNulls": false,
            "stacking": {
              "group": "A",
              "mode": "none"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              }
            ]
          },
          "unit": "short"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 0,
        "y": 15
      },
      "id": 21,
      "options": {
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom",
          "showLegend": true
        },
        "tooltip": {
          "mode": "multi",
          "sort": "none"
        }
      },
      "pluginVersion": "10.2.3",
      "targets": [
        {
          "datasource": {
            "type": "prometheus",
            "uid": "prometheus"
          },
          "expr": "sum(rate(brawny_tx_broadcast_total[5m])) * 60 or vector(0)",
          "legendFormat": "broadcast/min",
          "refId": "A"
        },
        {
          "datasource": {
            "type": "prometheus",
            "uid": "prometheus"
          },
          "expr": "sum(rate(brawny_tx_confirmed_total[5m])) * 60 or vector(0)",
          "legendFormat": "confirmed/min",
          "refId": "B"
        },
        {
          "datasource": {
            "type": "prometheus",
            "uid": "prometheus"
          },
          "expr": "sum(rate(brawny_tx_failed_total[5m])) * 60 or vector(0)",
          "legendFormat": "failed/min",
          "refId": "C"
        }
      ],
      "title": "TX Throughput",
      "type": "timeseries"
    },
    {
      "datasource": {
        "type": "prometheus",
        "uid": "prometheus"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisBorderShow": false,
            "axisCenteredZero": false,
            "axisColorMode": "text",
            "axisLabel": "",
            "axisPlacement": "auto",
            "barAlignment": 0,
            "drawStyle": "line",
            "fillOpacity": 10,
            "gradientMode": "none",
            "hideFrom": {
              "legend": false,
              "tooltip": false,
              "viz": false
            },
            "insertNulls": false,
            "lineInterpolation": "linear",
            "lineWidth": 1,
            "pointSize": 5,
            "scaleDistribution": {
              "type": "linear"
            },
            "showPoints": "never",
            "spanNulls": false,
            "stacking": {
              "group": "A",
              "mode": "none"
            },
            "thresholdsStyle": {
              "mode": "line"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "yellow",
                "value": 120
              },
              {
                "color": "red",
                "value": 300
              }
            ]
          },
          "unit": "s"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 12,
        "y": 15
      },
      "id": 22,
      "options": {
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom",
          "showLegend": true
        },
        "tooltip": {
          "mode": "multi",
          "sort": "none"
        }
      },
      "pluginVersion": "10.2.3",
      "targets": [
        {
          "datasource": {
            "type": "prometheus",
            "uid": "prometheus"
          },
          "expr": "max(brawny_oldest_pending_intent_age_seconds)",
          "legendFormat": "oldest pending age",
          "refId": "A"
        }
      ],
      "title": "Oldest Pending Intent Age",
      "type": "timeseries"
    }
  ],
  "refresh": "10s",
  "schemaVersion": 39,
  "tags": [
    "brawny"
  ],
  "templating": {
    "list": []
  },
  "time": {
    "from": "now-1h",
    "to": "now"
  },
  "timepicker": {},
  "timezone": "browser",
  "title": "Brawny Overview",
  "uid": "brawny-overview",
  "version": 1,
  "weekStart": ""
}
"""
