from datetime import date, timedelta
from decimal import Decimal
from random import Random

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.database import SessionLocal
from app.models.campaign import Campaign
from app.models.customer import Customer
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.sales_channel import SalesChannel
from app.models.user import User

random = Random(42)


def seed_users(db: Session) -> None:
    existing_user = db.scalar(select(User.id).limit(1))
    if existing_user:
        return

    users = [
        User(name="Admin DataTalk", email="admin@datatalk.ai", hashed_password=hash_password("admin123"), role="admin"),
        User(name="Analyst DataTalk", email="analyst@datatalk.ai", hashed_password=hash_password("analyst123"), role="analyst"),
        User(name="Viewer DataTalk", email="viewer@datatalk.ai", hashed_password=hash_password("viewer123"), role="viewer"),
    ]
    db.add_all(users)


def seed_business_data(db: Session) -> None:
    existing_customer = db.scalar(select(Customer.id).limit(1))
    if existing_customer:
        return

    customers = [
        Customer(
            name=f"Cliente {index:02d}",
            email=f"cliente{index:02d}@example.com",
            city=random.choice(["Sao Paulo", "Rio de Janeiro", "Curitiba", "Belo Horizonte", "Recife"]),
            state=random.choice(["SP", "RJ", "PR", "MG", "PE"]),
        )
        for index in range(1, 51)
    ]

    products = [
        Product(name=name, category=category, price=Decimal(str(price)))
        for name, category, price in [
            ("Notebook Pro", "Eletronicos", "5899.90"),
            ("Smartwatch X", "Eletronicos", "899.90"),
            ("Mouse Gamer", "Acessorios", "249.90"),
            ("Headset Ultra", "Acessorios", "399.90"),
            ("Monitor 27", "Eletronicos", "1499.90"),
            ("Teclado Mecanico", "Acessorios", "349.90"),
            ("Cadeira Office", "Moveis", "1199.90"),
            ("Mesa Ajustavel", "Moveis", "1899.90"),
            ("Camera HD", "Eletronicos", "549.90"),
            ("Microfone Studio", "Acessorios", "699.90"),
            ("Tablet Air", "Eletronicos", "3299.90"),
            ("Carregador USB-C", "Acessorios", "129.90"),
            ("Mochila Tech", "Acessorios", "289.90"),
            ("Impressora Laser", "Escritorio", "999.90"),
            ("Scanner Compacto", "Escritorio", "749.90"),
            ("Roteador Mesh", "Eletronicos", "649.90"),
            ("SSD 1TB", "Componentes", "499.90"),
            ("Memoria 32GB", "Componentes", "599.90"),
            ("Webcam Pro", "Eletronicos", "449.90"),
            ("Hub USB", "Acessorios", "159.90"),
        ]
    ]

    sales_channels = [
        SalesChannel(name="Website", type="online"),
        SalesChannel(name="App Mobile", type="online"),
        SalesChannel(name="Marketplace", type="partner"),
        SalesChannel(name="Loja Fisica", type="offline"),
        SalesChannel(name="WhatsApp", type="direct"),
    ]

    today = date.today()
    campaigns = [
        Campaign(
            name=f"Campanha {index:02d}",
            channel=random.choice(["email", "paid_search", "social", "influencer", "display"]),
            start_date=today - timedelta(days=120 - index * 5),
            end_date=today + timedelta(days=index),
            budget=Decimal(str(random.randint(5000, 30000))),
            target_audience=random.choice(["novos clientes", "clientes recorrentes", "alto valor", "carrinho abandonado"]),
        )
        for index in range(1, 11)
    ]

    db.add_all([*customers, *products, *sales_channels, *campaigns])
    db.flush()

    orders: list[Order] = []
    statuses = ["paid", "cancelled", "pending", "refunded"]
    for _ in range(200):
        order = Order(
            customer_id=random.choice(customers).id,
            sales_channel_id=random.choice(sales_channels).id,
            campaign_id=random.choice(campaigns).id,
            order_date=today - timedelta(days=random.randint(0, 180)),
            status=random.choices(statuses, weights=[75, 10, 10, 5], k=1)[0],
            total_amount=Decimal("0.00"),
        )
        db.add(order)
        orders.append(order)

    db.flush()

    items: list[OrderItem] = []
    for index in range(500):
        order = orders[index % len(orders)]
        product = random.choice(products)
        quantity = random.randint(1, 4)
        subtotal = product.price * quantity
        order.total_amount += subtotal
        items.append(
            OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=quantity,
                unit_price=product.price,
                subtotal=subtotal,
            )
        )

    db.add_all(items)


def seed_database() -> None:
    with SessionLocal() as db:
        seed_users(db)
        seed_business_data(db)
        db.commit()


if __name__ == "__main__":
    seed_database()
    print("Database seeded successfully.")
