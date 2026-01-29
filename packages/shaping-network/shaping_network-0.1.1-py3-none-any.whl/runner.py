# Author: Bendik Brissach
# Created: 25.01.2026
# Description:

from ctx_vector import ContextVector
from layers import LayerBuilder
from shapes import Shapes
from shaping_network import ShapingNetworkBuilder
from type_defs import ShapingFunction

if __name__ == "__main__":
  model = ShapingNetworkBuilder() \
    .connect_in_range(0, 1,
      LayerBuilder().add_layer(Shapes.LOG_MEAN, 2)
    ).build()

  model.initialize(3)
  model.randomize()

  zeros = [
    ContextVector([0.001, 2.531, 1.523]),
    ContextVector([0.009, 2.231, 1.241])
  ]

  ones = [
    ContextVector([1.8, 0.001, 4.9]),
    ContextVector([2.5, 0.002, 4.5])
  ]

  training_data = {0: zeros, 1: ones}

  for _ in range(500):
    for target, vectors in training_data.items():
      for vec in vectors:
        model.feed(vec, target)

  print(f"Final Accuracy Score: {model.accuracy():.6f}")

  for target, vectors in training_data.items():
    print(f"\nClass {target}:")
    for vec in vectors:
      probs = model.predict(vec)
      max_val = max(probs)
      max_idx = probs.index(max_val)
      is_correct = max_idx == target
      print(f"Predicted Index={max_idx}, Prob={max_val:.6f}, Correct={is_correct}")