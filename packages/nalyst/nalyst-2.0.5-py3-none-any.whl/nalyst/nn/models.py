"""
Pre-built neural network model architectures.

Provides common architectures for:
- Image classification (ResNet, VGG, MobileNet)
- Sequence modeling (BERT-style Transformer)
- Simple feedforward networks
"""

from __future__ import annotations

from typing import Optional, List, Tuple
import numpy as np

from nalyst.nn.module import Module, Sequential
from nalyst.nn.parameter import Parameter
from nalyst.nn.tensor import Tensor
from nalyst.nn.layers import (
    Linear, Conv2d, BatchNorm2d, ReLU, MaxPool2d, AdaptiveAvgPool2d,
    Dropout, Flatten, GELU, LayerNorm, Embedding, MultiHeadAttention,
)


# Basic Building Blocks

class MLP(Module):
    """
    Multi-Layer Perceptron.

    Parameters
    ----------
    in_features : int
        Input dimension.
    hidden_sizes : list
        List of hidden layer sizes.
    out_features : int
        Output dimension.
    activation : str, default='relu'
        Activation function.
    dropout : float, default=0.0
        Dropout probability.

    Examples
    --------
    >>> mlp = MLP(784, [512, 256], 10)
    >>> x = Tensor(np.random.randn(32, 784))
    >>> output = mlp(x)  # (32, 10)
    """

    def __init__(
        self,
        in_features: int,
        hidden_sizes: List[int],
        out_features: int,
        activation: str = 'relu',
        dropout: float = 0.0,
    ):
        super().__init__()

        layers = []
        sizes = [in_features] + hidden_sizes

        for i in range(len(sizes) - 1):
            layers.append(Linear(sizes[i], sizes[i + 1]))
            layers.append(self._get_activation(activation))
            if dropout > 0:
                layers.append(Dropout(dropout))

        layers.append(Linear(sizes[-1], out_features))

        self.layers = Sequential(*layers)

    def _get_activation(self, name: str) -> Module:
        activations = {
            'relu': ReLU(),
            'gelu': GELU(),
        }
        return activations.get(name, ReLU())

    def forward(self, x: Tensor) -> Tensor:
        return self.layers(x)


class ConvBlock(Module):
    """
    Convolutional block with BatchNorm and ReLU.
    """

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int = 3,
        stride: int = 1,
        padding: int = 1,
    ):
        super().__init__()
        self.conv = Conv2d(in_channels, out_channels, kernel_size, stride, padding)
        self.bn = BatchNorm2d(out_channels)
        self.relu = ReLU()

    def forward(self, x: Tensor) -> Tensor:
        return self.relu(self.bn(self.conv(x)))


# ResNet Architecture

class BasicBlock(Module):
    """ResNet basic block (for ResNet-18, ResNet-34)."""

    expansion = 1

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        stride: int = 1,
        downsample: Optional[Module] = None,
    ):
        super().__init__()
        self.conv1 = Conv2d(in_channels, out_channels, 3, stride, 1)
        self.bn1 = BatchNorm2d(out_channels)
        self.relu = ReLU()
        self.conv2 = Conv2d(out_channels, out_channels, 3, 1, 1)
        self.bn2 = BatchNorm2d(out_channels)
        self.downsample = downsample

    def forward(self, x: Tensor) -> Tensor:
        identity = x

        out = self.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))

        if self.downsample is not None:
            identity = self.downsample(x)

        out = out + identity
        out = self.relu(out)

        return out


