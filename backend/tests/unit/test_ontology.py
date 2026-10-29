"""Unit tests for GraphWeave Knowledge Graph Ontology and Schema Constraints."""
import pytest
from app.domain.ontology import (
    EntityType,
    RelationType,
    validate_relation,
    RELATION_CONSTRAINTS,
)


def test_valid_relation_constraints():
    # ACQUIRED between two ORGANIZATIONS is valid
    res = validate_relation(
        EntityType.ORGANIZATION,
        RelationType.ACQUIRED,
        EntityType.ORGANIZATION,
    )
    assert res.is_valid is True
    assert res.reason is None

    # DEVELOPS: ORGANIZATION -> PRODUCT is valid
    res2 = validate_relation(
        EntityType.ORGANIZATION,
        RelationType.DEVELOPS,
        EntityType.PRODUCT,
    )
    assert res2.is_valid is True

    # COMPLIES_WITH: TECHNOLOGY -> STANDARD is valid
    res3 = validate_relation(
        EntityType.TECHNOLOGY,
        RelationType.COMPLIES_WITH,
        EntityType.STANDARD,
    )
    assert res3.is_valid is True


def test_invalid_relation_subject():
    # A PERSON cannot ACQUIRE an ORGANIZATION in our schema
    res = validate_relation(
        EntityType.PERSON,
        RelationType.ACQUIRED,
        EntityType.ORGANIZATION,
    )
    assert res.is_valid is False
    assert "Subject type 'PERSON' not permitted" in res.reason


def test_invalid_relation_object():
    # An ORGANIZATION cannot DEVELOP a LOCATION
    res = validate_relation(
        EntityType.ORGANIZATION,
        RelationType.DEVELOPS,
        EntityType.LOCATION,
    )
    assert res.is_valid is False
    assert "Object type 'LOCATION' not permitted" in res.reason
