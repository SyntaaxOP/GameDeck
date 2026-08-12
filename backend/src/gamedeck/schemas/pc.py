from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class PCProfileUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    cpu: str | None = Field(default=None, max_length=255)
    gpu: str | None = Field(default=None, max_length=255)
    memory_gb: int | None = Field(default=None, gt=0, le=4096)
    motherboard: str | None = Field(default=None, max_length=255)
    storage: str | None = Field(default=None, max_length=2000)
    notes: str | None = Field(default=None, max_length=10000)

    @field_validator("name")
    @classmethod
    def trim_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("cpu", "gpu", "motherboard", "storage", "notes")
    @classmethod
    def trim_optional(cls, value: str | None) -> str | None:
        return value.strip() or None if value else None


class PCProfileResponse(PCProfileUpdate):
    updated_at: datetime


class StorageVolume(BaseModel):
    name: str
    total_gb: int


class PCSnapshotResponse(BaseModel):
    operating_system: str
    cpu_label: str
    gpu_label: str
    motherboard: str
    logical_cpu_count: int
    memory_gb: int
    total_storage_gb: int
    storage_volumes: list[StorageVolume]
