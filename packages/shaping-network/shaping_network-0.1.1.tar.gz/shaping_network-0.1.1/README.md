# Shape Network (Python Edition)

An experimental neural network architecture ported from Java that utilizes sophisticated feature extraction and "shaping" functions. This network is designed for reliable classification tasks, such as facial recognition, by leveraging cosine similarity measures.

Unlike traditional backpropagation-based networks, this architecture performs well with single-class/label training, eliminating the need for complex weight balancing to achieve accurate predictions.

## Features

*   **Shaping Functions:** Uses mathematical "shapes" (Mean, Log-Mean, Min, Max) to adapt weights.
*   **Cosine Similarity:** Measures the orientation of vectors rather than just magnitude, providing robustness against scaling.
*   **Partition Layers:** Automatically selects and optimizes the best-fitting neurons for specific features.
*   **NumPy Backend:** Optimized for numerical vector operations in Python.

## Installation

This project requires **NumPy**.

```bash
pip install numpy
```

## Usage

### 1. Build the Network
Use the `ShapingNetworkBuilder` to define the architecture. You can connect layers to specific target ranges.

```python
from shape_network import ShapingNetworkBuilder, LayerBuilder, Shapes

model = ShapingNetworkBuilder() \
    .connect_in_range(0, 1, # Adds layers for targets 0 through 1
        LayerBuilder()
        .add_layer(Shapes.MEAN, 2) # Shaping function and number of nodes
    ).build()
```

### 2. Initialize and Randomize
Set the input dimension (number of features) and randomize the initial sum vectors.

```python
# Initialize with 3 input nodes
model.initialize(3)
model.randomize()
```

### 3. Prepare Training Data
Data is fed into the model using `ContextVector` objects.

```python
from shape_network import ContextVector

training_data = {
    0: [ # Class 0
        ContextVector([0.001, 2.531, 1.523]),
        ContextVector([0.009, 2.231, 1.241])
    ],
    1: [ # Class 1
        ContextVector([1.8, 0.001, 4.9]),
        ContextVector([2.5, 0.002, 4.5])
    ]
}
```

### 4. Training
Training is performed by "feeding" vectors to the model along with their target labels.

```python
epochs = 100
for i in range(epochs):
    for target, vectors in training_data.items():
        for vec in vectors:
            model.feed(vec, target) # Adjusts the weights/shapes for that target
```

### 5. Predict
The `predict` method returns a list of probabilities (similarity scores) for each layer/class.

```python
prediction = model.predict(test_vector)
# Get the index of the highest probability
max_index = prediction.index(max(prediction))
print(f"Predicted Class: {max_index}")
```

## Example Output
The network converges quickly to high accuracy:

```text
Accuracy: 0.998521
Class 0: 
Index=0, Probability=0.999873

Class 1: 
Index=1, Probability=0.997032
```

## Mathematical Overview
The core of the network is the **Shaping Function**. Instead of traditional gradient descent, neurons maintain a `sum_vector` and a `shape_vector`. When `feed()` is called:
1. The `sum_vector` accumulates the input data.
2. The `shaping_function` (e.g., `LOG_MEAN`) is applied to derive a new `shape_vector`.
3. Prediction is calculated as the **Cosine Similarity** between the input vector and the neuron's `shape_vector`.

## License
This project is licensed under the MIT License - see the LICENSE file for details.