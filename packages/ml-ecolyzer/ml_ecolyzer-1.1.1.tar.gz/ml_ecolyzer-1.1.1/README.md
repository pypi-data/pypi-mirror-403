# ML-EcoLyzer

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/ml-ecolyzer.svg)](https://badge.fury.io/py/ml-ecolyzer)

A framework for measuring the environmental impact of ML inference. Tracks CO2 emissions, energy consumption, and water usage across different hardware setups.

![ML-EcoLyzer Overview](docs/assets/ml_ecolyzer.png)

## Why?

Training gets all the attention, but inference runs 24/7 in production. We built this to answer: "How much does running this model actually cost the environment?"

## Install

Available on [PyPI](https://pypi.org/project/ml-ecolyzer/):

```bash
pip install ml-ecolyzer
```

With framework-specific dependencies:
```bash
pip install ml-ecolyzer[huggingface]  # transformers, diffusers
pip install ml-ecolyzer[pytorch]       # torchvision, torchaudio
pip install ml-ecolyzer[all]           # everything
```

## Quick Start

```python
from mlecolyzer import EcoLyzer

config = {
    "project": "my_analysis",
    "models": [{"name": "gpt2", "task": "text"}],
    "datasets": [{"name": "wikitext", "task": "text", "limit": 100}]
}

eco = EcoLyzer(config)
results = eco.run()

print(f"CO2: {results['final_report']['analysis_summary']['total_co2_emissions_kg']:.6f} kg")
print(f"Energy: {results['final_report']['analysis_summary']['total_energy_kwh']:.6f} kWh")
```

## What it measures

- **CO2 emissions** - Based on power draw and regional carbon intensity
- **Energy usage** - Via NVIDIA-SMI, psutil, or RAPL
- **Water footprint** - Cooling overhead varies by hardware tier
- **ESS (Environmental Sustainability Score)** - Parameters per gram of CO2, useful for comparing models

```
ESS = Effective Parameters (M) / CO2 (g)
```

Higher ESS = more efficient. INT8 models typically score ~74% higher than FP32.

## Supported setups

- GPUs: A100, T4, RTX series, GTX series
- CPU-only works too
- Frameworks: HuggingFace, PyTorch, scikit-learn

## Config file

```yaml
project: "benchmark_run"

models:
  - name: "facebook/opt-350m"
    task: "text"
    quantization:
      enabled: true
      target_dtype: "int8"

datasets:
  - name: "wikitext"
    task: "text"
    limit: 500

hardware:
  device_profile: "auto"

output:
  output_dir: "./results"
  export_formats: ["json", "csv"]
```

## CLI

```bash
# Single run
mlecolyzer analyze --model gpt2 --dataset wikitext --task text

# System info
mlecolyzer info
```

## Benchmarks

Ran 1,500+ inference configs across:
- Hardware: GTX 1650, RTX 4090, Tesla T4, A100
- Models: GPT-2, OPT, Qwen, LLaMA, Phi, Whisper, ViT
- Precisions: FP32, FP16, INT8

Key findings:
- A100 has poor ESS when underutilized (overkill for small batches)
- Consumer GPUs (RTX/T4) often more efficient for single-batch inference
- Quantization helps a lot, especially INT8

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). PRs welcome.

```bash
# Dev setup
pip install -e ".[dev]"
pytest
```

## Citation

```bibtex
@inproceedings{mlecolyzer2025,
  title={ML-EcoLyzer: A Framework for Quantifying the Environmental Impact of Machine Learning Inference},
  author={Minoza, Jose Marie Antonio and Laylo, Rex Gregor and Villarin, Christian and Ibanez, Sebastian},
  booktitle={AAAI Workshop on AI for Environmental Science},
  year={2025}
}
```

## License

MIT
