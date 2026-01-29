"""
Training utilities: optimizers and loss functions.

This module provides optimizer and loss function configurations for
training Cersys models.
"""

from typing import Dict, Any
from dataclasses import dataclass

__all__ = [
    "Optimizer", "SGD", "Adam", "AdamW",
    "BPRLoss", "MSELoss", "ContrastiveLoss",
]


@dataclass
class Optimizer:
    """
    Base class for optimizer configurations.
    
    Attributes:
        learning_rate (float): Learning rate for parameter updates.
        weight_decay (float): L2 regularization strength.
    """
    learning_rate: float = 0.01
    weight_decay: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "type": self.__class__.__name__,
            "learning_rate": self.learning_rate,
            "weight_decay": self.weight_decay,
        }


@dataclass
class SGD(Optimizer):
    """
    Stochastic Gradient Descent optimizer.
    
    Supports optional momentum for accelerated convergence.
    
    Attributes:
        learning_rate (float): Learning rate (default: 0.01).
        momentum (float): Momentum factor (default: 0.0).
        weight_decay (float): L2 regularization (default: 0.0).
    
    Example:
        >>> optimizer = cs.SGD(learning_rate=0.01, momentum=0.9)
    """
    momentum: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["momentum"] = self.momentum
        return d


@dataclass
class Adam(Optimizer):
    """
    Adam optimizer (Adaptive Moment Estimation).
    
    Combines momentum with per-parameter adaptive learning rates.
    Generally performs well across a wide range of problems.
    
    Attributes:
        learning_rate (float): Learning rate (default: 0.001).
        beta1 (float): Exponential decay for first moment (default: 0.9).
        beta2 (float): Exponential decay for second moment (default: 0.999).
        epsilon (float): Numerical stability constant (default: 1e-8).
        weight_decay (float): L2 regularization (default: 0.0).
    
    Example:
        >>> optimizer = cs.Adam(learning_rate=0.001)
    """
    learning_rate: float = 0.001
    beta1: float = 0.9
    beta2: float = 0.999
    epsilon: float = 1e-8
    
    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            "beta1": self.beta1,
            "beta2": self.beta2,
            "epsilon": self.epsilon,
        })
        return d


@dataclass
class AdamW(Adam):
    """
    AdamW optimizer (Adam with decoupled weight decay).
    
    Implements weight decay correctly for Adam, which can improve
    generalization compared to L2 regularization.
    
    Attributes:
        Same as Adam, but weight_decay is applied correctly.
    
    Example:
        >>> optimizer = cs.AdamW(learning_rate=0.001, weight_decay=0.01)
    """
    weight_decay: float = 0.01


# =============================================================================
# LOSS FUNCTIONS
# =============================================================================

@dataclass
class Loss:
    """Base class for loss function configurations."""
    
    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.__class__.__name__}


@dataclass
class BPRLoss(Loss):
    """
    Bayesian Personalized Ranking loss.
    
    Optimizes for correct ranking between positive and negative items.
    This is the standard loss for implicit feedback recommender systems.
    
    Attributes:
        margin (float): Margin for the pairwise comparison (default: 0.0).
    
    Example:
        >>> loss = cs.BPRLoss()
    """
    margin: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["margin"] = self.margin
        return d


@dataclass
class MSELoss(Loss):
    """
    Mean Squared Error loss.
    
    For explicit feedback (rating prediction) tasks.
    
    Example:
        >>> loss = cs.MSELoss()
    """
    pass


@dataclass
class ContrastiveLoss(Loss):
    """
    Contrastive loss for representation learning.
    
    Brings similar items closer and pushes dissimilar items apart
    in the embedding space.
    
    Attributes:
        temperature (float): Temperature scaling factor (default: 0.1).
        margin (float): Margin for negative pairs (default: 0.5).
    
    Example:
        >>> loss = cs.ContrastiveLoss(temperature=0.07)
    """
    temperature: float = 0.1
    margin: float = 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            "temperature": self.temperature,
            "margin": self.margin,
        })
        return d