class Bottleneck(Module):
    """ResNet bottleneck block (for ResNet-50, ResNet-101, ResNet-152)."""

    expansion = 4

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        stride: int = 1,
        downsample: Optional[Module] = None,
    ):
        super().__init__()
        self.conv1 = Conv2d(in_channels, out_channels, 1)
        self.bn1 = BatchNorm2d(out_channels)
        self.conv2 = Conv2d(out_channels, out_channels, 3, stride, 1)
        self.bn2 = BatchNorm2d(out_channels)
        self.conv3 = Conv2d(out_channels, out_channels * self.expansion, 1)
        self.bn3 = BatchNorm2d(out_channels * self.expansion)
        self.relu = ReLU()
        self.downsample = downsample

    def forward(self, x: Tensor) -> Tensor:
        identity = x

        out = self.relu(self.bn1(self.conv1(x)))
        out = self.relu(self.bn2(self.conv2(out)))
        out = self.bn3(self.conv3(out))

        if self.downsample is not None:
            identity = self.downsample(x)

        out = out + identity
        out = self.relu(out)

        return out


class ResNet(Module):
    """
    ResNet architecture.

    Parameters
    ----------
    block : type
        Block type (BasicBlock or Bottleneck).
    layers : list
        Number of blocks in each layer.
    num_classes : int, default=1000
        Number of output classes.
    in_channels : int, default=3
        Number of input channels.

    Examples
    --------
    >>> model = ResNet(BasicBlock, [2, 2, 2, 2], num_classes=10)  # ResNet-18
    >>> x = Tensor(np.random.randn(1, 3, 224, 224))
    >>> output = model(x)  # (1, 10)
    """

    def __init__(
        self,
        block,
        layers: List[int],
        num_classes: int = 1000,
        in_channels: int = 3,
    ):
        super().__init__()
        self.in_channels = 64

        self.conv1 = Conv2d(in_channels, 64, 7, 2, 3)
        self.bn1 = BatchNorm2d(64)
        self.relu = ReLU()
        self.maxpool = MaxPool2d(3, 2, 1)

        self.layer1 = self._make_layer(block, 64, layers[0])
        self.layer2 = self._make_layer(block, 128, layers[1], stride=2)
        self.layer3 = self._make_layer(block, 256, layers[2], stride=2)
        self.layer4 = self._make_layer(block, 512, layers[3], stride=2)

        self.avgpool = AdaptiveAvgPool2d((1, 1))
        self.flatten = Flatten()
        self.fc = Linear(512 * block.expansion, num_classes)

    def _make_layer(
        self,
        block,
        out_channels: int,
        blocks: int,
        stride: int = 1,
    ) -> Sequential:
        downsample = None

        if stride != 1 or self.in_channels != out_channels * block.expansion:
            downsample = Sequential(
                Conv2d(self.in_channels, out_channels * block.expansion, 1, stride),
                BatchNorm2d(out_channels * block.expansion),
            )

        layers = [block(self.in_channels, out_channels, stride, downsample)]
        self.in_channels = out_channels * block.expansion

        for _ in range(1, blocks):
            layers.append(block(self.in_channels, out_channels))

        return Sequential(*layers)

    def forward(self, x: Tensor) -> Tensor:
        x = self.relu(self.bn1(self.conv1(x)))
        x = self.maxpool(x)

        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)

        x = self.avgpool(x)
        x = self.flatten(x)
        x = self.fc(x)

        return x


def resnet18(num_classes: int = 1000) -> ResNet:
    """ResNet-18 model."""
    return ResNet(BasicBlock, [2, 2, 2, 2], num_classes)


def resnet34(num_classes: int = 1000) -> ResNet:
    """ResNet-34 model."""
    return ResNet(BasicBlock, [3, 4, 6, 3], num_classes)


def resnet50(num_classes: int = 1000) -> ResNet:
    """ResNet-50 model."""
    return ResNet(Bottleneck, [3, 4, 6, 3], num_classes)


def resnet101(num_classes: int = 1000) -> ResNet:
    """ResNet-101 model."""
    return ResNet(Bottleneck, [3, 4, 23, 3], num_classes)


def resnet152(num_classes: int = 1000) -> ResNet:
    """ResNet-152 model."""
    return ResNet(Bottleneck, [3, 8, 36, 3], num_classes)


# VGG Architecture

