# fiddler-client

[![Python Version](https://img.shields.io/pypi/pyversions/fiddler-client.svg)](https://pypi.org/project/fiddler-client/)
[![PyPI Version](https://img.shields.io/pypi/v/fiddler-client.svg)](https://pypi.org/project/fiddler-client/)
[![License](https://img.shields.io/pypi/l/fiddler-client.svg)](https://pypi.org/project/fiddler-client/)

The official Python client for [Fiddler](https://www.fiddler.ai), the enterprise-grade AI Observability platform. Monitor, analyze, and protect your ML models, LLMs, GenAI applications, and AI Agents in production.

## Platform Features

- 🚀 **Easy Integration** - Simple Python API for model and GenAI application onboarding
- 📊 **Real-time Monitoring** - Stream production events for drift detection, performance tracking, and anomaly detection
- 🎯 **Data Drift & Integrity** - Detect distribution changes, data quality issues, and schema violations
- 📈 **Custom Metrics** - Define and track business KPIs, custom performance metrics, and model-specific measurements
- 🔍 **Data Segments** - Analyze model behavior across cohorts with custom segments and slices
- 🤖 **GenAI & LLM Monitoring** - Track hallucinations, toxicity, PII leakage, prompt injection, and response quality
- 🛡️ **Guardrails** - Real-time protection against unsafe outputs and policy violations in LLM applications
- 📊 **Enrichments** - Add embeddings, sentiment, topics, and other ML-derived features to your data
- 🔄 **Model Comparison** - Compare performance across model versions, champion/challenger analysis
- 🎨 **Custom Dashboards** - Build tailored monitoring views with charts, alerts, and analytics
- 🔔 **Smart Alerts** - Multi-channel notifications (Slack, Email, PagerDuty) with customizable thresholds
- 🤝 **MLOps Integrations** - Native support for MLflow, SageMaker, Vertex AI, and other platforms

## Installation

```bash
pip install fiddler-client
```

## Requirements

- Python 3.9 or higher
- pip 19.0 or higher (latest release preferred)

## Quick Start

```python
import fiddler as fdl

# Initialize the client
fdl.init(
    url='https://your-company.fiddler.ai',
    token='your-api-token'
)

# List the existing projects
for project in fdl.Project.list():
    print(project.name)
```

## Documentation

* 📚 [Complete Documentation](https://docs.fiddler.ai/)
* 🚀 [Getting Started with LLMs](https://docs.fiddler.ai/first-steps/getting-started-with-llm-monitoring)
  * [LLM Quick Start Guide](https://docs.fiddler.ai/tutorials-and-quick-starts/llm-and-genai/simple-llm-monitoring)
* 🚀 [Getting Started with ML](https://docs.fiddler.ai/first-steps/getting-started-with-ml-model-observability)
  * [ML Quick Start Guide](https://docs.fiddler.ai/tutorials-and-quick-starts/ml-observability/quick-start)
* 📖 [API Reference](https://docs.fiddler.ai/reference/about-the-fiddler-client)
* 💡 [Example Notebooks](https://github.com/fiddler-labs/fiddler-examples)

## Example Notebooks

Check out our [GitHub repository](https://github.com/fiddler-labs/fiddler-examples) for Jupyter notebooks demonstrating:

- Model onboarding and monitoring setup
- Drift detection and root cause analysis
- Custom metrics and alerting
- LLM and GenAI monitoring
- Integration with popular ML frameworks

## Version History

See our [release notes](https://docs.fiddler.ai/history/python-client-history) for detailed version history.

## Support

- 📧 Email: [support@fiddler.ai](support@fiddler.ai)
- 💬 Community: [Join our Slack](https://www.fiddler.ai/slack)

## License

This package is proprietary software. Please refer to your Fiddler license agreement for terms of use.

---

**Want to see Fiddler in action?** [Request a demo](https://www.fiddler.ai/demo)
