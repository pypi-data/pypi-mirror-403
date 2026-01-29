# MLCore Models (Artifact Tier)

## Overview
The `models/` directory serves as the immutable storage layer for serialized machine learning artifacts. It governs the transition from offline training outputs to production-ready assets.

## Artifact Standards
All models stored within this tier must adhere to the following serialization standards to ensure backend compatibility:

### 1. Serialized weights
- **ONNX (`.onnx`)**: The mandatory format for production-grade inference across heterogeneous hardware.
- **PyTorch Trace (`.pt`)**: Permitted for JIT-optimized execution in pure Python/Torch environments.
- **TensorRT Engines**: Optionally stored for specific hardware acceleration profiles.

### 2. Configuration Metadata (`config.json`)
Every model artifact must be accompanied by a `config.json` containing:
- `schema_version`: Version of the metadata schema.
- `model_type`: Architectural classification (e.g., 'transformer-encoder', 'cnn-classifier').
- `input_node_configurations`: Expected tensor shapes and data types.
- `output_node_configurations`: Description of output headers and probability distributions.

### 3. Performance Metrics (`metrics.json`)
Evaluation summaries from the training phase, including:
- Accuracy/Precision/Recall/F1 scores.
- Latency benchmarks (p50, p99) on standard reference hardware.

## Versioning and Immutability
- **Versioning**: All artifacts are versioned using `vX.Y.Z` semantics.
- **Immutability**: Once an artifact is registered in `models/`, it must never be modified. Updates require the registration of a new version.
- **Pruning**: Deprecated models are archived but retained to support legacy tool versions still in circulation.
