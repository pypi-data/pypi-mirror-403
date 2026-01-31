"""
Recurrent layers (RNN, LSTM, GRU).
"""

from __future__ import annotations

from typing import Optional, Tuple
import numpy as np

from nalyst.nn.module import Module
from nalyst.nn.parameter import Parameter
from nalyst.nn.tensor import Tensor


class RNNCell(Module):
    """
    An Elman RNN cell.

    h' = tanh(W_ih @ x + b_ih + W_hh @ h + b_hh)

    Parameters
    ----------
    input_size : int
        Size of input features.
    hidden_size : int
        Size of hidden state.
    bias : bool, default=True
        If True, adds bias terms.
    nonlinearity : str, default='tanh'
        Nonlinearity ('tanh' or 'relu').

    Examples
    --------
    >>> rnn_cell = nn.RNNCell(10, 20)
    >>> x = Tensor(np.random.randn(32, 10))
    >>> h = Tensor(np.random.randn(32, 20))
    >>> h_new = rnn_cell(x, h)
    """

    def __init__(
        self,
        input_size: int,
        hidden_size: int,
        bias: bool = True,
        nonlinearity: str = 'tanh',
    ):
        super().__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.nonlinearity = nonlinearity

        k = 1 / hidden_size

        self.weight_ih = Parameter(
            np.random.uniform(-np.sqrt(k), np.sqrt(k), (hidden_size, input_size))
        )
        self.weight_hh = Parameter(
            np.random.uniform(-np.sqrt(k), np.sqrt(k), (hidden_size, hidden_size))
        )

        if bias:
            self.bias_ih = Parameter(np.zeros(hidden_size))
            self.bias_hh = Parameter(np.zeros(hidden_size))
        else:
            self.register_parameter("bias_ih", None)
            self.register_parameter("bias_hh", None)

    def forward(
        self,
        x: Tensor,
        h: Optional[Tensor] = None,
    ) -> Tensor:
        batch_size = x.shape[0]

        if h is None:
            h = Tensor(np.zeros((batch_size, self.hidden_size)))

        # Compute new hidden state
        ih = x.matmul(self.weight_ih.transpose())
        hh = h.matmul(self.weight_hh.transpose())

        if self.bias_ih is not None:
            ih = ih + self.bias_ih
        if self.bias_hh is not None:
            hh = hh + self.bias_hh

        h_new = ih + hh

        if self.nonlinearity == 'tanh':
            h_new = h_new.tanh()
        else:
            h_new = h_new.relu()

        return h_new

    def __repr__(self) -> str:
        return f"RNNCell({self.input_size}, {self.hidden_size})"


