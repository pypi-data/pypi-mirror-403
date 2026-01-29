"""
This module contains the Tensor class implementation for automatic differentiation.
It supports basic tensor operations, tracks gradients, and can be used to build computational graphs for backpropagation.
It also contains some utility functions for managing tensors and their gradients.
"""

from __future__ import annotations

from enum import IntEnum
from typing import Callable, Dict, List, Optional, Set, Tuple, Union

import numpy as np


class TensorType(IntEnum):
    """
    Defines tensor types in the computational graph. Each type controls gradient computation and tensor behavior.
    
    Examples:
    
        >>> input_tensor = Tensor([1, 2, 3], tensor_type=TensorType.INPUT)
        >>> param_tensor = Tensor([0.5, 0.3], tensor_type=TensorType.PARAMETER)
        >>> result = input_tensor + param_tensor  # Creates INTERMEDIATE tensor
    """
    
    INPUT = 0
    """
    Input tensor that feeds data into the computation graph.
    
    Use when:
    - You do not need gradients for this tensor.
    - It should be a constant or a placeholder within the computation graph.
    """
    
    PARAMETER = 1
    """
    Trainable parameter tensor (weights, biases).
    
    Use when:
    - You want calculate gradients for this tensor.
    - You want to optimize this tensor during training.
    """
    
    INTERMEDIATE = 2
    """
    Intermediate computation result.
    
    You are recommended not to use this type.
    """

