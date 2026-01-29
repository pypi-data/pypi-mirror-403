import gc
import os
import sys
import psutil

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.clumsygrad.math import cos, exp, log, sin, sum, tan
from src.clumsygrad.tensor import Tensor, TensorType, TensorUtils
from src.clumsygrad.loss import mse_loss

class TestTensorCreation:
    """Test tensor creation and basic properties."""
    
    def test_tensor_init_with_list(self):
        data = [1, 2, 3, 4]
        tensor = Tensor(data)
        assert tensor.shape == (4,)
        assert tensor.data.dtype == np.float32
        assert tensor._tensor_type == TensorType.INPUT
        assert not tensor.requires_grad
    
    def test_tensor_init_with_numpy_array(self):
        data = np.array([[1, 2], [3, 4]])
        tensor = Tensor(data)
        assert tensor.shape == (2, 2)
        np.testing.assert_array_equal(tensor.data, data.astype(np.float32))
    
    def test_tensor_init_parameter_type(self):
        tensor = Tensor([1, 2, 3], tensor_type=TensorType.PARAMETER)
        assert tensor._tensor_type == TensorType.PARAMETER
        assert tensor.requires_grad


class TestTensorProperties:
    """Test tensor properties and setters."""
    
    def test_data_property(self):
        data = [1, 2, 3]
        tensor = Tensor(data)
        np.testing.assert_array_equal(tensor.data, np.array(data, dtype=np.float32))
    
    def test_shape_property(self):
        tensor = Tensor([[1, 2], [3, 4]])
        assert tensor.shape == (2, 2)
    
    def test_grad_property(self):
        tensor = Tensor([1, 2, 3], tensor_type=TensorType.PARAMETER)
        assert tensor.grad is None
        
        grad = np.array([0.1, 0.2, 0.3])
        tensor.grad = grad
        np.testing.assert_array_equal(tensor.grad, grad)


class TestTensorArithmetic:
    """Test tensor arithmetic operations."""
    
    def test_tensor_addition(self):
        a = Tensor([1, 2, 3], tensor_type=TensorType.PARAMETER)
        b = Tensor([4, 5, 6], tensor_type=TensorType.PARAMETER)
        c = a + b
        
        expected = np.array([5, 7, 9], dtype=np.float32)
        np.testing.assert_array_equal(c.data, expected)
        assert c.requires_grad
        assert len(c._parents) == 2
    
    def test_scalar_addition(self):
        a = Tensor([1, 2, 3], tensor_type=TensorType.PARAMETER)
        c = a + 5
        
        expected = np.array([6, 7, 8], dtype=np.float32)
        np.testing.assert_array_equal(c.data, expected)
        assert c.requires_grad
        assert len(c._parents) == 1
    
    def test_tensor_subtraction(self):
        a = Tensor([5, 7, 9], tensor_type=TensorType.PARAMETER)
        b = Tensor([1, 2, 3], tensor_type=TensorType.PARAMETER)
        c = a - b
        
        expected = np.array([4, 5, 6], dtype=np.float32)
        np.testing.assert_array_equal(c.data, expected)
        assert c.requires_grad
    
    def test_scalar_subtraction(self):
        a = Tensor([5, 6, 7], tensor_type=TensorType.PARAMETER)
        c = a - 2
        
        expected = np.array([3, 4, 5], dtype=np.float32)
        np.testing.assert_array_equal(c.data, expected)
    
    def test_tensor_multiplication(self):
        a = Tensor([2, 3, 4], tensor_type=TensorType.PARAMETER)
        b = Tensor([5, 6, 7], tensor_type=TensorType.PARAMETER)
        c = a * b
        
        expected = np.array([10, 18, 28], dtype=np.float32)
        np.testing.assert_array_equal(c.data, expected)
        assert c.requires_grad
    
    def test_scalar_multiplication(self):
        a = Tensor([2, 3, 4], tensor_type=TensorType.PARAMETER)
        c = a * 3
        
        expected = np.array([6, 9, 12], dtype=np.float32)
        np.testing.assert_array_equal(c.data, expected)
    
    def test_tensor_negation(self):
        a = Tensor([1, -2, 3], tensor_type=TensorType.PARAMETER)
        c = -a
        
        expected = np.array([-1, 2, -3], dtype=np.float32)
        np.testing.assert_array_equal(c.data, expected)
        assert c.requires_grad

