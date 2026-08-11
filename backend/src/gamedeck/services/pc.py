import platform
from pathlib import Path
import psutil
from sqlalchemy.orm import Session
from gamedeck.models.pc_profile import PCProfile
from gamedeck.schemas.pc import PCProfileResponse,PCProfileUpdate,PCSnapshotResponse
from gamedeck.services.games import utc_now
class PCService:
    def __init__(self,session:Session):self.session=session
    def get(self)->PCProfileResponse|None:
        item=self.session.get(PCProfile,1);return PCProfileResponse.model_validate(item,from_attributes=True) if item else None
    def update(self,payload:PCProfileUpdate)->PCProfileResponse:
        item=self.session.get(PCProfile,1) or PCProfile(id=1,name=payload.name,updated_at=utc_now());self.session.add(item)
        for key,value in payload.model_dump().items():setattr(item,key,value)
        item.updated_at=utc_now();self.session.commit();return PCProfileResponse.model_validate(item,from_attributes=True)
    def snapshot(self)->PCSnapshotResponse:
        memory=round(psutil.virtual_memory().total/(1024**3));storage=round(psutil.disk_usage(str(Path.home().anchor or "C:\\")).total/(1024**3))
        return PCSnapshotResponse(operating_system=f"{platform.system()} {platform.release()}",cpu_label=platform.processor() or platform.machine() or "Unknown CPU",logical_cpu_count=psutil.cpu_count() or 0,memory_gb=memory,storage_gb=storage)