class LSTMCell(Module):
    """
    Long Short-Term Memory cell.

    Parameters
    ----------
    input_size : int
        Size of input features.
    hidden_size : int
        Size of hidden state.
    bias : bool, default=True
        If True, adds bias terms.

    Examples
    --------
    >>> lstm_cell = nn.LSTMCell(10, 20)
    >>> x = Tensor(np.random.randn(32, 10))
    >>> h, c = Tensor(np.zeros((32, 20))), Tensor(np.zeros((32, 20)))
    >>> h_new, c_new = lstm_cell(x, (h, c))
    """

    def __init__(
        self,
        input_size: int,
        hidden_size: int,
        bias: bool = True,
    ):
        super().__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size

        k = 1 / hidden_size

        # Combined weights for all 4 gates: input, forget, cell, output
        self.weight_ih = Parameter(
            np.random.uniform(-np.sqrt(k), np.sqrt(k), (4 * hidden_size, input_size))
        )
        self.weight_hh = Parameter(
            np.random.uniform(-np.sqrt(k), np.sqrt(k), (4 * hidden_size, hidden_size))
        )

        if bias:
            self.bias_ih = Parameter(np.zeros(4 * hidden_size))
            self.bias_hh = Parameter(np.zeros(4 * hidden_size))
        else:
            self.register_parameter("bias_ih", None)
            self.register_parameter("bias_hh", None)

    def forward(
        self,
        x: Tensor,
        hx: Optional[Tuple[Tensor, Tensor]] = None,
    ) -> Tuple[Tensor, Tensor]:
        batch_size = x.shape[0]

        if hx is None:
            h = Tensor(np.zeros((batch_size, self.hidden_size)))
            c = Tensor(np.zeros((batch_size, self.hidden_size)))
        else:
            h, c = hx

        # Compute gates
        gates = x.matmul(self.weight_ih.transpose()) + h.matmul(self.weight_hh.transpose())

        if self.bias_ih is not None:
            gates = gates + self.bias_ih
        if self.bias_hh is not None:
            gates = gates + self.bias_hh

        # Split into 4 gates
        hs = self.hidden_size
        i_gate = Tensor(gates.data[:, :hs], requires_grad=gates.requires_grad).sigmoid()
        f_gate = Tensor(gates.data[:, hs:2*hs], requires_grad=gates.requires_grad).sigmoid()
        g_gate = Tensor(gates.data[:, 2*hs:3*hs], requires_grad=gates.requires_grad).tanh()
        o_gate = Tensor(gates.data[:, 3*hs:], requires_grad=gates.requires_grad).sigmoid()

        # Update cell and hidden state
        c_new = f_gate * c + i_gate * g_gate
        h_new = o_gate * c_new.tanh()

        return h_new, c_new

    def __repr__(self) -> str:
        return f"LSTMCell({self.input_size}, {self.hidden_size})"


class GRUCell(Module):
    """
    Gated Recurrent Unit cell.

    Parameters
    ----------
    input_size : int
        Size of input features.
    hidden_size : int
        Size of hidden state.
    bias : bool, default=True
        If True, adds bias terms.

    Examples
    --------
    >>> gru_cell = nn.GRUCell(10, 20)
    >>> x = Tensor(np.random.randn(32, 10))
    >>> h = Tensor(np.zeros((32, 20)))
    >>> h_new = gru_cell(x, h)
    """

    def __init__(
        self,
        input_size: int,
        hidden_size: int,
        bias: bool = True,
    ):
        super().__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size

        k = 1 / hidden_size

        # Weights for reset and update gates
        self.weight_ih = Parameter(
            np.random.uniform(-np.sqrt(k), np.sqrt(k), (3 * hidden_size, input_size))
        )
        self.weight_hh = Parameter(
            np.random.uniform(-np.sqrt(k), np.sqrt(k), (3 * hidden_size, hidden_size))
        )

        if bias:
            self.bias_ih = Parameter(np.zeros(3 * hidden_size))
            self.bias_hh = Parameter(np.zeros(3 * hidden_size))
        else:
            self.register_parameter("bias_ih", None)
            self.register_parameter("bias_hh", None)

    def forward(
        self,
        x: Tensor,
        h: Optional[Tensor] = None,
    ) -> Tensor:
        batch_size = x.shape[0]

        if h is None:
            h = Tensor(np.zeros((batch_size, self.hidden_size)))

        hs = self.hidden_size

        # Input projection
        gi = x.matmul(self.weight_ih.transpose())
        if self.bias_ih is not None:
            gi = gi + self.bias_ih

        # Hidden projection
        gh = h.matmul(self.weight_hh.transpose())
        if self.bias_hh is not None:
            gh = gh + self.bias_hh

        # Reset and update gates
        r = Tensor(gi.data[:, :hs] + gh.data[:, :hs], requires_grad=gi.requires_grad).sigmoid()
        z = Tensor(gi.data[:, hs:2*hs] + gh.data[:, hs:2*hs], requires_grad=gi.requires_grad).sigmoid()

        # New gate
        n = Tensor(gi.data[:, 2*hs:] + r.data * gh.data[:, 2*hs:], requires_grad=gi.requires_grad).tanh()

        # Update hidden state
        ones = Tensor(np.ones_like(z.data))
        h_new = (ones - z) * n + z * h

        return h_new

    def __repr__(self) -> str:
        return f"GRUCell({self.input_size}, {self.hidden_size})"


