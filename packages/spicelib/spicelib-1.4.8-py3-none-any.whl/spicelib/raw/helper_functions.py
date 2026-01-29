from typing import List, Union, BinaryIO

from typing import List, Union, BinaryIO


def read_sparse(
    fp: BinaryIO,
    start: int,
    chunk_size: int,
    sep: int,
    count: int,
    *,
    join: bool = False,
    strict: bool = True,
) -> Union[List[bytes], bytes]:
    """
    Read sparse chunks from a (seekable) binary file.

    Parameters:
        fp:        Open file object (must be seekable, recommended in 'rb' mode).
        start:     Byte offset in the file where the first chunk starts (>= 0).
        chunk_size:Size in bytes of each chunk to read (>= 0).
        sep:       Start-to-start separation in bytes between consecutive chunks.
                   Can be smaller than chunk_size (overlap) or even 0 (same spot).
        count:     Number of chunks to read (>= 0).

        join:      If True, returns a single bytes object of length
                   (k * chunk_size). If False, returns a List[bytes].
        strict:    If True, raises EOFError if any chunk is shorter than
                   chunk_size (i.e., end of file reached). If False, stops
                   at the first short read and returns what was read so far.

    Returns:
        - If join is False: a list of 'count' bytes objects (unless strict=False
          and EOF is hit early, in which case fewer).
        - If join is True: a single bytes object with concatenated chunks. With
          strict=False and early EOF, it may be shorter than count*chunk_size.

    Raises:
        ValueError: on invalid arguments or non-seekable file.
        EOFError: if strict=True and EOF prevents a full chunk read.
    """
    # Basic validations
    if start < 0:
        raise ValueError("start must be >= 0")
    if chunk_size < 0:
        raise ValueError("chunk_size must be >= 0")
    if count < 0:
        raise ValueError("count must be >= 0")
    if not hasattr(fp, "seek") or not hasattr(fp, "read"):
        raise ValueError("fp must be a seekable, readable file object")
    try:
        if not fp.seekable():  # type: ignore[attr-defined]
            raise ValueError("File object must be seekable")
    except Exception:
        # If the object doesn't expose seekable(), we attempt to proceed but may still fail on seek.
        pass

    # Handle trivial cases quickly
    if count == 0 or chunk_size == 0:
        return b"" if join else []

    if join:
        # Efficient: preallocate and use readinto slices
        out = bytearray(count * chunk_size)
        write_off = 0
        for i in range(count):
            pos = start + i * sep
            fp.seek(pos)
            view = memoryview(out)[write_off:write_off + chunk_size]
            n = fp.readinto(view)
            if n is None:
                n = 0  # readinto may return None on some file-like objects; treat as 0
            if n < chunk_size:
                if strict:
                    raise EOFError(
                        f"Short read at chunk {i}: expected {chunk_size} bytes, got {n}."
                    )
                # Truncate to what we actually filled and return early
                write_off += max(n, 0)
                return bytes(out[:write_off])
            write_off += n
        return bytes(out)
    else:
        chunks: List[bytes] = []
        for i in range(count):
            pos = start + i * sep
            fp.seek(pos)
            data = fp.read(chunk_size)
            if data is None:
                data = b""
            if len(data) < chunk_size:
                if strict:
                    raise EOFError(
                        f"Short read at chunk {i}: expected {chunk_size} bytes, got {len(data)}."
                    )
                chunks.append(data)
                break
            chunks.append(data)
        return chunks