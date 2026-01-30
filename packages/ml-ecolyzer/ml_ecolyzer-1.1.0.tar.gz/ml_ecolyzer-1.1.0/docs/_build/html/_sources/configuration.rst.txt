Configuration
=============

ML-EcoLyzer uses a structured configuration system to define analysis parameters.

Configuration Structure
-----------------------

A complete configuration includes:

- **project**: Project name for tracking
- **models**: List of model configurations
- **datasets**: List of dataset configurations
- **monitoring**: Monitoring settings
- **hardware**: Hardware configuration
- **output**: Output settings

YAML Configuration Example
--------------------------

.. code-block:: yaml

    project: "ml_sustainability_benchmark"

    models:
      - name: "gpt2"
        task: "text"
        framework: "huggingface"
        batch_size: 1
        max_length: 512

      - name: "facebook/opt-350m"
        task: "text"
        framework: "huggingface"
        quantization:
          enabled: true
          method: "dynamic"
          target_dtype: "int8"

    datasets:
      - name: "wikitext"
        task: "text"
        framework: "huggingface"
        split: "test"
        limit: 100

    monitoring:
      duration_seconds: 300
      frequency_hz: 1.0
      enable_quantization_analysis: true

    hardware:
      device_profile: "auto"
      deployment_environment: "local"
      force_cpu: false

    output:
      output_dir: "./results"
      export_formats: ["json", "csv"]
      log_level: "INFO"

Model Configuration
-------------------

.. list-table::
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - name
     - str
     - Model name or HuggingFace identifier
   * - task
     - str
     - Task type (text, image, audio, classification, regression)
   * - framework
     - str
     - Framework (huggingface, sklearn, pytorch)
   * - batch_size
     - int
     - Processing batch size (default: 1)
   * - max_length
     - int
     - Maximum sequence length (default: 1024)
   * - quantization
     - dict
     - Quantization settings (optional)

Dataset Configuration
---------------------

.. list-table::
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - name
     - str
     - Dataset name or identifier
   * - task
     - str
     - Task type (must match model task)
   * - framework
     - str
     - Framework (must match model framework)
   * - split
     - str
     - Dataset split to use (default: "test")
   * - limit
     - int
     - Maximum samples to load (optional)

Hardware Configuration
----------------------

.. list-table::
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - device_profile
     - str
     - Device profile (auto, datacenter, desktop_gpu, desktop_cpu, mobile, edge)
   * - deployment_environment
     - str
     - Environment (auto, local, aws, gcp, azure)
   * - cloud_region
     - str
     - Cloud region for carbon intensity
   * - force_cpu
     - bool
     - Force CPU-only execution
   * - force_gpu
     - bool
     - Force GPU execution

Presets
-------

ML-EcoLyzer provides configuration presets for common use cases:

- **quick**: Minimal samples for fast testing
- **test**: Small-scale testing
- **standard**: Standard evaluation
- **comprehensive**: Full analysis
- **memory_efficient**: For memory-constrained systems
