ML-EcoLyzer Documentation
==========================

**ML-EcoLyzer** is a reproducible benchmarking and analysis framework for quantifying
the environmental cost of machine learning inference.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   getting_started
   configuration
   api/index
   contributing

Features
--------

- **Inference-Centric Analysis**: Quantifies CO2 emissions, energy use, and water impact
- **Cross-Hardware Profiling**: Supports A100, T4, RTX, GTX, and CPU-only setups
- **Model-Agnostic Framework**: Runs LLMs, ViTs, audio models, and traditional ML
- **ESS Metric**: Environmental Sustainability Score for normalized emissions comparison
- **Quantization Insights**: Analyzes FP16 and INT8 savings for sustainable deployment

Quick Start
-----------

Installation::

    pip install ml-ecolyzer

Basic Usage::

    from mlecolyzer import EcoLyzer

    config = {
        "project": "sustainability_demo",
        "models": [{"name": "gpt2", "task": "text"}],
        "datasets": [{"name": "wikitext", "task": "text"}]
    }

    eco = EcoLyzer(config)
    results = eco.run()

    print(f"CO2: {results['final_report']['analysis_summary']['total_co2_emissions_kg']:.6f} kg")

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
