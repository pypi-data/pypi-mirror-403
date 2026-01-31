# Machine Learning Extension for pyPhases

This Extension adds:
- an Exporter for `PyTorch` and `TensorFlow` Models.
- an Modelmanager that can handle `PyTorch` and `TensorFlow` Models

## Documentation

📚 **[Complete Configuration Documentation](docs/configuration.md)** - Comprehensive guide to all configuration options

🚀 **[Quick Reference Guide](docs/quick-reference.md)** - Common patterns and minimal examples

📋 **[JSON Schema](schema/config-schema.json)** | **[YAML Schema](schema/config-schema.yaml)** - For validation and IDE support

🔧 **[Configuration Validator](scripts/validate_config.py)** - Script to validate your configuration files

📖 **[Complete Example](examples/complete-config.yaml)** - Full configuration with all options

## Setup

- add pyPhasesML to your dependencies or run `pip install -U pyPhasesML`
- add `pyPhasesML` to your plugins in the main project config f.e: in your `project.yaml`
```yaml
name: bumpDetector
namespace: ibmt.tud

# load machine learning plugin
plugins:
  - pyPhasesML
```
- you do not need to add the ModelExporter manually

## Getting Started

### Minimal Example

For a complete minimal example see, with loading data, training and evaluation see:
https://gitlab.com/tud.ibmt.public/pyphases/pyphasesml-example-bumpdetector

### Quick Start Configuration

Here's a minimal configuration to get started:

```yaml
# Required configuration
modelPath: models/mymodels
modelName: MyCNN
inputShape: [16, 50]

classification:
  labelNames: [MyClassification]
  classNames:
    - [A, B]

trainingParameter:
  batchSize: 32
```

For more configuration options, see the [complete example](examples/complete-config.yaml) or [documentation](docs/configuration.md).

## Configuration Validation

Validate your configuration files using the provided script:

```bash
# Validate a configuration file
python scripts/validate_config.py config.yaml

# Validate with verbose output
python scripts/validate_config.py --verbose config.yaml

# Use custom schema
python scripts/validate_config.py --schema custom-schema.json config.yaml
```

## IDE Support

For better IDE support with autocompletion and validation:

1. **VS Code**: Install the YAML extension and add this to your settings:
```json
{
  "yaml.schemas": {
    "./schema/config-schema.json": ["**/config.yaml", "**/config.yml"]
  }
}
```

2. **PyCharm**: Go to Settings → Languages & Frameworks → Schemas and DTDs → JSON Schema Mappings and add the schema file.

## Configuration Examples

### Basic Binary Classification
```yaml
modelPath: models/binary
modelName: BinaryClassifier
inputShape: [32, 64]

classification:
  labelNames: [BinaryTask]
  classNames:
    - [Positive, Negative]

trainingParameter:
  batchSize: 64
  maxEpochs: 50
  learningRate: 0.001
  validationMetrics: ["acc", "auroc"]
```

## Adding a PyTorch Model `CNNPytorch`

Create a class that is compatible with your `modelPath` and `modelname`. So in this example, we need a class `CNNPytorch` in the path `models/mymodels/CNNPytorch.py` relative to your root. 

This class is required to:
- inherit from `ModelTorchAdapter`:
- populate the `self.model` with a valid PyTorch-Model, in the `define` method
- return a valid loss function in the method `getLossFunction`

```python
import torch.nn as nn

from pyPhasesML.adapter.ModelTorchAdapter import ModelTorchAdapter

class CNNPytorch(ModelTorchAdapter):
    def define(self):
        length, channelCount = self.inputShape
        numClasses = self.config.numClasses

        self.model = nn.Conv1d(
            in_channels=channelCount, 
            out_channels=self.config.numClasses,
            kernel_size=self.getOption("kernelSize"),
        )

    def getLossFunction(self):
        return torch.nn.MultiLabelSoftMarginLoss(reduction="mean", weight=self.weightTensors)

```

### Load the model

In a phase you can simply use the `ModelManager` to get the Model and `registerData` to save the state. There is no dependency on `pyTorch` or `TensorFlow` in this example, so you swap your models dynamicly depending on your environment:

```php
import numpy as np
from pathlib import Path

from pyPhases import Phase
from pyPhasesML import DatasetWrapXY, ModelManager, TrainingSet


class TestModel(Phase):
    def main(self):
        # loads the model depending on modelPath and modelName
        model = ModelManager.getModel()
        
        input = np.randn(20, 16, 50)        
        output = model(input)
        # save the model state
        self.project.registerData("modelState", model)
```


## Configuration

- test is assumed to be the first split (if not everything is set to manual splits)
- combined splits: trainvaltest, trainval are possible

```yaml
dataversion:
  split:
    test: 0:500
    validation: 500:1000
    training: 1000:1500

```