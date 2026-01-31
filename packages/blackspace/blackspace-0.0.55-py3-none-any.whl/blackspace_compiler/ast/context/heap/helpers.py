from __future__ import annotations

from typing import TYPE_CHECKING

from ....whitespace.snippets import ADD, DUPLICATE, FETCH, PUSH, STORE, SWAP
from ...debugstatement import debug_statement

if TYPE_CHECKING:
    from ..evaluation_context import EvaluationContext


def initialize_heap(context: EvaluationContext) -> str:
    """
    Initialize the heap by setting up the heap allocation counter.
    This function should be called once at the start of the program execution.
    """
    return (
        debug_statement("Initializing heap")
        + PUSH(context.compiler_config.heap_counter)
        + PUSH(context.compiler_config.free_heap_start)
        + STORE
    )


def place_const_data_on_heap(context: EvaluationContext, data: list[int]) -> str:
    """
    Place constant data on the heap and return the starting address.
    This can be used for string literals or other constant data.
    The context stack offset is NOT incremented, that is the responsibility of the caller.
    """
    # get the current free heap location address
    res = (
        debug_statement(f"Placing {len(data)} long const data on heap")
        + PUSH(context.compiler_config.heap_counter)
        + FETCH
        + DUPLICATE
    )

    data = [len(data)] + data  # prepend length

    for i in range(len(data)):
        res += DUPLICATE
        res += PUSH(data[i]) + STORE
        res += PUSH(1) + ADD
    res += PUSH(context.compiler_config.heap_counter) + SWAP + STORE
    return res


def allocate_data_on_heap(context: EvaluationContext, size: int) -> str:
    """
    Allocate space on the heap for a given size and return the starting address.
    The first word at that address will contain the size of the allocated block.
    The context stack offset is NOT incremented, that is the responsibility of the caller.
    """
    _ = context  # Unused

    # get the current free heap location address
    res = (
        debug_statement(f"Allocating {size} long space on heap")
        + PUSH(context.compiler_config.heap_counter)
        + FETCH
    )

    # on the free location, first store the size
    res += DUPLICATE + PUSH(size) + STORE

    # increment the free heap location by size + 1
    res += DUPLICATE + PUSH(size + 1) + ADD
    res += PUSH(context.compiler_config.heap_counter) + SWAP + STORE

    return res
