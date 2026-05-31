from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.schemas.catalog import CatalogTableSchema, CatalogTableSummary
from app.services.catalog_service import CatalogService, CatalogTableBlockedError, CatalogTableNotFoundError

router = APIRouter(prefix="/catalog", tags=["catalog"], dependencies=[Depends(get_current_user)])
catalog_service = CatalogService()


@router.get("/tables", response_model=list[CatalogTableSummary])
def list_tables() -> list[CatalogTableSummary]:
    return catalog_service.list_tables()


@router.get("/tables/{table_name}/schema", response_model=CatalogTableSchema)
def get_table_schema(table_name: str) -> CatalogTableSchema:
    try:
        return catalog_service.get_table_schema(table_name)
    except CatalogTableBlockedError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Table '{error.table_name}' is internal and cannot be queried.",
        ) from error
    except CatalogTableNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Table '{error.table_name}' was not found in the queryable catalog.",
        ) from error
