import os
import subprocess
from pathlib import Path
import platform
import requests
import json
import shutil
import psutil
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.panel import Panel
from rich.table import Table
from typing import Dict, Any, List, Tuple, Optional
import pytest
import socket
import psycopg
import yaml
from datetime import datetime

class DevEnvSetup:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.venv_path = self.project_root / ".venv"
        self.requirements_file = self.project_root / "requirements_windows.txt"
        self.docker_compose_file = self.project_root / "docker-compose.yml"
        self.console = Console()
        self.monitoring_config_file = self.project_root / "config" / "monitoring.yml"
        self.min_requirements = {
            "python": (3, 9),
            "ram_gb": 8,
            "disk_gb": 10,
            "cpu_cores": 2
        }
        self.tests_dir = self.project_root / "tests"
        self.test_config_file = self.project_root / "pytest.ini"
        self.test_templates = {
            "unit": {
                "agents": self.create_agent_tests,
                "tools": self.create_tool_tests,
                "models": self.create_model_tests,
                "vector_store": self.create_vector_store_tests,
                "knowledge_base": self.create_knowledge_base_tests,
                "monitoring": self.create_monitoring_tests,
            },
            "integration": {
                "database": self.create_db_tests,
                "api": self.create_api_tests,
                "storage": self.create_storage_tests,
                "redis": self.create_redis_tests,
                "qdrant": self.create_qdrant_tests,
                "team_coordination": self.create_team_coordination_tests,
            },
            "e2e": {
                "workflow": self.create_workflow_tests,
                "performance": self.create_performance_tests,
                "deployment": self.create_deployment_tests,
                "security": self.create_security_tests,
                "load": self.create_load_tests,
            }
        }
        self.monitoring_config = {
            "metrics": {
                "enabled": True,
                "port": 9090,
                "path": "/metrics",
                "collectors": [
                    "process",
                    "python",
                    "platform",
                    "agent_performance",
                    "database_connections",
                    "api_requests",
                    "vector_store_operations",
                    "team_coordination",
                    "knowledge_base_access",
                ],
                "custom_metrics": {
                    "agent_response_time": {
                        "type": "Histogram",
                        "description": "Agent response time in seconds",
                        "buckets": [0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
                    },
                    "token_usage": {
                        "type": "Counter",
                        "description": "Total tokens used by model",
                        "labels": ["model_id", "agent_id", "task_type"],
                    },
                    "vector_store_latency": {
                        "type": "Histogram",
                        "description": "Vector store operation latency",
                        "buckets": [0.01, 0.05, 0.1, 0.5, 1.0],
                    },
                    "team_coordination_events": {
                        "type": "Counter",
                        "description": "Team coordination events",
                        "labels": ["event_type", "agent_id", "status"],
                    },
                    "knowledge_base_hits": {
                        "type": "Counter",
                        "description": "Knowledge base access counts",
                        "labels": ["operation", "status", "agent_id"],
                    }
                },
            },
            "logging": {
                "level": "INFO",
                "format": "json",
                "handlers": ["console", "file", "elasticsearch"],
                "file": {
                    "path": "logs/app.log",
                    "max_size": "10MB",
                    "backup_count": 5,
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                },
                "elasticsearch": {
                    "hosts": ["http://localhost:9200"],
                    "index": "aigi3-logs",
                    "flush_interval": 30,
                },
            },
            "tracing": {
                "enabled": True,
                "exporter": "jaeger",
                "host": "localhost",
                "port": 6831,
                "service_name": "aigi3",
                "sample_rate": 1.0,
            },
            "alerting": {
                "enabled": True,
                "providers": ["email", "slack", "prometheus", "teams"],
                "rules": [
                    {
                        "name": "agent_performance",
                "rules": [
                    {
                        "name": "high_latency",
                        "condition": "agent_response_time_seconds > 10",
                        "duration": "5m",
                        "severity": "warning",
                                "channels": ["ops", "dev"],
                                "description": "Agent response time is higher than expected",
                                "runbook_url": "docs/runbooks/high_latency.md",
                                "dashboard": "grafana/d/agent-performance"
                            },
                            {
                                "name": "token_usage_spike",
                                "condition": 'rate(token_usage_total[5m]) > 1000',
                                "duration": "5m",
                                "severity": "warning",
                                "channels": ["ops"],
                                "description": "Unusually high token usage detected",
                                "runbook_url": "docs/runbooks/token_usage.md"
                            }
                        ]
                    },
                    {
                        "name": "system_resources",
                        "rules": [
                            {
                                "name": "memory_usage",
                                "condition": "process_resident_memory_bytes > 1.5e9",
                                "duration": "10m",
                                "severity": "warning",
                                "channels": ["ops"],
                                "description": "High memory usage detected",
                                "runbook_url": "docs/runbooks/memory_usage.md"
                            },
                            {
                                "name": "cpu_usage",
                                "condition": "rate(process_cpu_seconds_total[5m]) > 0.8",
                                "duration": "5m",
                                "severity": "warning",
                                "channels": ["ops"],
                                "description": "High CPU usage detected",
                                "runbook_url": "docs/runbooks/cpu_usage.md"
                            }
                        ]
                    },
                    {
                        "name": "database",
                        "rules": [
                            {
                                "name": "connection_pool",
                                "condition": "database_connections > 80",
                        "duration": "5m",
                        "severity": "critical",
                                "channels": ["ops", "dev"],
                                "description": "Database connection pool near capacity",
                                "runbook_url": "docs/runbooks/db_connections.md"
                            },
                            {
                                "name": "query_latency",
                                "condition": "database_query_duration_seconds > 5",
                                "duration": "5m",
                        "severity": "warning",
                                "channels": ["dev"],
                                "description": "Slow database queries detected",
                                "runbook_url": "docs/runbooks/query_latency.md"
                            }
                        ]
                    },
                    {
                        "name": "vector_store",
                        "rules": [
                            {
                                "name": "indexing_errors",
                                "condition": 'rate(vector_store_operations_total{status="error"}[15m]) > 0.1',
                                "duration": "15m",
                                "severity": "critical",
                                "channels": ["ops"],
                                "description": "Vector store indexing errors detected",
                                "runbook_url": "docs/runbooks/vector_store.md"
                            },
                            {
                                "name": "search_latency",
                                "condition": "vector_store_search_duration_seconds > 1",
                        "duration": "5m",
                        "severity": "warning",
                                "channels": ["dev"],
                                "description": "Slow vector store searches detected",
                                "runbook_url": "docs/runbooks/vector_search.md"
                            }
                        ]
                    }
                ],
                "notification_templates": {
                    "slack": {
                        "warning": {
                            "color": "warning",
                            "blocks": [
                                {
                                    "type": "header",
                                    "text": {
                                        "type": "plain_text",
                                        "text": ":warning: Alert: {alert_name}"
                                    }
                                },
                                {
                                    "type": "section",
                                    "text": {
                                        "type": "mrkdwn",
                                        "text": "*Description:* {description}\n*Condition:* `{condition}`\n*Duration:* {duration}\n*Severity:* {severity}"
                                    }
                                },
                                {
                                    "type": "section",
                                    "text": {
                                        "type": "mrkdwn",
                                        "text": "*Runbook:* <{runbook_url}|View Runbook>\n*Dashboard:* <{dashboard}|View Dashboard>"
                                    }
                                }
                            ]
                        },
                        "critical": {
                            "color": "danger",
                            "blocks": [
                                {
                                    "type": "header",
                                    "text": {
                                        "type": "plain_text",
                                        "text": ":rotating_light: CRITICAL Alert: {alert_name}"
                                    }
                                },
                                {
                                    "type": "section",
                                    "text": {
                                        "type": "mrkdwn",
                                        "text": "*Description:* {description}\n*Condition:* `{condition}`\n*Duration:* {duration}\n*Severity:* {severity}"
                                    }
                                },
                                {
                                    "type": "section",
                                    "text": {
                                        "type": "mrkdwn",
                                        "text": "*Runbook:* <{runbook_url}|View Runbook>\n*Dashboard:* <{dashboard}|View Dashboard>"
                                    }
                                }
                            ]
                        }
                    },
                    "teams": {
                        "warning": {
                            "type": "message",
                            "attachments": [
                                {
                                    "contentType": "application/vnd.microsoft.card.adaptive",
                                    "content": {
                                        "type": "AdaptiveCard",
                                        "body": [
                                            {
                                                "type": "TextBlock",
                                                "text": "⚠️ Warning Alert: {alert_name}",
                                                "weight": "bolder",
                                                "size": "large"
                                            },
                                            {
                                                "type": "FactSet",
                                                "facts": [
                                                    {"title": "Description", "value": "{description}"},
                                                    {"title": "Condition", "value": "{condition}"},
                                                    {"title": "Duration", "value": "{duration}"},
                                                    {"title": "Severity", "value": "{severity}"}
                                                ]
                                            }
                                        ],
                                        "actions": [
                                            {
                                                "type": "Action.OpenUrl",
                                                "title": "View Runbook",
                                                "url": "{runbook_url}"
                                            },
                                            {
                                                "type": "Action.OpenUrl",
                                                "title": "View Dashboard",
                                                "url": "{dashboard}"
                                            }
                                        ]
                                    }
                                }
                            ]
                        }
                    }
                }
            }
        }

        # Add retry mechanisms and circuit breakers
        self.retry_config = {
            "max_attempts": 3,
            "backoff_factor": 2,
            "max_delay": 30
        }

        # Enhanced logging configuration
        self.logging_config = {
            "version": 1,
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "detailed"
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": "logs/app.log",
                    "maxBytes": 10485760,
                    "backupCount": 5
                }
            },
            "formatters": {
                "detailed": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                }
            }
        }

    def check_system_requirements(self) -> Tuple[bool, List[str]]:
        """Check if system meets minimum requirements"""
        issues = []
        try:
            # Check Python version
            current = platform.python_version_tuple()
            if (int(current[0]), int(current[1])) < self.min_requirements["python"]:
                issues.append(f"Python {self.min_requirements['python'][0]}.{self.min_requirements['python'][1]} or higher required")

            # Check RAM
            memory = psutil.virtual_memory()
            ram_gb = memory.total / (1024 * 1024 * 1024)
            if ram_gb < self.min_requirements["ram_gb"]:
                issues.append(f"Minimum {self.min_requirements['ram_gb']}GB RAM required, found {ram_gb:.1f}GB")

            # Check disk space
            disk = psutil.disk_usage(self.project_root)
            free_gb = disk.free / (1024 * 1024 * 1024)
            if free_gb < self.min_requirements["disk_gb"]:
                issues.append(f"Minimum {self.min_requirements['disk_gb']}GB free disk space required, found {free_gb:.1f}GB")

            # Check CPU cores
            cpu_count = psutil.cpu_count(logical=False)
            if cpu_count < self.min_requirements["cpu_cores"]:
                issues.append(f"Minimum {self.min_requirements['cpu_cores']} CPU cores required, found {cpu_count}")

            return len(issues) == 0, issues
        except Exception as e:
            issues.append(f"Error checking system requirements: {str(e)}")
            return False, issues

    def validate_dependencies(self) -> Tuple[bool, List[str]]:
        """Validate required dependencies"""
        issues = []
        try:
            # Check Git
            if not shutil.which("git"):
                issues.append("Git is not installed")

            # Check Docker
            if not self.check_docker_installation():
                issues.append("Docker is not installed or not running")

            # Check Node.js (if needed)
            if not shutil.which("node"):
                issues.append("Node.js is recommended but not installed")

            return len(issues) == 0, issues
        except Exception as e:
            issues.append(f"Error validating dependencies: {str(e)}")
            return False, issues

    def setup_monitoring(self) -> None:
        """Setup monitoring with enhanced alerts"""
        
        # Update monitoring configuration with enhanced alerts
        self.monitoring_config["alerting"] = {
            "enabled": True,
            "providers": ["email", "slack", "prometheus", "teams"],
            "rules": [
                {
                    "name": "agent_performance",
            "rules": [
                {
                    "name": "high_latency",
                    "condition": "agent_response_time_seconds > 10",
                    "duration": "5m",
                    "severity": "warning",
                    "channels": ["ops", "dev"],
                            "description": "Agent response time is higher than expected",
                            "runbook_url": "docs/runbooks/high_latency.md",
                            "dashboard": "grafana/d/agent-performance"
                        },
                        {
                            "name": "token_usage_spike",
                            "condition": 'rate(token_usage_total[5m]) > 1000',
                            "duration": "5m",
                            "severity": "warning",
                            "channels": ["ops"],
                            "description": "Unusually high token usage detected",
                            "runbook_url": "docs/runbooks/token_usage.md"
                        }
                    ]
                },
                {
                    "name": "system_resources",
                    "rules": [
                {
                    "name": "memory_usage",
                            "condition": "process_resident_memory_bytes > 1.5e9",
                    "duration": "10m",
                    "severity": "warning",
                    "channels": ["ops"],
                            "description": "High memory usage detected",
                            "runbook_url": "docs/runbooks/memory_usage.md"
                        },
                        {
                            "name": "cpu_usage",
                            "condition": "rate(process_cpu_seconds_total[5m]) > 0.8",
                            "duration": "5m",
                            "severity": "warning",
                            "channels": ["ops"],
                            "description": "High CPU usage detected",
                            "runbook_url": "docs/runbooks/cpu_usage.md"
                        }
                    ]
                },
                {
                    "name": "database",
                    "rules": [
                        {
                            "name": "connection_pool",
                    "condition": "database_connections > 80",
                    "duration": "5m",
                    "severity": "critical",
                    "channels": ["ops", "dev"],
                            "description": "Database connection pool near capacity",
                            "runbook_url": "docs/runbooks/db_connections.md"
                        },
                        {
                            "name": "query_latency",
                            "condition": "database_query_duration_seconds > 5",
                    "duration": "5m",
                            "severity": "warning",
                            "channels": ["dev"],
                            "description": "Slow database queries detected",
                            "runbook_url": "docs/runbooks/query_latency.md"
                        }
                    ]
                },
                {
                    "name": "vector_store",
                    "rules": [
                        {
                            "name": "indexing_errors",
                            "condition": 'rate(vector_store_operations_total{status="error"}[15m]) > 0.1',
                    "duration": "15m",
                            "severity": "critical",
                            "channels": ["ops"],
                            "description": "Vector store indexing errors detected",
                            "runbook_url": "docs/runbooks/vector_store.md"
                        },
                        {
                            "name": "search_latency",
                            "condition": "vector_store_search_duration_seconds > 1",
                            "duration": "5m",
                    "severity": "warning",
                    "channels": ["dev"],
                            "description": "Slow vector store searches detected",
                            "runbook_url": "docs/runbooks/vector_search.md"
                        }
                    ]
                }
            ],
            "notification_templates": {
                "slack": {
                    "warning": {
                        "color": "warning",
                        "blocks": [
                            {
                                "type": "header",
                                "text": {
                                    "type": "plain_text",
                                    "text": ":warning: Alert: {alert_name}"
                                }
                            },
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": "*Description:* {description}\n*Condition:* `{condition}`\n*Duration:* {duration}\n*Severity:* {severity}"
                                }
                            },
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": "*Runbook:* <{runbook_url}|View Runbook>\n*Dashboard:* <{dashboard}|View Dashboard>"
                                }
                            }
                        ]
                    },
                    "critical": {
                        "color": "danger",
                        "blocks": [
                            {
                                "type": "header",
                                "text": {
                                    "type": "plain_text",
                                    "text": ":rotating_light: CRITICAL Alert: {alert_name}"
                                }
                            },
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": "*Description:* {description}\n*Condition:* `{condition}`\n*Duration:* {duration}\n*Severity:* {severity}"
                                }
                            },
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": "*Runbook:* <{runbook_url}|View Runbook>\n*Dashboard:* <{dashboard}|View Dashboard>"
                                }
                            }
                        ]
                    }
                },
                "teams": {
                    "warning": {
                        "type": "message",
                        "attachments": [
                            {
                                "contentType": "application/vnd.microsoft.card.adaptive",
                                "content": {
                                    "type": "AdaptiveCard",
                                    "body": [
                                        {
                                            "type": "TextBlock",
                                            "text": "⚠️ Warning Alert: {alert_name}",
                                            "weight": "bolder",
                                            "size": "large"
                                        },
                                        {
                                            "type": "FactSet",
                                            "facts": [
                                                {"title": "Description", "value": "{description}"},
                                                {"title": "Condition", "value": "{condition}"},
                                                {"title": "Duration", "value": "{duration}"},
                                                {"title": "Severity", "value": "{severity}"}
                                            ]
                                        }
                                    ],
                                    "actions": [
                                        {
                                            "type": "Action.OpenUrl",
                                            "title": "View Runbook",
                                            "url": "{runbook_url}"
                                        },
                                        {
                                            "type": "Action.OpenUrl",
                                            "title": "View Dashboard",
                                            "url": "{dashboard}"
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                }
            }
        }

        self.monitoring_config.update({
            "ui_metrics": {
                "enabled": True,
                "collectors": [
                    "streamlit_performance",
                    "user_interactions",
                    "response_quality",
                    "conversation_metrics"
                ],
                "dashboards": {
                    "user_experience": {
                        "latency_threshold": 2.0,
                        "error_rate_threshold": 0.01
                    }
                }
            }
        })

    def handle_service_restart(self, target: str) -> None:
        """Handle service restart auto-fix"""
        try:
            service_name = f"{target}-service"
            subprocess.run(["docker-compose", "restart", service_name], check=True)
            self.log_auto_fix(f"Restarted service: {service_name}")
        except Exception as e:
            self.log_auto_fix_error(f"Failed to restart service: {str(e)}")

    def handle_cache_clear(self, target: str) -> None:
        """Handle cache clearing auto-fix"""
        try:
            if target == "vector_store":
                with psycopg.connect(self.get_db_url()) as conn:
                    with conn.cursor() as cur:
                        cur.execute("VACUUM ANALYZE vector_store")
            self.log_auto_fix(f"Cleared cache for: {target}")
        except Exception as e:
            self.log_auto_fix_error(f"Failed to clear cache: {str(e)}")

    def handle_connection_optimization(self, target: str) -> None:
        """Handle database connection optimization"""
        try:
            with psycopg.connect(self.get_db_url()) as conn:
                with conn.cursor() as cur:
                    # Terminate idle connections
                    cur.execute("""
                        SELECT pg_terminate_backend(pid) 
                        FROM pg_stat_activity 
                        WHERE datname = current_database()
                        AND state = 'idle'
                        AND state_change < current_timestamp - INTERVAL '10 minutes'
                    """)
            self.log_auto_fix("Optimized database connections")
        except Exception as e:
            self.log_auto_fix_error(f"Failed to optimize connections: {str(e)}")

    def log_auto_fix(self, message: str) -> None:
        """Log auto-fix action"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "type": "auto_fix",
            "message": message,
            "status": "success"
        }
        self.console.print(f"[green]Auto-fix: {message}")
        self.write_to_log(log_entry)

    def log_auto_fix_error(self, message: str) -> None:
        """Log auto-fix error"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "type": "auto_fix",
            "message": message,
            "status": "error"
        }
        self.console.print(f"[red]Auto-fix Error: {message}")
        self.write_to_log(log_entry)

    def write_to_log(self, entry: Dict[str, Any]) -> None:
        """Write entry to log file"""
        log_file = self.project_root / "logs" / "auto_fix.log"
        log_file.parent.mkdir(exist_ok=True)
        
        with open(log_file, "a") as f:
            json.dump(entry, f)
            f.write("\n")

    def display_system_info(self) -> None:
        """Display system information in a table"""
        table = Table(title="System Information")
        table.add_column("Component", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Python Version", platform.python_version())
        table.add_row("OS", f"{platform.system()} {platform.release()}")
        table.add_row("CPU Cores", str(psutil.cpu_count(logical=False)))
        ram_gb = psutil.virtual_memory().total / (1024 * 1024 * 1024)
        table.add_row("RAM", f"{ram_gb:.1f}GB")
        disk = psutil.disk_usage(self.project_root)
        table.add_row("Free Disk Space", f"{disk.free / (1024**3):.1f}GB")
        
        self.console.print(table)

    def setup_test_environment(self) -> None:
        """Setup testing environment and configuration"""
        try:
            # Create tests directory structure
            test_dirs = [
                "tests/unit",
                "tests/integration",
                "tests/e2e",
                "tests/fixtures",
                "tests/mocks",
            ]
            
            for test_dir in test_dirs:
                (self.project_root / test_dir).mkdir(parents=True, exist_ok=True)

            # Create pytest.ini
            pytest_config = """[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --tb=short
    --cov=aigi3
    --cov-report=term-missing
    --cov-report=html:coverage_report
    --cov-fail-under=80
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
"""
            with open(self.test_config_file, 'w') as f:
                f.write(pytest_config)

            # Create conftest.py
            conftest_content = """import pytest
from typing import Generator
from pathlib import Path

@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    return Path(__file__).parent / "fixtures"

@pytest.fixture(scope="session")
def mock_openai_key() -> str:
    return "sk-mock-key"

@pytest.fixture(scope="session")
def mock_db_url() -> str:
    return "postgresql://test:test@localhost:5432/test_db"
"""
            with open(self.tests_dir / "conftest.py", 'w') as f:
                f.write(conftest_content)

            # Create example test files
            self.create_example_tests()

    def create_example_tests(self) -> None:
        """Create example test files for different test types"""
        
        # Unit test example
        unit_test = """import pytest
from aigi3.agents.example import get_finance_agent

def test_finance_agent_creation():
    agent = get_finance_agent()
    assert agent.name == "Finance Analyst"
    assert agent.agent_id == "finance-analyst"
    assert len(agent.tools) >= 5  # At least 5 tools should be present
"""
        with open(self.tests_dir / "unit" / "test_agents.py", 'w') as f:
            f.write(unit_test)

        # Integration test example
        integration_test = """import pytest
from aigi3.db.session import get_db_session

@pytest.mark.integration
def test_db_connection(mock_db_url):
    session = get_db_session(mock_db_url)
    assert session is not None
    # Add more specific database tests
"""
        with open(self.tests_dir / "integration" / "test_database.py", 'w') as f:
            f.write(integration_test)

        # E2E test example
        e2e_test = """import pytest
from fastapi.testclient import TestClient
from aigi3.api.main import app

@pytest.mark.e2e
def test_api_health_check():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
"""
        with open(self.tests_dir / "e2e" / "test_api.py", 'w') as f:
            f.write(e2e_test)

    def run_tests(self, test_type: Optional[str] = None) -> bool:
        """Run tests with specified type or all tests"""
        try:
            cmd = ["pytest"]
            if test_type:
                cmd.extend(["-m", test_type])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            self.console.print(result.stdout)
            if result.stderr:
                self.console.print("[yellow]Test Warnings:[/yellow]")
                self.console.print(result.stderr)
            
            return result.returncode == 0
        except Exception as e:
            self.console.print(f"[red]Error running tests: {str(e)}[/red]")
            return False

    def setup_dev_environment(self) -> None:
        """Enhanced main setup function with test environment setup"""
        self.console.print(Panel("[bold blue]Setting up AIGI3 Development Environment[/bold blue]"))
        self.display_system_info()

        # System requirements check
        meets_requirements, requirement_issues = self.check_system_requirements()
        if not meets_requirements:
            self.console.print("\n[bold red]System Requirements Issues:[/bold red]")
            for issue in requirement_issues:
                self.console.print(f"[red]- {issue}[/red]")
            if not self.console.input("\nContinue anyway? (y/n): ").lower().startswith('y'):
                return

        # Dependencies check
        deps_ok, dependency_issues = self.validate_dependencies()
        if not deps_ok:
            self.console.print("\n[bold yellow]Dependency Issues:[/bold yellow]")
            for issue in dependency_issues:
                self.console.print(f"[yellow]- {issue}[/yellow]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console,
        ) as progress:
            try:
                # ... (rest of the setup steps with enhanced progress tracking)
                # Previous implementation remains the same
                
                task_id = progress.add_task("Setting up test environment...", total=None)
                self.setup_test_environment()
                progress.update(task_id, completed=True)

                task_id = progress.add_task("Running initial tests...", total=None)
                tests_passed = self.run_tests("unit")  # Run only unit tests initially
                progress.update(task_id, completed=True)

                if not tests_passed:
                    self.console.print("[yellow]Warning: Some initial tests failed[/yellow]")

                self.console.print(Panel("""
[bold green]Development Environment Setup Complete![/bold green]

[bold yellow]Next Steps:[/bold yellow]
1. Update the .env file with your credentials
2. Start Docker Desktop
3. Run 'docker-compose up' to start the services
4. Run 'streamlit run app/Home.py' to start the application

[bold blue]Testing:[/bold blue]
- Run unit tests: pytest -m unit
- Run integration tests: pytest -m integration
- Run e2e tests: pytest -m e2e
- View coverage report: open coverage_report/index.html

[bold blue]Monitoring Endpoints:[/bold blue]
- Metrics: http://localhost:9090/metrics
- Health Check: http://localhost:8080/health
- Logs: logs/app.log
- Profiles: logs/profiles

[bold cyan]Documentation:[/bold cyan]
- API Docs: http://localhost:8000/docs
- Streamlit App: http://localhost:8501
                """))
                
            except Exception as e:
                self.console.print(Panel(f"[red]Error during setup: {str(e)}[/red]", title="Error"))
                raise

    def create_agent_tests(self) -> None:
        """Create unit tests for agents"""
        test_content = """
import pytest
from agents.example import get_finance_agent, get_research_agent, get_productivity_agent, get_example_agent

class TestAgents:
    def test_finance_agent_creation(self):
        agent = get_finance_agent()
        assert agent.name == "Finance Analyst"
        assert len(agent.tools) >= 5
        assert any(isinstance(t, YFinanceTools) for t in agent.tools)

    def test_research_agent_creation(self):
        agent = get_research_agent()
        assert agent.name == "Research Analyst"
        assert len(agent.tools) >= 5
        assert any(isinstance(t, DuckDuckGo) for t in agent.tools)

    def test_productivity_agent_creation(self):
        agent = get_productivity_agent()
        assert agent.name == "Productivity Assistant"
        assert len(agent.tools) >= 5
        assert any(isinstance(t, PythonREPL) for t in agent.tools)

    def test_super_agent_team_coordination(self):
        agent = get_example_agent(debug_mode=True)
        assert len(agent.team) == 3
        assert agent.storage is not None
        assert agent.knowledge is not None
"""
        self.write_test_file("unit/test_agents.py", test_content)

    def create_db_tests(self) -> None:
        """Create integration tests for database"""
        test_content = """
import pytest
from sqlalchemy import create_engine, text
from db.session import get_db_url

class TestDatabase:
    @pytest.fixture(scope="session")
    def db_engine(self):
        return create_engine(get_db_url())

    def test_db_connection(self, db_engine):
        with db_engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

    def test_pgvector_extension(self, db_engine):
        with db_engine.connect() as conn:
            result = conn.execute(text(
                "SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')"
            ))
            assert result.scalar() is True

    def test_knowledge_tables(self, db_engine):
        with db_engine.connect() as conn:
            result = conn.execute(text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'example_agent_knowledge')"
            ))
            assert result.scalar() is True
"""
        self.write_test_file("integration/test_database.py", test_content)

    def create_performance_tests(self) -> None:
        """Create end-to-end performance tests"""
        test_content = """
import pytest
import time
from agents.example import get_example_agent

class TestPerformance:
    @pytest.mark.performance
    def test_agent_response_time(self):
        agent = get_example_agent(debug_mode=True)
        start_time = time.time()
        response = agent.chat("What is the current price of AAPL?")
        end_time = time.time()
        
        assert response is not None
        assert (end_time - start_time) < 10  # Response should be under 10 seconds

    @pytest.mark.performance
    def test_concurrent_requests(self):
        import asyncio
        import aiohttp
        
        async def fetch_health(session, url):
            async with session.get(url) as response:
                return await response.json()
        
        async def test_concurrent():
            async with aiohttp.ClientSession() as session:
                tasks = []
                for _ in range(10):
                    task = fetch_health(session, "http://localhost:8000/health")
                    tasks.append(task)
                
                responses = await asyncio.gather(*tasks)
                assert all(r["status"] == "healthy" for r in responses)
        
        asyncio.run(test_concurrent())
"""
        self.write_test_file("e2e/test_performance.py", test_content)

    def create_vector_store_tests(self) -> None:
        """Create tests for vector store functionality"""
        test_content = """
import pytest
from phi.vectordb.pgvector import PgVector, SearchType
from phi.knowledge.agent import AgentKnowledge

class TestVectorStore:
    @pytest.fixture
    def vector_db(self):
        return PgVector(
            table_name="test_knowledge",
            db_url="postgresql://ai:ai@localhost:5432/ai",
            search_type=SearchType.hybrid
        )

    def test_vector_storage(self, vector_db):
        # Test document storage
        docs = [
            {"text": "Test document 1", "metadata": {"source": "test"}},
            {"text": "Test document 2", "metadata": {"source": "test"}}
        ]
        vector_db.add_texts([d["text"] for d in docs])
        
        # Test similarity search
        results = vector_db.similarity_search("test", k=2)
        assert len(results) == 2
        
        # Test hybrid search
        results = vector_db.hybrid_search("test", k=2)
        assert len(results) == 2
"""
        self.write_test_file("unit/test_vector_store.py", test_content)

    def create_load_tests(self) -> None:
        """Create load testing suite"""
        test_content = """
import pytest
import asyncio
import aiohttp
from locust import HttpUser, task, between

class LoadTest(HttpUser):
    wait_time = between(1, 2)
    
    @task
    def test_agent_chat(self):
        payload = {
            "message": "What is the current price of AAPL?",
            "session_id": "test_session",
            "stream": False
        }
        with self.client.post("/chat", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")

    @task
    def test_knowledge_search(self):
        with self.client.get("/knowledge/search?query=finance", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")
"""
        self.write_test_file("e2e/test_load.py", test_content)

    def create_security_tests(self) -> None:
        """Create security testing suite"""
        test_content = """
import pytest
import jwt
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from api.main import app
from api.security import create_access_token

class TestSecurity:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_unauthorized_access(self, client):
        response = client.get("/api/protected")
        assert response.status_code == 401

    def test_invalid_token(self, client):
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/protected", headers=headers)
        assert response.status_code == 401

    def test_token_expiration(self, client):
        # Create an expired token
        expired_token = create_access_token(
            data={"sub": "test@example.com"},
            expires_delta=timedelta(minutes=-1)
        )
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/protected", headers=headers)
        assert response.status_code == 401

    def test_sql_injection(self, client):
        payload = {"username": "' OR '1'='1"}
        response = client.post("/api/login", json=payload)
        assert response.status_code != 200
"""
        self.write_test_file("e2e/test_security.py", test_content)

    def create_redis_tests(self) -> None:
        """Create integration tests for Redis"""
        test_content = """
import pytest
from redis import Redis
from db.session import get_redis_url

class TestRedis:
    @pytest.fixture
    def redis_client(self):
        return Redis.from_url(get_redis_url())

    def test_redis_connection(self, redis_client):
        assert redis_client.ping() is True
"""
        self.write_test_file("integration/test_redis.py", test_content)

    def create_qdrant_tests(self) -> None:
        """Create integration tests for Qdrant"""
        test_content = """
import pytest
from qdrant_client import QdrantClient
from db.session import get_qdrant_url

class TestQdrant:
    @pytest.fixture
    def qdrant_client(self):
        return QdrantClient(url=get_qdrant_url())

    def test_qdrant_connection(self, qdrant_client):
        assert qdrant_client.get_collections() is not None
"""
        self.write_test_file("integration/test_qdrant.py", test_content)

    def create_team_coordination_tests(self) -> None:
        """Create integration tests for team coordination"""
        test_content = """
import pytest
from typing import Generator
from pathlib import Path

@pytest.fixture(scope="session")
def team_coordination_data() -> Generator[List[str], None, None]:
    return ["team1", "team2", "team3"]

class TestTeamCoordination:
    @pytest.mark.integration
    def test_team_coordination(self, team_coordination_data):
        # Add more specific team coordination tests
"""
        self.write_test_file("integration/test_team_coordination.py", test_content)

    def create_deployment_tests(self) -> None:
        """Create end-to-end deployment tests"""
        test_content = """
import pytest
from fastapi.testclient import TestClient
from aigi3.api.main import app

@pytest.mark.e2e
def test_deployment(client):
    # Add more specific deployment tests
"""
        self.write_test_file("e2e/test_deployment.py", test_content)

    def create_security_tests(self) -> None:
        """Create security testing suite"""
        test_content = """
import pytest
from fastapi.testclient import TestClient
from aigi3.api.main import app

@pytest.mark.e2e
def test_security(client):
    # Add more specific security tests
"""
        self.write_test_file("e2e/test_security.py", test_content)

    def create_load_tests(self) -> None:
        """Create load testing suite"""
        test_content = """
import pytest
from fastapi.testclient import TestClient
from aigi3.api.main import app

@pytest.mark.e2e
def test_load(client):
    # Add more specific load tests
"""
        self.write_test_file("e2e/test_load.py", test_content)

    def validate_configuration(self) -> Tuple[bool, List[str]]:
        """Validate the entire configuration"""
        issues = []
        
        # Check environment variables
        required_vars = ["OPENAI_API_KEY", "PHI_API_KEY"]
        for var in required_vars:
            if not os.getenv(var):
                issues.append(f"Missing environment variable: {var}")

        # Check Docker Compose configuration
        if not self.docker_compose_file.exists():
            issues.append("Missing docker-compose.yml file")
        
        # Check database configuration
        db_config = {
            "DB_HOST": "localhost",
            "DB_PORT": "5432",
            "DB_USER": "ai",
            "DB_PASSWORD": "ai",
            "DB_DATABASE": "ai",
        }
        for key, value in db_config.items():
            if not os.getenv(key, value):
                issues.append(f"Missing database configuration: {key}")

        return len(issues) == 0, issues

    def validate_deployment(self) -> Tuple[bool, List[str], Dict[str, str]]:
        """Enhanced deployment validation with comprehensive checks and fix suggestions"""
        issues = []
        fixes = {}

        # Docker Environment Checks
        try:
            docker_info = subprocess.run(["docker", "info"], check=True, capture_output=True, text=True)
            if "Server Version" not in docker_info.stdout:
                issues.append("Docker server not running properly")
                fixes["docker_server"] = "Start Docker Desktop and wait for it to initialize completely"
                
            # Check Docker resources
            if platform.system() == "Windows":
                try:
                    wsl_memory = subprocess.run(["wsl", "free", "-g"], capture_output=True, text=True)
                    if not wsl_memory.stdout or int(wsl_memory.stdout.split()[1]) < 8:
                        issues.append("Docker/WSL memory allocation insufficient")
                        fixes["docker_memory"] = "Open Docker Desktop > Settings > Resources > Advanced and increase memory to at least 8GB"
                except subprocess.CalledProcessError:
                    issues.append("WSL not properly configured")
                    fixes["wsl_config"] = "Run 'wsl --install' in PowerShell as administrator"
        except subprocess.CalledProcessError:
            issues.append("Docker is not running or not installed properly")
            fixes["docker_install"] = "Download and install Docker Desktop from https://www.docker.com/products/docker-desktop"

        # Service Health Checks
        services = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "check_cmd": ["pg_isready", "-h", "localhost", "-p", "5432"],
                "fix": "docker-compose up -d db",
                "verify_cmd": "SELECT version(), current_database()",
            },
            "redis": {
                "host": "localhost",
                "port": 6379,
                "check_cmd": ["redis-cli", "ping"],
                "fix": "docker-compose up -d redis",
                "verify_cmd": "PING",
            },
            "qdrant": {
                "host": "localhost",
                "port": 6333,
                "url": "http://localhost:6333/health",
                "fix": "docker-compose up -d qdrant",
            },
            "streamlit": {
                "host": "localhost",
                "port": 8501,
                "url": "http://localhost:8501/health",
                "fix": "docker-compose up -d streamlit",
            },
            "fastapi": {
                "host": "localhost",
                "port": 8000,
                "url": "http://localhost:8000/health",
                "fix": "docker-compose up -d api",
            },
        }
        
        for service_name, config in services.items():
            try:
                # Basic connection check
                with socket.create_connection((config["host"], config["port"]), timeout=5):
                    pass
                    
                # Service-specific health check
                if "url" in config:
                    response = requests.get(config["url"], timeout=5)
                    if response.status_code != 200:
                        issues.append(f"{service_name} health check failed with status {response.status_code}")
                        fixes[f"{service_name}_health"] = config["fix"]
                elif "check_cmd" in config:
                    result = subprocess.run(config["check_cmd"], capture_output=True, timeout=5)
                    if result.returncode != 0:
                        issues.append(f"{service_name} health check command failed")
                        fixes[f"{service_name}_health"] = config["fix"]
                        
                # Additional service verification
                if "verify_cmd" in config:
                    if service_name == "database":
                        with psycopg.connect(self.get_db_url()) as conn:
                            with conn.cursor() as cur:
                                cur.execute(config["verify_cmd"])
                                if not cur.fetchone():
                                    issues.append(f"{service_name} verification failed")
                                    fixes[f"{service_name}_verify"] = "Check database logs: docker-compose logs db"
                    elif service_name == "redis":
                        redis_result = subprocess.run(["redis-cli", config["verify_cmd"]], capture_output=True, text=True)
                        if "PONG" not in redis_result.stdout:
                            issues.append(f"{service_name} verification failed")
                            fixes[f"{service_name}_verify"] = "Check Redis logs: docker-compose logs redis"
                        
            except (socket.timeout, socket.error, requests.RequestException, subprocess.SubprocessError) as e:
                issues.append(f"Cannot connect to {service_name} at {config['host']}:{config['port']}")
                fixes[f"{service_name}_connection"] = config["fix"]

        # Database Migration and Extension Checks
        try:
            # Check migrations
            alembic_output = subprocess.run(
                ["alembic", "current"], 
                check=True, 
                capture_output=True, 
                text=True
            )
            if "head" not in alembic_output.stdout:
                issues.append("Database migrations are not up to date")
                fixes["migrations"] = "Run 'alembic upgrade head' to update migrations"
                
            # Check vector extensions
            with psycopg.connect(self.get_db_url()) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM pg_extension WHERE extname = 'vector'")
                    if not cur.fetchone():
                        issues.append("PostgreSQL vector extension not installed")
                        fixes["vector_extension"] = """
                        1. Connect to database: docker exec -it aigi3-db psql -U ai -d ai
                        2. Run: CREATE EXTENSION IF NOT EXISTS vector;
                        """
        except Exception as e:
            issues.append(f"Database validation failed: {str(e)}")
            fixes["database"] = "Ensure database is running and accessible"

        # Environment Variable Validation
        env_vars = self.validate_env_vars()
        if env_vars[1]:  # If there are missing variables
            issues.extend(env_vars[1])
            fixes["env_vars"] = "Create or update .env file with missing variables"

        # Docker Compose Configuration
        compose_config = self.validate_docker_compose()
        if compose_config[1]:  # If there are issues
            issues.extend(compose_config[1])
            fixes["docker_compose"] = "Update docker-compose.yml with required services and configurations"

        return len(issues) == 0, issues, fixes

    def get_db_url(self) -> str:
        """Get database URL from environment variables"""
        return f"postgresql://ai:ai@localhost:5433/ai"

    def validate_env_vars(self) -> Tuple[bool, List[str]]:
        """Validate environment variables"""
        missing_vars = []
        required_vars = {
            "OPENAI_API_KEY": "OpenAI API key",
            "PHI_API_KEY": "Phi API key",
            "DB_HOST": "Database host",
            "DB_PORT": "Database port",
            "DB_USER": "Database user",
            "DB_PASSWORD": "Database password",
            "DB_DATABASE": "Database name",
            "REDIS_HOST": "Redis host",
            "REDIS_PORT": "Redis port",
            "REDIS_PASSWORD": "Redis password",
            "QDRANT_HOST": "Qdrant host",
            "QDRANT_PORT": "Qdrant port",
            "RUNTIME_ENV": "Runtime environment",
            "PHI_MONITORING": "Phi monitoring",
        }
        
        for var, description in required_vars.items():
            if not os.getenv(var):
                missing_vars.append(f"Missing {description} in environment variables: {var}")
                
        return len(missing_vars) == 0, missing_vars

    def validate_docker_compose(self) -> Tuple[bool, List[str]]:
        """Validate docker-compose.yml configuration"""
        issues = []
        required_services = ["db", "redis", "qdrant", "api", "streamlit"]
        
        if not self.docker_compose_file.exists():
            issues.append("docker-compose.yml file not found")
            return False, issues
            
        try:
            with open(self.docker_compose_file) as f:
                compose_config = yaml.safe_load(f)
                
            if "services" not in compose_config:
                issues.append("No services defined in docker-compose.yml")
                return False, issues
                
            for service in required_services:
                if service not in compose_config["services"]:
                    issues.append(f"Required service '{service}' not found in docker-compose.yml")
                    
            # Validate service configurations
            services = compose_config["services"]
            if "db" in services:
                db_service = services["db"]
                if "environment" not in db_service:
                    issues.append("Database environment variables not configured")
                if "volumes" not in db_service:
                    issues.append("Database volumes not configured")
                    
        except Exception as e:
            issues.append(f"Error validating docker-compose.yml: {str(e)}")
            
        return len(issues) == 0, issues

    def handle_service_failure(self, service_name: str) -> None:
        """Handle service failures with automated recovery"""
        try:
            if service_name in self.critical_services:
                self.restart_service(service_name)
                self.validate_service_health(service_name)
            self.notify_admins(f"Service {service_name} recovered")
        except Exception as e:
            self.escalate_incident(service_name, str(e))

if __name__ == "__main__":
    setup = DevEnvSetup()
    setup.setup_dev_environment()