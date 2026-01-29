# Neural Network Training Results

## Overview
This document summarizes training results for various architectures.

## Model Comparison

| Model | Params | Training Time | Test Accuracy |
|-------|--------|---------------|---------------|
| ResNet-50 | 25.6M | 4h 23m | 76.1% |
| ViT-B/16 | 86M | 12h 15m | 77.9% |
| EfficientNet-B4 | 19M | 3h 45m | 82.6% |

## Loss Function

The cross-entropy loss is defined as:

L = -sum(y_i * log(p_i))

where y_i is the true label and p_i is the predicted probability.

## Hyperparameters

- Learning rate: 0.001
- Batch size: 256
- Epochs: 100
- Optimizer: AdamW (beta1=0.9, beta2=0.999)
