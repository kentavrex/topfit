"""update statistics date field

Revision ID: 84d915024ccd
Revises: 63f757340c69
Create Date: 2025-05-02 17:08:16.535391

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '84d915024ccd'
down_revision: Union[str, None] = '63f757340c69'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Переименовываем столбец
    op.alter_column('statistics', 'date', new_column_name='created_at')
    # Изменяем тип столбца
    op.alter_column('statistics', 'created_at',
                    existing_type=sa.DATE(),
                    type_=sa.TIMESTAMP(timezone=True),
                    existing_nullable=False)


def downgrade() -> None:
    # Возвращаем тип обратно
    op.alter_column('statistics', 'created_at',
                    existing_type=sa.TIMESTAMP(timezone=True),
                    type_=sa.DATE(),
                    existing_nullable=False)
    # Переименовываем обратно
    op.alter_column('statistics', 'created_at', new_column_name='date')
