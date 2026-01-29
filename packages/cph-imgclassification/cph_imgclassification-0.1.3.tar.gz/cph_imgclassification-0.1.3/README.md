# CPH Image Classification

A generic, modular, and reusable PyTorch Lightning pipeline for training image classification models using CNNs. This package is fully config-driven, allowing you to train models on any image classification dataset by simply modifying a YAML configuration file.

## Installation

```bash
pip install cph-imgclassification
```

## Quick Start

### 1. Install the Package

```bash
pip install cph-imgclassification
```

### 2. Organize Your Data

Organize your images in class folders:

```
YourProjectName/data/images/
├── class1/
│   ├── image1.jpg
│   ├── image2.jpg
│   └── ...
├── class2/
│   ├── image1.jpg
│   ├── image2.jpg
│   └── ...
└── class3/
    ├── image1.jpg
    └── ...
```

### 3. Create Configuration File

Create `config.yaml`:

```yaml
# Image Classification Model Configuration
seed_everything: true

trainer:
  callbacks:
    - class_path: lightning.pytorch.callbacks.ModelCheckpoint
      init_args:
        filename: "{epoch}-{val_acc:.2f}.best"
        monitor: "val_acc"
        mode: "max"
        save_top_k: 1
    - class_path: cph_imgclassification.imageclassification.callbacks.ONNXExportCallback
      init_args:
        output_dir: "models"
        model_name: "my_model"
        input_shape: [3, 224, 224]

  logger:
    class_path: lightning.pytorch.loggers.TensorBoardLogger
    init_args:
      save_dir: "lightning_logs"
      name: "MyProjectTraining"

  max_epochs: 50
  accelerator: auto
  devices: auto
  precision: 16-mixed

model:
  class_path: cph_imgclassification.imageclassification.modelmodule.ModelModuleIMG
  init_args:
    lr: 0.001
    weight_decay: 0.0001
    model:
      class_path: cph_imgclassification.imageclassification.modelfactory.ImageClassificationModel
      init_args:
        input_channels: 3
        num_classes: 0  # Auto-set from datamodule
        architecture: "medium"  # "simple", "medium", "deep", or "custom"
        input_size: [224, 224]

optimizer: 
  class_path: torch.optim.Adam
  init_args:
    lr: 0.001
    weight_decay: 0.0001

data:
  class_path: cph_imgclassification.imageclassification.datamodule.DataModuleIMG
  init_args:
    data_dir: "YourProjectName/data/images"
    image_size: [224, 224]
    batch_size: 32
    num_workers: 4
    val_split: 0.2
    random_seed: 42
    augmentation:
      enabled: true
      rotation: 15
      horizontal_flip: true
    normalization:
      mean: [0.485, 0.456, 0.406]
      std: [0.229, 0.224, 0.225]
    save_preprocessor: true
    preprocessor_path: "models/label_encoder.joblib"

fit:
  ckpt_path: null

test:
  ckpt_path: best
```

### 4. Train Your Model

**Automatic fit + test (default behavior):**
```bash
cph-imgclassification --config config.yaml
```

**Or use standard Lightning CLI subcommands:**
```bash
# Training only
cph-imgclassification fit --config config.yaml

# Testing only
cph-imgclassification test --config config.yaml

# Validation
cph-imgclassification validate --config config.yaml

# Prediction
cph-imgclassification predict --config config.yaml
```

## Features

- **Fully Config-Driven**: All settings controlled via YAML files
- **Generic & Reusable**: Use for any image classification task
- **Flexible Data Formats**: Supports folder-based and CSV-based datasets
- **Auto-Dimension Detection**: Automatically detects number of classes
- **Configurable CNN Architectures**: Choose from preset architectures or define custom layers
- **Data Augmentation**: Built-in augmentation support
- **Production-Ready**: Exports models to ONNX format
- **PyTorch Lightning**: Built on PyTorch Lightning for scalable training
- **Comprehensive Metrics**: Tracks Accuracy, F1-Score, Precision, and Recall

## Usage Examples

### Training Only

```bash
cph-imgclassification fit --config config.yaml
```

### Testing Only

```bash
cph-imgclassification test --config config.yaml
```

### Resume Training

```bash
cph-imgclassification fit --config config.yaml --fit.ckpt_path path/to/checkpoint.ckpt
```

### Using CSV Data Format

In your config file, use:

```yaml
data:
  class_path: cph_imgclassification.imageclassification.datamodule.DataModuleIMG
  init_args:
    csv_path: "data/image_labels.csv"
    image_path_col: "image_path"
    label_col: "label"
    # ... other settings
```

## Configuration Reference

### Model Architectures

- **simple**: 2 conv blocks (32, 64 channels) - Good for small datasets
- **medium**: 4 conv blocks (64, 128, 256, 512 channels) - Balanced performance
- **deep**: 6 conv blocks (64, 128, 256, 256, 512, 512 channels) - For large datasets
- **custom**: Define your own conv layers

### Data Augmentation Options

- `rotation`: Random rotation degrees
- `horizontal_flip`: Random horizontal flip
- `vertical_flip`: Random vertical flip
- `color_jitter`: Color jitter intensity
- `random_crop`: Crop size for random cropping

## Output Files

After training, you'll find:

- **ONNX Model**: `models/your_model_name.onnx`
- **Label Encoder**: `models/label_encoder.joblib`
- **Checkpoints**: `lightning_logs/.../checkpoints/`
- **TensorBoard Logs**: `lightning_logs/`

## Viewing Training Progress

```bash
tensorboard --logdir lightning_logs
```

Then open `http://localhost:6006` in your browser.

## Python API

You can also use the package programmatically:

```python
from cph_imgclassification.imageclassification import (
    DataModuleIMG,
    ImageClassificationModel,
    ModelModuleIMG
)

# Create datamodule
datamodule = DataModuleIMG(
    data_dir="data/images",
    image_size=(224, 224),
    batch_size=32
)

# Create model
model = ImageClassificationModel(
    input_channels=3,
    num_classes=10,
    architecture="medium"
)

# Create Lightning module
lightning_model = ModelModuleIMG(model=model, lr=0.001)
```

## Requirements

- Python >= 3.8
- PyTorch >= 2.0.0
- PyTorch Lightning >= 2.1.0

See `requirements.txt` for full dependency list.

## License

MIT License

## Author

chandra

## Repository

https://github.com/imchandra11/cph-imgclassification

## Support

For issues, questions, or contributions, please visit the [GitHub repository](https://github.com/imchandra11/cph-imgclassification/issues).