class TestMatrixOperations:
    """Test matrix operations."""
    
    def test_matrix_multiplication(self):
        a = Tensor([[1, 2], [3, 4]], tensor_type=TensorType.PARAMETER)
        b = Tensor([[5, 6], [7, 8]], tensor_type=TensorType.PARAMETER)
        c = a @ b
        
        expected = np.array([[19, 22], [43, 50]], dtype=np.float32)
        np.testing.assert_array_equal(c.data, expected)
        assert c.requires_grad
    
    def test_matrix_multiplication_shape_error(self):
        a = Tensor([[1, 2, 3]], tensor_type=TensorType.PARAMETER)
        b = Tensor([[1, 2], [3, 4]], tensor_type=TensorType.PARAMETER)
        
        with pytest.raises(ValueError, match="Matrix shapes not aligned"):
            a @ b
    
    def test_matrix_multiplication_dimension_error(self):
        a = Tensor([1, 2, 3], tensor_type=TensorType.PARAMETER)
        b = Tensor([4, 5, 6], tensor_type=TensorType.PARAMETER)
        
        with pytest.raises(ValueError, match="Matrix multiplication requires at least 2D tensors"):
            a @ b
    
    def test_transpose(self):
        a = Tensor([[1, 2, 3], [4, 5, 6]], tensor_type=TensorType.PARAMETER)
        b = a.T()
        
        expected = np.array([[1, 4], [2, 5], [3, 6]], dtype=np.float32)
        np.testing.assert_array_equal(b.data, expected)
        assert b.shape == (3, 2)
        assert b.requires_grad
    
    def test_double_transpose_optimization(self):
        a = Tensor([[1, 2], [3, 4]], tensor_type=TensorType.PARAMETER)
        b = a.T().T()
        
        assert b is a

class TestBroadcastingOperations:
    """Tests for broadcasting operations and their backward functions."""

    def test_add_broadcast_scalar_to_tensor(self):
        """Test addition of scalar to tensor (broadcasting)."""
        x_data = np.array([[1., 2.], [3., 4.]])
        scalar = 5.0
        x = Tensor(x_data, tensor_type=TensorType.PARAMETER)
        
        result = x + scalar
        expected_data = x_data + scalar
        
        np.testing.assert_array_almost_equal(result.data, expected_data)
        assert result.shape == x_data.shape

    def test_add_broadcast_different_shapes(self):
        """Test addition with different but broadcastable shapes."""
        x_data = np.array([[1., 2., 3.], [4., 5., 6.]])  # Shape (2, 3)
        y_data = np.array([10., 20., 30.])                # Shape (3,)
        
        x = Tensor(x_data, tensor_type=TensorType.PARAMETER)
        y = Tensor(y_data, tensor_type=TensorType.PARAMETER)
        
        result = x + y
        expected_data = x_data + y_data  # NumPy handles broadcasting
        
        np.testing.assert_array_almost_equal(result.data, expected_data)
        assert result.shape == (2, 3)

    def test_broadcast_1d_to_2d(self):
        """Test broadcasting 1D tensor to 2D tensor."""
        x_data = np.array([[1., 2., 3.], [4., 5., 6.]])  # Shape (2, 3)
        y_data = np.array([[1.], [2.]])                   # Shape (2, 1)
        
        x = Tensor(x_data, tensor_type=TensorType.PARAMETER)
        y = Tensor(y_data, tensor_type=TensorType.PARAMETER)
        
        result = x + y
        expected_data = x_data + y_data
        
        np.testing.assert_array_almost_equal(result.data, expected_data)
        assert result.shape == (2, 3)
        
        # Test full backward pass
        result.backward(np.ones((2, 3)))
        
        # x gradient should be ones
        np.testing.assert_array_almost_equal(x.grad, np.ones((2, 3)))
        
        # y gradient should be reduced along axis 1
        expected_y_grad = np.sum(np.ones((2, 3)), axis=1, keepdims=True)
        np.testing.assert_array_almost_equal(y.grad, expected_y_grad)

    def test_broadcast_error_incompatible_shapes(self):
        """Test that incompatible shapes raise ValueError."""
        x_data = np.array([[1., 2., 3.]])    # Shape (1, 3)
        y_data = np.array([[1., 2.], [3., 4.]])  # Shape (2, 2)
        
        x = Tensor(x_data, tensor_type=TensorType.PARAMETER)
        y = Tensor(y_data, tensor_type=TensorType.PARAMETER)
        
        with pytest.raises(ValueError, match="Cannot broadcast shapes"):
            result = x + y

    def test_end_to_end_broadcast_backward(self):
        """Test complete forward and backward pass with broadcasting."""
        # Create tensors with different shapes
        x_data = np.array([[1., 2., 3.], [4., 5., 6.]])  # Shape (2, 3)
        y_data = np.array([0.1, 0.2, 0.3])               # Shape (3,)
        
        x = Tensor(x_data, tensor_type=TensorType.PARAMETER)
        y = Tensor(y_data, tensor_type=TensorType.PARAMETER)
        
        # Forward pass: z = x * y (with broadcasting)
        z = x * y
        
        # Compute loss (sum of all elements)
        loss = sum(z.reshape((6,)))  # This will create a chain: mul -> reshape -> sum
        
        # Backward pass
        loss.backward()
        
        # Check that gradients have correct shapes
        assert x.grad.shape == x_data.shape
        assert y.grad.shape == y_data.shape
        
        # Verify gradient values
        # For x: gradient should be y_data broadcasted to x's shape
        expected_x_grad = np.broadcast_to(y_data, x_data.shape)
        np.testing.assert_array_almost_equal(x.grad, expected_x_grad)
        
        # For y: gradient should be sum of x_data along axis 0
        expected_y_grad = np.sum(x_data, axis=0)
        np.testing.assert_array_almost_equal(y.grad, expected_y_grad)

