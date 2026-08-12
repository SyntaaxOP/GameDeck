export interface PCProfile { name: string; cpu: string | null; gpu: string | null; memory_gb: number | null; motherboard: string | null; storage: string | null; notes: string | null; updated_at: string }
export type PCProfileInput = Omit<PCProfile, 'updated_at'>
export interface StorageVolume { name: string; total_gb: number }
export interface PCSnapshot { operating_system: string; cpu_label: string; gpu_label: string; motherboard: string; logical_cpu_count: number; memory_gb: number; total_storage_gb: number; storage_volumes: StorageVolume[] }
