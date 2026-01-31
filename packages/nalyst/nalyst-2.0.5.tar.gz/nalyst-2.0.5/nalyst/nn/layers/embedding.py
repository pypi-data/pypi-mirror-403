"""
Embedding layers.
"""

from __future__ import annotations

from typing import Optional
import numpy as np

from nalyst.nn.module import Module
from nalyst.nn.parameter import Parameter
from nalyst.nn.tensor import Tensor


class Embedding(Module):
    """
    A lookup table that stores embeddings of a fixed dictionary.

    Parameters
    ----------
    num_embeddings : int
        Size of the vocabulary.
    embedding_dim : int
        Dimension of each embedding vector.
    padding_idx : int, optional
        If specified, entries at this index won't contribute to gradient.
    max_norm : float, optional
        If given, renormalize embeddings to have max norm.

    Examples
    --------
    >>> embedding = nn.Embedding(10000, 300)
    >>> input_ids = Tensor([[1, 2, 3], [4, 5, 6]])
    >>> embeddings = embedding(input_ids)  # (2, 3, 300)
    """

    def __init__(
        self,
        num_embeddings: int,
        embedding_dim: int,
        padding_idx: Optional[int] = None,
        max_norm: Optional[float] = None,
    ):
        super().__init__()
        self.num_embeddings = num_embeddings
        self.embedding_dim = embedding_dim
        self.padding_idx = padding_idx
        self.max_norm = max_norm

        # Initialize embeddings
        self.weight = Parameter(
            np.random.normal(0, 1, (num_embeddings, embedding_dim))
        )

        # Zero out padding index
        if padding_idx is not None:
            self.weight.data[padding_idx] = 0

    def forward(self, x: Tensor) -> Tensor:
        """
        Look up embeddings.

        Parameters
        ----------
        x : Tensor
            Input indices of shape (*).

        Returns
        -------
        Tensor
            Embeddings of shape (*, embedding_dim).
        """
        indices = x.data.astype(np.int64)

        # Look up embeddings
        output_data = self.weight.data[indices]

        # Renormalize if max_norm specified
        if self.max_norm is not None:
            norms = np.linalg.norm(output_data, axis=-1, keepdims=True)
            output_data = np.where(
                norms > self.max_norm,
                output_data * self.max_norm / (norms + 1e-8),
                output_data
            )

        output = Tensor(
            output_data,
            requires_grad=self.weight.requires_grad,
            _children=(self.weight,),
            _op="embedding",
        )

        def _backward():
            if self.weight.requires_grad:
                if self.weight.grad is None:
                    self.weight.grad = np.zeros_like(self.weight.data)

                # Accumulate gradients for each index
                np.add.at(
                    self.weight.grad,
                    indices.flatten(),
                    output.grad.reshape(-1, self.embedding_dim)
                )

                # Zero gradient for padding index
                if self.padding_idx is not None:
                    self.weight.grad[self.padding_idx] = 0

        output._backward = _backward
        return output

    @classmethod
    def from_pretrained(
        cls,
        embeddings: np.ndarray,
        freeze: bool = True,
        padding_idx: Optional[int] = None,
    ) -> "Embedding":
        """
        Create Embedding from pretrained weights.

        Parameters
        ----------
        embeddings : ndarray
            Pretrained embeddings of shape (num_embeddings, embedding_dim).
        freeze : bool, default=True
            If True, embeddings are not updated during training.
        padding_idx : int, optional
            Padding index.

        Returns
        -------
        Embedding
            Embedding layer with pretrained weights.
        """
        num_embeddings, embedding_dim = embeddings.shape
        embedding = cls(num_embeddings, embedding_dim, padding_idx=padding_idx)
        embedding.weight.data = embeddings.copy()
        embedding.weight.requires_grad = not freeze
        return embedding

    def __repr__(self) -> str:
        return f"Embedding({self.num_embeddings}, {self.embedding_dim})"


