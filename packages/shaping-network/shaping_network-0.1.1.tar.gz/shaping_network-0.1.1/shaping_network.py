# Author: Bendik Brissach
# Created: 25.01.2026
# Description:
from typing import List

from ctx_vector import ContextVector
from layers import LayerConfig, PartitionLayer, LayerBuilder


class ShapingNetwork:
  def __init__(self, configs: List[LayerConfig]):
    self.configs = configs
    self.layers: List[PartitionLayer] = []
    self.epochs = 0
    self.loss = 0.0
    self.initialized = False

  def initialize(self, input_dim: int):
    if self.initialized: return
    for config in self.configs:
      self.layers.append(PartitionLayer(config.attribute, config.functions, input_dim))
    self.initialized = True

  def randomize(self):
    if not self.initialized: raise RuntimeError("Network not initialized")
    for layer in self.layers:
      layer.randomize()

  def feed(self, vector: ContextVector, target: int):
    self.initialize(vector.dimension())

    target_layers = [l for l in self.layers if l.attribute() == target]
    if not target_layers:
      raise ValueError(f"No layers found for target {target}")

    for layer in target_layers:
      layer.shape(vector)

    probs = self.predict(vector)
    self.loss = 1.0 - max(probs)
    self.epochs += 1

  def predict(self, vector: ContextVector) -> List[float]:
    return [layer.predict(vector) for layer in self.layers]

  def accuracy(self) -> float:
    return 1.0 - self.loss


class ShapingNetworkBuilder:
  def __init__(self):
    self.configs = []

  def connect(self, layer_builder: LayerBuilder):
    self.configs.append(layer_builder.build())
    return self

  def connect_in_range(self, start: int, end: int, layer_builder: LayerBuilder):
    for i in range(start, end + 1):
      builder = layer_builder.copy().attribute(i)
      self.configs.append(builder.build())
    return self

  def build(self) -> ShapingNetwork:
    return ShapingNetwork(self.configs)