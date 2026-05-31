from app.schemas.catalog import CatalogColumn, CatalogTableSchema

INTERNAL_TABLE_NAMES = frozenset({"users", "query_logs", "query_feedback"})

TABLE_CATALOG = {
    "customers": CatalogTableSchema(
        name="customers",
        description="Business customers who place orders.",
        queryable=True,
        columns=(
            CatalogColumn(name="id", type="integer", description="Customer identifier.", queryable=True),
            CatalogColumn(name="name", type="varchar", description="Customer name.", queryable=True),
            CatalogColumn(name="email", type="varchar", description="Customer email address.", queryable=True),
            CatalogColumn(name="city", type="varchar", description="Customer city.", queryable=True),
            CatalogColumn(name="state", type="varchar", description="Customer state code.", queryable=True),
            CatalogColumn(name="created_at", type="timestamp", description="Customer creation timestamp.", queryable=True),
        ),
    ),
    "products": CatalogTableSchema(
        name="products",
        description="Products available for sale.",
        queryable=True,
        columns=(
            CatalogColumn(name="id", type="integer", description="Product identifier.", queryable=True),
            CatalogColumn(name="name", type="varchar", description="Product name.", queryable=True),
            CatalogColumn(name="category", type="varchar", description="Product category.", queryable=True),
            CatalogColumn(name="price", type="numeric", description="Product unit price.", queryable=True),
            CatalogColumn(name="created_at", type="timestamp", description="Product creation timestamp.", queryable=True),
        ),
    ),
    "orders": CatalogTableSchema(
        name="orders",
        description="Customer orders and their commercial totals.",
        queryable=True,
        columns=(
            CatalogColumn(name="id", type="integer", description="Order identifier.", queryable=True),
            CatalogColumn(name="customer_id", type="integer", description="Customer identifier.", queryable=True),
            CatalogColumn(
                name="sales_channel_id",
                type="integer",
                description="Sales channel identifier.",
                queryable=True,
            ),
            CatalogColumn(name="campaign_id", type="integer", description="Marketing campaign identifier.", queryable=True),
            CatalogColumn(name="order_date", type="date", description="Order date.", queryable=True),
            CatalogColumn(name="status", type="varchar", description="Order status.", queryable=True),
            CatalogColumn(name="total_amount", type="numeric", description="Order total amount.", queryable=True),
            CatalogColumn(name="created_at", type="timestamp", description="Order creation timestamp.", queryable=True),
        ),
    ),
    "order_items": CatalogTableSchema(
        name="order_items",
        description="Products and quantities included in each order.",
        queryable=True,
        columns=(
            CatalogColumn(name="id", type="integer", description="Order item identifier.", queryable=True),
            CatalogColumn(name="order_id", type="integer", description="Order identifier.", queryable=True),
            CatalogColumn(name="product_id", type="integer", description="Product identifier.", queryable=True),
            CatalogColumn(name="quantity", type="integer", description="Quantity purchased.", queryable=True),
            CatalogColumn(name="unit_price", type="numeric", description="Product unit price at purchase.", queryable=True),
            CatalogColumn(name="subtotal", type="numeric", description="Order item subtotal.", queryable=True),
        ),
    ),
    "campaigns": CatalogTableSchema(
        name="campaigns",
        description="Marketing campaigns associated with orders.",
        queryable=True,
        columns=(
            CatalogColumn(name="id", type="integer", description="Campaign identifier.", queryable=True),
            CatalogColumn(name="name", type="varchar", description="Campaign name.", queryable=True),
            CatalogColumn(name="channel", type="varchar", description="Marketing channel.", queryable=True),
            CatalogColumn(name="start_date", type="date", description="Campaign start date.", queryable=True),
            CatalogColumn(name="end_date", type="date", description="Campaign end date.", queryable=True),
            CatalogColumn(name="budget", type="numeric", description="Campaign budget.", queryable=True),
            CatalogColumn(name="target_audience", type="varchar", description="Target audience.", queryable=True),
            CatalogColumn(name="created_at", type="timestamp", description="Campaign creation timestamp.", queryable=True),
        ),
    ),
    "sales_channels": CatalogTableSchema(
        name="sales_channels",
        description="Channels through which orders are placed.",
        queryable=True,
        columns=(
            CatalogColumn(name="id", type="integer", description="Sales channel identifier.", queryable=True),
            CatalogColumn(name="name", type="varchar", description="Sales channel name.", queryable=True),
            CatalogColumn(name="type", type="varchar", description="Sales channel type.", queryable=True),
            CatalogColumn(
                name="created_at",
                type="timestamp",
                description="Sales channel creation timestamp.",
                queryable=True,
            ),
        ),
    ),
}

QUERYABLE_TABLE_NAMES = frozenset(TABLE_CATALOG)


class CatalogRepository:
    def list_queryable_tables(self) -> list[CatalogTableSchema]:
        return list(TABLE_CATALOG.values())

    def get_queryable_table(self, table_name: str) -> CatalogTableSchema | None:
        return TABLE_CATALOG.get(table_name)

    def is_internal_table(self, table_name: str) -> bool:
        return table_name in INTERNAL_TABLE_NAMES
