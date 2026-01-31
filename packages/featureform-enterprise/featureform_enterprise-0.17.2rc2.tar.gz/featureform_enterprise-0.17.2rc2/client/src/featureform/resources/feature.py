# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Feature resource classes for Featureform.

This module contains classes for defining and managing features.
"""

from dataclasses import dataclass, field
from datetime import timedelta
from typing import TYPE_CHECKING, Any, List, Optional, Tuple, Union

import dill

if TYPE_CHECKING:
    from ..registrar.realtime_feature import FeatureInput, RealtimeInput

from typeguard import typechecked

# Type alias for realtime feature inputs
RealtimeFeatureInput = Union["FeatureInput", "RealtimeInput"]

from ..config import ResourceSnowflakeConfig
from ..core import ResourceVariant
from ..enums import (
    AggregateFunction,
    ComputationMode,
    OperationType,
    ResourceStatus,
    ResourceType,
    ScalarType,
)
from ..operations.equivalence import _get_and_set_equivalent_variant
from ..proto import metadata_pb2 as pb
from ..types import VectorType, type_from_proto
from .base import NameVariant
from .mappings import ColumnSchema, ResourceColumnMapping
from .provider import Properties, ServerStatus
from .schedule import Schedule

# Type alias for resource location
ResourceLocation = ResourceColumnMapping


def _duration_to_timedelta(duration_proto: Optional["Duration"]) -> timedelta:
    """Convert protobuf Duration to Python timedelta."""
    from google.protobuf.duration_pb2 import Duration

    if duration_proto is None:
        return timedelta(0)

    duration = Duration()
    duration.CopyFrom(duration_proto)
    return duration.ToTimedelta()


@dataclass(frozen=True)
class AttributeFeature:
    """Represents a simple attribute feature.

    Attributes:
        name: Name assigned to the feature.
        input_column: Column used for the value of the feature.
        input_type: Type of the feature.
    """

    name: str
    input_column: str
    input_type: ScalarType

    def to_proto(self):
        return pb.AttributeFeatureDefinition(
            name=self.name,
            input_column=ColumnSchema(
                name=self.input_column,
                value_type=self.input_type,
            ).to_proto(),
        )

    @staticmethod
    def from_proto(attribute: pb.AttributeFeatureDefinition) -> "AttributeFeature":
        column = ColumnSchema.from_proto(attribute.input_column)

        return AttributeFeature(
            name=attribute.name,
            input_column=column.name,
            input_type=column.value_type,
        )


@dataclass(frozen=True)
class AggregateFeature:
    """Represents a time windowed aggregate feature."""

    name: str
    input_column: str
    input_type: ScalarType
    function: Union[AggregateFunction, str]
    time_window: timedelta

    def __post_init__(self) -> None:
        try:
            aggregate_function = AggregateFunction(self.function)
        except ValueError as error:
            allowed = ", ".join(AggregateFunction._valid_functions())
            raise ValueError(
                f"Unsupported aggregate function: {self.function}. Allowed values are: {allowed}"
            ) from error
        object.__setattr__(self, "function", aggregate_function)

    def to_proto(self):
        return pb.AggregateFeatureDefinition(
            name=self.name,
            input_column=ColumnSchema(
                name=self.input_column,
                value_type=self.input_type,
            ).to_proto(),
            function=AggregateFunction._aggregate_function_to_proto(
                self.function,
            ),
            time_window=self.time_window,
        )

    @staticmethod
    def from_proto(aggregate: pb.AggregateFeatureDefinition) -> "AggregateFeature":
        column = ColumnSchema.from_proto(aggregate.input_column)

        return AggregateFeature(
            name=aggregate.name,
            input_column=column.name,
            input_type=column.value_type,
            function=AggregateFunction._aggregate_function_from_proto(
                aggregate.function
            ),
            time_window=_duration_to_timedelta(aggregate.time_window),
        )


@dataclass
class RealtimeFeatureDefinition:
    """
    Definition for a realtime feature that executes a Python function at serving time.

    Realtime features combine real-time request data with pre-computed feature values
    to compute feature values on-the-fly during inference.
    """

    serialized_function: bytes
    function_source: str
    inputs: List[RealtimeFeatureInput]
    return_type: str
    requirements: List[str] = field(default_factory=list)

    def to_proto(self) -> pb.RealtimeFeatureDefinition:
        """Convert to protobuf message."""
        # Import here to avoid circular imports
        from ..registrar.realtime_feature import FeatureInput, RealtimeInput

        inputs_proto = []
        for inp in self.inputs:
            if isinstance(inp, FeatureInput):
                feature_input_proto = pb.FeatureInput(
                    feature=pb.NameVariant(
                        name=inp.feature_name,
                        variant=inp.feature_variant,
                    ),
                )
                inputs_proto.append(
                    pb.RealtimeFeatureInput(feature_input=feature_input_proto)
                )
            elif isinstance(inp, RealtimeInput):
                realtime_input_proto = pb.RealtimeInput(
                    parameter_name=inp.parameter_name,
                )
                # Add training feature if specified
                if inp.training_feature is not None:
                    realtime_input_proto.training_feature.CopyFrom(
                        pb.NameVariant(
                            name=inp.training_feature_name,
                            variant=inp.training_feature_variant,
                        )
                    )
                inputs_proto.append(
                    pb.RealtimeFeatureInput(realtime_input=realtime_input_proto)
                )

        return pb.RealtimeFeatureDefinition(
            serialized_function=self.serialized_function,
            function_source=self.function_source,
            inputs=inputs_proto,
            requirements=self.requirements,
            return_type=self.return_type,
        )

    @staticmethod
    def from_proto(
        proto: pb.RealtimeFeatureDefinition,
    ) -> "RealtimeFeatureDefinition":
        """Create from protobuf message."""
        from ..registrar.realtime_feature import FeatureInput, RealtimeInput

        inputs = []
        for inp in proto.inputs:
            if inp.HasField("feature_input"):
                fi = inp.feature_input
                inputs.append(
                    FeatureInput(
                        feature=fi.feature.name,
                        variant=fi.feature.variant,
                    )
                )
            elif inp.HasField("realtime_input"):
                ri = inp.realtime_input
                training_feature = None
                if ri.HasField("training_feature"):
                    training_feature = (
                        ri.training_feature.name,
                        ri.training_feature.variant,
                    )
                inputs.append(
                    RealtimeInput(
                        name=ri.parameter_name,
                        training_feature=training_feature,
                    )
                )

        return RealtimeFeatureDefinition(
            serialized_function=proto.serialized_function,
            function_source=proto.function_source,
            inputs=inputs,
            return_type=proto.return_type,
            requirements=list(proto.requirements),
        )


# Type alias for feature definition payloads
FeatureDefinitionPayload = Union[
    AttributeFeature, AggregateFeature, RealtimeFeatureDefinition
]


class FeatureDefinition:
    """Helper class for converting feature definitions to/from protobuf."""

    @staticmethod
    def to_proto(
        definition: Optional[FeatureDefinitionPayload],
    ) -> Optional[pb.FeatureDefinition]:
        if definition is None:
            return None

        if isinstance(definition, AttributeFeature):
            return pb.FeatureDefinition(
                attribute=definition.to_proto(),
            )

        if isinstance(definition, AggregateFeature):
            return pb.FeatureDefinition(
                aggregate=definition.to_proto(),
            )

        if isinstance(definition, RealtimeFeatureDefinition):
            return pb.FeatureDefinition(
                realtime=definition.to_proto(),
            )

        raise TypeError(f"Unsupported feature definition type: {type(definition)}")

    @staticmethod
    def from_proto(
        proto_definition: Optional[pb.FeatureDefinition],
    ) -> FeatureDefinitionPayload:
        if proto_definition is None:
            return None

        if proto_definition.HasField("attribute"):
            attribute = proto_definition.attribute
            return AttributeFeature.from_proto(attribute)

        if proto_definition.HasField("aggregate"):
            aggregate = proto_definition.aggregate
            return AggregateFeature.from_proto(aggregate)

        if proto_definition.HasField("realtime"):
            realtime = proto_definition.realtime
            return RealtimeFeatureDefinition.from_proto(realtime)

        return None


@typechecked
@dataclass
class Feature:
    """High-level feature resource containing multiple variants."""

    name: str
    default_variant: str
    variants: List[str]

    def to_dictionary(self):
        return {
            "name": self.name,
            "default_variant": self.default_variant,
            "variants": self.variants,
        }


class PrecomputedFeatureParameters:
    """Parameters for precomputed features."""

    pass


@typechecked
@dataclass
class OndemandFeatureParameters:
    """Parameters for on-demand features."""

    definition: str = ""

    def proto(self) -> pb.FeatureParameters:
        ondemand_feature_parameters = pb.OndemandFeatureParameters(
            definition=self.definition
        )
        feature_parameters = pb.FeatureParameters()
        feature_parameters.ondemand.CopyFrom(ondemand_feature_parameters)
        return feature_parameters


# Type alias for additional feature parameters
Additional_Parameters = Union[
    PrecomputedFeatureParameters, OndemandFeatureParameters, None
]


# FeatureVariant class
@typechecked
@dataclass
class FeatureVariant(ResourceVariant):
    name: str
    owner: str
    variant: str
    source: Optional[Any] = None
    value_type: Optional[Union[VectorType, ScalarType, str]] = None
    entity: str = ""
    location: Optional[ResourceLocation] = None
    description: str = ""
    provider: Optional[str] = None
    created: str = None
    tags: Optional[list] = None
    properties: Optional[dict] = None
    schedule: str = ""
    schedule_obj: Schedule = None
    status: str = "NO_STATUS"
    error: Optional[str] = None
    additional_parameters: Optional[Additional_Parameters] = None  # TODO Remove
    server_status: Optional[ServerStatus] = None
    resource_snowflake_config: Optional[ResourceSnowflakeConfig] = None
    feature_definition: Optional[FeatureDefinitionPayload] = None

    def __post_init__(self):
        if isinstance(self.value_type, str):
            self.value_type = ScalarType(self.value_type)

    @property
    def is_realtime(self) -> bool:
        """Check if this is a realtime feature."""
        return isinstance(self.feature_definition, RealtimeFeatureDefinition)

    def update_schedule(self, schedule) -> None:
        self.schedule_obj = Schedule(
            name=self.name,
            variant=self.variant,
            resource_type=4,
            schedule_string=schedule,
        )
        self.schedule = schedule

    @staticmethod
    def operation_type() -> OperationType:
        return OperationType.CREATE

    @staticmethod
    def get_resource_type() -> ResourceType:
        return ResourceType.FEATURE_VARIANT

    def name_variant(self) -> NameVariant:
        return (self.name, self.variant)

    def get(self, stub) -> "FeatureVariant":
        return FeatureVariant.get_by_name_variant(stub, self.name, self.variant)

    @staticmethod
    def get_by_name_variant(stub, name, variant):
        name_variant = pb.NameVariantRequest(
            name_variant=pb.NameVariant(name=name, variant=variant)
        )
        feature = next(stub.GetFeatureVariants(iter([name_variant])))

        return FeatureVariant(
            created=None,
            name=feature.name,
            variant=feature.variant,
            source=(feature.source.name, feature.source.variant),
            value_type=type_from_proto(feature.type),
            entity=feature.entity,
            owner=feature.owner,
            provider=feature.provider,
            location=ResourceColumnMapping("", "", ""),
            description=feature.description,
            tags=list(feature.tags.tag),
            properties=dict(feature.properties.property.items()),
            status=feature.status.Status._enum_type.values[feature.status.status].name,
            error=feature.status.error_message,
            server_status=ServerStatus.from_proto(feature.status),
            additional_parameters=None,
            feature_definition=FeatureDefinition.from_proto(feature.feature_definition),
        )

    def _get_and_set_equivalent_variant(self, req_id, stub):
        if hasattr(self.source, "name_variant"):
            self.source = self.source.name_variant()

        feature_definition_proto = FeatureDefinition.to_proto(self.feature_definition)

        # Determine mode and status based on feature type
        if self.is_realtime:
            mode = ComputationMode.CLIENT_COMPUTED.proto()
            status = pb.ResourceStatus(status=pb.ResourceStatus.READY)
        else:
            mode = ComputationMode.PRECOMPUTED.proto()
            status = pb.ResourceStatus(status=pb.ResourceStatus.NO_STATUS)

        feature_variant_message = pb.FeatureVariant(
            name=self.name,
            variant=self.variant,
            source=(
                pb.NameVariant(name=self.source[0], variant=self.source[1])
                if self.source
                else None
            ),
            type=self.value_type.to_proto() if self.value_type else None,
            entity=self.entity,
            owner=self.owner,
            description=self.description,
            schedule=self.schedule,
            provider=self.provider,
            offline_store_provider=self.provider or "",
            columns=self.location.proto() if self.location else None,
            mode=mode,
            tags=pb.Tags(tag=self.tags or []),
            properties=Properties(self.properties).serialized,
            status=status,
            additional_parameters=None,
            resource_snowflake_config=(
                self.resource_snowflake_config.to_proto()
                if self.resource_snowflake_config
                else None
            ),
            feature_definition=feature_definition_proto,
        )

        # Initialize the FeatureVariantRequest message with the FeatureVariant message
        serialized = pb.FeatureVariantRequest(
            feature_variant=feature_variant_message,
            request_id="",
        )

        return (
            serialized,
            _get_and_set_equivalent_variant(
                req_id, serialized, "feature_variant", stub
            ),
            "feature_variant",
        )

    def _create(self, req_id, stub) -> Tuple[Optional[str], Optional[str]]:
        serialized, existing_variant, _ = self._get_and_set_equivalent_variant(
            req_id, stub
        )
        if existing_variant is None:
            stub.CreateFeatureVariant(serialized)
        return serialized.feature_variant.variant, existing_variant

    def get_status(self):
        return ResourceStatus(self.status)

    def is_ready(self):
        return self.status == ResourceStatus.READY.value


# OnDemandFeatureVariant class
@typechecked
@dataclass
class OnDemandFeatureVariant(ResourceVariant):
    owner: str
    variant: str
    tags: List[str] = field(default_factory=list)
    properties: dict = field(default_factory=dict)
    name: str = ""
    description: str = ""
    status: str = "READY"
    error: Optional[str] = None
    additional_parameters: Optional[Additional_Parameters] = None
    server_status: Optional[ServerStatus] = None

    def __call__(self, fn):
        if self.description == "" and fn.__doc__ is not None:
            self.description = fn.__doc__
        if self.name == "":
            self.name = fn.__name__

        self.query = dill.dumps(fn.__code__)
        feature_text = dill.source.getsource(fn)
        self.additional_parameters = OndemandFeatureParameters(definition=feature_text)
        fn.name_variant = self.name_variant
        fn.query = self.query
        return fn

    def name_variant(self):
        return (self.name, self.variant)

    @staticmethod
    def operation_type() -> OperationType:
        return OperationType.CREATE

    @staticmethod
    def get_resource_type() -> ResourceType:
        return ResourceType.ONDEMAND_FEATURE

    def _get_and_set_equivalent_variant(self, req_id, stub):
        serialized = pb.FeatureVariantRequest(
            feature_variant=pb.FeatureVariant(
                name=self.name,
                variant=self.variant,
                owner=self.owner,
                description=self.description,
                function=pb.PythonFunction(query=self.query),
                mode=ComputationMode.CLIENT_COMPUTED.proto(),
                tags=pb.Tags(tag=self.tags),
                properties=Properties(self.properties).serialized,
                status=pb.ResourceStatus(status=pb.ResourceStatus.READY),
                additional_parameters=self.additional_parameters.proto(),
            ),
            request_id="",
        )

        return (
            serialized,
            _get_and_set_equivalent_variant(
                req_id, serialized, "feature_variant", stub
            ),
            "feature_variant",
        )

    def _create(self, req_id, stub) -> Tuple[Optional[str], Optional[str]]:
        serialized, existing_variant, _ = self._get_and_set_equivalent_variant(
            req_id, stub
        )
        if existing_variant is None:
            stub.CreateFeatureVariant(serialized)
        return serialized.feature_variant.variant, existing_variant

    def get(self, stub) -> "OnDemandFeatureVariant":
        name_variant = pb.NameVariantRequest(
            name_variant=pb.NameVariant(name=self.name, variant=self.variant)
        )
        ondemand_feature = next(stub.GetFeatureVariants(iter([name_variant])))
        additional_Parameters = self._get_additional_parameters(ondemand_feature)

        return OnDemandFeatureVariant(
            name=ondemand_feature.name,
            variant=ondemand_feature.variant,
            owner=ondemand_feature.owner,
            description=ondemand_feature.description,
            tags=list(ondemand_feature.tags.tag),
            properties=dict(ondemand_feature.properties.property.items()),
            status=ondemand_feature.status.Status._enum_type.values[
                ondemand_feature.status.status
            ].name,
            error=ondemand_feature.status.error_message,
            additional_parameters=additional_Parameters,
        )

    def _get_additional_parameters(self, feature):
        return OndemandFeatureParameters(definition="() => FUNCTION")

    def get_status(self):
        return ResourceStatus(self.status)

    def is_ready(self):
        return self.status == ResourceStatus.READY.value
