from typing import Mapping


def coerce_value(registry: Mapping[str, str], value: str, field_name: str) -> str:
    if value is None:
        raise ValueError(f"{field_name} is required")
    if value in registry:
        return registry[value]
    if value in registry.values():
        return value
    for key, mapped in registry.items():
        if key.lower() == value.lower():
            return mapped
        if mapped.lower() == value.lower():
            return mapped
    valid = ", ".join(registry.keys())
    raise ValueError(f"Invalid {field_name}: {value}, must be one of {valid}")
