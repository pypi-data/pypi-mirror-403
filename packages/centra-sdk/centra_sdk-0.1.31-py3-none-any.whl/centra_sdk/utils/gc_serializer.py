from typing import Type, Callable, Any, Dict, Optional
from pydantic_core import InitErrorDetails, core_schema
from pydantic import model_serializer, model_validator, ValidationError

# Type aliases for better readability
ValidatorFunc = Callable[[Any, Callable, core_schema.ValidationInfo], Any]
SerializerFunc = Callable[[Dict[str, Any]], Dict[str, Any]]

# Public API
__all__ = ['GcSerializer', 'register_validator', 'register_serializer', 'ValidatorFunc', 'SerializerFunc']


def register_validator(_cls: Type['GcSerializer']):
    """Register a custom validator function for a model class.
    
    Args:
        _cls: The model class to register the validator for (must inherit from GcSerializer)
        
    Returns:
        Decorator function that expects a validator with signature:
        func(model: Any, handler: Callable, info: ValidationInfo) -> Any
        
    Raises:
        TypeError: If _cls is not a subclass of GcSerializer
        
    Example:
        @register_validator(MyModel)
        def validate_my_model(model, handler, info):
            # Custom validation logic
            if 'required_field' not in model:
                raise ValueError('Missing required field')
            return handler(model)
    """
    if not (isinstance(_cls, type) and hasattr(_cls, 'add_validator')):
        raise TypeError(f"Class {_cls} must inherit from GcSerializer and have add_validator method")
    
    def decorator(func: ValidatorFunc):
        _cls.add_validator(func)
        return func
    return decorator


def register_serializer(_cls: Type['GcSerializer']):
    """Register a custom serializer function for a model class.
    
    Args:
        _cls: The model class to register the serializer for (must inherit from GcSerializer)
        
    Returns:
        Decorator function that expects a serializer with signature:
        func(model_dict: Dict[str, Any]) -> Dict[str, Any]
        
    Raises:
        TypeError: If _cls is not a subclass of GcSerializer
    """
    if not (isinstance(_cls, type) and hasattr(_cls, 'add_serializer')):
        raise TypeError(f"Class {_cls} must inherit from GcSerializer and have add_serializer method")
    
    def decorator(func: SerializerFunc):
        _cls.add_serializer(func)
        return func
    return decorator


class GcSerializer:
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Each subclass gets its own serializer and validator
        cls._serializer: Optional[SerializerFunc] = None
        cls._validator: Optional[ValidatorFunc] = None

    @classmethod
    def add_serializer(cls, serializer_func: SerializerFunc) -> None:
        """Add a serializer function for this class."""
        cls._serializer = serializer_func

    @classmethod
    def add_validator(cls, validator_func: ValidatorFunc) -> None:
        """Add a validator function for this class."""
        cls._validator = validator_func

    @model_serializer(mode='wrap')
    def serialize_model(self, handler: Callable, **kwargs) -> Dict[str, Any]:
        """Serialize model using registered custom serializer if available."""
        model = handler(self)
        if self.__class__._serializer:
            return self.__class__._serializer(model)
        return model

    @model_validator(mode='wrap')
    @classmethod
    def validate_model(cls, model: Any, handler: Callable, info: core_schema.ValidationInfo) -> Any:
        """Validate model using registered custom validator if available."""
        if cls._validator:
            try:
                return cls._validator(model, handler, info)
            except ValidationError:
                # Re-raise ValidationError as-is
                raise
            except Exception as exc:
                # Convert other exceptions to ValidationError for consistency with Pydantic
                raise ValidationError.from_exception_data(
                    title=f"{cls.__name__} Custom Validation Error",
                    line_errors=[InitErrorDetails(
                        type="value_error",
                        input=model,
                        ctx={
                            'validator': cls._validator.__name__ if hasattr(cls._validator, '__name__') else str(cls._validator),
                            'error': str(exc),
                            'model_type': cls.__name__
                        }
                    )]
                )
        return handler(model)
