"""
Index sets for optimization models.

Provides utilities for defining and manipulating index sets used in
indexed variables and constraints.
"""

from typing import Any, Callable, Iterator, List, Optional, Tuple, Union


class IndexSet:
    """
    A simple index set for optimization models.
    
    Represents a set of indices that can be used for indexed variables
    and constraints.
    """
    
    def __init__(self, name: str, elements: List[Any]):
        """
        Initialize index set.
        
        Args:
            name: Set name
            elements: List of elements in the set
        """
        self.name = name
        self._elements = list(elements)
    
    def __iter__(self) -> Iterator:
        return iter(self._elements)
    
    def __len__(self) -> int:
        return len(self._elements)
    
    def __contains__(self, item: Any) -> bool:
        return item in self._elements
    
    def __getitem__(self, index: int) -> Any:
        return self._elements[index]
    
    @property
    def elements(self) -> List[Any]:
        return self._elements
    
    def filter(self, predicate: Callable[[Any], bool]) -> "IndexSet":
        """Return a new set with elements matching the predicate."""
        filtered = [e for e in self._elements if predicate(e)]
        return IndexSet(f"{self.name}_filtered", filtered)
    
    def __repr__(self) -> str:
        if len(self._elements) <= 5:
            return f"IndexSet({self.name}, {self._elements})"
        return f"IndexSet({self.name}, [{self._elements[0]}, ..., {self._elements[-1]}], n={len(self._elements)})"


class IndexedSet:
    """
    A multi-dimensional index set (Cartesian product of sets).
    
    Useful for creating indexed variables like x[i,j].
    """
    
    def __init__(self, name: str, *sets: Union[IndexSet, List[Any]]):
        """
        Initialize indexed set as Cartesian product of input sets.
        
        Args:
            name: Set name
            *sets: Index sets or lists to combine
        """
        self.name = name
        self._sets = []
        for s in sets:
            if isinstance(s, IndexSet):
                self._sets.append(s)
            else:
                self._sets.append(IndexSet("anon", list(s)))
    
    def __iter__(self) -> Iterator[Tuple]:
        """Iterate over all index combinations."""
        if not self._sets:
            return iter([])
        
        # Generate Cartesian product
        def cartesian(*sets):
            if not sets:
                yield ()
            else:
                for item in sets[0]:
                    for rest in cartesian(*sets[1:]):
                        yield (item,) + rest
        
        return cartesian(*[s.elements for s in self._sets])
    
    def __len__(self) -> int:
        if not self._sets:
            return 0
        result = 1
        for s in self._sets:
            result *= len(s)
        return result
    
    @property
    def dimension(self) -> int:
        """Return the number of dimensions."""
        return len(self._sets)
    
    def filter(self, predicate: Callable[[Tuple], bool]) -> List[Tuple]:
        """Return list of tuples matching the predicate."""
        return [t for t in self if predicate(t)]
    
    def __repr__(self) -> str:
        dims = " x ".join(str(len(s)) for s in self._sets)
        return f"IndexedSet({self.name}, dims={dims}, total={len(self)})"


def range_set(name: str, start: int, end: int) -> IndexSet:
    """Create an index set from a range."""
    return IndexSet(name, list(range(start, end)))


def product(*sets: Union[IndexSet, List]) -> IndexedSet:
    """Create Cartesian product of sets."""
    return IndexedSet("product", *sets)
