"""
Attention and Transformer layers.
"""

from __future__ import annotations

from typing import Optional, Tuple
import numpy as np

from nalyst.nn.module import Module, ModuleList
from nalyst.nn.parameter import Parameter
from nalyst.nn.tensor import Tensor
from nalyst.nn.layers.linear import Linear
from nalyst.nn.layers.normalization import LayerNorm
from nalyst.nn.layers.dropout import Dropout


class MultiHeadAttention(Module):
    """
    Multi-Head Attention mechanism.

    Parameters
    ----------
    embed_dim : int
        Total dimension of the model.
    num_heads : int
        Number of attention heads.
    dropout : float, default=0.0
        Dropout probability.
    bias : bool, default=True
        If True, adds bias to projections.

    Examples
    --------
    >>> mha = nn.MultiHeadAttention(512, 8)
    >>> query = Tensor(np.random.randn(32, 10, 512))
    >>> key = Tensor(np.random.randn(32, 20, 512))
    >>> value = Tensor(np.random.randn(32, 20, 512))
    >>> output, weights = mha(query, key, value)
    """

    def __init__(
        self,
        embed_dim: int,
        num_heads: int,
        dropout: float = 0.0,
        bias: bool = True,
    ):
        super().__init__()
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        self.dropout_p = dropout

        if self.head_dim * num_heads != embed_dim:
            raise ValueError("embed_dim must be divisible by num_heads")

        self.scale = self.head_dim ** -0.5

        # Linear projections
        self.q_proj = Linear(embed_dim, embed_dim, bias=bias)
        self.k_proj = Linear(embed_dim, embed_dim, bias=bias)
        self.v_proj = Linear(embed_dim, embed_dim, bias=bias)
        self.out_proj = Linear(embed_dim, embed_dim, bias=bias)

        if dropout > 0:
            self.dropout = Dropout(dropout)
        else:
            self.dropout = None

    def forward(
        self,
        query: Tensor,
        key: Tensor,
        value: Tensor,
        attn_mask: Optional[Tensor] = None,
        key_padding_mask: Optional[Tensor] = None,
    ) -> Tuple[Tensor, Tensor]:
        """
        Compute multi-head attention.

        Parameters
        ----------
        query : Tensor
            Query tensor of shape (batch, seq_q, embed_dim).
        key : Tensor
            Key tensor of shape (batch, seq_k, embed_dim).
        value : Tensor
            Value tensor of shape (batch, seq_k, embed_dim).
        attn_mask : Tensor, optional
            Attention mask of shape (seq_q, seq_k) or (batch, seq_q, seq_k).
        key_padding_mask : Tensor, optional
            Padding mask of shape (batch, seq_k).

        Returns
        -------
        output : Tensor
            Output of shape (batch, seq_q, embed_dim).
        weights : Tensor
            Attention weights of shape (batch, num_heads, seq_q, seq_k).
        """
        batch_size, seq_q, _ = query.shape
        seq_k = key.shape[1]

        # Project Q, K, V
        Q = self.q_proj(query)
        K = self.k_proj(key)
        V = self.v_proj(value)

        # Reshape for multi-head: (batch, seq, embed) -> (batch, num_heads, seq, head_dim)
        Q = Tensor(
            Q.data.reshape(batch_size, seq_q, self.num_heads, self.head_dim).transpose(0, 2, 1, 3),
            requires_grad=Q.requires_grad
        )
        K = Tensor(
            K.data.reshape(batch_size, seq_k, self.num_heads, self.head_dim).transpose(0, 2, 1, 3),
            requires_grad=K.requires_grad
        )
        V = Tensor(
            V.data.reshape(batch_size, seq_k, self.num_heads, self.head_dim).transpose(0, 2, 1, 3),
            requires_grad=V.requires_grad
        )

        # Compute attention scores: (batch, heads, seq_q, seq_k)
        scores = Tensor(
            np.einsum('bhqd,bhkd->bhqk', Q.data, K.data) * self.scale,
            requires_grad=Q.requires_grad or K.requires_grad
        )

        # Apply attention mask
        if attn_mask is not None:
            if attn_mask.ndim == 2:
                mask = attn_mask.data[None, None, :, :]
            else:
                mask = attn_mask.data[:, None, :, :]
            scores = Tensor(scores.data + mask, requires_grad=scores.requires_grad)

        # Apply key padding mask
        if key_padding_mask is not None:
            mask = key_padding_mask.data[:, None, None, :]
            scores = Tensor(
                np.where(mask, -np.inf, scores.data),
                requires_grad=scores.requires_grad
            )

        # Softmax
        weights = scores.softmax(axis=-1)

        # Apply dropout
        if self.dropout is not None and self.training:
            weights = self.dropout(weights)

        # Compute output: (batch, heads, seq_q, head_dim)
        output = Tensor(
            np.einsum('bhqk,bhkd->bhqd', weights.data, V.data),
            requires_grad=V.requires_grad
        )

        # Reshape back: (batch, seq_q, embed_dim)
        output = Tensor(
            output.data.transpose(0, 2, 1, 3).reshape(batch_size, seq_q, self.embed_dim),
            requires_grad=output.requires_grad
        )

        # Output projection
        output = self.out_proj(output)

        return output, weights

    def __repr__(self) -> str:
        return f"MultiHeadAttention(embed_dim={self.embed_dim}, num_heads={self.num_heads})"


