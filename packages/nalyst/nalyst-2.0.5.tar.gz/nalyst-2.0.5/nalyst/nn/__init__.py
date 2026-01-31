"""
Nalyst Neural Network Module (nn)
=================================

A comprehensive deep learning framework providing:

- Tensor operations with automatic differentiation
- Neural network layers (Linear, Conv, RNN, Transformer)
- Optimizers (SGD, Adam, RMSprop, AdamW)
- Loss functions
- Data loading utilities

Inspired by modern deep learning frameworks with original implementations.

Quick Start
-----------
>>> from nalyst import nn
>>>
>>> # Define a model
>>> class MyModel(nn.Module):
...     def __init__(self):
...         super().__init__()
...         self.fc1 = nn.Linear(784, 128)
...         self.fc2 = nn.Linear(128, 10)
...
...     def forward(self, x):
...         x = nn.functional.relu(self.fc1(x))
...         return self.fc2(x)
>>>
>>> model = MyModel()
>>> optimizer = nn.optim.Adam(model.parameters(), lr=0.001)
>>> criterion = nn.CrossEntropyLoss()
"""

# Core components
from nalyst.nn.tensor import Tensor
from nalyst.nn.module import Module, Sequential, ModuleList, ModuleDict
from nalyst.nn.parameter import Parameter

# Layers
from nalyst.nn.layers import (
    # Linear
    Linear,
    Bilinear,
    # Convolution
    Conv1d,
    Conv2d,
    Conv3d,
    ConvTranspose1d,
    ConvTranspose2d,
    # Pooling
    MaxPool1d,
    MaxPool2d,
    AvgPool1d,
    AvgPool2d,
    AdaptiveAvgPool1d,
    AdaptiveAvgPool2d,
    GlobalAvgPool2d,
    # Normalization
    BatchNorm1d,
    BatchNorm2d,
    LayerNorm,
    GroupNorm,
    InstanceNorm1d,
    InstanceNorm2d,
    # Activation
    ReLU,
    LeakyReLU,
    ELU,
    SELU,
    GELU,
    Sigmoid,
    Tanh,
    Softmax,
    LogSoftmax,
    Swish,
    Mish,
    # Dropout
    Dropout,
    Dropout2d,
    AlphaDropout,
    # Recurrent
    RNN,
    LSTM,
    GRU,
    RNNCell,
    LSTMCell,
    GRUCell,
    # Attention
    MultiHeadAttention,
    TransformerEncoderLayer,
    TransformerDecoderLayer,
    TransformerEncoder,
    TransformerDecoder,
    Transformer,
    # Embedding
    Embedding,
    EmbeddingBag,
    PositionalEncoding,
    # Reshape
    Flatten,
    Unflatten,
    Reshape,
    Squeeze,
    Unsqueeze,
    Permute,
    Identity,
    Lambda,
    # Additional activation/layers
    Hardswish,
    Hardsigmoid,
    PReLU,
    DropPath,
    LearnedPositionalEncoding,
)

# Loss functions
from nalyst.nn.loss import (
    Loss,
    MSELoss,
    L1Loss,
    SmoothL1Loss,
    CrossEntropyLoss,
    NLLLoss,
    BCELoss,
    BCEWithLogitsLoss,
    HuberLoss,
    KLDivLoss,
    CosineEmbeddingLoss,
    TripletMarginLoss,
    CTCLoss,
    FocalLoss,
)

# Optimizers
from nalyst.nn import optim

# Functional API
from nalyst.nn import functional

# Data utilities
from nalyst.nn.data import (
    Dataset,
    DataLoader,
    TensorDataset,
    ConcatDataset,
    Subset,
    random_split,
    Sampler,
    SequentialSampler,
    RandomSampler,
    BatchSampler,
)

# Initialization
from nalyst.nn import init

# Pre-built models
from nalyst.nn import models

# Utilities
from nalyst.nn.utils import (
    save_model,
    load_model,
    save_state_dict,
    load_state_dict,
    clip_grad_norm_,
    clip_grad_value_,
    count_parameters,
    model_summary,
    freeze,
    unfreeze,
    set_requires_grad,
    EarlyStopping,
    ModelCheckpoint,
    set_seed,
)

__all__ = [
    # Core
    "Tensor",
    "Module",
    "Sequential",
    "ModuleList",
    "ModuleDict",
    "Parameter",
    # Layers - Linear
    "Linear",
    "Bilinear",
    # Layers - Convolution
    "Conv1d",
    "Conv2d",
    "Conv3d",
    "ConvTranspose1d",
    "ConvTranspose2d",
    # Layers - Pooling
    "MaxPool1d",
    "MaxPool2d",
    "AvgPool1d",
    "AvgPool2d",
    "AdaptiveAvgPool1d",
    "AdaptiveAvgPool2d",
    "GlobalAvgPool2d",
    # Layers - Normalization
    "BatchNorm1d",
    "BatchNorm2d",
    "LayerNorm",
    "GroupNorm",
    "InstanceNorm1d",
    "InstanceNorm2d",
    # Layers - Activation
    "ReLU",
    "LeakyReLU",
    "ELU",
    "SELU",
    "GELU",
    "Sigmoid",
    "Tanh",
    "Softmax",
    "LogSoftmax",
    "Swish",
    "Mish",
    "Hardswish",
    "Hardsigmoid",
    "PReLU",
    # Layers - Dropout
    "Dropout",
    "Dropout2d",
    "AlphaDropout",
    "DropPath",
    # Layers - Recurrent
    "RNN",
    "LSTM",
    "GRU",
    "RNNCell",
    "LSTMCell",
    "GRUCell",
    # Layers - Attention
    "MultiHeadAttention",
    "TransformerEncoderLayer",
    "TransformerDecoderLayer",
    "TransformerEncoder",
    "TransformerDecoder",
    "Transformer",
    # Layers - Embedding
    "Embedding",
    "EmbeddingBag",
    "PositionalEncoding",
    "LearnedPositionalEncoding",
    # Layers - Reshape
    "Flatten",
    "Unflatten",
    "Reshape",
    "Squeeze",
    "Unsqueeze",
    "Permute",
    "Identity",
    "Lambda",
    # Loss functions
    "Loss",
    "MSELoss",
    "L1Loss",
    "SmoothL1Loss",
    "CrossEntropyLoss",
    "NLLLoss",
    "BCELoss",
    "BCEWithLogitsLoss",
    "HuberLoss",
    "KLDivLoss",
    "CosineEmbeddingLoss",
    "TripletMarginLoss",
    "CTCLoss",
    "FocalLoss",
    # Submodules
    "optim",
    "functional",
    "init",
    "models",
    # Data utilities
    "Dataset",
    "DataLoader",
    "TensorDataset",
    "ConcatDataset",
    "Subset",
    "random_split",
    "Sampler",
    "SequentialSampler",
    "RandomSampler",
    "BatchSampler",
    # Utility functions
    "save_model",
    "load_model",
    "save_state_dict",
    "load_state_dict",
    "clip_grad_norm_",
    "clip_grad_value_",
    "count_parameters",
    "model_summary",
    "freeze",
    "unfreeze",
    "set_requires_grad",
    "EarlyStopping",
    "ModelCheckpoint",
    "set_seed",
]