class VGG(Module):
    """
    VGG architecture.

    Parameters
    ----------
    config : list
        Layer configuration.
    num_classes : int, default=1000
        Number of output classes.
    dropout : float, default=0.5
        Dropout probability.

    Examples
    --------
    >>> model = vgg16(num_classes=10)
    >>> x = Tensor(np.random.randn(1, 3, 224, 224))
    >>> output = model(x)  # (1, 10)
    """

    def __init__(
        self,
        config: List,
        num_classes: int = 1000,
        dropout: float = 0.5,
    ):
        super().__init__()
        self.features = self._make_layers(config)
        self.avgpool = AdaptiveAvgPool2d((7, 7))
        self.classifier = Sequential(
            Flatten(),
            Linear(512 * 7 * 7, 4096),
            ReLU(),
            Dropout(dropout),
            Linear(4096, 4096),
            ReLU(),
            Dropout(dropout),
            Linear(4096, num_classes),
        )

    def _make_layers(self, config: List) -> Sequential:
        layers = []
        in_channels = 3

        for v in config:
            if v == 'M':
                layers.append(MaxPool2d(2, 2))
            else:
                layers.append(Conv2d(in_channels, v, 3, 1, 1))
                layers.append(BatchNorm2d(v))
                layers.append(ReLU())
                in_channels = v

        return Sequential(*layers)

    def forward(self, x: Tensor) -> Tensor:
        x = self.features(x)
        x = self.avgpool(x)
        x = self.classifier(x)
        return x


VGG_CONFIGS = {
    'A': [64, 'M', 128, 'M', 256, 256, 'M', 512, 512, 'M', 512, 512, 'M'],
    'B': [64, 64, 'M', 128, 128, 'M', 256, 256, 'M', 512, 512, 'M', 512, 512, 'M'],
    'D': [64, 64, 'M', 128, 128, 'M', 256, 256, 256, 'M', 512, 512, 512, 'M', 512, 512, 512, 'M'],
    'E': [64, 64, 'M', 128, 128, 'M', 256, 256, 256, 256, 'M', 512, 512, 512, 512, 'M', 512, 512, 512, 512, 'M'],
}


def vgg11(num_classes: int = 1000) -> VGG:
    """VGG-11 model."""
    return VGG(VGG_CONFIGS['A'], num_classes)


def vgg13(num_classes: int = 1000) -> VGG:
    """VGG-13 model."""
    return VGG(VGG_CONFIGS['B'], num_classes)


def vgg16(num_classes: int = 1000) -> VGG:
    """VGG-16 model."""
    return VGG(VGG_CONFIGS['D'], num_classes)


def vgg19(num_classes: int = 1000) -> VGG:
    """VGG-19 model."""
    return VGG(VGG_CONFIGS['E'], num_classes)


# Simple CNN for MNIST/CIFAR

class SimpleCNN(Module):
    """
    Simple CNN for small image classification (MNIST, CIFAR-10).

    Parameters
    ----------
    in_channels : int, default=1
        Number of input channels.
    num_classes : int, default=10
        Number of output classes.

    Examples
    --------
    >>> model = SimpleCNN(in_channels=1, num_classes=10)  # For MNIST
    >>> x = Tensor(np.random.randn(32, 1, 28, 28))
    >>> output = model(x)  # (32, 10)
    """

    def __init__(self, in_channels: int = 1, num_classes: int = 10):
        super().__init__()
        self.features = Sequential(
            Conv2d(in_channels, 32, 3, 1, 1),
            ReLU(),
            MaxPool2d(2, 2),
            Conv2d(32, 64, 3, 1, 1),
            ReLU(),
            MaxPool2d(2, 2),
            Conv2d(64, 128, 3, 1, 1),
            ReLU(),
        )
        self.avgpool = AdaptiveAvgPool2d((4, 4))
        self.classifier = Sequential(
            Flatten(),
            Linear(128 * 4 * 4, 256),
            ReLU(),
            Dropout(0.5),
            Linear(256, num_classes),
        )

    def forward(self, x: Tensor) -> Tensor:
        x = self.features(x)
        x = self.avgpool(x)
        x = self.classifier(x)
        return x


