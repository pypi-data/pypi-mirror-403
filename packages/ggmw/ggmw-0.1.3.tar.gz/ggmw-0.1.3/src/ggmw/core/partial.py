from typing import (
    Any, TypeVar, Union,        # pyright: ignore[reportDeprecated] 
    get_origin, get_args, cast
)    
from collections.abc import Callable
import types
import operator
from functools import lru_cache, reduce, wraps
from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

ModelT = TypeVar("ModelT", bound=BaseModel)

def _make_recursive(annotation: Any) -> Any:
    """Helper to transform nested types."""
    
    if isinstance(annotation, type) and issubclass(annotation, BaseModel): 
        return partial_model(annotation)
    else:
        # Signal to the static checker to not narrow the type
        annotation = cast(Any, annotation)

    # 2. If it is a generic (List, Dict, Union, etc.), recurse into arguments
    origin = get_origin(annotation)
    args = get_args(annotation)

    if origin is not None and args:
        # Recursively transform each argument
        new_args = tuple(_make_recursive(arg) for arg in args)

        if new_args == args:
            return annotation

        # Handle A | B syntax (Python 3.10+)
        if hasattr(types, "UnionType") and origin is types.UnionType:
            return reduce(operator.or_, new_args)

        # Handle typing.Union
        if origin is Union:              # pyright: ignore[reportDeprecated]
            return Union[new_args]       # pyright: ignore[reportDeprecated]

        # Reconstruct standard generics (List[T], Dict[K,V])
        try:
            return origin[new_args]
        except TypeError:
            return annotation

    return annotation


"""
We introduce a helper decorator rather than applying lru_cache directly
because lru_cache obscures the partial_model function’s signature and docstring. 
This negatively impacts ergonomics on the front end when calling the function.
"""
def _cached_partial_model(
    partial_model: Callable[[type[ModelT]], type[ModelT]]
) -> Callable[[type[ModelT]], type[ModelT]]:
    cached_func = lru_cache(maxsize=None)(partial_model)
    return wraps(partial_model)(cached_func)
@_cached_partial_model
def partial_model(model: type[ModelT]) -> type[ModelT]:
    """
    Recursively transforms a Pydantic model into a new model where all fields are optional and validation constraints are relaxed.

    This is particularly useful for parsing streaming or incomplete JSON data where the full validation rules 
    (length, regex, ranges) might fail on partial chunks, but correct field mapping (aliases) is still required.

    Key Behaviors:
        - All fields `T` become `T | None`.
        - Nested Pydantic models are also transformed into their `Partial` counterparts.
        - Non-Pydantic types (e.g., `@dataclass`, `Enum`, standard classes) are treated as leaf nodes. The field becomes optional (`T | None`), but the class structure itself is not recursed or relaxed.
        - Constraints like `min_length`, `gt`, `pattern` are REMOVED to allow partial data.
        - Aliases (`Field(alias=...)`) are preserved so incoming JSON keys map correctly.
        - Fields with existing defaults keep them (e.g., `i: int = 0` remains `0`).
        - Required fields default to `None`.

    Args:
        model (`type[ModelT]`): The original Pydantic model class.

    Returns:
        `type[ModelT]`: A new Pydantic model class with the prefix `Partial`.
    
    Example:
        ```python 
        from dataclasses import dataclass

        @dataclass
        class Point:
            x: int
            y: int

        # Original model
        class Nested(BaseModel):
            val: str = Field(min_length=100) # Constraint

        class Model(BaseModel):
            x: int = Field(gt=0, alias="xAxis") # Constraint + Alias
            y: int                              # Required
            z: int = 10                         # Default
            child: Nested                       # Nested Pydantic Model
            pt: Point                           # Nested Dataclass

        # partial_model(Model) results in equivalent of:
        
        class PartialNested(BaseModel):
            # Type is optional, 'min_length' constraint is REMOVED
            val: str | None = None 

        class PartialModel(BaseModel):
            # 'gt' removed, but 'alias' PRESERVED
            x: int | None = Field(default=None, alias="xAxis") 
            
            # Required field becomes optional (default None)
            y: int | None = None
            
            # Existing default is PRESERVED
            z: int | None = 10
            
            # Nested Pydantic model IS recursively transformed
            child: PartialNested | None = None

            # Nested Dataclass is NOT transformed (Atomic)
            # You must provide a complete 'Point' or None.
            pt: Point | None = None
        ``` 
    """
    pydantic_fields: dict[str, tuple[Any, Any]] = {}

    for name, field in model.model_fields.items():
        # Transform the annotation
        annotation = _make_recursive(field.annotation)

        # Make the top-level field optional
        updated_annotation: Any
        if get_origin(annotation) is None:
            updated_annotation = annotation | None
        elif type(None) not in get_args(annotation):
            updated_annotation = annotation | None
        else:
            updated_annotation = annotation

        new_default = field.default
        new_default_factory = field.default_factory
        if new_default is PydanticUndefined and new_default_factory is None:
            new_default = None

        new_field_info = FieldInfo(
            annotation=updated_annotation,
            default=new_default,          # Use the calculated default
            default_factory=new_default_factory, # Keep the factory (e.g. list, dict)
            
            # KEEP Aliases
            alias=field.alias,
            alias_priority=field.alias_priority,
            validation_alias=field.validation_alias,
            serialization_alias=field.serialization_alias,
            
            # KEEP Metadata
            title=field.title,
            description=field.description,
            
            # DROP Constraints (validation)
            # We intentionally omit min_length, pattern, gt, etc.
        )
        pydantic_fields[name] = (updated_annotation, new_field_info)

    # Create the new class
    # We pass __base__=model so the new class inherits validators/configs of the original
    return create_model(
        f"Partial{model.__name__}",
        __base__=model, 
        **pydantic_fields,     # pyright: ignore 
    )