class Tensor:
    """
    The main Tensor class, comprising the core functionality for creation and manipulation of tensors in the computational graph.
    """
    
    _id_counter = 0
    
    __slots__ = ('_data', '_shape', '_id', '_grad_fn', '_grad', '_parents',
                 '_extra', '_tensor_type', '_requires_grad')
    
    @staticmethod
    def _create_node(data: np.ndarray | list | float,
                     grad_fn: Optional[Callable], 
                     parents: Tuple[Tensor, ...],
                     extra: Optional[dict] = None) -> Tensor:
        
        """
        Creates a new tensor node in the computational graph.
        By default, this node is created as an INTERMEDIATE tensor.
        
        Args:
            data: The data for the new tensor.
            grad_fn: The gradient function to use for backpropagation.
            parents: The parent tensors that this tensor depends on.
            extra: Additional metadata for the tensor (optional).
            
        Returns:
            A new Tensor instance representing the node in the computational graph. 
        """
        tensor_type = TensorType.INPUT
        
        for parent in parents:
            if parent._tensor_type == TensorType.PARAMETER or parent._tensor_type == TensorType.INTERMEDIATE:
                tensor_type = TensorType.INTERMEDIATE
                break
        
        node = Tensor(data=data, tensor_type=tensor_type)
        
        if tensor_type != TensorType.INPUT:
            node._grad_fn = grad_fn
            node._parents = parents
            
            if extra: 
                node._extra.update(extra)
            
        node._requires_grad = any(parent._requires_grad for parent in parents)
        
        return node
    
    @staticmethod
    def _broadcast_shapes(shape1: tuple, shape2: tuple) -> tuple:
        """
        Determine the broadcasted shape for two tensor shapes.
        
        Args:
            shape1: Shape of the first tensor
            shape2: Shape of the second tensor
            
        Returns:
            The broadcasted shape
            
        Raises:
            ValueError: If shapes are not broadcastable
        """
        # Pad shorter shape with 1s on the left
        len_diff = abs(len(shape1) - len(shape2))
        if len(shape1) < len(shape2):
            shape1 = (1,) * len_diff + shape1
        elif len(shape2) < len(shape1):
            shape2 = (1,) * len_diff + shape2
        
        # Check compatibility and compute result shape
        result_shape = []
        for dim1, dim2 in zip(shape1, shape2):
            if dim1 == 1:
                result_shape.append(dim2)
            elif dim2 == 1:
                result_shape.append(dim1)
            elif dim1 == dim2:
                result_shape.append(dim1)
            else:
                raise ValueError(f"Cannot broadcast shapes {shape1} and {shape2}")
        
        return tuple(result_shape)
    
    @staticmethod
    def _can_broadcast(shape1: tuple, shape2: tuple) -> bool:
        """
        Check if two shapes can be broadcasted together.
        
        Args:
            shape1: Shape of the first tensor
            shape2: Shape of the second tensor
            
        Returns:
            True if shapes are broadcastable, False otherwise
        """
        try:
            Tensor._broadcast_shapes(shape1, shape2)
            return True
        except ValueError:
            return False
                
    def _cleanup_references(self):                    
        self._parents = ()
    
    def __init__(self, 
                 data: np.ndarray | list | float,
                 tensor_type: TensorType = TensorType.INPUT,
                ):
        """
        Initialize a new tensor.
        
        Args:
            data: The initial data for the tensor.
            tensor_type (TensorType): The type of the tensor, as TensorType.INPUT/PARAMETER/INTERMEDIATE (default is INPUT).
            
        Note: 
            - The tensor will not track/propagate gradients if it is of type INPUT.
            - If it is of type PARAMETER, it will be treated as a trainable parameter.
            - Do not use INTERMEDIATE type unless you are explicitly creating a node in the graph.
            - By default, data type is set to float32.
        """
        
        self._data = np.array(data, dtype=np.float32)
        self._shape = self._data.shape
        self._grad_fn = None
        self._grad = None
        self._tensor_type = tensor_type
        
        if self._tensor_type == TensorType.PARAMETER:
            self._requires_grad = True
        else:
            self._requires_grad = False
        
        self._parents: Tuple[Tensor, ...] = ()
        
        self._id = Tensor._id_counter
        Tensor._id_counter += 1
        
        self._extra = {}
    
    def __repr__(self):
        grad_fn_name = self._grad_fn.__name__ if self._grad_fn else None
        return (f"Tensor(id={self._id}, shape={self._shape}, "
                f"tensor_type={self._tensor_type.name}, "
                f"grad_fn={grad_fn_name}, "
                f"requires_grad={self._requires_grad})")
    
    @property
    def data(self) -> np.ndarray:
        """Return the data of the tensor."""
        return self._data
    
    @property
    def shape(self) -> tuple:
        """Return the shape of the tensor."""
        return self._shape
    
    @property
    def grad(self) -> Optional[np.ndarray]:
        """Return the gradient of the tensor."""
        return self._grad
    
    @grad.setter
    def grad(self, value: np.ndarray):
        """Set the gradient of the tensor."""
        self._grad = value
    
    @property
    def requires_grad(self) -> bool:
        """Return whether this tensor requires gradients."""
        return self._requires_grad
    
    def T(self) -> Tensor:
        """
        Returns the transpose of the tensor.
        """
        new_tensor = None
        
        from .grad import transpose_backward
        
        if self._grad_fn == transpose_backward:
            new_tensor = self._parents[0]
            self._cleanup_references()
        else:
            new_tensor = Tensor._create_node(
                data=self._data.T,
                grad_fn=transpose_backward,
                parents=(self,),
            )
        
        return new_tensor
    
    def __add__(self, other: Union[Tensor, float]) -> Tensor:
        from .grad import (add_backward, add_broadcast_backward,
                           add_scalar_backward)
        
        if isinstance(other, Tensor):
            if Tensor._can_broadcast(self._shape, other._shape):
                result_data = self._data + other._data
                
                if self._shape == other._shape:
                    grad_fn = add_backward
                    extra = None
                else:
                    grad_fn = add_broadcast_backward
                    extra = {
                        'left_shape': self._shape,
                        'right_shape': other._shape,
                    }
                
                new_tensor = Tensor._create_node(
                    data=result_data,
                    grad_fn=grad_fn,
                    parents=(self, other),
                    extra=extra
                )
            else:
                raise ValueError(f"Cannot broadcast shapes {self._shape} and {other._shape}")
        else:
            new_tensor = Tensor._create_node(
                data=self._data + other,
                grad_fn=add_scalar_backward,
                parents=(self,),
                extra={'scalar_value': float(other)}
            )
            
        return new_tensor
    
    def __radd__(self, other: Union[Tensor, float]) -> Tensor:
        return self.__add__(other)
    
    def __sub__(self, other: Union[Tensor, float]) -> Tensor:
        from .grad import (sub_backward, sub_broadcast_backward,
                           sub_scalar_backward)
        
        if isinstance(other, Tensor):
            if Tensor._can_broadcast(self._shape, other._shape):
                result_data = self._data - other._data

                if self._shape == other._shape:
                    grad_fn = sub_backward
                    extra = None
                else:
                    grad_fn = sub_broadcast_backward
                    extra = {
                        'left_shape': self._shape,
                        'right_shape': other._shape,
                    }
                
                new_tensor = Tensor._create_node(
                    data=result_data,
                    grad_fn=grad_fn,
                    parents=(self, other),
                    extra=extra
                )
            else:
                raise ValueError(f"Cannot broadcast shapes {self._shape} and {other._shape}")
        else:
            new_tensor = Tensor._create_node(
                data=self._data - other,
                grad_fn=sub_scalar_backward,
                parents=(self,),
                extra={'scalar_value': float(other)}
            )
            
        return new_tensor
    
    def __mul__(self, other: Union[Tensor, float]) -> Tensor:
        from .grad import (mul_backward, mul_broadcast_backward,
                           mul_scalar_backward)
        
        if isinstance(other, Tensor):
            if Tensor._can_broadcast(self._shape, other._shape):
                result_data = self._data * other._data
                
                if self._shape == other._shape:
                    grad_fn = mul_backward
                    extra = None
                else:
                    grad_fn = mul_broadcast_backward
                    extra = {
                        'left_shape': self._shape,
                        'right_shape': other._shape,
                    }
                
                new_tensor = Tensor._create_node(
                    data=result_data,
                    grad_fn=grad_fn,
                    parents=(self, other),
                    extra=extra
                )
            else:
                raise ValueError(f"Cannot broadcast shapes {self._shape} and {other._shape}")
        else:
            new_tensor = Tensor._create_node(
                data=self._data * other,
                grad_fn=mul_scalar_backward,
                parents=(self,),
                extra={'scalar_value': float(other)}
            )
            
        return new_tensor
    
    def __rmul__(self, other: Union[Tensor, float]) -> Tensor:
        return self.__mul__(other)
    
    def __matmul__(self, other: Tensor) -> Tensor:
        if not isinstance(other, Tensor):
            raise TypeError("Right operand must be a Tensor for matrix multiplication.")
        
        if len(self._shape) < 2 or len(other._shape) < 2:
            raise ValueError("Matrix multiplication requires at least 2D tensors.")
        
        if self._shape[-1] != other._shape[-2]:
            raise ValueError(f"Matrix shapes not aligned: {self._shape} @ {other._shape}")
        
        from .grad import matmul_backward
        
        new_tensor = Tensor._create_node(
            data=self._data @ other._data,
            grad_fn=matmul_backward,
            parents=(self, other),
        )
        return new_tensor
    
    def __pow__(self, power: float) -> Tensor:
        from .grad import power_backward
        
        new_tensor = Tensor._create_node(
            data=self._data ** power,
            grad_fn=power_backward,
            parents=(self,),
            extra={'power': float(power)}
        )
        return new_tensor
    
    def __neg__(self) -> Tensor:
        from .grad import negate_backward
        
        new_tensor = Tensor._create_node(
            data=-self._data,
            grad_fn=negate_backward,
            parents=(self,),
        )
        return new_tensor
    
    def reshape(self, new_shape: Tuple[int, ...]) -> Tensor:
        """
        Reshape the tensor to a new shape.
        
        Args:
            new_shape: The desired shape for the tensor.
            
        Returns:
            A new Tensor with the reshaped data.
            
        Raises:
            ValueError: If the new shape does not have the same number of elements as the original shape.
        """
    
        if np.prod(new_shape) != np.prod(self._shape):
            raise ValueError("New shape must have the same number of elements as the original shape.")
        
        from .grad import reshape_backward
        
        new_tensor = Tensor._create_node(
            data=self._data.reshape(new_shape),
            grad_fn=reshape_backward,
            parents=(self,),
            extra={'original_shape': self._shape}
        )
        return new_tensor
    
    def backward(self, gradient: Optional[np.ndarray | float] = None, keep_graph: bool = False):
        """
        backward pass to compute gradients. Once the backward pass is completed, the graph is freed from memory unless `keep_graph` is set to True.
        Only the current tensor and all INPUT/PARAMETER tensors will be retained in memory.
        
        Args:
            gradient: Optional gradient to start the backward pass. If None, it assumes a scalar output and uses ones.
            keep_graph: If True, keeps the computational graph for further backward passes.
            
        Raises:
            RuntimeError: If the tensor does not require gradients or if the gradient is not compatible.
            
        Note:
            - Setting `keep_graph=True` inside a training loop can lead to memory leaks.
            
        Example:
            >>> t = Tensor(np.array([1.0, 2.0, 3.0]), tensor_type=TensorType.PARAMETER)
            >>> y = t ** 2 + 3 * t + 2
            >>> y.backward()
        """
        
        if not self._requires_grad:
            raise RuntimeError("Tensor does not require gradients")
        
        if self._parents == () and self._tensor_type == TensorType.INTERMEDIATE:
            raise RuntimeError("No backward graph exists for this tensor")
        
        if gradient is None:
                if self._data.size != 1:
                    raise RuntimeError("Gradient can only be implicitly created for scalar outputs")
                gradient = np.ones_like(self._data, dtype=np.float32)
        else:
            gradient = np.array(gradient, dtype=np.float32)
            if gradient.shape != self._shape:
                raise ValueError(f"Gradient shape {gradient.shape} does not match tensor shape {self._shape}")
            
        if self._grad is None:
            self._grad = gradient.copy()
        else:
            self._grad += gradient
        
        topo_order: List[Tensor] = []
        visited: Set[int] = set()
        
        def build_topo(node: Tensor):
            if node._id in visited or not node._requires_grad:
                return
            visited.add(node._id)
            
            for parent in node._parents:
                build_topo(parent)
                
            topo_order.append(node)
        
        build_topo(self)
        
        for node in reversed(topo_order):
            if node._grad_fn is not None and node._grad is not None:
                try:
                    gradients = node._grad_fn(node, node._grad)
                    
                    for parent, grad in zip(node._parents, gradients):
                        if parent._requires_grad and grad is not None:
                            grad = np.array(grad, dtype=np.float32)
                            
                            if grad.shape != parent._shape:
                                raise ValueError(f"Gradient shape mismatch for tensor {parent._id}")
                            
                            if parent._grad is None:
                                parent._grad = grad.copy()
                            else:
                                parent._grad += grad
                                
                except Exception as e:
                    raise RuntimeError(f"Error in backward pass at tensor {node._id}: {str(e)}")
               
        if not keep_graph:    
            for node in topo_order:
                if node._tensor_type == TensorType.INTERMEDIATE:
                    node._cleanup_references()
            
