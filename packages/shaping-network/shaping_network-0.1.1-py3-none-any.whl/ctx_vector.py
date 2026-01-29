# Author: Bendik Brissach
# Created: 25.01.2026
# Description:
from typing import Any

import numpy as np


class ContextVector:
  """A wrapper for NumPy arrays providing specific Shape-Network operations."""

  def __init__(self, values: Any):
    if isinstance(values, (list, tuple)):
      self.values = np.array(values, dtype=float)
    elif isinstance(values, np.ndarray):
      self.values = values.astype(float)
    else:
      self.values = np.array([], dtype=float)

  @staticmethod
  def new_vector():
    return ContextVector([])

  @staticmethod
  def fill(size: int, value: float):
    return ContextVector(np.full(size, value, dtype=float))

  def add_values_to_vector(self, *args):
    # Handles both a list of values or individual args
    if len(args) == 1 and isinstance(args[0], (list, np.ndarray)):
      new_vals = np.array(args[0])
    else:
      new_vals = np.array(args)

    if self.values.size == 0:
      self.values = new_vals.astype(float)
    else:
      self.values = np.concatenate([self.values, new_vals.astype(float)])
    return self

  def get(self, index: int) -> float:
    return float(self.values[index])

  def modify(self, index: int, value: float):
    self.values[index] = value
    return self

  def dimension(self) -> int:
    return self.values.size

  def copy(self):
    return ContextVector(np.copy(self.values))

  def merge(self, other: 'ContextVector'):
    if self.dimension() != other.dimension():
      # If current is empty, initialize it
      if self.dimension() == 0:
        self.values = np.copy(other.values)
        return self
      raise ValueError("Dimensions must match for merge")
    self.values += other.values
    return self

  def cosine(self, other: 'ContextVector') -> float:
    if self.dimension() == 0 or other.dimension() == 0:
      return 0.0
    norm_a = np.linalg.norm(self.values)
    norm_b = np.linalg.norm(other.values)
    if norm_a == 0 or norm_b == 0:
      return 0.0
    return float(np.dot(self.values, other.values) / (norm_a * norm_b))

  def __repr__(self):
    return f"ContextVector(dim={self.dimension()}, values={self.values.tolist()})"