import uuid

import pytest
import pytest_asyncio
from sqlalchemy import select

from src.core.repository.exception import RepositoryException
from src.core.repository.repository import Repository, Filters, OrderBy, Distinct
from src.plugin.model import Plugin


class TestRepository:
    @pytest_asyncio.fixture
    async def plugin_repo(self, db_session):
        return Repository(Plugin, db_session)

    def make_plugin(
        self,
        name: str,
        created_by: str = "tester",
        catalog_url: str = "http://example.com",
        description: str = "desc",
        file_name: str | None = None,
        directly_identifies_objects: bool = False,
    ) -> Plugin:
        return Plugin(
            name=name,
            catalog_url=catalog_url,
            description=description,
            created_by=created_by,
            file_name=file_name,
            directly_identifies_objects=directly_identifies_objects,
        )

    @pytest.mark.asyncio
    async def test_find_with_simple_eq_filter(self, db_session, plugin_repo):
        p1 = self.make_plugin("Alpha")
        p2 = self.make_plugin("Beta")
        db_session.add_all([p1, p2])
        await db_session.commit()

        filters = Filters(filters={"name__eq": "Alpha"})

        total_count, results = await plugin_repo.find(filters=filters)

        assert total_count == 1
        assert len(results) == 1
        assert results[0].name == "Alpha"

    @pytest.mark.asyncio
    async def test_find_with_and_or_filters(self, db_session, plugin_repo):
        p1 = self.make_plugin("Alpha", created_by="user1")
        p2 = self.make_plugin("Beta", created_by="user1")
        p3 = self.make_plugin("Gamma", created_by="user2")
        db_session.add_all([p1, p2, p3])
        await db_session.commit()

        # (created_by == user1) AND (name == 'Alpha' OR name == 'Beta')
        filters = Filters(
            filters={
                "and": [
                    {"created_by__eq": "user1"},
                    {
                        "or": [
                            {"name__eq": "Alpha"},
                            {"name__eq": "Beta"},
                        ]
                    },
                ]
            }
        )

        total_count, results = await plugin_repo.find(filters=filters)

        assert total_count == 2
        names = sorted(p.name for p in results)
        assert names == ["Alpha", "Beta"]

    @pytest.mark.asyncio
    async def test_build_filter_invalid_format_raises(self, db_session, plugin_repo):
        # key without "__<op>" should raise
        with pytest.raises(RepositoryException) as excinfo:
            plugin_repo._build_filter(name="Alpha")  # type: ignore[arg-type]

        assert "Invalid filter format" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_build_filter_unsupported_operator_raises(
        self, db_session, plugin_repo
    ):
        with pytest.raises(RepositoryException) as excinfo:
            plugin_repo._build_filter(name__foobar="Alpha")  # type: ignore[call-arg]

        assert "Unsupported filter operator" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_build_filter_unknown_field_raises(self, db_session, plugin_repo):
        with pytest.raises(RepositoryException) as excinfo:
            plugin_repo._build_filter(nonexistent__eq="x")  # type: ignore[call-arg]

        assert "Unknown field" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_subexpressions_invalid_type_raises(self, db_session, plugin_repo):
        # `and` expects dict or list of dicts
        with pytest.raises(RepositoryException) as excinfo:
            plugin_repo._build_filter(filters={"and": 123})  # type: ignore[call-arg]

            assert "Invalid subexpression type" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_find_with_order_by_desc(self, db_session, plugin_repo):
        p1 = self.make_plugin("Alpha")
        p2 = self.make_plugin("Beta")
        p3 = self.make_plugin("Gamma")
        db_session.add_all([p1, p2, p3])
        await db_session.commit()

        filters = Filters(order_by=OrderBy(field="name", value="desc"))

        total_count, results = await plugin_repo.find(filters=filters)

        assert total_count == 3
        names = [p.name for p in results]
        # Descending by name: Gamma, Beta, Alpha
        assert names == ["Gamma", "Beta", "Alpha"]

    @pytest.mark.asyncio
    async def test_find_order_by_unknown_field_raises(self, db_session, plugin_repo):
        filters = Filters(order_by=OrderBy(field="does_not_exist", value="asc"))

        with pytest.raises(RepositoryException) as excinfo:
            await plugin_repo.find(filters=filters)

        assert "Unknown field" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_find_with_distinct(self, db_session, plugin_repo):
        p1 = self.make_plugin("A1", created_by="u1")
        p2 = self.make_plugin("A2", created_by="u1")
        p3 = self.make_plugin("A3", created_by="u2")
        db_session.add_all([p1, p2, p3])
        await db_session.commit()

        filters = Filters(distinct=Distinct(fields=["created_by"]))

        total_count, results = await plugin_repo.find(filters=filters)

        # we expect only 2 distinct created_by values
        created_bys = {p.created_by for p in results}
        assert len(created_bys) == 2
        assert total_count == len(results)

    @pytest.mark.asyncio
    async def test_find_distinct_unknown_field_raises(self, db_session, plugin_repo):
        filters = Filters(distinct=Distinct(fields=["does_not_exist"]))

        with pytest.raises(RepositoryException) as excinfo:
            await plugin_repo.find(filters=filters)

        assert "Unknown distinct field" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_distinct_entity_attribute_values(self, db_session, plugin_repo):
        p1 = self.make_plugin("Alpha", created_by="u1")
        p2 = self.make_plugin("Beta", created_by="u1")
        p3 = self.make_plugin("Gamma", created_by="u2")
        db_session.add_all([p1, p2, p3])
        await db_session.commit()

        values = await plugin_repo.distinct_entity_attribute_values(
            "created_by",
            filters={"name__ilike": "%a%"},  # Alpha, Gamma
        )

        assert set(values) == {"u1", "u2"}

    @pytest.mark.asyncio
    async def test_distinct_entity_attribute_values_unknown_field_raises(
        self, db_session, plugin_repo
    ):
        with pytest.raises(RepositoryException) as excinfo:
            await plugin_repo.distinct_entity_attribute_values("does_not_exist")

        assert "Unknown field" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_get_and_get_optional_existing_entity(self, db_session, plugin_repo):
        plugin = self.make_plugin("Alpha")
        db_session.add(plugin)
        await db_session.commit()
        await db_session.refresh(plugin)

        fetched_optional = await plugin_repo.get_optional(plugin.id)
        assert fetched_optional is not None
        assert fetched_optional.id == plugin.id

        fetched = await plugin_repo.get(plugin.id)
        assert fetched.id == plugin.id

    @pytest.mark.asyncio
    async def test_get_raises_for_missing_entity(self, plugin_repo):
        random_id = uuid.uuid4()

        with pytest.raises(RepositoryException) as excinfo:
            await plugin_repo.get(random_id)

        assert "not found" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_get_optional_returns_none_for_missing_entity(self, plugin_repo):
        random_id = uuid.uuid4()
        result = await plugin_repo.get_optional(random_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_find_first_returns_first(self, db_session, plugin_repo):
        p1 = self.make_plugin("Alpha")
        p2 = self.make_plugin("Beta")
        db_session.add_all([p1, p2])
        await db_session.commit()

        filters = Filters(filters={"name__ilike": "%a%"})
        result = await plugin_repo.find_first(filters=filters)

        assert result is not None
        # alphabetic ordering in DB is not guaranteed here, but find_first
        # uses default ordering (no ORDER BY), so we only check that it's one of them
        assert result.name in {"Alpha", "Beta"}

    @pytest.mark.asyncio
    async def test_find_first_returns_none_when_no_match(self, plugin_repo):
        filters = Filters(filters={"name__eq": "nonexistent"})
        result = await plugin_repo.find_first(filters=filters)
        assert result is None

    @pytest.mark.asyncio
    async def test_find_first_or_raise_returns_entity(self, db_session, plugin_repo):
        p1 = self.make_plugin("Alpha")
        db_session.add(p1)
        await db_session.commit()

        filters = Filters(filters={"name__eq": "Alpha"})
        result = await plugin_repo.find_first_or_raise(filters=filters)

        assert result is not None
        assert result.name == "Alpha"

    @pytest.mark.asyncio
    async def test_find_first_or_raise_raises_when_no_entity(self, plugin_repo):
        filters = Filters(filters={"name__eq": "nonexistent"})

        with pytest.raises(RepositoryException) as excinfo:
            await plugin_repo.find_first_or_raise(filters=filters)

        assert "Entity not found" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_save_persists_entity(self, plugin_repo, db_session):
        plugin = self.make_plugin("NewPlugin")
        saved = await plugin_repo.save(plugin)

        assert saved.id is not None

        stmt = select(Plugin).where(Plugin.id == saved.id)
        result = await db_session.execute(stmt)
        db_obj = result.scalar_one_or_none()

        assert db_obj is not None
        assert db_obj.name == "NewPlugin"

    @pytest.mark.asyncio
    async def test_update_changes_fields(self, plugin_repo, db_session):
        plugin = self.make_plugin("OldName", description="old")
        db_session.add(plugin)
        await db_session.commit()
        await db_session.refresh(plugin)

        updated = await plugin_repo.update(
            plugin.id,
            {"name": "NewName", "description": "new"},
        )

        assert updated.name == "NewName"
        assert updated.description == "new"

        stmt = select(Plugin).where(Plugin.id == plugin.id)
        result = await db_session.execute(stmt)
        db_obj = result.scalar_one()
        assert db_obj.name == "NewName"
        assert db_obj.description == "new"

    @pytest.mark.asyncio
    async def test_delete_removes_entity(self, plugin_repo, db_session):
        plugin = self.make_plugin("ToDelete")
        db_session.add(plugin)
        await db_session.commit()
        await db_session.refresh(plugin)

        await plugin_repo.delete(plugin.id)

        stmt = select(Plugin).where(Plugin.id == plugin.id)
        result = await db_session.execute(stmt)
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_bulk_insert_inserts_all(self, plugin_repo, db_session):
        plugins = [
            self.make_plugin("P1"),
            self.make_plugin("P2"),
            self.make_plugin("P3"),
        ]

        await plugin_repo.bulk_insert(plugins)

        stmt = select(Plugin).where(Plugin.name.in_(["P1", "P2", "P3"]))
        result = await db_session.execute(stmt)
        rows = result.scalars().all()

        assert len(rows) == 3
