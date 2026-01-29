""" Chunking utils
"""

import logging
from functools import reduce

from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


def get_nested_value(dictionary, path, default=None):
    """Get value in nested dictionary

    Args:
        dictionary:
        path:
        default:

    Returns:

    """
    return reduce(
        lambda d, key: d.get(key, default) if isinstance(d, dict) else default,
        path.split("."),
        dictionary,
    )


def flatten_dict(obj, parent_key="", separator=" > "):
    """Flatten dict - generator

    Args:
        obj:
        parent_key:
        separator

    Returns:

    """
    # Flatten dict
    if isinstance(obj, dict):
        for k, v in obj.items():
            flat_key = f"{parent_key}{separator}{k}" if parent_key else k
            yield from flatten_dict(v, flat_key, separator)
    # Flatten list
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            flat_key = f"{parent_key}{separator}{i}" if parent_key else str(i)
            yield from flatten_dict(v, flat_key, separator)
    else:
        # Yield leaf node
        yield parent_key, obj


def sliding_window(text, chunk_size=1000, chunk_overlap=200):
    """Split text with a sliding window

    Args:
        text:
        chunk_size:
        chunk_overlap:

    Returns:

    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )

    return text_splitter.split_text(text)


def chunk_json_dict(
    json_dict,
    chunk_size=1000,
    chunk_overlap=200,
    target_keys=None,
    key_sep=" > ",
    value_sep=" | ",
):
    """Convert a JSON dict into a list of texts (key > path | text)

    Args:
        json_dict:
        chunk_size:
        chunk_overlap:
        target_keys:
        key_sep:
        value_sep:

    Returns:

    """
    # Flatten the dict
    flat_data = {}
    if target_keys:
        # Extract selected keys
        for target in target_keys:
            value = get_nested_value(json_dict, target)
            # When a value is found
            if value is not None:
                # Replace dot notation by key separator
                formatted_parent_key = target.replace(".", key_sep)
                # Flatten the sub dict
                sub_flat = dict(
                    flatten_dict(
                        value,
                        parent_key=formatted_parent_key,
                        separator=key_sep,
                    )
                )
                # Add sub dict to flat data
                flat_data.update(sub_flat)
    else:
        # Flatten the entire JSON dict
        flat_data = dict(flatten_dict(json_dict, separator=key_sep))

    # Initialize variables
    separator = " \n "
    sep_len = len(separator)

    # Initialize final list of chunks
    final_chunks = []
    # Initialize chunks buffer
    current_chunk_lines = []
    # Initialize size of chunks buffer
    current_chunk_size = 0

    # Split the dictionary into chunks
    for key, value in flat_data.items():
        # Remove new lines from value
        clean_val = str(value).replace("\n", " ")
        line_format = f"{key}{value_sep}{clean_val}"
        line_len = len(line_format)

        # Value fits in the current chunk
        if current_chunk_size + line_len + sep_len <= chunk_size:
            # Add the chunk to chunk buffer
            current_chunk_lines.append(line_format)
            # Increase current size of buffer
            current_chunk_size += line_len + sep_len

        # Value is bigger than a chunk, split it
        elif line_len > chunk_size:
            prefix = f"{key}{value_sep}"
            # Calculate space left for the value
            available_space = max(chunk_size - len(prefix), 0)
            # If the key is too big, keep only the value (set empty prefix)
            if available_space == 0:
                available_space = chunk_size
                prefix = ""

            # Split the value with sliding window
            segments = sliding_window(
                clean_val,
                chunk_size=available_space,
                chunk_overlap=chunk_overlap,
            )

            # Iterate over all segments of the long value
            for segment in segments:
                # Add prefix key before text segment
                seg_line = f"{prefix}{segment}"

                # If the segment fits the current chunk
                if current_chunk_size + len(seg_line) + sep_len <= chunk_size:
                    # add the segment to current buffer
                    current_chunk_lines.append(seg_line)
                    # increase current buffer size
                    current_chunk_size += len(seg_line) + sep_len
                else:
                    # the segment does not fit the current buffer and the buffer is not empty
                    if current_chunk_lines:
                        # add the lines in the current buffer to final list
                        final_chunks.append(
                            separator.join(current_chunk_lines)
                        )
                    # Initialize a new buffer with the current segment
                    current_chunk_lines = [seg_line]
                    # Set the current size of the buffer
                    current_chunk_size = len(seg_line)

        # Value fits in a chunk, but is too big for current one
        else:
            # Check if lines are currently in the buffer
            if current_chunk_lines:
                # Add lines to final list of chunks
                final_chunks.append(separator.join(current_chunk_lines))
            # Initialize new buffer with current value
            current_chunk_lines = [line_format]
            # Set current buffer length to the new value
            current_chunk_size = line_len

    # If there are chunks left in the buffer
    if current_chunk_lines:
        # Add the chunks to final list of chunks
        final_chunks.append(separator.join(current_chunk_lines))

    # Return final list of chunks
    return final_chunks
