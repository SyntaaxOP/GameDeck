"""Add local PC profile.

Revision ID: 0007
Revises: 0006
"""
from typing import Sequence
from alembic import op
import sqlalchemy as sa
revision:str="0007";down_revision:str|None="0006";branch_labels:str|Sequence[str]|None=None;depends_on:str|Sequence[str]|None=None
def upgrade():
    op.create_table("pc_profile",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("name",sa.String(100),nullable=False),sa.Column("cpu",sa.String(255)),sa.Column("gpu",sa.String(255)),sa.Column("memory_gb",sa.Integer()),sa.Column("motherboard",sa.String(255)),sa.Column("storage",sa.Text()),sa.Column("notes",sa.Text()),sa.Column("updated_at",sa.DateTime(),nullable=False),sa.CheckConstraint("id = 1",name="ck_pc_profile_singleton"),sa.CheckConstraint("memory_gb IS NULL OR memory_gb > 0",name="ck_pc_profile_memory_positive"))
def downgrade():op.drop_table("pc_profile")
