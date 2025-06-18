"""add_unique_constraint_to_product_name

Revision ID: 0f8014aec60c
Revises: 0202e069e7c2
Create Date: 2025-06-18 11:10:13.220116

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0f8014aec60c'
down_revision: Union[str, None] = '0202e069e7c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint('uq_products_name', 'products', ['name'])


def downgrade() -> None:
    op.drop_constraint('uq_products_name', 'products', type_='unique')
