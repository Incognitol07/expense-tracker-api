"""removed debt notifications

Revision ID: 743f3ecab378
Revises: 74bd68cc9d8b
Create Date: 2024-12-20 21:36:20.948257

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '743f3ecab378'
down_revision: Union[str, None] = '74bd68cc9d8b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_debt_notifications_id', table_name='debt_notifications')
    op.drop_table('debt_notifications')
    op.add_column(
        'notifications',
        sa.Column(
            'type',
            sa.Enum('ALERT', 'GROUP_DEBT', 'SYSTEM', name='notificationtype'),
            nullable=False,
            server_default='SYSTEM'  # Adjust to the most appropriate default
        )
    )
    # Remove the default value
    op.alter_column('notifications', 'type', server_default=None)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('notifications', 'type')
    op.create_table('debt_notifications',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('amount', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False),
    sa.Column('description', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('debtor_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('creditor_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('status', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['creditor_id'], ['users.id'], name='debt_notifications_creditor_id_fkey'),
    sa.ForeignKeyConstraint(['debtor_id'], ['users.id'], name='debt_notifications_debtor_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='debt_notifications_pkey')
    )
    op.create_index('ix_debt_notifications_id', 'debt_notifications', ['id'], unique=False)
    # ### end Alembic commands ###