class RNN(Module):
    """
    Multi-layer Elman RNN.

    Parameters
    ----------
    input_size : int
        Size of input features.
    hidden_size : int
        Size of hidden state.
    num_layers : int, default=1
        Number of recurrent layers.
    bias : bool, default=True
        If True, adds bias terms.
    batch_first : bool, default=False
        If True, input is (batch, seq, features).
    dropout : float, default=0.0
        Dropout probability between layers.
    bidirectional : bool, default=False
        If True, use bidirectional RNN.
    nonlinearity : str, default='tanh'
        Nonlinearity ('tanh' or 'relu').

    Examples
    --------
    >>> rnn = nn.RNN(10, 20, num_layers=2, batch_first=True)
    >>> x = Tensor(np.random.randn(32, 50, 10))  # (batch, seq, features)
    >>> output, h_n = rnn(x)
    """

    def __init__(
        self,
        input_size: int,
        hidden_size: int,
        num_layers: int = 1,
        bias: bool = True,
        batch_first: bool = False,
        dropout: float = 0.0,
        bidirectional: bool = False,
        nonlinearity: str = 'tanh',
    ):
        super().__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.batch_first = batch_first
        self.dropout = dropout
        self.bidirectional = bidirectional
        self.num_directions = 2 if bidirectional else 1

        # Create cells for each layer
        self.cells = []
        for layer in range(num_layers):
            for direction in range(self.num_directions):
                layer_input_size = input_size if layer == 0 else hidden_size * self.num_directions
                cell = RNNCell(layer_input_size, hidden_size, bias, nonlinearity)
                self.add_module(f"cell_{layer}_{direction}", cell)
                self.cells.append(cell)

    def forward(
        self,
        x: Tensor,
        h_0: Optional[Tensor] = None,
    ) -> Tuple[Tensor, Tensor]:
        if self.batch_first:
            batch_size, seq_len, _ = x.shape
        else:
            seq_len, batch_size, _ = x.shape
            x = Tensor(x.data.transpose(1, 0, 2), requires_grad=x.requires_grad)

        if h_0 is None:
            h_0 = Tensor(np.zeros((self.num_layers * self.num_directions, batch_size, self.hidden_size)))

        # Process each layer
        h_n_list = []
        layer_input = x

        for layer in range(self.num_layers):
            outputs_forward = []
            h = Tensor(h_0.data[layer * self.num_directions], requires_grad=h_0.requires_grad)

            # Forward direction
            cell_idx = layer * self.num_directions
            for t in range(seq_len):
                xt = Tensor(layer_input.data[:, t, :], requires_grad=layer_input.requires_grad)
                h = self.cells[cell_idx](xt, h)
                outputs_forward.append(h.data)

            h_n_list.append(h.data)

            if self.bidirectional:
                outputs_backward = []
                h_back = Tensor(h_0.data[layer * self.num_directions + 1], requires_grad=h_0.requires_grad)

                cell_idx = layer * self.num_directions + 1
                for t in range(seq_len - 1, -1, -1):
                    xt = Tensor(layer_input.data[:, t, :], requires_grad=layer_input.requires_grad)
                    h_back = self.cells[cell_idx](xt, h_back)
                    outputs_backward.insert(0, h_back.data)

                h_n_list.append(h_back.data)

                # Concatenate forward and backward
                layer_output = np.concatenate(
                    [np.stack(outputs_forward, axis=1), np.stack(outputs_backward, axis=1)],
                    axis=2
                )
            else:
                layer_output = np.stack(outputs_forward, axis=1)

            layer_input = Tensor(layer_output, requires_grad=x.requires_grad)

        output = layer_input
        h_n = Tensor(np.stack(h_n_list), requires_grad=h_0.requires_grad if h_0 is not None else False)

        if not self.batch_first:
            output = Tensor(output.data.transpose(1, 0, 2), requires_grad=output.requires_grad)

        return output, h_n

    def __repr__(self) -> str:
        return (f"RNN({self.input_size}, {self.hidden_size}, "
                f"num_layers={self.num_layers}, batch_first={self.batch_first})")


