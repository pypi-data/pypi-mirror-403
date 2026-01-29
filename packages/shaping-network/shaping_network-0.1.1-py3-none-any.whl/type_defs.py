# Author: Bendik Brissach
# Created: 25.01.2026
# Description: Type definitions

from typing import Callable, TYPE_CHECKING

from ctx_vector import ContextVector

if TYPE_CHECKING:
    from neuron import Neuron

ShapingFunction = Callable[['Neuron', int, ContextVector], ContextVector]