# Transformer Encoder (BERT-like)

class TransformerClassifier(Module):
    """
    Transformer-based sequence classifier.

    Parameters
    ----------
    vocab_size : int
        Vocabulary size.
    d_model : int, default=512
        Model dimension.
    nhead : int, default=8
        Number of attention heads.
    num_layers : int, default=6
        Number of transformer layers.
    num_classes : int, default=2
        Number of output classes.
    max_seq_len : int, default=512
        Maximum sequence length.
    dropout : float, default=0.1
        Dropout probability.

    Examples
    --------
    >>> model = TransformerClassifier(vocab_size=30000, num_classes=2)
    >>> input_ids = Tensor(np.random.randint(0, 30000, (8, 128)))
    >>> output = model(input_ids)  # (8, 2)
    """

    def __init__(
        self,
        vocab_size: int,
        d_model: int = 512,
        nhead: int = 8,
        num_layers: int = 6,
        num_classes: int = 2,
        max_seq_len: int = 512,
        dropout: float = 0.1,
    ):
        super().__init__()
        from nalyst.nn.layers.embedding import PositionalEncoding
        from nalyst.nn.layers.attention import TransformerEncoderLayer, TransformerEncoder

        self.embedding = Embedding(vocab_size, d_model)
        self.pos_encoder = PositionalEncoding(d_model, max_seq_len, dropout)

        encoder_layer = TransformerEncoderLayer(d_model, nhead, d_model * 4, dropout)
        self.transformer = TransformerEncoder(encoder_layer, num_layers)

        self.classifier = Linear(d_model, num_classes)
        self.dropout = Dropout(dropout)

    def forward(self, x: Tensor, mask: Optional[Tensor] = None) -> Tensor:
        # Embed tokens
        x = self.embedding(x)
        x = self.pos_encoder(x)

        # Transformer encoding
        x = self.transformer(x, mask)

        # Take [CLS] token or mean pooling
        x = x.mean(dim=1) if x.data.ndim == 3 else x[:, 0]

        # Classify
        x = self.dropout(x)
        x = self.classifier(x)

        return x


# Autoencoder

class Autoencoder(Module):
    """
    Simple autoencoder for dimensionality reduction.

    Parameters
    ----------
    input_dim : int
        Input dimension.
    hidden_dims : list
        Encoder hidden dimensions.
    latent_dim : int
        Latent space dimension.

    Examples
    --------
    >>> model = Autoencoder(784, [512, 256], 32)
    >>> x = Tensor(np.random.randn(32, 784))
    >>> reconstructed = model(x)  # (32, 784)
    >>> latent = model.encode(x)  # (32, 32)
    """

    def __init__(
        self,
        input_dim: int,
        hidden_dims: List[int],
        latent_dim: int,
    ):
        super().__init__()

        # Encoder
        encoder_layers = []
        in_dim = input_dim
        for h_dim in hidden_dims:
            encoder_layers.extend([
                Linear(in_dim, h_dim),
                ReLU(),
            ])
            in_dim = h_dim
        encoder_layers.append(Linear(in_dim, latent_dim))
        self.encoder = Sequential(*encoder_layers)

        # Decoder
        decoder_layers = []
        in_dim = latent_dim
        for h_dim in reversed(hidden_dims):
            decoder_layers.extend([
                Linear(in_dim, h_dim),
                ReLU(),
            ])
            in_dim = h_dim
        decoder_layers.append(Linear(in_dim, input_dim))
        self.decoder = Sequential(*decoder_layers)

    def encode(self, x: Tensor) -> Tensor:
        return self.encoder(x)

    def decode(self, z: Tensor) -> Tensor:
        return self.decoder(z)

    def forward(self, x: Tensor) -> Tensor:
        z = self.encode(x)
        return self.decode(z)


