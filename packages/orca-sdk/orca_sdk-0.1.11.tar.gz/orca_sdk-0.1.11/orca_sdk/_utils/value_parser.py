from __future__ import annotations

import base64
import io
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    # peer dependencies that are used for types only
    import numpy as np  # type: ignore
    from numpy.typing import NDArray  # type: ignore
    from PIL import Image as pil  # type: ignore

    ValueType = str | pil.Image | NDArray[np.float32]
    """
    The type of a value in a memoryset

    - `str`: string
    - `pil.Image`: image
    - `NDArray[np.float32]`: univariate or multivariate timeseries
    """
else:
    ValueType = Any


def decode_value(value: str) -> ValueType:
    if value.startswith("data:image"):
        try:
            from PIL import Image as pil  # type: ignore
        except ImportError as e:
            raise ImportError("Install Pillow to use image values") from e

        header, data = value.split(",", 1)
        return pil.open(io.BytesIO(base64.b64decode(data)))

    if value.startswith("data:numpy"):
        try:
            import numpy as np  # type: ignore
        except ImportError as e:
            raise ImportError("Install numpy to use timeseries values") from e

        header, data = value.split(",", 1)
        return np.load(io.BytesIO(base64.b64decode(data)))

    return value


def encode_value(value: ValueType) -> str:
    try:
        from PIL import Image as pil  # type: ignore
    except ImportError:
        pil = None  # type: ignore[assignment]

    try:
        import numpy as np  # type: ignore
    except ImportError:
        np = None  # type: ignore[assignment]

    if pil is not None and isinstance(value, pil.Image):
        header = f"data:image/{value.format.lower()};base64," if value.format else "data:image;base64,"  # type: ignore[union-attr]
        buffer = io.BytesIO()
        value.save(buffer, format=value.format)  # type: ignore[union-attr]
        bytes = buffer.getvalue()
        return header + base64.b64encode(bytes).decode("utf-8")

    if np is not None and isinstance(value, np.ndarray):
        header = f"data:numpy/{value.dtype.name};base64,"  # type: ignore[union-attr]
        buffer = io.BytesIO()
        np.save(buffer, value)
        return header + base64.b64encode(buffer.getvalue()).decode("utf-8")

    # Value is already a string, or an unhandled type (fall back to str conversion)
    return value if isinstance(value, str) else str(value)