class TensorUtils:
    @staticmethod
    def get_parameters(tensor: Tensor) -> List[Tensor]:
        """
        Collect all parameters in the computational graph starting from the given tensor.
        
        Args:
            tensor: The starting tensor from which to collect parameters.
            
        Returns:
            A list of Tensor objects that are parameters in the graph.
        """
        
        parameters: List[Tensor] = []
        stack = [tensor]
        visited: Set[int] = set()
        
        while stack:
            current = stack.pop()
            if current._id in visited:
                continue
            visited.add(current._id)
            
            if current._tensor_type == TensorType.PARAMETER:
                parameters.append(current)
            
            for parent in current._parents:
                stack.append(parent)
        
        return parameters
    
    @staticmethod
    def count_by_type(tensor: Tensor) -> Dict[TensorType, int]:
        """
        Counts the number of tensors of each type in the computational graph starting from the given tensor.
        
        Args:
            tensor: The starting tensor from which to count tensor types.
            
        Returns:
            A dictionary with counts of each tensor type (INPUT, PARAMETER, INTERMEDIATE).
        """
        
        counts: Dict[TensorType, int] = {TensorType.INPUT: 0, TensorType.PARAMETER: 0, TensorType.INTERMEDIATE: 0}
        
        stack: List[Tensor] = [tensor]
        visited: Set[int] = set()
        
        while stack:
            current = stack.pop()
            if current._id in visited:
                continue
            visited.add(current._id)
            
            counts[current._tensor_type] += 1
            
            for parent in current._parents:
                stack.append(parent)
        
        return counts