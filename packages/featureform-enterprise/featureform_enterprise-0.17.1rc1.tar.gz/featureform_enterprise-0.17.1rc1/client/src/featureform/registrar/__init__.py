# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Registrar module for Featureform.

This module contains registrar classes that wrap registered resources and
provide registration functionality.
"""

from .column_mapping import ColumnMapping
from .column_resources import (
    ColumnResource,
    EmbeddingColumnResource,
    FeatureColumnResource,
    LabelColumnResource,
)
from .entity_decorator import entity
from .feature_api import (
    AggregateBuiltFeatures,
    AggregateConfig,
    AttributeBuiltFeature,
    BackfillConfig,
    BuiltFeatures,
    Feature,
    FeatureBuilder,
    FeatureSourceType,
    FeatureType,
)
from .input_validators import (
    is_streaming_input,
    validate_batch_transformation_inputs,
    validate_streaming_transformation_inputs,
)
from .realtime_feature import (
    FeatureInput,
    RealtimeBuiltFeature,
    RealtimeFeatureConfig,
    RealtimeInput,
)
from .registrar import ONE_DAY_TARGET_LAG, Incremental, Registrar
from .registrars import (
    ColumnSourceRegistrar,
    EntityRegistrar,
    ModelRegistrar,
    ResourceRegistrar,
    SourceRegistrar,
    UserRegistrar,
)
from .transformation_decorators import (
    DFTransformationDecorator,
    SQLTransformationDecorator,
    SubscriptableTransformation,
)
from .variants import Variants

__all__ = [
    "Registrar",
    "Incremental",
    "ONE_DAY_TARGET_LAG",
    "EntityRegistrar",
    "UserRegistrar",
    "SourceRegistrar",
    "ColumnSourceRegistrar",
    "ResourceRegistrar",
    "ModelRegistrar",
    "ColumnMapping",
    "Variants",
    "SubscriptableTransformation",
    "SQLTransformationDecorator",
    "DFTransformationDecorator",
    "ColumnResource",
    "FeatureColumnResource",
    "LabelColumnResource",
    "EmbeddingColumnResource",
    "entity",
    # Feature API v2
    "Feature",
    "FeatureBuilder",
    "FeatureSourceType",
    "FeatureType",
    "AggregateConfig",
    "BackfillConfig",
    "BuiltFeatures",
    "AggregateBuiltFeatures",
    "AttributeBuiltFeature",
    # Input validators
    "is_streaming_input",
    "validate_streaming_transformation_inputs",
    "validate_batch_transformation_inputs",
    # Realtime Feature API
    "FeatureInput",
    "RealtimeInput",
    "RealtimeBuiltFeature",
    "RealtimeFeatureConfig",
]

# Create global registrar instance
global_registrar = Registrar()
