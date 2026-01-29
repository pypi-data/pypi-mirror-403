# Author: Bendik Brissach
# Created: 25.01.2026
# Description:
import numpy as np

from ctx_vector import ContextVector

class Shapes:
  @staticmethod
  def MEAN(node: 'Neuron', n: int, w: ContextVector) -> ContextVector:
    node.sum_vector.merge(w)
    shape = node.sum_vector.copy()
    if n > 0:
      shape.values /= n
    return shape

  @staticmethod
  def MIN(node: 'Neuron', n: int, w: ContextVector) -> ContextVector:
    if n == 0: return w.copy()
    node.sum_vector.merge(w)
    # Element-wise minimum
    new_vals = np.minimum(node.sum_vector.values, w.values)
    return ContextVector(new_vals)

  @staticmethod
  def MAX(node: 'Neuron', n: int, w: ContextVector) -> ContextVector:
    if n == 0: return w.copy()
    node.sum_vector.merge(w)
    new_vals = np.maximum(node.sum_vector.values, w.values)
    return ContextVector(new_vals)

  @staticmethod
  def LOG_MEAN(node: 'Neuron', n: int, w: ContextVector) -> ContextVector:
    node.sum_vector.merge(w)
    shape = node.sum_vector.copy()
    if n > 0:
      # Using log space to prevent overflow for geometric properties
      # Note: Requires positive values as per Java math logic
      safe_sum = np.where(shape.values > 0, shape.values, 1e-9)
      safe_w = np.where(w.values > 0, w.values, 1e-9)
      log_val = np.log(safe_sum) + np.log(safe_w) / n
      shape.values = np.exp(log_val)
    return shape
