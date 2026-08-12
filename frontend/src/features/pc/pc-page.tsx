import { useEffect, useState, type FormEvent } from 'react'
import { CircuitBoard, Cpu, HardDrive, MemoryStick, MonitorCog, Save, WandSparkles } from 'lucide-react'

import { getPCProfile, getPCSnapshot, savePCProfile } from '@/api/pc'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import type { PCProfileInput, PCSnapshot } from '@/types/pc'

const empty: PCProfileInput = { name: 'My gaming PC', cpu: null, gpu: null, memory_gb: null, motherboard: null, storage: null, notes: null }

function profileFromSnapshot(snapshot: PCSnapshot): PCProfileInput {
  return { name: 'My gaming PC', cpu: snapshot.cpu_label, gpu: snapshot.gpu_label, memory_gb: snapshot.memory_gb, motherboard: snapshot.motherboard, storage: snapshot.storage_volumes.map((volume) => `${volume.name} ${volume.total_gb} GB`).join(', '), notes: null }
}

export function PCPage() {
  const [form, setForm] = useState<PCProfileInput>(empty)
  const [snapshot, setSnapshot] = useState<PCSnapshot | null>(null)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    Promise.all([getPCProfile(controller.signal), getPCSnapshot(controller.signal)])
      .then(([profile, live]) => {
        if (profile) {
          const { updated_at: _updatedAt, ...profileInput } = profile
          void _updatedAt
          setForm(profileInput)
        } else setForm(profileFromSnapshot(live))
        setSnapshot(live)
      })
      .catch((caught: unknown) => { if (!(caught instanceof DOMException && caught.name === 'AbortError')) setError(caught instanceof Error ? caught.message : 'Unable to load PC profile.') })
    return () => controller.abort()
  }, [])

  function field<K extends keyof PCProfileInput>(key: K, value: PCProfileInput[K]) { setForm((current) => ({ ...current, [key]: value })) }
  function useDetectedHardware() { if (snapshot) { setForm((current) => ({ ...profileFromSnapshot(snapshot), name: current.name, notes: current.notes })); setMessage('Detected hardware filled in. Save to keep it in your profile.') } }
  async function submit(event: FormEvent) {
    event.preventDefault(); setSaving(true); setError(null)
    try { await savePCProfile(form); setMessage('PC profile saved locally.') }
    catch (caught) { setError(caught instanceof Error ? caught.message : 'Unable to save PC profile.') }
    finally { setSaving(false) }
  }

  return <div className="space-y-6">
    <header><p className="text-sm font-medium text-primary">Stable inventory, not surveillance</p><h1 className="mt-1 text-3xl font-semibold sm:text-4xl">PC profile</h1><p className="mt-2 max-w-2xl text-sm text-muted-foreground">GameDeck reads your hardware when this page opens. It does not record background resource usage.</p></header>
    {snapshot ? <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3"><Metric icon={MonitorCog} label="Operating system" value={snapshot.operating_system} /><Metric icon={Cpu} label="Processor" value={`${snapshot.cpu_label} · ${snapshot.logical_cpu_count} threads`} /><Metric icon={CircuitBoard} label="Graphics" value={snapshot.gpu_label} /><Metric icon={CircuitBoard} label="Motherboard" value={snapshot.motherboard} /><Metric icon={MemoryStick} label="Memory" value={`${snapshot.memory_gb} GB`} /><Metric icon={HardDrive} label="Total storage" value={`${snapshot.total_storage_gb} GB · ${snapshot.storage_volumes.map((volume) => `${volume.name} ${volume.total_gb} GB`).join(' · ')}`} /></div> : null}
    <Card><CardHeader><div className="flex flex-wrap items-center justify-between gap-3"><CardTitle>My hardware</CardTitle>{snapshot ? <Button type="button" variant="outline" size="sm" onClick={useDetectedHardware}><WandSparkles aria-hidden="true" /> Use detected hardware</Button> : null}</div></CardHeader><CardContent><form className="grid gap-4 sm:grid-cols-2" onSubmit={(event) => void submit(event)}>
      <Field id="pc-name" label="Profile name" value={form.name} onChange={(value) => field('name', value)} required />
      <Field id="pc-cpu" label="CPU" value={form.cpu ?? ''} onChange={(value) => field('cpu', value || null)} />
      <Field id="pc-gpu" label="GPU" value={form.gpu ?? ''} onChange={(value) => field('gpu', value || null)} />
      <div className="space-y-2"><Label htmlFor="pc-memory">Memory (GB)</Label><Input id="pc-memory" type="number" min="1" max="4096" value={form.memory_gb ?? ''} onChange={(event) => field('memory_gb', event.target.value ? Number(event.target.value) : null)} /></div>
      <Field id="pc-board" label="Motherboard" value={form.motherboard ?? ''} onChange={(value) => field('motherboard', value || null)} />
      <Field id="pc-storage" label="Storage details" value={form.storage ?? ''} onChange={(value) => field('storage', value || null)} />
      <div className="space-y-2 sm:col-span-2"><Label htmlFor="pc-notes">Notes</Label><Textarea id="pc-notes" rows={4} value={form.notes ?? ''} onChange={(event) => field('notes', event.target.value || null)} placeholder="Upgrade plans, cooling, peripherals…" /></div>
      {error ? <p role="alert" className="text-sm text-destructive sm:col-span-2">{error}</p> : null}{message ? <p role="status" className="text-sm text-primary sm:col-span-2">{message}</p> : null}
      <div className="sm:col-span-2"><Button type="submit" disabled={saving}><Save aria-hidden="true" /> {saving ? 'Saving…' : 'Save profile'}</Button></div>
    </form></CardContent></Card>
  </div>
}

function Metric({ icon: Icon, label, value }: { icon: typeof Cpu; label: string; value: string }) { return <Card><CardContent className="py-5"><p className="flex items-center gap-2 text-xs text-muted-foreground"><Icon className="size-4 text-primary" aria-hidden="true" />{label}</p><p className="mt-2 text-sm font-medium">{value}</p></CardContent></Card> }
function Field({ id, label, value, onChange, required = false }: { id: string; label: string; value: string; onChange: (value: string) => void; required?: boolean }) { return <div className="space-y-2"><Label htmlFor={id}>{label}</Label><Input id={id} value={value} onChange={(event) => onChange(event.target.value)} required={required} /></div> }
