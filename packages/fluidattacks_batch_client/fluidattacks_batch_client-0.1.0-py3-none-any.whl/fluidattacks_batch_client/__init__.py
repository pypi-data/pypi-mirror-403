from ._logger import (
    setup_logger,
)
from fa_purity import (
    Unsafe,
)

__version__ = "0.1.0"
Unsafe.compute(setup_logger(__name__))
