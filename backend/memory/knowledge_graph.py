"""Knowledge Graph — LLM entity extraction, storage, and recursive CTE traversal."""
import json
import logging
from uuid import UUID

from langchain_core.messages import BaseMessage
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import KnowledgeEntity, KnowledgeRelation
from db.session import async_session
from llm.gateway import get_llm
from llm.embeddings import embed_text

logger = logging.getLogger(__name__)

EXTRACT_PROMPT = """Trích xuất entities và relationships từ hội thoại.

Trả về JSON (KHÔNG markdown):
{{"entities": [{{"name": "...", "type": "person|place|project|concept|org", "description": "..."}}], "relations": [{{"source": "entity_name", "target": "entity_name", "type": "works_at|knows|interested_in|uses|part_of|located_in"}}]}}

Nếu không có gì: {{"entities": [], "relations": []}}

Hội thoại:
{conversation}"""


async def extract_and_store(messages: list[BaseMessage], user_id: str) -> dict:
    """Extract entities/relations from conversation and persist to DB."""
    if len(messages) < 2 or not user_id:
        return {}

    conversation = "\n".join(f"{m.type}: {m.content}" for m in messages[-6:])
    try:
        resp = await get_llm("gemini-2.0-flash").ainvoke(EXTRACT_PROMPT.format(conversation=conversation))
        data = json.loads(resp.content.strip().removeprefix("```json").removesuffix("```").strip())
    except Exception:
        logger.exception("KG extraction failed")
        return {}

    entities = data.get("entities", [])
    relations = data.get("relations", [])
    if not entities:
        return data

    uid = UUID(user_id)
    async with async_session() as db:
        name_to_id: dict[str, UUID] = {}

        for ent in entities:
            name = ent.get("name", "").strip()
            if not name:
                continue
            # Upsert: find existing or create
            row = (await db.execute(
                text("SELECT id FROM knowledge_entities WHERE user_id = :uid AND LOWER(name) = LOWER(:name) LIMIT 1"),
                {"uid": uid, "name": name},
            )).first()

            if row:
                name_to_id[name] = row[0]
            else:
                emb = await embed_text(name + ": " + ent.get("description", ""))
                entity = KnowledgeEntity(user_id=uid, name=name, entity_type=ent.get("type", "concept"), description=ent.get("description"), embedding=emb)
                db.add(entity)
                await db.flush()
                name_to_id[name] = entity.id

        for rel in relations:
            src, tgt = rel.get("source", ""), rel.get("target", "")
            if src in name_to_id and tgt in name_to_id:
                db.add(KnowledgeRelation(user_id=uid, source_id=name_to_id[src], target_id=name_to_id[tgt], relation_type=rel.get("type", "related_to")))

        await db.commit()

    return data


async def search_graph(user_id: str, query: str, db: AsyncSession, max_depth: int = 3, limit: int = 20) -> list[dict]:
    """Search knowledge graph via recursive CTE. Returns entities + relations."""
    query_emb = await embed_text(query)

    sql = text("""
    WITH RECURSIVE graph AS (
        SELECT e.id, e.name, e.entity_type, e.description, 0 AS depth
        FROM knowledge_entities e
        WHERE e.user_id = :uid AND e.embedding <=> :emb < 0.4
        ORDER BY e.embedding <=> :emb LIMIT 5

        UNION ALL

        SELECT e2.id, e2.name, e2.entity_type, e2.description, g.depth + 1
        FROM graph g
        JOIN knowledge_relations r ON r.source_id = g.id OR r.target_id = g.id
        JOIN knowledge_entities e2 ON e2.id = CASE WHEN r.source_id = g.id THEN r.target_id ELSE r.source_id END
        WHERE g.depth < :max_depth AND e2.user_id = :uid
    )
    SELECT DISTINCT ON (id) id, name, entity_type, description, depth
    FROM graph ORDER BY id, depth LIMIT :lim
    """)

    rows = (await db.execute(sql, {"uid": UUID(user_id), "emb": str(query_emb), "max_depth": max_depth, "lim": limit})).fetchall()
    return [{"name": r.name, "type": r.entity_type, "description": r.description, "depth": r.depth} for r in rows]