class EmbeddingBag(Module):
    """
    Computes sums or means of bags of embeddings.

    Parameters
    ----------
    num_embeddings : int
        Size of the vocabulary.
    embedding_dim : int
        Dimension of each embedding vector.
    mode : str, default='mean'
        Aggregation mode ('sum', 'mean', or 'max').

    Examples
    --------
    >>> embedding_bag = nn.EmbeddingBag(10, 3, mode='sum')
    >>> input_ids = Tensor([[1, 2, 4], [4, 3, 2]])
    >>> output = embedding_bag(input_ids)  # (2, 3)
    """

    def __init__(
        self,
        num_embeddings: int,
        embedding_dim: int,
        mode: str = 'mean',
    ):
        super().__init__()
        self.num_embeddings = num_embeddings
        self.embedding_dim = embedding_dim
        self.mode = mode

        self.weight = Parameter(
            np.random.normal(0, 1, (num_embeddings, embedding_dim))
        )

    def forward(self, x: Tensor, offsets: Optional[Tensor] = None) -> Tensor:
        """
        Compute aggregated embeddings.

        Parameters
        ----------
        x : Tensor
            Input indices.
        offsets : Tensor, optional
            Offsets for each bag (used with 1D input).

        Returns
        -------
        Tensor
            Aggregated embeddings.
        """
        indices = x.data.astype(np.int64)
        embeddings = self.weight.data[indices]

        if self.mode == 'sum':
            output_data = embeddings.sum(axis=-2)
        elif self.mode == 'mean':
            output_data = embeddings.mean(axis=-2)
        elif self.mode == 'max':
            output_data = embeddings.max(axis=-2)
        else:
            raise ValueError(f"Unknown mode: {self.mode}")

        return Tensor(output_data, requires_grad=self.weight.requires_grad)

    def __repr__(self) -> str:
        return f"EmbeddingBag({self.num_embeddings}, {self.embedding_dim}, mode='{self.mode}')"


class PositionalEncoding(Module):
    """
    Sinusoidal positional encoding for Transformers.

    Parameters
    ----------
    d_model : int
        Model dimension.
    max_len : int, default=5000
        Maximum sequence length.
    dropout : float, default=0.1
        Dropout probability.

    Examples
    --------
    >>> pos_enc = nn.PositionalEncoding(512)
    >>> x = Tensor(np.random.randn(32, 100, 512))
    >>> output = pos_enc(x)
    """

    def __init__(
        self,
        d_model: int,
        max_len: int = 5000,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.d_model = d_model
        self.dropout_p = dropout

        # Create positional encoding matrix
        pe = np.zeros((max_len, d_model))
        position = np.arange(max_len)[:, np.newaxis]
        div_term = np.exp(np.arange(0, d_model, 2) * (-np.log(10000.0) / d_model))

        pe[:, 0::2] = np.sin(position * div_term)
        pe[:, 1::2] = np.cos(position * div_term)

        # Register as buffer (not a parameter)
        self.register_buffer("pe", Tensor(pe[np.newaxis, :, :]))

        if dropout > 0:
            from nalyst.nn.layers.dropout import Dropout
            self.dropout = Dropout(dropout)
        else:
            self.dropout = None

    def forward(self, x: Tensor) -> Tensor:
        """
        Add positional encoding to input.

        Parameters
        ----------
        x : Tensor
            Input of shape (batch, seq_len, d_model).

        Returns
        -------
        Tensor
            Output with positional encoding added.
        """
        seq_len = x.shape[1]

        # Add positional encoding
        x = x + Tensor(self.pe.data[:, :seq_len, :], requires_grad=False)

        if self.dropout is not None:
            x = self.dropout(x)

        return x

    def __repr__(self) -> str:
        return f"PositionalEncoding(d_model={self.d_model})"


class LearnedPositionalEncoding(Module):
    """
    Learned positional embeddings.

    Parameters
    ----------
    d_model : int
        Model dimension.
    max_len : int, default=512
        Maximum sequence length.
    dropout : float, default=0.1
        Dropout probability.
    """

    def __init__(
        self,
        d_model: int,
        max_len: int = 512,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.d_model = d_model
        self.max_len = max_len

        self.embedding = Embedding(max_len, d_model)

        if dropout > 0:
            from nalyst.nn.layers.dropout import Dropout
            self.dropout = Dropout(dropout)
        else:
            self.dropout = None

    def forward(self, x: Tensor) -> Tensor:
        """
        Add learned positional encoding.

        Parameters
        ----------
        x : Tensor
            Input of shape (batch, seq_len, d_model).

        Returns
        -------
        Tensor
            Output with positional encoding added.
        """
        batch_size, seq_len = x.shape[:2]

        # Create position indices
        positions = Tensor(np.arange(seq_len)[np.newaxis, :].repeat(batch_size, axis=0))

        # Add positional embeddings
        x = x + self.embedding(positions)

        if self.dropout is not None:
            x = self.dropout(x)

        return x

    def __repr__(self) -> str:
        return f"LearnedPositionalEncoding(d_model={self.d_model}, max_len={self.max_len})"