class LSTM(Module):
    """
    Multi-layer Long Short-Term Memory RNN.

    Parameters
    ----------
    input_size : int
        Size of input features.
    hidden_size : int
        Size of hidden state.
    num_layers : int, default=1
        Number of recurrent layers.
    bias : bool, default=True
        If True, adds bias terms.
    batch_first : bool, default=False
        If True, input is (batch, seq, features).
    dropout : float, default=0.0
        Dropout probability between layers.
    bidirectional : bool, default=False
        If True, use bidirectional LSTM.

    Examples
    --------
    >>> lstm = nn.LSTM(10, 20, num_layers=2, batch_first=True)
    >>> x = Tensor(np.random.randn(32, 50, 10))
    >>> output, (h_n, c_n) = lstm(x)
    """

    def __init__(
        self,
        input_size: int,
        hidden_size: int,
        num_layers: int = 1,
        bias: bool = True,
        batch_first: bool = False,
        dropout: float = 0.0,
        bidirectional: bool = False,
    ):
        super().__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.batch_first = batch_first
        self.dropout = dropout
        self.bidirectional = bidirectional
        self.num_directions = 2 if bidirectional else 1

        self.cells = []
        for layer in range(num_layers):
            for direction in range(self.num_directions):
                layer_input_size = input_size if layer == 0 else hidden_size * self.num_directions
                cell = LSTMCell(layer_input_size, hidden_size, bias)
                self.add_module(f"cell_{layer}_{direction}", cell)
                self.cells.append(cell)

    def forward(
        self,
        x: Tensor,
        hx: Optional[Tuple[Tensor, Tensor]] = None,
    ) -> Tuple[Tensor, Tuple[Tensor, Tensor]]:
        if self.batch_first:
            batch_size, seq_len, _ = x.shape
        else:
            seq_len, batch_size, _ = x.shape
            x = Tensor(x.data.transpose(1, 0, 2), requires_grad=x.requires_grad)

        if hx is None:
            h_0 = Tensor(np.zeros((self.num_layers * self.num_directions, batch_size, self.hidden_size)))
            c_0 = Tensor(np.zeros((self.num_layers * self.num_directions, batch_size, self.hidden_size)))
        else:
            h_0, c_0 = hx

        h_n_list = []
        c_n_list = []
        layer_input = x

        for layer in range(self.num_layers):
            outputs_forward = []
            h = Tensor(h_0.data[layer * self.num_directions], requires_grad=h_0.requires_grad)
            c = Tensor(c_0.data[layer * self.num_directions], requires_grad=c_0.requires_grad)

            cell_idx = layer * self.num_directions
            for t in range(seq_len):
                xt = Tensor(layer_input.data[:, t, :], requires_grad=layer_input.requires_grad)
                h, c = self.cells[cell_idx](xt, (h, c))
                outputs_forward.append(h.data)

            h_n_list.append(h.data)
            c_n_list.append(c.data)

            if self.bidirectional:
                outputs_backward = []
                h_back = Tensor(h_0.data[layer * self.num_directions + 1])
                c_back = Tensor(c_0.data[layer * self.num_directions + 1])

                cell_idx = layer * self.num_directions + 1
                for t in range(seq_len - 1, -1, -1):
                    xt = Tensor(layer_input.data[:, t, :])
                    h_back, c_back = self.cells[cell_idx](xt, (h_back, c_back))
                    outputs_backward.insert(0, h_back.data)

                h_n_list.append(h_back.data)
                c_n_list.append(c_back.data)

                layer_output = np.concatenate(
                    [np.stack(outputs_forward, axis=1), np.stack(outputs_backward, axis=1)],
                    axis=2
                )
            else:
                layer_output = np.stack(outputs_forward, axis=1)

            layer_input = Tensor(layer_output, requires_grad=x.requires_grad)

        output = layer_input
        h_n = Tensor(np.stack(h_n_list))
        c_n = Tensor(np.stack(c_n_list))

        if not self.batch_first:
            output = Tensor(output.data.transpose(1, 0, 2))

        return output, (h_n, c_n)

    def __repr__(self) -> str:
        return (f"LSTM({self.input_size}, {self.hidden_size}, "
                f"num_layers={self.num_layers}, batch_first={self.batch_first})")


