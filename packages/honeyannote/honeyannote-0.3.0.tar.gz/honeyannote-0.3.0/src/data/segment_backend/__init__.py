"""
The `segment_backend` module has data structures for storing and managing segments.

Segment backends act as pluggable caches or indices for segments, supporting efficient
operations such as:
- Adding and removing segments
- Performing range queries and lookups
- Iterating over stored segments

Backends can be picked to suit the needs of your annotation or segment processing
pipeline.
"""
