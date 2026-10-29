"""GraphWeave Conservative Entity Resolution Service.

Performs mention normalization, alias tracking, type-constrained resolution,
and queues ambiguous matches for human review rather than forcing unsafe merges.
"""
import re
import uuid
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime, timezone

from app.core.config import settings
from app.core.logging import logger
from app.domain.ontology import EntityType
from app.domain.models import Entity
from app.domain.provenance import compute_canonical_entity_id, slugify_entity
from app.schemas.resolution_schemas import AmbiguousMatch
from app.repositories.postgres_repository import postgres_repo, PostgresRepository
from app.repositories.neo4j_repository import neo4j_repo, Neo4jRepository


# Common legal and honorific suffixes/prefixes to strip during normalization
ORG_SUFFIXES = re.compile(
    r"\b(inc|incorporated|llc|corp|corporation|ltd|limited|co|company|holdings|group|systems|laboratories|labs)\b\.?",
    re.IGNORECASE,
)
PERSON_PREFIXES = re.compile(
    r"\b(dr|doctor|prof|professor|mr|ms|mrs)\b\.?",
    re.IGNORECASE,
)


def calculate_string_similarity(s1: str, s2: str) -> float:
    """Calculates character bigram Dice coefficient similarity in [0.0, 1.0]."""
    a = s1.lower().strip()
    b = s2.lower().strip()
    if a == b:
        return 1.0
    if len(a) < 2 or len(b) < 2:
        return 1.0 if a == b else 0.0

    pairs_a = set(a[i : i + 2] for i in range(len(a) - 1))
    pairs_b = set(b[i : i + 2] for i in range(len(b) - 1))

    intersection = len(pairs_a.intersection(pairs_b))
    total = len(pairs_a) + len(pairs_b)
    if total == 0:
        return 0.0
    return (2.0 * intersection) / total


