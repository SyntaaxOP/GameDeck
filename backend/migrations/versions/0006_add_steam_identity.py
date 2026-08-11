"""Add optional Steam application identity.

Revision ID: 0006
Revises: 0005
"""
from typing import Sequence
from alembic import op
import sqlalchemy as sa
revision: str="0006"; down_revision: str|None="0005"; branch_labels: str|Sequence[str]|None=None; depends_on: str|Sequence[str]|None=None
def upgrade()->None:
    with op.batch_alter_table("games") as batch: batch.add_column(sa.Column("steam_app_id",sa.Integer(),nullable=True)); batch.create_unique_constraint("uq_games_steam_app_id",["steam_app_id"])
def downgrade()->None:
    with op.batch_alter_table("games") as batch: batch.drop_constraint("uq_games_steam_app_id",type_="unique"); batch.drop_column("steam_app_id")