class TestBackpropagation:
    """Test backward propagation."""
    
    def test_backward_scalar_output(self):
        a = Tensor([2, 3], tensor_type=TensorType.PARAMETER)
        b = Tensor([4, 5], tensor_type=TensorType.PARAMETER)
        c = a + b
        d = sum(c)  
        
        d.backward()
        
        np.testing.assert_array_equal(a.grad, np.array([1, 1], dtype=np.float32))
        np.testing.assert_array_equal(b.grad, np.array([1, 1], dtype=np.float32))
    
    def test_backward_with_custom_gradient(self):
        a = Tensor([[1, 2], [3, 4]], tensor_type=TensorType.PARAMETER)
        b = a * 2
        
        custom_grad = np.array([[1, 1], [1, 1]], dtype=np.float32)
        b.backward(custom_grad)
        
        expected_grad = np.array([[2, 2], [2, 2]], dtype=np.float32)
        np.testing.assert_array_equal(a.grad, expected_grad)

class TestTensorUtils:
    """Test TensorUtils functionality."""
    
    def test_get_parameters(self):
        a = Tensor([1, 2], tensor_type=TensorType.PARAMETER)
        b = Tensor([3, 4], tensor_type=TensorType.PARAMETER)
        c = Tensor([5, 6])  # INPUT type
        d = a + b + c
        
        params = TensorUtils.get_parameters(d)
        assert len(params) == 2
        assert a in params
        assert b in params
        assert c not in params
    
    def test_count_by_type(self):
        a = Tensor([1, 2], tensor_type=TensorType.PARAMETER)
        b = Tensor([3, 4], tensor_type=TensorType.PARAMETER)
        c = Tensor([5, 6])  # INPUT type
        d = a + b  # INTERMEDIATE type
        e = d + c  # INTERMEDIATE type
        
        counts = TensorUtils.count_by_type(e)
        assert counts[TensorType.PARAMETER] == 2
        assert counts[TensorType.INPUT] == 1
        assert counts[TensorType.INTERMEDIATE] == 2


