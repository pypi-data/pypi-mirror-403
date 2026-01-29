# SPDX-FileCopyrightText: © 2025 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0
# Auto-generated submodule wrapper

from .tt_umd import wormhole as _submodule

# Re-export all attributes from the C++ submodule
__all__ = [name for name in dir(_submodule) if not name.startswith('_')]
globals().update({name: getattr(_submodule, name) for name in __all__})
