import os
from pathlib import Path
from typing import List, Dict

from needle.operators import I18NFactoryOperator, OverlayOperator
from needle.spec import OperatorProtocol


class MessageStore:
    """
    Orchestrates resource loading using the PyNeedle Operator system.

    Instead of manually loading JSONs, it maintains a list of 'Asset Roots'.
    When an operator is requested for a language, it builds an OverlayOperator
    that stacks I18NFactoryOperators for each root.
    """

    def __init__(self):
        # List of paths where 'needle/<lang>/*.json' structures can be found.
        # Order matters: later roots override earlier ones (if we prepend)
        # or earlier ones override later (if we prepend).
        # Strategy: New roots are added to the FRONT of the list (High Priority).
        self._asset_roots: List[Path] = []

        # Cache operators by language code
        self._operator_cache: Dict[str, OperatorProtocol] = {}

    def register_asset_root(self, path: Path) -> None:
        """
        Register a new directory containing 'needle' assets.
        This directory should contain the 'needle' folder directly?
        No, usually it points TO the 'needle' folder or the parent?

        Convention: The path passed here MUST be the parent of the 'needle' directory.
        e.g. .../src/stitcher/assets  (which contains ./needle/en/...)
        """
        resolved = path.resolve()
        if resolved not in self._asset_roots:
            # Insert at beginning to give higher priority to user/plugin overrides
            self._asset_roots.insert(0, resolved)
            # Invalidate cache because the overlay structure has changed
            self._operator_cache.clear()

    def get_operator(self, lang: str) -> OperatorProtocol:
        """
        Get the fully composed Operator for a specific language.
        """
        if lang in self._operator_cache:
            return self._operator_cache[lang]

        # Build the chain
        operators: List[OperatorProtocol] = []
        for root in self._asset_roots:
            # I18NFactoryOperator takes the 'assets root' and
            # internally appends "needle/<lang>" when called with a lang pointer.
            # But wait, I18NFactoryOperator(root)(lang_ptr) returns a FileSystemOperator.

            factory = I18NFactoryOperator(root)
            # We treat the lang string as a pointer path (e.g. "en")
            # The factory resolves this to root/needle/en
            op = factory(lang)
            operators.append(op)

        # Create the overlay
        # Operators are in priority order (Head of list = Highest Priority)
        overlay = OverlayOperator(operators)

        self._operator_cache[lang] = overlay
        return overlay

    @staticmethod
    def detect_lang() -> str:
        """
        Helper to detect system language.
        """
        # 1. Explicit override
        env_lang = os.getenv("NEEDLE_LANG") or os.getenv("STITCHER_LANG")
        if env_lang:
            return env_lang

        # 2. System LANG
        sys_lang = os.getenv("LANG")
        if sys_lang:
            base_lang = sys_lang.split(".")[0].split("_")[0]
            if base_lang:
                return base_lang

        return "en"
