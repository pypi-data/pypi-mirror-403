"""
Neural network layers package.
"""

# Linear layers
from nalyst.nn.layers.linear import Linear, Bilinear

# Convolution layers
from nalyst.nn.layers.conv import (
    Conv1d,
    Conv2d,
    Conv3d,
    ConvTranspose1d,
    ConvTranspose2d,
)

# Pooling layers
from nalyst.nn.layers.pooling import (
    MaxPool1d,
    MaxPool2d,
    AvgPool1d,
    AvgPool2d,
    AdaptiveAvgPool1d,
    AdaptiveAvgPool2d,
    GlobalAvgPool2d,
)

# Normalization layers
from nalyst.nn.layers.normalization import (
    BatchNorm1d,
    BatchNorm2d,
    LayerNorm,
    GroupNorm,
    InstanceNorm1d,
    InstanceNorm2d,
)

# Activation layers
from nalyst.nn.layers.activation import (
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
)

# Dropout layers
from nalyst.nn.layers.dropout import (
    Dropout,
    Dropout2d,
    AlphaDropout,
    DropPath,
)

# Recurrent layers
from nalyst.nn.layers.recurrent import (
    RNN,
    LSTM,
    GRU,
    RNNCell,
    LSTMCell,
    GRUCell,
)

# Attention layers
from nalyst.nn.layers.attention import (
    MultiHeadAttention,
    TransformerEncoderLayer,
    TransformerDecoderLayer,
    TransformerEncoder,
    TransformerDecoder,
    Transformer,
)

# Embedding layers
from nalyst.nn.layers.embedding import (
    Embedding,
    EmbeddingBag,
    PositionalEncoding,
    LearnedPositionalEncoding,
)

# Reshape layers
from nalyst.nn.layers.reshape import (
    Flatten,
    Unflatten,
    Reshape,
    Squeeze,
    Unsqueeze,
    Permute,
    Identity,
    Lambda,
)

__all__ = [
    # Linear
    "Linear",
    "Bilinear",
    # Convolution
    "Conv1d",
    "Conv2d",
    "Conv3d",
    "ConvTranspose1d",
    "ConvTranspose2d",
    # Pooling
    "MaxPool1d",
    "MaxPool2d",
    "AvgPool1d",
    "AvgPool2d",
    "AdaptiveAvgPool1d",
    "AdaptiveAvgPool2d",
    "GlobalAvgPool2d",
    # Normalization
    "BatchNorm1d",
    "BatchNorm2d",
    "LayerNorm",
    "GroupNorm",
    "InstanceNorm1d",
    "InstanceNorm2d",
    # Activation
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
    # Dropout
    "Dropout",
    "Dropout2d",
    "AlphaDropout",
    "DropPath",
    # Recurrent
    "RNN",
    "LSTM",
    "GRU",
    "RNNCell",
    "LSTMCell",
    "GRUCell",
    # Attention
    "MultiHeadAttention",
    "TransformerEncoderLayer",
    "TransformerDecoderLayer",
    "TransformerEncoder",
    "TransformerDecoder",
    "Transformer",
    # Embedding
    "Embedding",
    "EmbeddingBag",
    "PositionalEncoding",
    "LearnedPositionalEncoding",
    # Reshape
    "Flatten",
    "Unflatten",
    "Reshape",
    "Squeeze",
    "Unsqueeze",
    "Permute",
    "Identity",
    "Lambda",
]
