"""
Base transformer class with | operator support.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseTransformer(ABC):
    """
    Base class for chainable transformers.
    
    Supports | operator for chaining:
        >>> chain = Rename({"a": "b"}) | AddField("c", "value") | Drop(["d"])
        >>> result = chain.transform(data)
    """
    
    @abstractmethod
    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform a batch of records."""
        ...
    
    def __or__(self, other: "BaseTransformer") -> "TransformerChain":
        """Chain transformers with | operator."""
        if isinstance(other, TransformerChain):
            return TransformerChain([self] + other.transformers)
        return TransformerChain([self, other])
    
    def __ror__(self, other: "BaseTransformer") -> "TransformerChain":
        """Support other | self."""
        if isinstance(other, TransformerChain):
            return TransformerChain(other.transformers + [self])
        return TransformerChain([other, self])


class TransformerChain(BaseTransformer):
    """
    Chain of transformers that processes data through each in sequence.
    
    Created automatically when using | operator.
    """
    
    def __init__(self, transformers: Optional[List[BaseTransformer]] = None):
        self.transformers: List[BaseTransformer] = list(transformers) if transformers else []
    
    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform data through all transformers."""
        result = data
        for transformer in self.transformers:
            result = transformer.transform(result)
        return result
    
    def __or__(self, other: BaseTransformer) -> "TransformerChain":
        """Add transformer to chain."""
        if isinstance(other, TransformerChain):
            return TransformerChain(self.transformers + other.transformers)
        return TransformerChain(self.transformers + [other])
    
    def __len__(self) -> int:
        return len(self.transformers)
    
    def __iter__(self):
        return iter(self.transformers)
