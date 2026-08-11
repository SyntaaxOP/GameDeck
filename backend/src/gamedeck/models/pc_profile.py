"""Single local PC hardware profile."""
from datetime import datetime
from sqlalchemy import CheckConstraint,DateTime,Integer,String,Text
from sqlalchemy.orm import Mapped,mapped_column
from gamedeck.db import Base
class PCProfile(Base):
    __tablename__="pc_profile";__table_args__=(CheckConstraint("id = 1",name="ck_pc_profile_singleton"),CheckConstraint("memory_gb IS NULL OR memory_gb > 0",name="ck_pc_profile_memory_positive"))
    id:Mapped[int]=mapped_column(Integer,primary_key=True);name:Mapped[str]=mapped_column(String(100),nullable=False);cpu:Mapped[str|None]=mapped_column(String(255));gpu:Mapped[str|None]=mapped_column(String(255));memory_gb:Mapped[int|None]=mapped_column(Integer);motherboard:Mapped[str|None]=mapped_column(String(255));storage:Mapped[str|None]=mapped_column(Text);notes:Mapped[str|None]=mapped_column(Text);updated_at:Mapped[datetime]=mapped_column(DateTime,nullable=False)