class GRU(Module):
    """
    Multi-layer Gated Recurrent Unit RNN.

    Parameters
    ----------
    input_size : int
        Size of input features.
    hidden_size : int
        Size of hidden state.
    num_layers : int, default=1
        Number of recurrent layers.
    bias : bool, default=True
        If True, adds bias terms.
    batch_first : bool, default=False
        If True, input is (batch, seq, features).
    dropout : float, default=0.0
        Dropout probability between layers.
    bidirectional : bool, default=False
        If True, use bidirectional GRU.

    Examples
    --------
    >>> gru = nn.GRU(10, 20, num_layers=2, batch_first=True)
    >>> x = Tensor(np.random.randn(32, 50, 10))
    >>> output, h_n = gru(x)
    """

    def __init__(
        self,
        input_size: int,
        hidden_size: int,
        num_layers: int = 1,
        bias: bool = True,
        batch_first: bool = False,
        dropout: float = 0.0,
        bidirectional: bool = False,
    ):
        super().__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.batch_first = batch_first
        self.dropout = dropout
        self.bidirectional = bidirectional
        self.num_directions = 2 if bidirectional else 1

        self.cells = []
        for layer in range(num_layers):
            for direction in range(self.num_directions):
                layer_input_size = input_size if layer == 0 else hidden_size * self.num_directions
                cell = GRUCell(layer_input_size, hidden_size, bias)
                self.add_module(f"cell_{layer}_{direction}", cell)
                self.cells.append(cell)

    def forward(
        self,
        x: Tensor,
        h_0: Optional[Tensor] = None,
    ) -> Tuple[Tensor, Tensor]:
        if self.batch_first:
            batch_size, seq_len, _ = x.shape
        else:
            seq_len, batch_size, _ = x.shape
            x = Tensor(x.data.transpose(1, 0, 2), requires_grad=x.requires_grad)

        if h_0 is None:
            h_0 = Tensor(np.zeros((self.num_layers * self.num_directions, batch_size, self.hidden_size)))

        h_n_list = []
        layer_input = x

        for layer in range(self.num_layers):
            outputs_forward = []
            h = Tensor(h_0.data[layer * self.num_directions])

            cell_idx = layer * self.num_directions
            for t in range(seq_len):
                xt = Tensor(layer_input.data[:, t, :])
                h = self.cells[cell_idx](xt, h)
                outputs_forward.append(h.data)

            h_n_list.append(h.data)

            if self.bidirectional:
                outputs_backward = []
                h_back = Tensor(h_0.data[layer * self.num_directions + 1])

                cell_idx = layer * self.num_directions + 1
                for t in range(seq_len - 1, -1, -1):
                    xt = Tensor(layer_input.data[:, t, :])
                    h_back = self.cells[cell_idx](xt, h_back)
                    outputs_backward.insert(0, h_back.data)

                h_n_list.append(h_back.data)

                layer_output = np.concatenate(
                    [np.stack(outputs_forward, axis=1), np.stack(outputs_backward, axis=1)],
                    axis=2
                )
            else:
                layer_output = np.stack(outputs_forward, axis=1)

            layer_input = Tensor(layer_output, requires_grad=x.requires_grad)

        output = layer_input
        h_n = Tensor(np.stack(h_n_list))

        if not self.batch_first:
            output = Tensor(output.data.transpose(1, 0, 2))

        return output, h_n

    def __repr__(self) -> str:
        return (f"GRU({self.input_size}, {self.hidden_size}, "
                f"num_layers={self.num_layers}, batch_first={self.batch_first})")
