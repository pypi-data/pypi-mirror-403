"""
Data loading utilities.
"""

from __future__ import annotations

from typing import Optional, List, Iterator, Tuple, Callable, Any, Union
import numpy as np

from nalyst.nn.tensor import Tensor


class Dataset:
    """
    Abstract base class for datasets.

    Subclasses must implement __len__ and __getitem__.

    Examples
    --------
    >>> class MyDataset(Dataset):
    ...     def __init__(self, data, labels):
    ...         self.data = data
    ...         self.labels = labels
    ...
    ...     def __len__(self):
    ...         return len(self.data)
    ...
    ...     def __getitem__(self, idx):
    ...         return self.data[idx], self.labels[idx]
    """

    def __len__(self) -> int:
        """Return dataset size."""
        raise NotImplementedError

    def __getitem__(self, index: int) -> Any:
        """Get item at index."""
        raise NotImplementedError

    def __add__(self, other: "Dataset") -> "ConcatDataset":
        """Concatenate datasets."""
        return ConcatDataset([self, other])


class TensorDataset(Dataset):
    """
    Dataset wrapping tensors.

    Parameters
    ----------
    *tensors : Tensor or ndarray
        Tensors with same first dimension.

    Examples
    --------
    >>> X = Tensor(np.random.randn(100, 10))
    >>> y = Tensor(np.random.randint(0, 2, 100))
    >>> dataset = TensorDataset(X, y)
    >>> x_i, y_i = dataset[0]
    """

    def __init__(self, *tensors: Union[Tensor, np.ndarray]):
        tensors = tuple(
            t if isinstance(t, Tensor) else Tensor(t)
            for t in tensors
        )

        # Check all tensors have same length
        assert all(t.shape[0] == tensors[0].shape[0] for t in tensors), \
            "All tensors must have same first dimension"

        self.tensors = tensors

    def __len__(self) -> int:
        return self.tensors[0].shape[0]

    def __getitem__(self, index: int) -> Tuple[Tensor, ...]:
        return tuple(Tensor(t.data[index]) for t in self.tensors)


class ConcatDataset(Dataset):
    """
    Concatenation of multiple datasets.

    Parameters
    ----------
    datasets : list
        List of datasets to concatenate.
    """

    def __init__(self, datasets: List[Dataset]):
        self.datasets = list(datasets)
        self.cumulative_sizes = []

        cumsum = 0
        for d in self.datasets:
            cumsum += len(d)
            self.cumulative_sizes.append(cumsum)

    def __len__(self) -> int:
        return self.cumulative_sizes[-1] if self.cumulative_sizes else 0

    def __getitem__(self, index: int) -> Any:
        if index < 0:
            index = len(self) + index

        dataset_idx = 0
        for i, size in enumerate(self.cumulative_sizes):
            if index < size:
                dataset_idx = i
                break

        if dataset_idx > 0:
            index = index - self.cumulative_sizes[dataset_idx - 1]

        return self.datasets[dataset_idx][index]


class Subset(Dataset):
    """
    Subset of a dataset at specified indices.

    Parameters
    ----------
    dataset : Dataset
        Source dataset.
    indices : list
        Indices to include.
    """

    def __init__(self, dataset: Dataset, indices: List[int]):
        self.dataset = dataset
        self.indices = indices

    def __len__(self) -> int:
        return len(self.indices)

    def __getitem__(self, index: int) -> Any:
        return self.dataset[self.indices[index]]


def random_split(
    dataset: Dataset,
    lengths: List[int],
    generator: Optional[np.random.Generator] = None,
) -> List[Subset]:
    """
    Randomly split dataset into non-overlapping subsets.

    Parameters
    ----------
    dataset : Dataset
        Dataset to split.
    lengths : list
        Lengths of splits.
    generator : Generator, optional
        Random generator for reproducibility.

    Returns
    -------
    list
        List of Subset objects.

    Examples
    --------
    >>> train_set, val_set = random_split(dataset, [800, 200])
    """
    if sum(lengths) != len(dataset):
        raise ValueError(f"Sum of lengths ({sum(lengths)}) != dataset size ({len(dataset)})")

    if generator is None:
        generator = np.random.default_rng()

    indices = generator.permutation(len(dataset)).tolist()

    subsets = []
    offset = 0
    for length in lengths:
        subsets.append(Subset(dataset, indices[offset:offset + length]))
        offset += length

    return subsets


class Sampler:
    """
    Base class for samplers.

    Samplers produce indices for DataLoader.
    """

    def __iter__(self) -> Iterator[int]:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError


class SequentialSampler(Sampler):
    """
    Sample sequentially.

    Parameters
    ----------
    data_source : Dataset
        Dataset to sample from.
    """

    def __init__(self, data_source: Dataset):
        self.data_source = data_source

    def __iter__(self) -> Iterator[int]:
        return iter(range(len(self.data_source)))

    def __len__(self) -> int:
        return len(self.data_source)


