from app.repositories.catalog_repository import CatalogRepository
from app.schemas.catalog import CatalogTableSchema, CatalogTableSummary


class CatalogTableBlockedError(Exception):
    def __init__(self, table_name: str) -> None:
        self.table_name = table_name
        super().__init__(table_name)


class CatalogTableNotFoundError(Exception):
    def __init__(self, table_name: str) -> None:
        self.table_name = table_name
        super().__init__(table_name)


class CatalogService:
    def __init__(self, repository: CatalogRepository | None = None) -> None:
        self.repository = repository or CatalogRepository()

    def list_tables(self) -> list[CatalogTableSummary]:
        return [
            CatalogTableSummary(
                name=table.name,
                description=table.description,
                queryable=table.queryable,
            )
            for table in self.repository.list_queryable_tables()
        ]

    def get_table_schema(self, table_name: str) -> CatalogTableSchema:
        normalized_table_name = table_name.strip().lower()
        if self.repository.is_internal_table(normalized_table_name):
            raise CatalogTableBlockedError(normalized_table_name)

        table = self.repository.get_queryable_table(normalized_table_name)
        if not table:
            raise CatalogTableNotFoundError(normalized_table_name)
        return table