class TransformerEncoderLayer(Module):
    """
    Transformer encoder layer.

    Parameters
    ----------
    d_model : int
        Model dimension.
    nhead : int
        Number of attention heads.
    dim_feedforward : int, default=2048
        Dimension of feedforward network.
    dropout : float, default=0.1
        Dropout probability.
    activation : str, default='relu'
        Activation function ('relu' or 'gelu').
    layer_norm_eps : float, default=1e-5
        Epsilon for layer normalization.

    Examples
    --------
    >>> encoder_layer = nn.TransformerEncoderLayer(512, 8)
    >>> x = Tensor(np.random.randn(32, 10, 512))
    >>> output = encoder_layer(x)
    """

    def __init__(
        self,
        d_model: int,
        nhead: int,
        dim_feedforward: int = 2048,
        dropout: float = 0.1,
        activation: str = 'relu',
        layer_norm_eps: float = 1e-5,
    ):
        super().__init__()
        self.self_attn = MultiHeadAttention(d_model, nhead, dropout=dropout)

        # Feedforward
        self.linear1 = Linear(d_model, dim_feedforward)
        self.linear2 = Linear(dim_feedforward, d_model)

        # Layer norms
        self.norm1 = LayerNorm(d_model, eps=layer_norm_eps)
        self.norm2 = LayerNorm(d_model, eps=layer_norm_eps)

        # Dropout
        self.dropout = Dropout(dropout)
        self.dropout1 = Dropout(dropout)
        self.dropout2 = Dropout(dropout)

        self.activation = activation

    def forward(
        self,
        src: Tensor,
        src_mask: Optional[Tensor] = None,
        src_key_padding_mask: Optional[Tensor] = None,
    ) -> Tensor:
        """
        Forward pass.

        Parameters
        ----------
        src : Tensor
            Source sequence of shape (batch, seq, d_model).
        src_mask : Tensor, optional
            Attention mask.
        src_key_padding_mask : Tensor, optional
            Padding mask.

        Returns
        -------
        Tensor
            Output of shape (batch, seq, d_model).
        """
        # Self-attention with residual connection
        attn_output, _ = self.self_attn(src, src, src, attn_mask=src_mask, key_padding_mask=src_key_padding_mask)
        src = src + self.dropout1(attn_output)
        src = self.norm1(src)

        # Feedforward with residual connection
        ff_output = self.linear1(src)
        if self.activation == 'relu':
            ff_output = ff_output.relu()
        else:
            ff_output = ff_output.gelu()
        ff_output = self.dropout(ff_output)
        ff_output = self.linear2(ff_output)

        src = src + self.dropout2(ff_output)
        src = self.norm2(src)

        return src

    def __repr__(self) -> str:
        return f"TransformerEncoderLayer(d_model={self.self_attn.embed_dim}, nhead={self.self_attn.num_heads})"


