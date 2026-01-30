Getting Started
===============

Installation
------------

Install ML-EcoLyzer using pip::

    pip install ml-ecolyzer

For framework-specific features, install with extras::

    # HuggingFace support
    pip install ml-ecolyzer[huggingface]

    # PyTorch support
    pip install ml-ecolyzer[pytorch]

    # Full installation
    pip install ml-ecolyzer[all]

Basic Usage
-----------

Here's a simple example to analyze the environmental impact of a model::

    from mlecolyzer import EcoLyzer

    config = {
        "project": "my_analysis",
        "models": [
            {"name": "gpt2", "task": "text", "framework": "huggingface"}
        ],
        "datasets": [
            {"name": "wikitext", "task": "text", "framework": "huggingface", "limit": 100}
        ]
    }

    eco = EcoLyzer(config)
    results = eco.run()

    # Print results
    print(f"CO2 Emissions: {results['final_report']['analysis_summary']['total_co2_emissions_kg']:.6f} kg")
    print(f"Energy Used: {results['final_report']['analysis_summary']['total_energy_kwh']:.6f} kWh")

Using the CLI
-------------

ML-EcoLyzer also provides a command-line interface::

    # Analyze a single model-dataset pair
    mlecolyzer analyze --model gpt2 --dataset wikitext --framework huggingface --task text

    # Get system information
    mlecolyzer info

    # Validate a configuration file
    mlecolyzer validate --config my_config.yaml

Understanding Results
---------------------

ML-EcoLyzer provides several key metrics:

- **CO2 Emissions**: Total carbon dioxide emissions in kg
- **Energy Consumption**: Total energy used in kWh
- **Water Footprint**: Estimated water consumption in liters
- **ESS (Environmental Sustainability Score)**: Efficiency metric (parameters per gram of CO2)

The ESS metric allows comparing different models' environmental efficiency::

    ESS = Effective Parameters (M) / CO2 (g)

Higher ESS values indicate more environmentally efficient models.