class RandomSampler(Sampler):
    """
    Sample randomly.

    Parameters
    ----------
    data_source : Dataset
        Dataset to sample from.
    replacement : bool, default=False
        Sample with replacement.
    num_samples : int, optional
        Number of samples (for replacement=True).
    generator : Generator, optional
        Random generator.
    """

    def __init__(
        self,
        data_source: Dataset,
        replacement: bool = False,
        num_samples: Optional[int] = None,
        generator: Optional[np.random.Generator] = None,
    ):
        self.data_source = data_source
        self.replacement = replacement
        self._num_samples = num_samples
        self.generator = generator or np.random.default_rng()

    @property
    def num_samples(self) -> int:
        if self._num_samples is None:
            return len(self.data_source)
        return self._num_samples

    def __iter__(self) -> Iterator[int]:
        n = len(self.data_source)
        if self.replacement:
            for _ in range(self.num_samples):
                yield self.generator.integers(0, n)
        else:
            yield from self.generator.permutation(n).tolist()

    def __len__(self) -> int:
        return self.num_samples


class BatchSampler(Sampler):
    """
    Wraps another sampler to yield mini-batches.

    Parameters
    ----------
    sampler : Sampler
        Base sampler.
    batch_size : int
        Batch size.
    drop_last : bool, default=False
        Drop last incomplete batch.
    """

    def __init__(
        self,
        sampler: Sampler,
        batch_size: int,
        drop_last: bool = False,
    ):
        self.sampler = sampler
        self.batch_size = batch_size
        self.drop_last = drop_last

    def __iter__(self) -> Iterator[List[int]]:
        batch = []
        for idx in self.sampler:
            batch.append(idx)
            if len(batch) == self.batch_size:
                yield batch
                batch = []

        if batch and not self.drop_last:
            yield batch

    def __len__(self) -> int:
        if self.drop_last:
            return len(self.sampler) // self.batch_size
        return (len(self.sampler) + self.batch_size - 1) // self.batch_size


class DataLoader:
    """
    Data loader for iterating over a dataset.

    Parameters
    ----------
    dataset : Dataset
        Dataset to load from.
    batch_size : int, default=1
        Batch size.
    shuffle : bool, default=False
        Shuffle data each epoch.
    drop_last : bool, default=False
        Drop last incomplete batch.
    collate_fn : callable, optional
        Function to collate samples.
    sampler : Sampler, optional
        Custom sampler.

    Examples
    --------
    >>> loader = DataLoader(dataset, batch_size=32, shuffle=True)
    >>> for batch_x, batch_y in loader:
    ...     # Training step
    ...     pass
    """

    def __init__(
        self,
        dataset: Dataset,
        batch_size: int = 1,
        shuffle: bool = False,
        drop_last: bool = False,
        collate_fn: Optional[Callable] = None,
        sampler: Optional[Sampler] = None,
    ):
        self.dataset = dataset
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.drop_last = drop_last
        self.collate_fn = collate_fn or self._default_collate

        if sampler is not None:
            self.sampler = sampler
        elif shuffle:
            self.sampler = RandomSampler(dataset)
        else:
            self.sampler = SequentialSampler(dataset)

        self.batch_sampler = BatchSampler(
            self.sampler, batch_size, drop_last
        )

    def _default_collate(self, batch: List) -> Tuple[Tensor, ...]:
        """Default collation function."""
        if isinstance(batch[0], tuple):
            # Multiple tensors per sample
            num_items = len(batch[0])
            result = []

            for i in range(num_items):
                items = [sample[i] for sample in batch]

                if isinstance(items[0], Tensor):
                    stacked = np.stack([item.data for item in items])
                    result.append(Tensor(stacked))
                elif isinstance(items[0], np.ndarray):
                    result.append(Tensor(np.stack(items)))
                else:
                    result.append(Tensor(np.array(items)))

            return tuple(result)

        elif isinstance(batch[0], Tensor):
            stacked = np.stack([item.data for item in batch])
            return Tensor(stacked)

        else:
            return Tensor(np.array(batch))

    def __iter__(self) -> Iterator:
        for indices in self.batch_sampler:
            batch = [self.dataset[i] for i in indices]
            yield self.collate_fn(batch)

    def __len__(self) -> int:
        return len(self.batch_sampler)


class IterableDataset:
    """
    Base class for iterable datasets.

    Useful for streaming data or very large datasets.

    Examples
    --------
    >>> class StreamDataset(IterableDataset):
    ...     def __iter__(self):
    ...         for line in open('data.txt'):
    ...             yield process(line)
    """

    def __iter__(self):
        raise NotImplementedError


class ChunkedDataset(Dataset):
    """
    Dataset that loads data in chunks for memory efficiency.

    Parameters
    ----------
    file_path : str
        Path to data file.
    chunk_size : int
        Size of each chunk.
    load_fn : callable
        Function to load chunk from file.
    """

    def __init__(
        self,
        file_path: str,
        chunk_size: int,
        load_fn: Callable,
        total_size: int,
    ):
        self.file_path = file_path
        self.chunk_size = chunk_size
        self.load_fn = load_fn
        self.total_size = total_size
        self._cache = {}
        self._cache_idx = -1

    def __len__(self) -> int:
        return self.total_size

    def __getitem__(self, index: int) -> Any:
        chunk_idx = index // self.chunk_size
        local_idx = index % self.chunk_size

        if chunk_idx != self._cache_idx:
            self._cache = self.load_fn(
                self.file_path,
                chunk_idx * self.chunk_size,
                self.chunk_size
            )
            self._cache_idx = chunk_idx

        return self._cache[local_idx]