class TransformerDecoderLayer(Module):
    """
    Transformer decoder layer.

    Parameters
    ----------
    d_model : int
        Model dimension.
    nhead : int
        Number of attention heads.
    dim_feedforward : int, default=2048
        Dimension of feedforward network.
    dropout : float, default=0.1
        Dropout probability.
    activation : str, default='relu'
        Activation function.
    layer_norm_eps : float, default=1e-5
        Epsilon for layer normalization.
    """

    def __init__(
        self,
        d_model: int,
        nhead: int,
        dim_feedforward: int = 2048,
        dropout: float = 0.1,
        activation: str = 'relu',
        layer_norm_eps: float = 1e-5,
    ):
        super().__init__()
        self.self_attn = MultiHeadAttention(d_model, nhead, dropout=dropout)
        self.multihead_attn = MultiHeadAttention(d_model, nhead, dropout=dropout)

        # Feedforward
        self.linear1 = Linear(d_model, dim_feedforward)
        self.linear2 = Linear(dim_feedforward, d_model)

        # Layer norms
        self.norm1 = LayerNorm(d_model, eps=layer_norm_eps)
        self.norm2 = LayerNorm(d_model, eps=layer_norm_eps)
        self.norm3 = LayerNorm(d_model, eps=layer_norm_eps)

        # Dropout
        self.dropout = Dropout(dropout)
        self.dropout1 = Dropout(dropout)
        self.dropout2 = Dropout(dropout)
        self.dropout3 = Dropout(dropout)

        self.activation = activation

    def forward(
        self,
        tgt: Tensor,
        memory: Tensor,
        tgt_mask: Optional[Tensor] = None,
        memory_mask: Optional[Tensor] = None,
        tgt_key_padding_mask: Optional[Tensor] = None,
        memory_key_padding_mask: Optional[Tensor] = None,
    ) -> Tensor:
        """
        Forward pass.

        Parameters
        ----------
        tgt : Tensor
            Target sequence of shape (batch, tgt_seq, d_model).
        memory : Tensor
            Encoder output of shape (batch, src_seq, d_model).

        Returns
        -------
        Tensor
            Output of shape (batch, tgt_seq, d_model).
        """
        # Self-attention
        attn_output, _ = self.self_attn(tgt, tgt, tgt, attn_mask=tgt_mask, key_padding_mask=tgt_key_padding_mask)
        tgt = tgt + self.dropout1(attn_output)
        tgt = self.norm1(tgt)

        # Cross-attention
        attn_output, _ = self.multihead_attn(tgt, memory, memory, attn_mask=memory_mask, key_padding_mask=memory_key_padding_mask)
        tgt = tgt + self.dropout2(attn_output)
        tgt = self.norm2(tgt)

        # Feedforward
        ff_output = self.linear1(tgt)
        if self.activation == 'relu':
            ff_output = ff_output.relu()
        else:
            ff_output = ff_output.gelu()
        ff_output = self.dropout(ff_output)
        ff_output = self.linear2(ff_output)

        tgt = tgt + self.dropout3(ff_output)
        tgt = self.norm3(tgt)

        return tgt

    def __repr__(self) -> str:
        return f"TransformerDecoderLayer(d_model={self.self_attn.embed_dim}, nhead={self.self_attn.num_heads})"


class TransformerEncoder(Module):
    """
    Stack of Transformer encoder layers.

    Parameters
    ----------
    encoder_layer : TransformerEncoderLayer
        Single encoder layer.
    num_layers : int
        Number of encoder layers.

    Examples
    --------
    >>> encoder_layer = nn.TransformerEncoderLayer(512, 8)
    >>> encoder = nn.TransformerEncoder(encoder_layer, num_layers=6)
    >>> x = Tensor(np.random.randn(32, 10, 512))
    >>> output = encoder(x)
    """

    def __init__(
        self,
        encoder_layer: TransformerEncoderLayer,
        num_layers: int,
    ):
        super().__init__()
        self.layers = ModuleList([encoder_layer for _ in range(num_layers)])
        self.num_layers = num_layers

    def forward(
        self,
        src: Tensor,
        mask: Optional[Tensor] = None,
        src_key_padding_mask: Optional[Tensor] = None,
    ) -> Tensor:
        output = src
        for layer in self.layers:
            output = layer(output, src_mask=mask, src_key_padding_mask=src_key_padding_mask)
        return output

    def __repr__(self) -> str:
        return f"TransformerEncoder(num_layers={self.num_layers})"


