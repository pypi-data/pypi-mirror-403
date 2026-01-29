# ClumsyGrad

[![PyPI version](https://badge.fury.io/py/clumsygrad.svg)](https://badge.fury.io/py/clumsygrad)
[![Docs](https://readthedocs.org/projects/clumsygrad/badge/?version=latest)](https://clumsygrad.readthedocs.io/en/latest/)
[![Tests](https://github.com/Sayan-001/ClumsyGrad/actions/workflows/tests.yml/badge.svg)](https://github.com/Sayan-001/ClumsyGrad/actions/workflows/tests.yml)

A minimal Python library for automatic differentiation, built on top of NumPy. The `Tensor` class has support for creating and expanding a computation graph dynamically with each operation.

<p align="center">
  <img src="./ComputationalGraph.png" alt="Computation Graph" width="500" height="500" align="center">
</p>

## Features

- **Dynamic Computational Graphs**: Graphs are created on the fly.
- **Automatic Differentiation**: Compute gradients automatically using the chain rule.
- **Basic Tensor Operations**: Supports addition, subtraction, multiplication, matrix multiplication, power, exp, etc.

## Installation

You can install the library using pip:

```shell
pip install clumsygrad
```

## Basics

Here's a brief overview of how to use the library:

### Creating Tensors

```python
from clumsygrad.tensor import Tensor, TensorType

# Create a tensor from a list (defaults to TensorType.INPUT)
a = Tensor([1.0, 2.0, 3.0])
print(a)
# Output: Tensor(id=0, shape=(3,), tensor_type=INPUT, grad_fn=None, requires_grad=False)

# Create a tensor that requires gradients (e.g., a parameter)
b = Tensor([[4.0], [5.0], [6.0]], tensor_type=TensorType.PARAMETER)
print(b)
# Output: Tensor(id=1, shape=(3, 1), tensor_type=PARAMETER, grad_fn=None, requires_grad=True)
```

### Performing Operations

```python
from clumsygrad.tensor import Tensor, TensorType
from clumsygrad.math import exp, sin

x = Tensor([1.0, 2.0, 3.0])
y = exp(x**2 + 3*x + 2)
z = sin(y)

# As implicitly tensors are of type INPUT, the computational graph is not built, signified by
# grad_fn = None.
print(z) # Tensor(id=6, shape=(3,), tensor_type=INPUT, grad_fn=None, requires_grad=False)
print(z.data) # [0.9648606  0.99041617 0.83529955]

x = Tensor([1.0, 2.0, 3.0], tensor_type=TensorType.PARAMETER)
y = exp(x**2 + 3*x + 2)
z = sin(y)

# Now, the tensor is of type PARAMETER, and the computational graph is built.
print(z) # Tensor(id=13, shape=(3,), tensor_type=INTERMEDIATE, grad_fn=sin_backward, requires_grad=True)
print(z.data) # [0.9648606  0.99041617 0.83529955]
```

### Automatic Differentiation (Backpropagation)

Consider the function $~z = e^{sin(x)^2 + cos(y)}$. We can evaluate $\frac{dz}{dx}$ and $\frac{dz}{dy}$ at particular point as:

```python
from clumsygrad.tensor import Tensor, TensorType
from clumsygrad.math import exp, sin, cos, sum

# Set tensor_type to PARAMETER to ensure gradients are tracked
x = Tensor(1.0, tensor_type=TensorType.PARAMETER)
y = Tensor(0.5, tensor_type=TensorType.PARAMETER)
z = exp(sin(x)**2 + cos(y))

# Calculating dz/dx and dz/dy
z.backward()

# Value of dz/dx
print(x.grad) # [4.43963]
# Value of dz/dy
print(y.grad) # [-2.34079]
```

## License

This project is licensed under the [MIT License](LICENSE).

## Documentation

For more detailed information, tutorials, and API reference, you can check out the [official documentation](https://clumsygrad.readthedocs.io/en/latest/).
