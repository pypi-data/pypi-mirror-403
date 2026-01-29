# Opportunity Core

Core library for Opportunity Radar project. Contains shared utilities, models, and services used across all microservices.

## Components

- **utils**: Common utilities (authentication, deal detection, notifications, etc.)
- **models**: Data models and schemas
- **services**: Shared business logic
- **config**: Configuration management

## Installation

### From PyPI (Recommended for production)

```bash
pip install opportunity-core
```

### For Development

```bash
# Clone the repository
git clone https://github.com/mustafaaykon/opportunity-radar.git
cd opportunity-radar/core

# Install in editable mode
pip install -e .
```

## Usage

```python
from opportunity_core.utils.deal_detector import DealDetector
from opportunity_core.utils.telegram_notifier import TelegramNotifier
```

