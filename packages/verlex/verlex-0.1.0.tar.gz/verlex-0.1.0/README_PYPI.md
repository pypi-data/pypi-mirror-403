# Verlex

**Run your code in the cloud for the price of a coffee.**

Verlex is a Python SDK that lets you execute code on the cheapest available cloud infrastructure across AWS, GCP, and Azure — all with a single function call.

## Installation

```bash
pip install verlex
```

With ML dependencies:

```bash
pip install verlex[ml]
```

## Quick Start

```python
import verlex

def train_model():
    import torch
    model = torch.nn.Linear(100, 10)
    # Your training code here...
    return {"accuracy": 0.95}

# Run it in the cloud - that's it!
with verlex.GateWay(api_key="gw_your_key") as gw:
    result = gw.run(train_model)
    print(result)
```

## Basic Usage

### Context Manager (Recommended)

```python
import verlex

with verlex.GateWay(api_key="gw_your_key") as gw:
    # Analyze resources your function needs
    recommendation = gw.analyze(my_function)
    print(f"Recommended: {recommendation.gpu_type}")

    # Run in the cloud
    result = gw.run(my_function)
```

### Specifying Resources

```python
with verlex.GateWay(api_key="gw_your_key") as gw:
    result = gw.run(
        train_model,
        gpu="A100",       # Specific GPU type
        gpu_count=2,      # Multiple GPUs
        memory="64GB",    # Memory requirement
        timeout=7200,     # 2 hour timeout
    )
```

### Async Execution

```python
with verlex.GateWay(api_key="gw_your_key") as gw:
    # Submit jobs (non-blocking)
    job1 = gw.run_async(train_model_1)
    job2 = gw.run_async(train_model_2)

    # Wait for results when needed
    result1 = job1.result()
    result2 = job2.result()
```

## Pricing Modes

Choose your price-speed tradeoff:

| Mode | Margin | Wait Time | Best For |
|------|--------|-----------|----------|
| **Priority** | +25% | Immediate | Time-sensitive workloads |
| **Patient** | +12% | Up to 10 min | Batch jobs, cost-sensitive |
| **Flexible** | +10% | Variable | Long-running, can migrate |
| **Sticky** | +15% | Up to 10 min | Jobs that can't be interrupted |

```python
# Priority mode - immediate execution
with verlex.GateWay(api_key="gw_your_key", priority=True) as gw:
    result = gw.run(my_function)

# Patient mode - wait for lower prices
with verlex.GateWay(api_key="gw_your_key", priority=False) as gw:
    result = gw.run(my_function)

# Flexible mode - can migrate to cheaper providers
with verlex.GateWay(api_key="gw_your_key", priority=False, flexible=True) as gw:
    result = gw.run(my_function)
```

## Authentication

### Option 1: Direct API Key

```python
with verlex.GateWay(api_key="gw_your_key") as gw:
    result = gw.run(my_function)
```

### Option 2: Environment Variable

```bash
export VERLEX_API_KEY="gw_your_key"
```

```python
with verlex.GateWay() as gw:
    result = gw.run(my_function)
```

## CLI

```bash
# Login
verlex login

# Run a script
verlex run train.py

# Run with specific GPU
verlex run train.py --gpu A100

# Check job status
verlex jobs

# View account info
verlex whoami
```

## Supported Cloud Providers

- **AWS** - EC2, with Spot instances (up to 90% off)
- **GCP** - Compute Engine, with Preemptible VMs (up to 91% off)
- **Azure** - VMs, with Spot instances (up to 81% off)

## Links

- **Website**: [verlex.dev](https://verlex.dev)
- **Documentation**: [verlex.dev/docs](https://verlex.dev/docs)

## License

Apache 2.0
