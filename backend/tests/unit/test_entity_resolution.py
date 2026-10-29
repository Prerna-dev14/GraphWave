"""Unit tests for Conservative Entity Resolution Service."""
import pytest
from app.services.entity_resolution_service import EntityResolutionService, calculate_string_similarity
from app.domain.ontology import EntityType


def test_string_similarity_metric():
    assert calculate_string_similarity("Acme Cloud", "Acme Cloud") == 1.0
    assert calculate_string_similarity("Acme Cloud", "Different Name") < 0.3
    # Close variations have high similarity
    sim = calculate_string_similarity("DataWeaver", "DataWeaver Inc")
    assert sim > 0.80


def test_normalization():
    service = EntityResolutionService()
    # Strips corporate suffixes for organizations
    assert service.normalize_name("DataWeaver Inc.", EntityType.ORGANIZATION) == "dataweaver"
    assert service.normalize_name("Acme Cloud Corporation", EntityType.ORGANIZATION) == "acme cloud"
    # Strips honorifics for persons
    assert service.normalize_name("Dr. Elena Vance", EntityType.PERSON) == "elena vance"
    assert service.normalize_name("Professor Charles", EntityType.PERSON) == "charles"


@pytest.mark.asyncio
async def test_exact_alias_resolution():
    service = EntityResolutionService()

    # Mention 1: "DataWeaver Inc."
    e1 = await service.resolve_entity("DataWeaver Inc.", EntityType.ORGANIZATION)
    assert e1.name == "DataWeaver Inc."
    assert "DataWeaver Inc." in e1.aliases

    # Mention 2: "DataWeaver" (normalized form matches e1)
    e2 = await service.resolve_entity("DataWeaver", EntityType.ORGANIZATION)

    # Must resolve to the SAME canonical entity
    assert e1.canonical_id == e2.canonical_id
    assert "DataWeaver" in e2.aliases


@pytest.mark.asyncio
async def test_strict_type_isolation():
    service = EntityResolutionService()

    # Even with identical names, distinct entity types MUST NOT merge
    e_org = await service.resolve_entity("NovaGen", EntityType.ORGANIZATION)
    e_person = await service.resolve_entity("NovaGen", EntityType.PERSON)

    assert e_org.canonical_id != e_person.canonical_id
    assert e_org.entity_type == EntityType.ORGANIZATION
    assert e_person.entity_type == EntityType.PERSON


@pytest.mark.asyncio
async def test_conservative_ambiguity_queueing():
    service = EntityResolutionService(auto_merge_threshold=0.92, ambiguity_threshold=0.55)

    # Mention 1: "Acme Cloud Platform"
    e1 = await service.resolve_entity("Acme Cloud Platform", EntityType.ORGANIZATION)

    # Mention 2: "Acme Cloud Edge" (similar prefix, but distinct products/divisions)
    e2 = await service.resolve_entity("Acme Cloud Edge", EntityType.ORGANIZATION)

    # Conservative rule: must NOT auto-merge
    assert e1.canonical_id != e2.canonical_id

    # Must be queued for review in ambiguities
    ambiguities = service.list_ambiguities(status="PENDING_REVIEW")
    assert len(ambiguities) >= 1
    assert any("Acme Cloud Edge" in a.mention_a or "Acme Cloud Edge" in a.mention_b for a in ambiguities)


@pytest.mark.asyncio
async def test_manual_ambiguity_approval():
    service = EntityResolutionService(auto_merge_threshold=0.95, ambiguity_threshold=0.60)

    e1 = await service.resolve_entity("ShieldPay Gateway", EntityType.ORGANIZATION)
    e2 = await service.resolve_entity("ShieldPay Gateway System", EntityType.ORGANIZATION)

    ambiguities = service.list_ambiguities(status="PENDING_REVIEW")
    assert len(ambiguities) == 1
    amb_id = ambiguities[0].id

    # Manually approve merge
    resolved = await service.resolve_ambiguity(amb_id, action="APPROVE_MERGE")
    assert resolved.status == "APPROVED"