class TestComplexOperations:
    """Test complex operation chains."""
    testing_values = [0.617, 0.591, 0.505, 0.956, 0.047, 0.128, 0.144, 0.452, 0.513, 0.749]

    def test_complex_expression1(self):
        for value in self.testing_values:
            x = Tensor(value, tensor_type=TensorType.PARAMETER)
            
            y = (x**2 + sin(x))*exp(cos(x))
            deriv_y = (2*x + cos(x))*exp(cos(x)) - (x**2 + sin(x))*exp(cos(x))*sin(x)
            y.backward()
            
            np.testing.assert_array_almost_equal(x.grad, deriv_y.data, decimal=3)
        
    def test_complex_expression2(self):
        for value in self.testing_values:
            x = Tensor(value, tensor_type=TensorType.PARAMETER)
            
            y = log(x**3 + tan(x)) * cos(exp(x))
            deriv_y = ((3 * x**2 + (cos(x)**-1)**2) * cos(exp(x))) * (x**3 + tan(x))**-1 - exp(x) * sin(exp(x)) * log(x**3 + tan(x))
            y.backward()
            
            np.testing.assert_array_almost_equal(x.grad, deriv_y.data, decimal=3)
    
    def test_complex_expression3(self):
        for value in self.testing_values:
            x = Tensor(value, tensor_type=TensorType.PARAMETER)
            
            y = (exp(2 * x) + sin(3 * x)) * (log(x) + cos(x**2))**-1
            deriv_y = ((2 * exp(2 * x) + 3 * cos(3 * x)) * (log(x) + cos(x**2)) - (exp(2 * x) + sin(3 * x)) * (x**-1 - 2 * x * sin(x**2))) * (log(x) + cos(x**2))**-2
            y.backward()
            
            np.testing.assert_array_almost_equal(x.grad, deriv_y.data, decimal=3)
    
    def test_complex_expression4(self):
        for value in self.testing_values:
            x = Tensor(value, tensor_type=TensorType.PARAMETER)
            
            y = (cos(4 * x) + log(x**2 + 1))**3
            deriv_y = 3 * (cos(4 * x) + log(x**2 + 1))**2 * (-4 * sin(4 * x) + (2 * x) * (x**2 + 1)**-1)
            y.backward()
            
            np.testing.assert_array_almost_equal(x.grad, deriv_y.data, decimal=3)
    
    def test_complex_expression5(self):
        for value in self.testing_values:
            x = Tensor(value, tensor_type=TensorType.PARAMETER)
            
            y = x * tan(x**0.5) - exp(sin(5 * x))
            deriv_y = tan(x**0.5) + 0.5 * x**0.5 * (cos(x**0.5))**-2 - 5 * cos(5 * x) * exp(sin(5 * x))
            y.backward()
            
            np.testing.assert_array_almost_equal(x.grad, deriv_y.data, decimal=3)
    
    def test_complex_forward_pass(self):
        # Test: (a * b + c) @ d
        a = Tensor([[1, 2]], tensor_type=TensorType.PARAMETER)
        b = Tensor([[3, 4]], tensor_type=TensorType.PARAMETER)
        c = Tensor([[5, 6]], tensor_type=TensorType.PARAMETER)
        d_val = np.array([[7], [8]], dtype=np.float32)
        d = Tensor(d_val, tensor_type=TensorType.PARAMETER)
        
        result = (a * b + c) @ d
        
        # a * b = [[1*3, 2*4]] = [[3, 8]]
        # a * b + c = [[3+5, 8+6]] = [[8, 14]]
        # (a * b + c) @ d = [[8*7 + 14*8]] = [[56 + 112]] = [[168]]
        expected = np.array([[168]], dtype=np.float32)
        np.testing.assert_array_equal(result.data, expected)

class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_matmul_type_error(self):
        a = Tensor([[1, 2]], tensor_type=TensorType.PARAMETER)
        
        with pytest.raises(TypeError, match="Right operand must be a Tensor"):
            a @ 5
    
    def test_gradient_accumulation(self):
        a = Tensor([1.0], tensor_type=TensorType.PARAMETER)
        
        # First computation
        b1 = a * 2
        b1.backward()
        first_grad = a.grad.copy()
        
        # Second computation without zero_grad
        b2 = a * 3
        b2.backward()
        
        # Gradients should accumulate
        expected_grad = first_grad + np.array([3.0], dtype=np.float32)
        np.testing.assert_array_equal(a.grad, expected_grad)

class TestMemoryManagement:
    """Test memory management to prevent leaks."""

    def test_memory_leak_training_loop(self):
        """Check for memory leaks during a simple training loop."""
        
        process = psutil.Process()
        gc.collect()
        initial_memory = process.memory_info().rss / (1024 * 1024)
        
        x = Tensor(np.random.rand(10), tensor_type=TensorType.PARAMETER)
        y = Tensor(np.random.rand(10), tensor_type=TensorType.INPUT)
        
        epochs = 1000
        for epoch in range(epochs):
            z = x ** 2 + 9 * x + 7
            loss = mse_loss(z, y)
            
            loss.backward()
                
        gc.collect()
        final_memory = process.memory_info().rss / (1024 * 1024)
        memory_growth_mb = final_memory - initial_memory
        
        # ALLowing a small threshold for memory growth
        threshold_percentage = 50.0
        max_allowed_growth_mb = max(1.0, initial_memory * threshold_percentage / 100)
        
        assert memory_growth_mb <= max_allowed_growth_mb, (
            f"Memory leak detected: {memory_growth_mb:.2f} MB growth "
            f"(threshold: {max_allowed_growth_mb:.2f} MB, {threshold_percentage}% of initial {initial_memory:.2f} MB)"
        )