class EntityResolutionService:
    def __init__(
        self,
        pg_repo: Optional[PostgresRepository] = None,
        graph_repo: Optional[Neo4jRepository] = None,
        auto_merge_threshold: float = 0.93,
        ambiguity_threshold: float = 0.72,
    ):
        self.pg_repo = pg_repo or postgres_repo
        self.graph_repo = graph_repo or neo4j_repo
        self.auto_merge_threshold = auto_merge_threshold
        self.ambiguity_threshold = ambiguity_threshold

        # In-memory registry of canonical entities: key = (tenant_id, corpus_id, canonical_id)
        self._entities: Dict[Tuple[str, str, str], Entity] = {}
        # Alias lookup index: key = (tenant_id, corpus_id, normalized_alias) -> canonical_id
        self._alias_index: Dict[Tuple[str, str, str], str] = {}
        # Mention counters: key = (tenant_id, corpus_id, canonical_id) -> count
        self._mention_counts: Dict[Tuple[str, str, str], int] = {}
        # Ambiguity review queue
        self._ambiguities: Dict[str, AmbiguousMatch] = {}

    def normalize_name(self, name: str, entity_type: EntityType) -> str:
        """Strips noise, punctuation, and legal suffixes based on entity type."""
        clean = name.strip()
        if entity_type == EntityType.ORGANIZATION:
            clean = ORG_SUFFIXES.sub("", clean)
        elif entity_type == EntityType.PERSON:
            clean = PERSON_PREFIXES.sub("", clean)

        clean = re.sub(r"[^\w\s]", " ", clean)
        clean = re.sub(r"\s+", " ", clean).strip().lower()
        return clean or name.strip().lower()

    async def resolve_entity(
        self,
        mention: str,
        entity_type: EntityType,
        tenant_id: str = settings.DEFAULT_TENANT_ID,
        corpus_id: str = settings.DEFAULT_CORPUS_ID,
        confidence: float = 1.0,
    ) -> Entity:
        """Resolves an entity mention to an existing canonical entity or registers a new one conservatively."""
        clean_mention = mention.strip()
        norm_name = self.normalize_name(clean_mention, entity_type)
        alias_key = (tenant_id, corpus_id, norm_name)

        # 1. Check if normalized mention is already an alias for a canonical entity
        if alias_key in self._alias_index:
            existing_cid = self._alias_index[alias_key]
            canonical = self._entities[(tenant_id, corpus_id, existing_cid)]
            # Verify type matches (Strict type isolation)
            if canonical.entity_type == entity_type:
                self._mention_counts[(tenant_id, corpus_id, existing_cid)] += 1
                if clean_mention not in canonical.aliases:
                    canonical.aliases.append(clean_mention)
                return canonical

        # 2. Check existing entities of the SAME type for similarity
        best_match: Optional[Entity] = None
        best_score = 0.0

        for (t_id, c_id, cid), existing in self._entities.items():
            if t_id == tenant_id and c_id == corpus_id and existing.entity_type == entity_type:
                existing_norm = self.normalize_name(existing.name, existing.entity_type)
                # Exact normalized match
                if norm_name == existing_norm:
                    best_match = existing
                    best_score = 1.0
                    break

                score = calculate_string_similarity(norm_name, existing_norm)
                if score > best_score:
                    best_score = score
                    best_match = existing

        # Rule A: High confidence merge
        if best_match and best_score >= self.auto_merge_threshold:
            if clean_mention not in best_match.aliases:
                best_match.aliases.append(clean_mention)
            self._alias_index[alias_key] = best_match.canonical_id
            self._mention_counts[(tenant_id, corpus_id, best_match.canonical_id)] += 1
            logger.info(
                f"Resolved '{clean_mention}' -> Canonical '{best_match.name}' (score={best_score:.2f})"
            )
            return best_match

        # Rule B: Ambiguous match - Queue for review, DO NOT merge!
        new_cid = compute_canonical_entity_id(entity_type.value, clean_mention)

        if best_match and self.ambiguity_threshold <= best_score < self.auto_merge_threshold:
            amb_id = f"amb_{uuid.uuid4().hex[:10]}"
            match = AmbiguousMatch(
                id=amb_id,
                mention_a=clean_mention,
                type_a=entity_type,
                canonical_id_a=new_cid,
                mention_b=best_match.name,
                type_b=best_match.entity_type,
                canonical_id_b=best_match.canonical_id,
                similarity_score=round(best_score, 3),
                status="PENDING_REVIEW",
                reason=(
                    f"Ambiguous similarity score {best_score:.2f} between '{clean_mention}' and "
                    f"'{best_match.name}'. Distinct canonical entities preserved pending review."
                ),
                created_at=datetime.now(timezone.utc),
            )
            self._ambiguities[amb_id] = match
            logger.warning(
                f"Ambiguity detected between '{clean_mention}' and '{best_match.name}' (score={best_score:.2f}). Queued as {amb_id}."
            )

        # Rule C: Create distinct canonical entity
        canonical_entity = Entity(
            canonical_id=new_cid,
            name=clean_mention,
            entity_type=entity_type,
            tenant_id=tenant_id,
            corpus_id=corpus_id,
            aliases=[clean_mention],
            confidence=confidence,
        )

        entity_key = (tenant_id, corpus_id, new_cid)
        self._entities[entity_key] = canonical_entity
        self._alias_index[alias_key] = new_cid
        self._mention_counts[entity_key] = 1

        # Idempotently write entity node to Neo4j
        await self.graph_repo.merge_entity_node(canonical_entity)

        return canonical_entity

    def list_canonical_entities(self, tenant_id: str, corpus_id: str) -> List[Tuple[Entity, int]]:
        results = []
        for (t_id, c_id, cid), entity in self._entities.items():
            if t_id == tenant_id and c_id == corpus_id:
                count = self._mention_counts.get((t_id, c_id, cid), 1)
                results.append((entity, count))
        return results

    def list_ambiguities(self, status: Optional[str] = "PENDING_REVIEW") -> List[AmbiguousMatch]:
        if status:
            return [a for a in self._ambiguities.values() if a.status == status]
        return list(self._ambiguities.values())

    async def resolve_ambiguity(self, match_id: str, action: str) -> Optional[AmbiguousMatch]:
        match = self._ambiguities.get(match_id)
        if not match:
            return None

        if action == "APPROVE_MERGE":
            match.status = "APPROVED"
            # Alias entity A into canonical entity B
            alias_key = (settings.DEFAULT_TENANT_ID, settings.DEFAULT_CORPUS_ID, self.normalize_name(match.mention_a, match.type_a))
            self._alias_index[alias_key] = match.canonical_id_b
            if (settings.DEFAULT_TENANT_ID, settings.DEFAULT_CORPUS_ID, match.canonical_id_b) in self._entities:
                target = self._entities[(settings.DEFAULT_TENANT_ID, settings.DEFAULT_CORPUS_ID, match.canonical_id_b)]
                if match.mention_a not in target.aliases:
                    target.aliases.append(match.mention_a)
                # Write ALIAS_OF edge in Neo4j
                await self.graph_repo.merge_alias_edge(match.canonical_id_a, match.canonical_id_b)
        elif action == "REJECT_MERGE":
            match.status = "REJECTED"

        return match


entity_resolution_service = EntityResolutionService()
