# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Column resource classes for Featureform.

This module contains classes for feature, label, and embedding column resources.
"""

from abc import ABC
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, Union

from ..config.offline_stores import ResourceSnowflakeConfig
from ..enums import ResourceType, ScalarType
from ..utils.helpers import set_tags_properties

if TYPE_CHECKING:
    from ..resources import Entity, NameVariant
    from . import UserRegistrar
    from .column_mapping import ColumnMapping


__all__ = [
    "ColumnResource",
    "FeatureColumnResource",
    "LabelColumnResource",
    "EmbeddingColumnResource",
]


class ColumnResource(ABC):
    """
    Base class for all column resources. This class is not meant to be instantiated directly.
    In the original syntax, features and labels were registered using the `register_resources`
    method on the sources (e.g. SQL/DF transformation or tables sources); however, in the new
    Class API syntax, features and labels can now be declared as class attributes on an entity
    class. This means that all possible params for either resource must be passed into this base
    class prior to calling `register_column_resources` on the registrar.
    """

    def __init__(
        self,
        transformation_args: tuple,
        type: Union[ScalarType, str],
        resource_type: ResourceType,
        entity: Union["Entity", str],
        owner: Union[str, "UserRegistrar"],
        timestamp_column: str,
        description: str,
        schedule: str,
        tags: List[str],
        properties: Dict[str, str],
        inference_store: Union[str, "OnlineProvider", "FileStoreProvider"] = "",
        name: str = "",
        variant: str = "",
        resource_snowflake_config: Optional[ResourceSnowflakeConfig] = None,
    ):
        registrar, source_name_variant, columns = transformation_args
        self.type = type if isinstance(type, str) else type.value
        self.registrar = registrar
        self.source = source_name_variant
        self.entity_column = columns[0]
        self.source_column = columns[1]
        self.resource_type = resource_type
        self.entity = entity
        self.name = name
        self.owner = owner
        self.inference_store = inference_store
        if not timestamp_column and len(columns) == 3:
            self.timestamp_column = columns[2]
        elif timestamp_column and len(columns) == 3:
            raise Exception("Timestamp column specified twice.")
        else:
            self.timestamp_column = timestamp_column
        self.description = description
        self.schedule = schedule
        tags, properties = set_tags_properties(tags, properties)
        self.tags = tags
        self.properties = properties
        self.variant = variant
        self.resource_snowflake_config = resource_snowflake_config

    def register(self):
        features, labels = self.get_resources_by_type(self.resource_type)

        self.registrar.register_column_resources(
            source=self.source,
            entity=self.entity,
            entity_column=self.entity_column,
            owner=self.owner,
            inference_store=self.inference_store,
            features=features,
            labels=labels,
            timestamp_column=self.timestamp_column,
            schedule=self.schedule,
            client_object=self,
        )

    def get_resources_by_type(
        self, resource_type: ResourceType
    ) -> Tuple[List["ColumnMapping"], List["ColumnMapping"]]:
        resources = [
            {
                "name": self.name,
                "variant": self.variant,
                "column": self.source_column,
                "type": self.type,
                "description": self.description,
                "tags": self.tags,
                "properties": self.properties,
                "resource_snowflake_config": self.resource_snowflake_config,
            }
        ]

        if resource_type == ResourceType.FEATURE_VARIANT:
            features = resources
            labels = []
        elif resource_type == ResourceType.LABEL_VARIANT:
            features = []
            labels = resources
        else:
            raise ValueError(
                f"Resource type {self.resource_type.to_string()} not supported"
            )
        return (features, labels)

    def name_variant(self) -> "NameVariant":
        if self.name is None:
            raise ValueError("Resource name not set")
        if self.variant is None:
            raise ValueError("Resource variant not set")
        return (self.name, self.variant)

    def get_resource_type(self) -> ResourceType:
        return self.resource_type

    def to_key(self) -> tuple[ResourceType, str, str]:
        return self.resource_type, self.name, self.variant


# Variants class moved to registrar/variants.py


class FeatureColumnResource(ColumnResource):
    def __init__(
        self,
        transformation_args: tuple,
        type: Union[ScalarType, str],
        entity: Union["Entity", str] = "",
        name: str = "",
        variant: str = "",
        owner: str = "",
        inference_store: Union[str, "OnlineProvider", "FileStoreProvider"] = "",
        timestamp_column: str = "",
        description: str = "",
        schedule: str = "",
        tags: Optional[List[str]] = None,
        properties: Optional[Dict[str, str]] = None,
        resource_snowflake_config: Optional[ResourceSnowflakeConfig] = None,
    ):
        """
        Feature registration object.

        **Example**
        ```
        @ff.entity
        class Customer:
        # Register a column from a transformation as a feature
            transaction_amount = ff.Feature(
                fare_per_family_member[["CustomerID", "Amount", "Transaction Time"]],
                variant="quickstart",
                type=ff.Float64,
                inference_store=redis,
            )
        ```

        Args:
            transformation_args (tuple): A transformation or source function and the columns name in the format: <transformation_function>[[<entity_column>, <value_column>, <timestamp_column (optional)>]].
            variant (str): An optional variant name for the feature.
            type (Union[ScalarType, str]): The type of the value in for the feature.
            inference_store (Union[str, "OnlineProvider", "FileStoreProvider"]): Where to store for online serving.
        """
        super().__init__(
            transformation_args=transformation_args,
            type=type,
            resource_type=ResourceType.FEATURE_VARIANT,
            entity=entity,
            name=name,
            variant=variant,
            owner=owner,
            inference_store=inference_store,
            timestamp_column=timestamp_column,
            description=description,
            schedule=schedule,
            tags=tags,
            properties=properties,
            resource_snowflake_config=resource_snowflake_config,
        )


class LabelColumnResource(ColumnResource):
    def __init__(
        self,
        transformation_args: tuple,
        type: Union[ScalarType, str],
        entity: Union["Entity", str] = "",
        name: str = "",
        variant: str = "",
        owner: str = "",
        timestamp_column: str = "",
        description: str = "",
        schedule: str = "",
        tags: List[str] = [],
        properties: Dict[str, str] = {},
    ):
        """
        Label registration object.

        **Example**
        ```
        @ff.entity
        class Customer:
        # Register a column from a transformation as a label
            transaction_amount = ff.Label(
                fare_per_family_member[["CustomerID", "Amount", "Transaction Time"]],
                variant="quickstart",
                type=ff.Float64
            )
        ```

        Args:
            transformation_args (tuple): A transformation or source function and the columns name in the format: <transformation_function>[[<entity_column>, <value_column>, <timestamp_column (optional)>]]
            variant (str): An optional variant name for the label.
            type (Union[ScalarType, str]): The type of the value in for the label.
        """
        super().__init__(
            transformation_args=transformation_args,
            type=type,
            resource_type=ResourceType.LABEL_VARIANT,
            entity=entity,
            name=name,
            variant=variant,
            owner=owner,
            timestamp_column=timestamp_column,
            description=description,
            schedule=schedule,
            tags=tags,
            properties=properties,
        )


class EmbeddingColumnResource(ColumnResource):
    def __init__(
        self,
        transformation_args: tuple,
        dims: int,
        vector_db: Union[str, "OnlineProvider", "FileStoreProvider"],
        entity: Union["Entity", str] = "",
        name="",
        variant="",
        owner: str = "",
        timestamp_column: str = "",
        description: str = "",
        schedule: str = "",
        tags: List[str] = [],
        properties: Dict[str, str] = {},
    ):
        """
        Embedding Feature registration object.

        **Example**
        ```
        @ff.entity
        class Speaker:
        # Register a column from a transformation as a label
            transaction_amount = ff.Embedding(
                vectorize_comments[["PK", "Vector"]],
                dims=384,
                vector_db=pinecone,
                description="Embeddings created from speakers' comments in episodes",
                variant="v1"
            )
        ```

        Args:
            transformation_args (tuple): A transformation or source function and the columns name in the format: <transformation_function>[[<entity_column>, <value_column>]]
            dims (int): Dimensionality of the embedding.
            vector_db (Union[str, OnlineProvider]): The name of the vector database to store the embeddings in.
            variant (str): An optional variant name for the feature.
            description (str): An optional description for the feature.
        """
        super().__init__(
            transformation_args=transformation_args,
            type=ScalarType.FLOAT32,
            resource_type=ResourceType.FEATURE_VARIANT,
            entity=entity,
            name=name,
            variant=variant,
            owner=owner,
            inference_store=vector_db,
            timestamp_column=timestamp_column,
            description=description,
            schedule=schedule,
            tags=tags,
            properties=properties,
        )
        if dims < 1:
            raise ValueError("Vector dimensions must be a positive integer")
        self.dims = dims

    def get_resources_by_type(
        self, resource_type: ResourceType
    ) -> Tuple[List["ColumnMapping"], List["ColumnMapping"]]:
        features, labels = super().get_resources_by_type(resource_type)
        features[0]["dims"] = self.dims
        features[0]["is_embedding"] = True
        return (features, labels)
