from future.utils.surrogateescape import fn
import copy
import json
import hashlib
from rich.pretty import pprint
from typing import Dict, Any, Callable, Optional, List, Tuple


class DictUtils:
    """
    General-purpose dictionary manipulation utilities.
    """

    @staticmethod
    def flatten(
        d: Dict[str, Any],
        parent_key: str = "",
        sep: str = ".",
        is_leaf_predicate: Optional[Callable[[Any], bool]] = None,
    ) -> Dict[str, Any]:
        """
        Recursively flattens a nested dictionary.

        Args:
            d: The dictionary to flatten.
            parent_key: Prefix for keys (used during recursion).
            sep: Separator for dot-notation keys.
            is_leaf_predicate: Optional function that returns True if a value should
                               be treated as a leaf (value) rather than a branch to recurse.
                               Useful if you have dicts you don't want flattened.
        """
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k

            # Check if we should treat this as a leaf (custom logic)
            if is_leaf_predicate and is_leaf_predicate(v):
                items.append((new_key, v))
            # Standard recursion
            elif isinstance(v, dict):
                items.extend(
                    DictUtils.flatten(
                        v, new_key, sep=sep, is_leaf_predicate=is_leaf_predicate
                    ).items()
                )
            else:
                items.append((new_key, v))
        return dict(items)

    @staticmethod
    def unflatten(flat_dict: Dict[str, Any], sep: str = ".") -> Dict[str, Any]:
        """
        Converts flat dot-notation keys back to nested dictionaries.
        e.g., {'a.b': 1} -> {'a': {'b': 1}}
        """
        nested = {}
        for key, value in flat_dict.items():
            DictUtils.deep_set(nested, key, value, sep=sep)
        return nested

    @staticmethod
    def deep_update(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively merges 'update' dict into 'base' dict.

        Unlike the standard `dict.update()`, which replaces nested dictionaries entirely,
        this method enters nested dictionaries and updates them key-by-key. This preserves
        existing keys in 'base' that are not present in 'update'.

        Args:
            base: The original dictionary to modify.
            update: The dictionary containing new values.

        Returns:
            The modified 'base' dictionary.

        Example:
            >>> base = {'model': {'name': 'v1', 'dropout': 0.5}}
            >>> new_vals = {'model': {'name': 'v2'}}
            >>> # Standard update would delete 'dropout'. deep_update keeps it:
            >>> DictUtils.deep_update(base, new_vals)
            {'model': {'name': 'v2', 'dropout': 0.5}}
        """
        for k, v in update.items():
            if isinstance(v, dict) and k in base and isinstance(base[k], dict):
                DictUtils.deep_update(base[k], v)
            else:
                base[k] = v
        return base

    @staticmethod
    def deep_set(d: Dict[str, Any], dot_key: str, value: Any, sep: str = ".") -> None:
        """
        Sets a value in a nested dictionary using a dot-notation key path.
        Automatically creates any missing intermediate dictionaries.

        Args:
            d: The dictionary to modify.
            dot_key: The path to the value (e.g., "model.backbone.layers").
            value: The value to set.
            sep: The separator used in the key (default is ".").

        Example:
            >>> cfg = {}
            >>> DictUtils.deep_set(cfg, "a.b.c", 10)
            >>> print(cfg)
            {'a': {'b': {'c': 10}}}
        """
        parts = dot_key.split(sep)
        target = d
        for part in parts[:-1]:
            if part not in target:
                target[part] = {}
            target = target[part]
            if not isinstance(target, dict):
                # Handle conflict if a path was previously a value (e.g. overwriting a leaf)
                target = {}
        target[parts[-1]] = value

    @staticmethod
    def get_unique_hash(input_dict, length=12):
        """
        Returns a unique hash string for a dictionary.

        :param input_dict: The dictionary params
        :param length: The desired length of the hash string (default 12)
        """
        assert length >= 12, "Hash length must be at least 12 to ensure uniqueness."
        # 1. Sort keys to ensure {a:1, b:2} == {b:2, a:1}
        config_str = json.dumps(input_dict, sort_keys=True)

        # 2. Generate full SHA-256 hash (64 chars long)
        full_hash = hashlib.sha256(config_str.encode("utf-8")).hexdigest()

        # 3. Truncate to desired length
        return full_hash[:length]

    @staticmethod
    def deep_exclude(
        d: Dict[str, Any],
        keys_to_exclude: List[str],
        in_place: bool = False,
        sep: str = ".",
    ) -> Dict[str, Any]:
        """
        Removes keys from a nested dictionary based on a list of dot-notation paths.

        Args:
            d: The dictionary to filter.
            keys_to_exclude: A list of flattened keys to exclude (e.g., ['model.layers.dropout']).
            in_place: If True, modifies the dictionary directly.
                      If False, creates and modifies a deep copy, leaving the original untouched.
            sep: Separator used in the dot-notation keys (default: ".").

        Returns:
            The modified dictionary (either the original object or the new copy).

        Example:
            >>> data = {'a': {'b': 1, 'c': 2}}
            >>> DictUtils.deep_exclude(data, ['a.b'], in_place=False)
            {'a': {'c': 2}}
        """
        # 1. Handle the copy logic based on the in_place flag
        if in_place:
            target_dict = d
        else:
            target_dict = copy.deepcopy(d)

        # 2. Iterate over each dot-notation key we want to delete
        for flat_key in keys_to_exclude:
            parts = flat_key.split(sep)

            # 3. Traverse to the parent container of the key we want to delete
            current_level = target_dict
            parent_found = True

            # Loop through path parts up to the second-to-last item (the parent)
            for part in parts[:-1]:
                if isinstance(current_level, dict) and part in current_level:
                    current_level = current_level[part]
                else:
                    # The path doesn't exist in this dict, safely skip deletion
                    parent_found = False
                    break

            # 4. Delete the final key (leaf) if the parent was found
            if parent_found and isinstance(current_level, dict):
                leaf_key = parts[-1]
                if leaf_key in current_level:
                    del current_level[leaf_key]

        return target_dict

    @staticmethod
    def deep_include(
        d: Dict[str, Any],
        keys_to_include: List[str],
        in_place: bool = False,
        sep: str = ".",
    ) -> Dict[str, Any]:
        """
        Filters a nested dictionary to keep ONLY the specified dot-notation paths.

        Args:
            d: The dictionary to filter.
            keys_to_include: A list of flattened keys to include (e.g., ['a.b.c']).
            in_place: If True, modifies the original dictionary.
            sep: Separator used in the dot-notation keys.

        Returns:
            The filtered dictionary.
        """
        # 1. Create a fresh container for the keys we want to preserve
        # Unlike deep_remove, it's often cleaner to build a new dict
        # than to delete everything else.
        new_dict = {}

        for flat_key in keys_to_include:
            parts = flat_key.split(sep)

            # Pointers to traverse both dictionaries
            current_source = d
            current_target = new_dict

            for i, part in enumerate(parts):
                if isinstance(current_source, dict) and part in current_source:
                    # Move down the source
                    current_source = current_source[part]

                    # If we are at the leaf of the 'keep' path, copy the value
                    if i == len(parts) - 1:
                        current_target[part] = copy.deepcopy(current_source)
                    else:
                        # If the path doesn't exist in our new_dict yet, create it
                        if part not in current_target or not isinstance(
                            current_target[part], dict
                        ):
                            current_target[part] = {}
                        current_target = current_target[part]
                else:
                    # The path to keep doesn't exist in the source, skip it
                    break

        # 2. Handle the in_place logic
        if in_place:
            d.clear()
            d.update(new_dict)
            return d

        return new_dict

    @staticmethod
    def apply_exclusion_mask(
        d: Dict[str, Any],
        config_mask: Dict[str, Any],
        in_place: bool = False,
        sep: str = ".",
    ) -> Dict[str, Any]:
        """
        Uses a dictionary 'mask' to define what to throw away.
        """
        # Assuming your DictUtils.flatten returns a dict of {path: value}
        flatten_dict = DictUtils.flatten(config_mask, sep=sep)
        paths_to_exclude = list(flatten_dict.keys())
        return DictUtils.deep_exclude(d, paths_to_exclude, in_place=in_place, sep=sep)

    @staticmethod
    def apply_inclusion_mask(
        d: Dict[str, Any],
        config_mask: Dict[str, Any],
        in_place: bool = False,
        sep: str = ".",
    ) -> Dict[str, Any]:
        """
        Renamed from 'deep_keep_by_config'.
        Uses a dictionary 'mask' to define what to allow.
        """
        flatten_dict = DictUtils.flatten(config_mask, sep=sep)
        paths_to_include = list(flatten_dict.keys())
        return DictUtils.deep_include(d, paths_to_include, in_place=in_place, sep=sep)

    @staticmethod
    def prune(d: Any, prune_values: Tuple[Any, ...] = (None, {}, [], "")) -> Any:
        """
        Recursively removes keys where values match any item in 'prune_values'.

        Args:
            d: The dictionary or list to clean.
            prune_values: A tuple of values to be removed.
                          Default is (None, {}, [], "") which removes all empty types.
                          Pass specific values (e.g., ({}, "")) to keep None or [].

        Returns:
            The cleaned structure.
        """
        if isinstance(d, dict):
            new_dict = {}
            for k, v in d.items():
                # 1. Recursively clean children first
                cleaned_v = DictUtils.prune(v, prune_values)

                # 2. Check if the CLEANED value is in the delete list
                # We use strict check to ensure we don't delete 0 or False unless requested
                if cleaned_v not in prune_values:
                    new_dict[k] = cleaned_v
            return new_dict

        elif isinstance(d, list):
            new_list = []
            for v in d:
                cleaned_v = DictUtils.prune(v, prune_values)
                if cleaned_v not in prune_values:
                    new_list.append(cleaned_v)
            return new_list

        else:
            return d
