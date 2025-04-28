import logging
from typing import Dict, Any, Optional
from django.db import transaction

from core.application.interfaces.repositories import CacheRepository
from core.infrastructure.models.sql_models import SchemaType
from core.domain.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class SQLCacheRepository(CacheRepository):
    def get_schema_by_type_id(self, type_id: str) -> Optional[SchemaType]:
        try:
            return SchemaType.objects.filter(type_id=type_id).first()
        except Exception as e:
            logger.error(f"Error retrieving schema for type {type_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve schema: {str(e)}")

    @transaction.atomic
    def save_schema(self, type_id: str, schema_data: Dict[str, Any]) -> SchemaType:
        try:
            properties = []
            for property in schema_data["Schema"]["Properties"]:
                properties.append(f"doi:{schema_data['Identifier']}#{property['Name']}")
            schema, created = SchemaType.objects.update_or_create(
                type_id=type_id,
                defaults={
                    "schema_data": schema_data,
                    "name": schema_data["name"].replace("_", " ").capitalize(),
                    "property": properties,
                    "description": schema_data["description"],
                },
            )

            if created:
                logger.info(f"Created new schema cache for type {type_id}")
            else:
                logger.info(f"Updated schema cache for type {type_id}")
            return schema

        except Exception as e:
            logger.error(f"Error saving schema for type {type_id}: {str(e)}")
            raise DatabaseError(f"Failed to save schema: {str(e)}")
