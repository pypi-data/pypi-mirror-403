# Author: Bendik Brissach
# Created: 25.01.2026
# Description:
import numpy as np

from ctx_vector import ContextVector
from type_defs import ShapingFunction


class Neuron:
  def __init__(self, input_size: int, shaping_function: ShapingFunction):
    self.shaping_function = shaping_function
    self.sum_vector = ContextVector.fill(input_size, 0.0)
    self.shape_vector = ContextVector.fill(input_size, 0.0)
    self.num_shapes = 0

  def randomize(self):
    self.sum_vector.values = np.random.uniform(-1.0, 1.0, self.sum_vector.dimension())

  def shape(self, y: ContextVector, n: int):
    self.shape_vector = self.shaping_function(self, n, y)
    self.num_shapes += 1