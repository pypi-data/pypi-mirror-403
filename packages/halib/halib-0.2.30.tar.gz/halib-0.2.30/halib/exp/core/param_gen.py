import os
import copy
import numpy as np
from itertools import product
from typing import Dict, Any, List, Iterator, Optional
from ...filetype import yamlfile
from ...utils.dict import DictUtils

# Assuming DictUtils is available in the scope or imported
# from .dict_utils import DictUtils


class ParamGen:
    """
    A flexible parameter grid generator for hyperparameter tuning and experiment management.

    This class generates a Cartesian product of parameters from a "sweep configuration"
    and optionally merges them into a "base configuration". It abstracts away the complexity
    of handling nested dictionaries and range generation.

    Key Features:
    -----------
    1. **Flexible Syntax**: Define parameters using standard nested dictionaries or
       dot-notation keys (e.g., `'model.backbone.layers'`).
    2. **Range Shortcuts**:
       - **Choices**: Standard lists `[1, 2, 3]`.
       - **String Ranges**: `"start:stop:step"` (e.g., `"0:10:2"` -> `[0, 2, 4, 6, 8]`).
       - **Dict Ranges**: `{'start': 0, 'stop': 1, 'step': 0.1}`.
    3. **Deep Merging**: Automatically updates deep keys in `base_cfg` without overwriting siblings.

    Example:
    --------
    >>> base = {'model': {'name': 'resnet', 'dropout': 0.1}, 'seed': 42}
    >>> sweep = {
    ...     'model.name': ['resnet', 'vit'],      # Dot notation
    ...     'model.dropout': "0.1:0.3:0.1",       # Range string
    ...     'seed': [42, 100]                     # Simple choice
    ... }
    >>> grid = ParamGen(sweep, base)
    >>> configs = grid.expand()
    >>> print(len(configs))  # Outputs: 8 (2 models * 2 dropouts * 2 seeds)
    Attributes:
        keys (List[str]): List of flattened dot-notation keys being swept.
        values (List[List[Any]]): List of value options for each key.
    """

    def __init__(
        self, sweep_cfg: Dict[str, Any], base_cfg: Optional[Dict[str, Any]] = None
    ):
        """
        Args:
            sweep_cfg: The dictionary defining parameters to sweep.
            base_cfg: (Optional) The base config to merge sweep parameters into.
                      If None, expand() behaves like expand_sweep().
        """
        self.base_cfg = base_cfg if base_cfg is not None else {}

        # Recursively flatten the nested sweep config into dot-notation keys
        # Refactored to use DictUtils, passing our custom leaf logic
        flat_sweep = DictUtils.flatten(sweep_cfg, is_leaf_predicate=self._is_sweep_leaf)

        # Expand values (ranges, strings) which DictUtils leaves as-is
        self.param_space = {k: self._expand_val(v) for k, v in flat_sweep.items()}

        self.keys = list(self.param_space.keys())
        self.values = list(self.param_space.values())

    def get_param_space(self) -> Dict[str, List[Any]]:
        """Returns the parameter space as a dictionary of dot-notation keys to value lists."""
        return self.param_space

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        """Yields fully merged configurations one by one."""
        for combination in product(*self.values):
            # 1. Create the flat sweep dict (dot notation)
            flat_params = dict(zip(self.keys, combination))

            # 2. Deep copy base and update with current params
            new_cfg = copy.deepcopy(self.base_cfg)

            # Refactored: Unflatten the specific params, then deep merge
            update_structure = DictUtils.unflatten(flat_params)
            DictUtils.deep_update(new_cfg, update_structure)

            # 3. Store metadata (Optional)
            # if "_meta" not in new_cfg:
            #     new_cfg["_meta"] = {}
            # We unflatten the sweep params here so the log is readable
            # new_cfg["_meta"]["sweep_params"] = DictUtils.unflatten(flat_params)

            yield new_cfg

    # ! --- Factory Methods ---
    @classmethod
    def from_dicts(
        cls, sweep_cfg: Dict[str, Any], base_cfg: Optional[Dict[str, Any]] = None
    ):
        """
        Load from dictionaries.
        Args:
            sweep_cfg: The dictionary defining parameters to sweep.
            base_cfg: (Optional) The base config to merge sweep parameters into.
        """
        return cls(sweep_cfg, base_cfg)

    @classmethod
    def from_files(cls, sweep_yaml: str, base_yaml: Optional[str] = None):
        """
        Load from files.
        Args:
            sweep_yaml: Path to sweep config.
            base_yaml: (Optional) Path to base config.
        """
        assert os.path.isfile(sweep_yaml), f"Sweep file not found: {sweep_yaml}"
        sweep_dict = yamlfile.load_yaml(sweep_yaml, to_dict=True)
        base_dict = None
        if base_yaml:
            base_dict = yamlfile.load_yaml(base_yaml, to_dict=True)
            if "__base__" in base_dict:
                del base_dict["__base__"]

        return cls(sweep_dict, base_dict)

    def expand(self) -> List[Dict[str, Any]]:
        """Generates and returns the full list of MERGED configurations."""
        return list(self)

    def expand_sweep_flat(self) -> List[Dict[str, Any]]:
        """
        Returns a list of ONLY the sweep parameters, formatted as FLAT dot-notation dictionaries.

        Returns:
            [{'exp_params.model': 'resnet', 'exp_params.lr': 0.01}, ...]
        """
        combinations = []
        for combination in product(*self.values):
            flat_dict = dict(zip(self.keys, combination))
            combinations.append(flat_dict)
        return combinations

    # Note: _unflatten, _flatten_params, and _apply_updates have been removed
    # as they are replaced by DictUtils methods.

    def _is_sweep_leaf(self, val: Any) -> bool:
        if isinstance(val, list):
            return True
        if isinstance(val, str) and ":" in val:
            return True
        if isinstance(val, dict) and "start" in val and "stop" in val:
            return True
        return False

    def _expand_val(self, val: Any) -> List[Any]:
        if isinstance(val, list):
            return val

        if isinstance(val, str) and ":" in val:
            try:
                parts = [float(x) for x in val.split(":")]
                if len(parts) == 3:
                    arr = np.arange(parts[0], parts[1], parts[2])
                    return [float(f"{x:.6g}") for x in arr]
            except ValueError:
                pass

        if isinstance(val, dict) and "start" in val:
            step = val.get("step", 1)
            return np.arange(val["start"], val["stop"], step).tolist()

        return [val]
