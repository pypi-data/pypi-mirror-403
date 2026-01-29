# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Realtime Feature API for Featureform.

This module provides Pydantic-based models and decorators for defining realtime features
that execute Python functions at serving time, combining real-time request data with
pre-computed feature values.

Note:
    Parameters that receive values from features (FeatureInput or RealtimeInput with
    training_feature) must have Optional types because feature values can be None.

Example Usage:
    ```python
    import featureform as ff
    from typing import Optional

    @spark.realtime_feature(
        inputs=[
            ff.RealtimeInput('transaction_amount', training_feature=('amount', 'v1')),
            ff.FeatureInput(feature='avg_txn_amt', variant='v1'),
        ]
    )
    def detect_fraud(transaction_amount: Optional[float], avg_txn_amt: Optional[float]) -> float:
        # Handle None values from features
        if transaction_amount is None or avg_txn_amt is None:
            return 0.5  # Default score when data is missing
        if transaction_amount > avg_txn_amt * 3:
            return 0.9
        return 0.1
    ```
"""

import inspect
import sys
from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    List,
    Optional,
    Tuple,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

from packaging.requirements import InvalidRequirement
from packaging.requirements import Requirement as PkgRequirement
from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from ..core import HasNameVariant
from .feature_api import BuiltFeatures, FeatureType
from .resource_variant_validators import (
    normalize_variant,
    validate_string_or_resource,
    validate_tuple_or_resource,
)


def _is_optional_type(type_hint: Any) -> bool:
    """
    Check if a type hint allows None values.

    Handles:
    - Optional[T] (which is Union[T, None])
    - Union[T, None, ...]
    - T | None (Python 3.10+ union syntax)

    Args:
        type_hint: A type annotation to check.

    Returns:
        True if the type allows None, False otherwise.
    """
    origin = get_origin(type_hint)

    # Handle Union types (including Optional which is Union[T, None])
    if origin is Union:
        return type(None) in get_args(type_hint)

    # Handle Python 3.10+ union syntax (T | None) which uses types.UnionType
    if sys.version_info >= (3, 10):
        import types

        if isinstance(type_hint, types.UnionType):
            return type(None) in get_args(type_hint)

    return False


class FeatureInput(BaseModel):
    """
    Specifies a pre-computed feature as input to a realtime feature function.

    FeatureInput references an existing feature that will be fetched from the
    feature store at serving time. The feature value is passed to the realtime
    function as the corresponding parameter.

    Attributes:
        feature: The feature to use. Can be:
            - A string feature name (requires variant to be specified)
            - An object implementing HasNameVariant (e.g., a Feature resource)
        variant: Optional variant override. Required when feature is a string.
            When feature is an object, this overrides the object's variant.

    Examples:
        Using a Feature resource object:
            >>> FeatureInput(feature=Customer.avg_txn_amt)

        Using a string feature name with variant:
            >>> FeatureInput(feature="avg_txn_amt", variant="v1")

        Overriding the variant of a Feature resource:
            >>> FeatureInput(feature=Customer.avg_txn_amt, variant="v2")
    """

    feature: Union[str, HasNameVariant]
    variant: Optional[str] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_validator("feature", mode="before")
    @classmethod
    def validate_feature(cls, v: Any):
        return validate_string_or_resource(v, field_name="feature")

    @field_validator("variant", mode="before")
    @classmethod
    def normalize_variant_field(cls, v: Any) -> Optional[str]:
        return normalize_variant(v, field_name="variant")

    @model_validator(mode="after")
    def validate_variant_rules(self):
        if isinstance(self.feature, str):
            if self.variant is None:
                raise ValueError(
                    "variant is required when feature is a string: "
                    "FeatureInput('featurename', 'variant')"
                )
            return self
        return self

    @property
    def parameter_name(self) -> str:
        """Get the function parameter name this input maps to.

        Returns the feature name, which is used to match against function parameters.
        """
        return self.feature_name

    @property
    def feature_name(self) -> str:
        """Get the name of the referenced feature."""
        if isinstance(self.feature, str):
            return self.feature
        name, _ = self.feature.name_variant()
        return name

    @property
    def feature_variant(self) -> str:
        """Get the variant of the referenced feature."""
        if self.variant is not None:
            return self.variant
        if isinstance(self.feature, str):
            return ""
        _, variant = self.feature.name_variant()
        return variant


class RealtimeInput(BaseModel):
    """
    Specifies a real-time value as input to a realtime feature function.

    RealtimeInput represents data that is provided at serving time (e.g., from
    an API request) rather than being fetched from the feature store. Optionally,
    a training_feature can be specified to enable training set generation.

    Attributes:
        name: The name of the input, which must match a function parameter name.
        training_feature: Optional feature to use during training. Can be:
            - A (name, variant) tuple
            - An object implementing HasNameVariant (e.g., a Feature resource)
            When specified, enables training set generation for this input.

    Examples:
        Basic realtime input (inference only):
            >>> RealtimeInput(name="transaction_amount")

        With training feature support using a Feature resource:
            >>> RealtimeInput(name="transaction_amount", training_feature=Transaction.amount)

        With training feature support using a tuple:
            >>> RealtimeInput(name="transaction_amount", training_feature=("amount", "v1"))
    """

    name: str
    # TODO: Backend should validate that training_feature's type is compatible
    # with the function parameter's expected type when training set support is added.
    training_feature: Optional[Union[Tuple[str, str], HasNameVariant]] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, v: Any) -> str:
        if v is None:
            raise ValueError("name cannot be None")
        v = str(v).strip()
        if not v:
            raise ValueError("name cannot be empty")
        return v

    @field_validator("training_feature", mode="before")
    @classmethod
    def validate_training_feature(cls, v: Any):
        return validate_tuple_or_resource(
            v, field_name="training_feature", allow_none=True
        )

    @property
    def parameter_name(self) -> str:
        """Get the function parameter name this input maps to.

        Returns the input name, which must match a function parameter.
        """
        return self.name

    @property
    def has_training_support(self) -> bool:
        """Check if this input can be used in training sets."""
        return self.training_feature is not None

    @property
    def training_feature_name(self) -> Optional[str]:
        """Get the name of the training feature, if specified."""
        if self.training_feature is None:
            return None
        if isinstance(self.training_feature, tuple):
            return self.training_feature[0]
        name, _ = self.training_feature.name_variant()
        return name

    @property
    def training_feature_variant(self) -> Optional[str]:
        """Get the variant of the training feature, if specified."""
        if self.training_feature is None:
            return None
        if isinstance(self.training_feature, tuple):
            return self.training_feature[1]
        _, variant = self.training_feature.name_variant()
        return variant


# Type alias for input specifications
RealtimeFeatureInput = Union[FeatureInput, RealtimeInput]


class RealtimeFeatureConfig(BaseModel):
    """
    Pydantic validation model for realtime feature configuration.

    This model is used during decoration to validate the function signature,
    type hints, and input specifications. After validation, its properties
    are used to construct RealtimeFeatureDefinition and FeatureVariant objects.
    The config itself is not stored - only the validated data is used.

    Attributes:
        fn: The Python function that computes the feature value.
        inputs: List of FeatureInput and RealtimeInput specifications.
        name: Optional feature name (defaults to function name).
        variant: Optional variant name.
        description: Optional description (defaults to function docstring).
        requirements: Optional list of pip requirements (e.g., ["numpy>=1.24.0"]).

    Example:
        ```python
        config = RealtimeFeatureConfig(
            fn=my_function,
            inputs=[
                FeatureInput(feature='avg_txn_amt'),
                RealtimeInput(name='transaction_amount'),
            ],
            requirements=["numpy>=1.24.0", "scikit-learn==1.2.0"],
        )
        ```
    """

    fn: Callable[..., Any]
    inputs: List[RealtimeFeatureInput]
    name: Optional[str] = None
    variant: Optional[str] = None
    description: Optional[str] = None
    requirements: List[str] = []

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_validator("requirements")
    @classmethod
    def validate_requirements(cls, requirements: List[str]) -> List[str]:
        """Validate that each requirement string matches PEP 508 format."""
        for req in requirements:
            try:
                PkgRequirement(req.strip())
            except InvalidRequirement as e:
                raise ValueError(
                    f"Invalid pip requirement: '{req}'. "
                    f"Requirements must follow PEP 508 format "
                    f"(e.g., 'numpy>=1.24.0', 'scikit-learn==1.2.0'). "
                    f"Error: {e}"
                ) from e
        return requirements

    @field_validator("fn")
    @classmethod
    def validate_function_has_type_hints(cls, fn: Callable) -> Callable:
        """Ensure function has type hints for all parameters and return type."""
        sig = inspect.signature(fn)

        try:
            type_hints = get_type_hints(fn)
        except Exception as e:
            raise ValueError(
                f"Failed to get type hints for function '{fn.__name__}': {e}. "
                f"Ensure all type hints are valid and importable."
            ) from e

        # Check all parameters have type hints
        for param_name, param in sig.parameters.items():
            if param_name not in type_hints:
                raise ValueError(
                    f"Function parameter '{param_name}' must have a type hint. "
                    f"Example: def {fn.__name__}({param_name}: float, ...) -> float:"
                )

        # Check return type hint exists
        if "return" not in type_hints:
            raise ValueError(
                f"Function '{fn.__name__}' must have a return type hint. "
                f"Example: def {fn.__name__}(...) -> float:"
            )

        return fn

    @model_validator(mode="after")
    def validate_inputs_match_function_signature(self) -> "RealtimeFeatureConfig":
        """Validate that inputs match function parameters in order."""
        sig = inspect.signature(self.fn)
        param_names_ordered = list(sig.parameters.keys())
        input_names_ordered = [inp.parameter_name for inp in self.inputs]

        # Check for missing inputs
        param_names_set = set(param_names_ordered)
        input_names_set = set(input_names_ordered)
        missing_inputs = param_names_set - input_names_set
        if missing_inputs:
            raise ValueError(
                f"Function parameters {missing_inputs} are not covered by inputs. "
                f"Add FeatureInput or RealtimeInput for each parameter."
            )

        # Check for extra inputs
        extra_inputs = input_names_set - param_names_set
        if extra_inputs:
            raise ValueError(
                f"Inputs {extra_inputs} do not match any function parameter. "
                f"Function parameters are: {param_names_set}"
            )

        # Check that inputs are in the same order as function parameters
        if input_names_ordered != param_names_ordered:
            raise ValueError(
                f"Inputs must be in the same order as function parameters. "
                f"Expected order: {param_names_ordered}, "
                f"got: {input_names_ordered}"
            )

        # Validate that parameters for feature-backed inputs have Optional types
        # Features can be None at runtime, so the function must handle this case
        try:
            type_hints = get_type_hints(self.fn)
        except Exception:
            # If we can't get type hints, skip Optional validation
            # The field_validator already verified type hints exist
            return self

        non_optional_feature_params = []

        for inp in self.inputs:
            param_name = inp.parameter_name
            param_type = type_hints.get(param_name)

            # Check if this input requires Optional type:
            # 1. FeatureInput - feature values can be None
            # 2. RealtimeInput with training_feature - training feature values can be None
            requires_optional = False
            if isinstance(inp, FeatureInput):
                requires_optional = True
            elif isinstance(inp, RealtimeInput) and inp.has_training_support:
                requires_optional = True

            if requires_optional and param_type is not None:
                if not _is_optional_type(param_type):
                    non_optional_feature_params.append(param_name)

        if non_optional_feature_params:
            raise ValueError(
                f"Parameters {non_optional_feature_params} must have Optional types "
                f"because they receive values from features which can be None. "
                f"Example: def {self.fn.__name__}({non_optional_feature_params[0]}: Optional[float], ...) -> ..."
            )

        return self

    @property
    def feature_name(self) -> str:
        """Get the feature name."""
        return self.name or self.fn.__name__

    @property
    def feature_description(self) -> str:
        """Get the feature description."""
        return self.description or self.fn.__doc__ or ""

    @property
    def supports_training(self) -> bool:
        """
        Determine if this realtime feature can be used in training sets.

        A realtime feature supports training only if all RealtimeInput
        specifications have a training_feature defined.
        """
        return all(
            isinstance(inp, FeatureInput) or inp.has_training_support
            for inp in self.inputs
        )


class RealtimeBuiltFeature(BuiltFeatures):
    """
    Built feature for a realtime feature.

    Contains a single FeatureVariant with a RealtimeFeatureDefinition payload.
    Provides callable behavior to invoke the underlying function.

    This class follows the same pattern as AttributeBuiltFeature and
    AggregateBuiltFeatures - it holds a reference to the FeatureVariant,
    so variant updates during equivalence resolution are automatically visible.

    Example:
        ```python
        @spark.realtime_feature(inputs=[ff.RealtimeInput('amount')])
        def my_feature(amount: float) -> float:
            return amount * 2

        # Access metadata
        print(my_feature.name)      # 'my_feature'
        print(my_feature.variant)   # variant string

        # Invoke the function directly
        result = my_feature(100.0)  # returns 200.0

        # Get the FeatureVariant for training sets
        my_feature.get_all_features()
        ```
    """

    def __init__(
        self,
        feature: "FeatureVariant",
        fn: Callable[..., Any],
        base_name: str,
        base_variant: str,
    ):
        super().__init__(base_name, base_variant)
        self._feature = feature
        self._fn = fn

    @property
    def feature_type(self) -> FeatureType:
        """Return the feature type."""
        return FeatureType.REALTIME

    @property
    def name(self) -> str:
        """Get the feature name."""
        return self._feature.name

    @property
    def variant(self) -> str:
        """Get the feature variant."""
        return self._feature.variant

    @property
    def description(self) -> str:
        """Get the feature description."""
        return self._feature.description

    @property
    def inputs(self) -> List[RealtimeFeatureInput]:
        """Get the input specifications."""
        return self._feature.feature_definition.inputs

    @property
    def supports_training(self) -> bool:
        """Check if this feature supports training."""
        return all(
            isinstance(inp, FeatureInput) or inp.has_training_support
            for inp in self.inputs
        )

    @property
    def requirements(self) -> List[str]:
        """Get the pip requirements for this feature."""
        return self._feature.feature_definition.requirements

    def __getitem__(self, window) -> "FeatureVariant":
        """Raises TypeError - realtime features cannot be indexed."""
        raise TypeError(
            f"'{self._base_name}' is a realtime feature and cannot be indexed. "
            f"Use name_variant() or get_all_features() instead."
        )

    def name_variant(self) -> Tuple[str, str]:
        """Return the (name, variant) tuple for this realtime feature."""
        return self._feature.name_variant()

    def get_all_features(self) -> List["FeatureVariant"]:
        """Return the single FeatureVariant as a list."""
        return [self._feature]

    def __call__(self, *args, **kwargs) -> Any:
        """Call the underlying function."""
        return self._fn(*args, **kwargs)

    def __repr__(self) -> str:
        return (
            f"RealtimeBuiltFeature({self._base_name!r}, variant={self.variant!r}, "
            f"supports_training={self.supports_training})"
        )


@dataclass
class RealtimeFeatureDecorator:
    """
    Decorator class for realtime features that registers the feature when applied.

    This class follows the same pattern as SQLTransformationDecorator - it holds
    the decorator parameters and registers the resource when __call__ is invoked.
    """

    registrar: Any  # Registrar, but avoiding circular import
    inputs: List[RealtimeFeatureInput]
    variant: str = ""
    owner: str = ""
    entity: str = ""
    offline_store_provider: str = ""
    description: str = ""
    requirements: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    properties: dict = field(default_factory=dict)

    def __call__(self, fn: Callable[..., Any]) -> RealtimeBuiltFeature:
        """Apply the decorator to a function, validate, and register."""
        import cloudpickle

        # Use docstring as description if not provided
        if self.description == "" and fn.__doc__ is not None:
            self.description = fn.__doc__

        # Create and validate the config (pydantic validation)
        config = RealtimeFeatureConfig(
            fn=fn,
            inputs=self.inputs,
            name=fn.__name__,
            variant=self.variant if self.variant else None,
            description=self.description if self.description else None,
            requirements=self.requirements,
        )

        # Resolve owner
        owner = self.owner
        if owner == "":
            owner = self.registrar.must_get_default_owner()

        # Resolve variant
        variant = self.variant
        if variant == "":
            variant = config.variant or self.registrar.get_run()

        # Get return type from function signature
        type_hints = inspect.signature(fn).return_annotation
        return_type = (
            type_hints.__name__ if hasattr(type_hints, "__name__") else str(type_hints)
        )

        # Serialize the function using cloudpickle
        serialized_function = cloudpickle.dumps(fn)

        # Get function source for display
        function_source = inspect.getsource(fn)

        # Import here to avoid circular dependency
        from ..resources import FeatureVariant, RealtimeFeatureDefinition

        # Create the FeatureVariant resource with RealtimeFeatureDefinition payload
        feature_variant = FeatureVariant(
            name=config.feature_name,
            variant=variant,
            owner=owner,
            description=config.feature_description,
            entity=self.entity,
            provider=self.offline_store_provider,
            tags=self.tags,
            properties=self.properties,
            feature_definition=RealtimeFeatureDefinition(
                serialized_function=serialized_function,
                function_source=function_source,
                inputs=list(config.inputs),
                return_type=return_type,
                requirements=list(config.requirements),
            ),
        )

        # Register the FeatureVariant resource
        self.registrar.add_resource(feature_variant)

        return RealtimeBuiltFeature(
            feature=feature_variant,
            fn=fn,
            base_name=config.feature_name,
            base_variant=variant,
        )
