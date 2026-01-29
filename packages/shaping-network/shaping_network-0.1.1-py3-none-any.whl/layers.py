# Author: Bendik Brissach
# Created: 25.01.2026
# Description:
import random
from dataclasses import dataclass
from typing import List, Dict

from ctx_vector import ContextVector
from neuron import Neuron
from type_defs import ShapingFunction


class PartitionLayer:
  def __init__(self, attribute: int, shaping_functions: List[ShapingFunction], input_dim: int):
    self._attribute = attribute
    self.nodes = [Neuron(input_dim, func) for func in shaping_functions]
    self.n = 0

  def randomize(self):
    for node in self.nodes:
      node.randomize()

  def shape(self, y: ContextVector):
    # Group neurons by shaping function
    func_map: Dict[ShapingFunction, List[Neuron]] = {}
    for node in self.nodes:
      if node.shaping_function not in func_map:
        func_map[node.shaping_function] = []
      func_map[node.shaping_function].append(node)

    for func, neurons in func_map.items():
      if len(neurons) > 1:
        all_shaped = all(node.num_shapes > 0 for node in neurons)
        if all_shaped:
          # Pick best matching neuron (Partition logic)
          winner = max(neurons, key=lambda node: node.shape_vector.cosine(y))
          winner.shape(y, self.n)
        else:
          # Pick random unshaped neuron
          random.choice(neurons).shape(y, self.n)
      else:
        # Only one neuron with this function
        neurons[0].shape(y, self.n)

    self.n += 1

  def predict(self, x: ContextVector) -> float:
    if not self.nodes: return 0.0
    scores = [x.cosine(node.shape_vector) for node in self.nodes]
    return sum(scores) / len(scores)

  def attribute(self) -> int:
    return self._attribute

@dataclass
class LayerConfig:
  attribute: int
  functions: List[ShapingFunction]


class LayerBuilder:
  def __init__(self):
    self._attribute = -1
    self._functions = []

  def attribute(self, attr: int):
    self._attribute = attr
    return self

  def add_layer(self, shape_func: ShapingFunction, copies: int = 1):
    for _ in range(copies):
      self._functions.append(shape_func)
    return self

  def build(self) -> LayerConfig:
    return LayerConfig(self._attribute, self._functions)

  def copy(self):
    new_builder = LayerBuilder()
    new_builder._attribute = self._attribute
    new_builder._functions = list(self._functions)
    return new_builder