"""Abstraction for reading/writing labeled ML examples."""
from __future__ import annotations

import json
import logging
import os
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class JsonlFileStore:
    """JSONL file-based storage for ML training examples."""

    def load_examples(self, data_file: str) -> List[dict]:
        """Load all examples from a JSONL file."""
        if not os.path.exists(data_file):
            return []
        examples: List[dict] = []
        with open(data_file, "r") as file_handle:
            for line_num, line in enumerate(file_handle, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    examples.append(json.loads(line))
                except json.JSONDecodeError:
                    logger.warning("Skipping malformed JSON at %s:%d", data_file, line_num)
        return examples

    def append_example(
        self,
        data_file: str,
        features: List[float],
        label: float,
        metadata: Optional[Dict] = None,
    ) -> None:
        """Append a single training example to a JSONL file."""
        directory = os.path.dirname(data_file)
        if directory:
            os.makedirs(directory, exist_ok=True)
        entry: Dict = {"features": features, "label": label}
        if metadata:
            entry.update(metadata)
        with open(data_file, "a") as file_handle:
            file_handle.write(json.dumps(entry) + "\n")

    def example_count(self, data_file: str) -> int:
        """Count the number of examples in a JSONL file."""
        if not os.path.exists(data_file):
            return 0
        count = 0
        with open(data_file, "r") as file_handle:
            for line in file_handle:
                if line.strip():
                    count += 1
        return count


# Module-level default instance
_default_store = JsonlFileStore()


def get_default_store() -> JsonlFileStore:
    """Get the shared default store instance."""
    return _default_store
