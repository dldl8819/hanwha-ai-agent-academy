"""rename usage_logs.occured_at to occurred_at

Revision ID: 9f2a041f60ca
Revises: cbd68bb8e46d
Create Date: 2026-09-22 16:26:40.027997

오타(occured_at, r 한 개)를 바른 철자(occurred_at)로 고친다.

--autogenerate 로 만들지 않고 손으로 적은 이유
    autogenerate 는 "이름이 바뀐 것"을 알아보지 못한다.
    없어진 컬럼 하나와 새로 생긴 컬럼 하나로 보고 drop + add 를 적어주는데,
    그대로 실행하면 기존 행의 값이 전부 사라진다.
    alter_column(new_column_name=...) 은 값을 그대로 둔 채 이름만 바꾼다.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9f2a041f60ca'
down_revision: Union[str, Sequence[str], None] = 'cbd68bb8e46d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "usage_logs",
        "occured_at",
        new_column_name="occurred_at",
        existing_type=sa.DateTime(),
        existing_nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "usage_logs",
        "occurred_at",
        new_column_name="occured_at",
        existing_type=sa.DateTime(),
        existing_nullable=False,
    )
