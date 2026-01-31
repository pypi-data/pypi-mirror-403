"""OpenBB Polymarket extension package.

Note: keep this module import-light. OpenBB loads extensions via entry points and
imports submodules directly. Importing OpenBB core modules here can create
circular-import issues during extension discovery.
"""

__all__: list[str] = []
