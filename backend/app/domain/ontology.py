"""GraphWeave Knowledge Graph Ontology and Schema Constraints.

Defines the entity types, typed relations, directionality, and validation rules.
Extracted claims are treated as candidate claims that must pass schema validation.
"""
from enum import Enum
from typing import Dict, Set, Optional, Tuple
from pydantic import BaseModel, Field


class EntityType(str, Enum):
    ORGANIZATION = "ORGANIZATION"
    PERSON = "PERSON"
    PRODUCT = "PRODUCT"
    TECHNOLOGY = "TECHNOLOGY"
    LOCATION = "LOCATION"
    EVENT = "EVENT"
    STANDARD = "STANDARD"
    CONCEPT = "CONCEPT"


class RelationType(str, Enum):
    ACQUIRED = "ACQUIRED"
    SUBSIDIARY_OF = "SUBSIDIARY_OF"
    FOUNDED_BY = "FOUNDED_BY"
    DEVELOPS = "DEVELOPS"
    USES_TECHNOLOGY = "USES_TECHNOLOGY"
    COMPLIES_WITH = "COMPLIES_WITH"
    LOCATED_IN = "LOCATED_IN"
    PARTNERS_WITH = "PARTNERS_WITH"
    LEADS = "LEADS"
    PRODUCED_BY = "PRODUCED_BY"


# Permitted subject and object entity types for each relation type.
RELATION_CONSTRAINTS: Dict[RelationType, Tuple[Set[EntityType], Set[EntityType]]] = {
    RelationType.ACQUIRED: (
        {EntityType.ORGANIZATION},
        {EntityType.ORGANIZATION},
    ),
    RelationType.SUBSIDIARY_OF: (
        {EntityType.ORGANIZATION},
        {EntityType.ORGANIZATION},
    ),
    RelationType.FOUNDED_BY: (
        {EntityType.ORGANIZATION},
        {EntityType.PERSON},
    ),
    RelationType.DEVELOPS: (
        {EntityType.ORGANIZATION, EntityType.PERSON},
        {EntityType.PRODUCT, EntityType.TECHNOLOGY},
    ),
    RelationType.USES_TECHNOLOGY: (
        {EntityType.ORGANIZATION, EntityType.PRODUCT, EntityType.TECHNOLOGY},
        {EntityType.TECHNOLOGY, EntityType.PRODUCT},
    ),
    RelationType.COMPLIES_WITH: (
        {EntityType.ORGANIZATION, EntityType.PRODUCT, EntityType.TECHNOLOGY},
        {EntityType.STANDARD, EntityType.CONCEPT},
    ),
    RelationType.LOCATED_IN: (
        {EntityType.ORGANIZATION, EntityType.PERSON, EntityType.EVENT},
        {EntityType.LOCATION},
    ),
    RelationType.PARTNERS_WITH: (
        {EntityType.ORGANIZATION},
        {EntityType.ORGANIZATION},
    ),
    RelationType.LEADS: (
        {EntityType.PERSON},
        {EntityType.ORGANIZATION, EntityType.EVENT, EntityType.PROJECT if hasattr(EntityType, "PROJECT") else EntityType.ORGANIZATION, EntityType.CONCEPT},
    ),
    RelationType.PRODUCED_BY: (
        {EntityType.PRODUCT, EntityType.TECHNOLOGY, EntityType.CONCEPT},
        {EntityType.ORGANIZATION, EntityType.PERSON, EntityType.EVENT, EntityType.CONCEPT},
    ),
}


class ValidationResult(BaseModel):
    is_valid: bool
    reason: Optional[str] = None


def validate_relation(
    subject_type: EntityType,
    relation: RelationType,
    object_type: EntityType,
) -> ValidationResult:
    """Validates whether a candidate relation complies with the ontology schema."""
    if relation not in RELATION_CONSTRAINTS:
        return ValidationResult(is_valid=False, reason=f"Unknown relation type '{relation}'")

    allowed_subjects, allowed_objects = RELATION_CONSTRAINTS[relation]

    if subject_type not in allowed_subjects:
        subj_name = subject_type.value if hasattr(subject_type, "value") else str(subject_type)
        rel_name = relation.value if hasattr(relation, "value") else str(relation)
        return ValidationResult(
            is_valid=False,
            reason=f"Subject type '{subj_name}' not permitted for relation '{rel_name}'. Allowed: {[t.value for t in allowed_subjects]}",
        )

    if object_type not in allowed_objects:
        obj_name = object_type.value if hasattr(object_type, "value") else str(object_type)
        rel_name = relation.value if hasattr(relation, "value") else str(relation)
        return ValidationResult(
            is_valid=False,
            reason=f"Object type '{obj_name}' not permitted for relation '{rel_name}'. Allowed: {[t.value for t in allowed_objects]}",
        )

    return ValidationResult(is_valid=True)
