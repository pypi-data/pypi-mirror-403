# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Input validation utilities for transformations.

This module provides utilities to detect and validate input types for
streaming and batch transformations.
"""

from typing import Any, List

from ..resources.locations import StreamingInput

__all__ = [
    "is_streaming_input",
    "validate_streaming_transformation_inputs",
    "validate_batch_transformation_inputs",
]


def is_streaming_input(input_source: Any) -> bool:
    """
    Determine if an input source is a streaming input.

    Streaming inputs are sources that extend the StreamingInput base class,
    such as KafkaTopic.

    Args:
        input_source: The input source to check.

    Returns:
        bool: True if the input is a streaming input, False otherwise.
    """
    return isinstance(input_source, StreamingInput)


def validate_streaming_transformation_inputs(inputs: List[Any]) -> List[Any]:
    """
    Validate inputs for a streaming transformation.

    Streaming transformations require all inputs to be streaming inputs.

    Args:
        inputs: List of input sources for the transformation.

    Returns:
        The validated list of streaming inputs.

    Raises:
        ValueError: If no inputs are provided or if any non-streaming inputs are found.
    """
    if not inputs:
        raise ValueError(
            "Streaming transformations require at least one input. "
            "No inputs were provided."
        )

    non_streaming_inputs = [inp for inp in inputs if not is_streaming_input(inp)]

    if non_streaming_inputs:
        non_streaming_count = len(non_streaming_inputs)
        raise ValueError(
            f"Streaming transformations can only have streaming inputs. "
            f"Found {non_streaming_count} non-streaming input(s). "
            f"All inputs must be streaming inputs."
        )

    return inputs


def validate_batch_transformation_inputs(inputs: List[Any]) -> List[Any]:
    """
    Validate inputs for a batch transformation.

    Batch transformations should not have streaming inputs.

    Args:
        inputs: List of input sources for the transformation.

    Returns:
        The validated list of inputs.

    Raises:
        ValueError: If any streaming inputs are found.
    """
    if not inputs:
        return inputs

    streaming_inputs = [inp for inp in inputs if is_streaming_input(inp)]

    if streaming_inputs:
        streaming_count = len(streaming_inputs)
        raise ValueError(
            f"Batch transformations cannot have streaming inputs. "
            f"Found {streaming_count} streaming input(s). "
            f"Use streaming_sql_transformation or streaming_df_transformation instead."
        )

    return inputs