class TransformerDecoder(Module):
    """
    Stack of Transformer decoder layers.

    Parameters
    ----------
    decoder_layer : TransformerDecoderLayer
        Single decoder layer.
    num_layers : int
        Number of decoder layers.
    """

    def __init__(
        self,
        decoder_layer: TransformerDecoderLayer,
        num_layers: int,
    ):
        super().__init__()
        self.layers = ModuleList([decoder_layer for _ in range(num_layers)])
        self.num_layers = num_layers

    def forward(
        self,
        tgt: Tensor,
        memory: Tensor,
        tgt_mask: Optional[Tensor] = None,
        memory_mask: Optional[Tensor] = None,
        tgt_key_padding_mask: Optional[Tensor] = None,
        memory_key_padding_mask: Optional[Tensor] = None,
    ) -> Tensor:
        output = tgt
        for layer in self.layers:
            output = layer(
                output, memory,
                tgt_mask=tgt_mask,
                memory_mask=memory_mask,
                tgt_key_padding_mask=tgt_key_padding_mask,
                memory_key_padding_mask=memory_key_padding_mask,
            )
        return output

    def __repr__(self) -> str:
        return f"TransformerDecoder(num_layers={self.num_layers})"


class Transformer(Module):
    """
    Complete Transformer model.

    Parameters
    ----------
    d_model : int, default=512
        Model dimension.
    nhead : int, default=8
        Number of attention heads.
    num_encoder_layers : int, default=6
        Number of encoder layers.
    num_decoder_layers : int, default=6
        Number of decoder layers.
    dim_feedforward : int, default=2048
        Dimension of feedforward network.
    dropout : float, default=0.1
        Dropout probability.
    activation : str, default='relu'
        Activation function.

    Examples
    --------
    >>> transformer = nn.Transformer(d_model=512, nhead=8)
    >>> src = Tensor(np.random.randn(32, 10, 512))
    >>> tgt = Tensor(np.random.randn(32, 20, 512))
    >>> output = transformer(src, tgt)
    """

    def __init__(
        self,
        d_model: int = 512,
        nhead: int = 8,
        num_encoder_layers: int = 6,
        num_decoder_layers: int = 6,
        dim_feedforward: int = 2048,
        dropout: float = 0.1,
        activation: str = 'relu',
    ):
        super().__init__()

        encoder_layer = TransformerEncoderLayer(
            d_model, nhead, dim_feedforward, dropout, activation
        )
        self.encoder = TransformerEncoder(encoder_layer, num_encoder_layers)

        decoder_layer = TransformerDecoderLayer(
            d_model, nhead, dim_feedforward, dropout, activation
        )
        self.decoder = TransformerDecoder(decoder_layer, num_decoder_layers)

        self.d_model = d_model
        self.nhead = nhead

    def forward(
        self,
        src: Tensor,
        tgt: Tensor,
        src_mask: Optional[Tensor] = None,
        tgt_mask: Optional[Tensor] = None,
        memory_mask: Optional[Tensor] = None,
        src_key_padding_mask: Optional[Tensor] = None,
        tgt_key_padding_mask: Optional[Tensor] = None,
        memory_key_padding_mask: Optional[Tensor] = None,
    ) -> Tensor:
        """
        Forward pass.

        Parameters
        ----------
        src : Tensor
            Source sequence of shape (batch, src_seq, d_model).
        tgt : Tensor
            Target sequence of shape (batch, tgt_seq, d_model).

        Returns
        -------
        Tensor
            Output of shape (batch, tgt_seq, d_model).
        """
        memory = self.encoder(src, mask=src_mask, src_key_padding_mask=src_key_padding_mask)
        output = self.decoder(
            tgt, memory,
            tgt_mask=tgt_mask,
            memory_mask=memory_mask,
            tgt_key_padding_mask=tgt_key_padding_mask,
            memory_key_padding_mask=memory_key_padding_mask,
        )
        return output

    @staticmethod
    def generate_square_subsequent_mask(size: int) -> Tensor:
        """
        Generate causal mask for decoder.

        Parameters
        ----------
        size : int
            Sequence length.

        Returns
        -------
        Tensor
            Mask of shape (size, size) with -inf above diagonal.
        """
        mask = np.triu(np.ones((size, size)) * -np.inf, k=1)
        return Tensor(mask.astype(np.float32))

    def __repr__(self) -> str:
        return f"Transformer(d_model={self.d_model}, nhead={self.nhead})"
