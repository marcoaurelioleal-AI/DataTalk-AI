from pydantic import BaseModel, ConfigDict


class CatalogColumn(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    type: str
    description: str
    queryable: bool


class CatalogTableSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    description: str
    queryable: bool


class CatalogTableSchema(CatalogTableSummary):
    columns: tuple[CatalogColumn, ...]
