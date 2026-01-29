"""
This module contains common optimizers for optimizing parameters in a computational graph.
"""

from abc import ABC
from typing import List

import numpy as np

from .tensor import Tensor, TensorType

class Optimizer(ABC):
    """
    Abstract base class for all optimizers.
    """
    
    def __init__(self, parameters: List[Tensor]):
        self.parameters = [p for p in parameters if p._tensor_type == TensorType.PARAMETER]
    
    def step(self):
        """Update parameters. Must be implemented by subclasses."""
        raise NotImplementedError("Optimizer subclasses must implement the step method.")
    
    def zero_grad(self):
        """Zero gradients for all parameters."""
        for param in self.parameters:
            param.grad = None

class SGD(Optimizer):
    """
    Stochastic Gradient Descent (SGD) optimizer.
    
    This optimizer updates parameters using the formula: `param -= lr * grad`,
    where `param` is a parameter tensor, `lr` is the learning rate, and `grad` is the gradient of the parameter.
    
    Reference: Robbins, H., & Monro, S. (1951). A stochastic approximation method.
    """
    
    def __init__(self, parameters: List[Tensor], lr: float = 0.01):
        """
        Initialize the SGD optimizer.
        
        Args:
            parameters (List[Tensor]): List of parameter tensors to optimize.
            lr (float): Learning rate for the optimizer. Default is 0.01.
        """
    
        super().__init__(parameters)
        self.lr = lr
    
    def step(self):
        """Update parameters."""
        for param in self.parameters:
            if param.grad is not None:
                param._data -= self.lr * param.grad
            
class Adam(Optimizer):
    """
    Adam (Adaptive Moment Estimation) optimizer.
    
    This optimizer combines the advantages of AdaGrad and RMSprop by computing
    adaptive learning rates for each parameter using estimates of first and
    second moments of the gradients.
    
    Reference: Kingma, D. P., & Ba, J. (2014). Adam: A method for stochastic optimization.
    """
    
    def __init__(self, parameters: List[Tensor], lr: float = 0.001, 
                 beta1: float = 0.9, beta2: float = 0.999, eps: float = 1e-8):
        """
        Initialize the Adam optimizer.
        
        Args:
            parameters (List[Tensor]): List of parameter tensors to optimize.
            lr (float): Learning rate. Default is 0.001.
            beta1 (float): Exponential decay rate for first moment estimates. Default is 0.9.
            beta2 (float): Exponential decay rate for second moment estimates. Default is 0.999.
            eps (float): Small constant for numerical stability. Default is 1e-8.
        """
        
        super().__init__(parameters)
        self.lr = lr
        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps
        self.t = 0  
        
        self.biased_first_moment = [np.zeros_like(p._data) for p in self.parameters]  
        self.biased_second_moment = [np.zeros_like(p._data) for p in self.parameters]
    
    def step(self):
        """Update parameters."""
        self.t += 1
        
        for i, param in enumerate(self.parameters):
            if param.grad is not None:
                grad = param.grad
                
                self.biased_first_moment[i] = self.beta1 * self.biased_first_moment[i] + (1 - self.beta1) * grad
                self.biased_second_moment[i] = self.beta2 * self.biased_second_moment[i] + (1 - self.beta2) * (grad ** 2)
                m_hat = self.biased_first_moment[i] / (1 - self.beta1 ** self.t)
                v_hat = self.biased_second_moment[i] / (1 - self.beta2 ** self.t)
                param._data -= self.lr * m_hat / (np.sqrt(v_hat) + self.eps)