class VAE(Autoencoder):
    """
    Variational Autoencoder.

    Parameters
    ----------
    input_dim : int
        Input dimension.
    hidden_dims : list
        Encoder hidden dimensions.
    latent_dim : int
        Latent space dimension.

    Examples
    --------
    >>> model = VAE(784, [512, 256], 32)
    >>> x = Tensor(np.random.randn(32, 784))
    >>> reconstructed, mu, logvar = model(x)
    >>> kl_loss = -0.5 * (1 + logvar - mu ** 2 - logvar.exp()).sum()
    """

    def __init__(
        self,
        input_dim: int,
        hidden_dims: List[int],
        latent_dim: int,
    ):
        # Build encoder up to last hidden layer
        Module.__init__(self)

        encoder_layers = []
        in_dim = input_dim
        for h_dim in hidden_dims:
            encoder_layers.extend([
                Linear(in_dim, h_dim),
                ReLU(),
            ])
            in_dim = h_dim
        self.encoder = Sequential(*encoder_layers)

        # Mean and variance heads
        self.fc_mu = Linear(in_dim, latent_dim)
        self.fc_var = Linear(in_dim, latent_dim)

        # Decoder
        decoder_layers = []
        in_dim = latent_dim
        for h_dim in reversed(hidden_dims):
            decoder_layers.extend([
                Linear(in_dim, h_dim),
                ReLU(),
            ])
            in_dim = h_dim
        decoder_layers.append(Linear(in_dim, input_dim))
        self.decoder = Sequential(*decoder_layers)

    def encode(self, x: Tensor) -> Tuple[Tensor, Tensor]:
        h = self.encoder(x)
        mu = self.fc_mu(h)
        logvar = self.fc_var(h)
        return mu, logvar

    def reparameterize(self, mu: Tensor, logvar: Tensor) -> Tensor:
        std = Tensor(np.exp(0.5 * logvar.data))
        eps = Tensor(np.random.randn(*mu.shape))
        return mu + eps * std

    def forward(self, x: Tensor) -> Tuple[Tensor, Tensor, Tensor]:
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar)
        return self.decode(z), mu, logvar


# GAN Components

class Generator(Module):
    """
    Generator for GAN.

    Parameters
    ----------
    latent_dim : int
        Latent dimension.
    output_dim : int
        Output dimension.
    hidden_dims : list, optional
        Hidden layer dimensions.
    """

    def __init__(
        self,
        latent_dim: int,
        output_dim: int,
        hidden_dims: Optional[List[int]] = None,
    ):
        super().__init__()

        if hidden_dims is None:
            hidden_dims = [256, 512, 1024]

        layers = []
        in_dim = latent_dim
        for h_dim in hidden_dims:
            layers.extend([
                Linear(in_dim, h_dim),
                ReLU(),
            ])
            in_dim = h_dim

        layers.append(Linear(in_dim, output_dim))
        self.model = Sequential(*layers)

    def forward(self, z: Tensor) -> Tensor:
        return self.model(z).tanh()


class Discriminator(Module):
    """
    Discriminator for GAN.

    Parameters
    ----------
    input_dim : int
        Input dimension.
    hidden_dims : list, optional
        Hidden layer dimensions.
    """

    def __init__(
        self,
        input_dim: int,
        hidden_dims: Optional[List[int]] = None,
    ):
        super().__init__()

        if hidden_dims is None:
            hidden_dims = [512, 256]

        layers = []
        in_dim = input_dim
        for h_dim in hidden_dims:
            layers.extend([
                Linear(in_dim, h_dim),
                ReLU(),
                Dropout(0.3),
            ])
            in_dim = h_dim

        layers.append(Linear(in_dim, 1))
        self.model = Sequential(*layers)

    def forward(self, x: Tensor) -> Tensor:
        return self.model(x).sigmoid()
