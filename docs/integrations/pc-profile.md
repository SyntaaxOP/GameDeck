# PC hardware profile

The PC page stores one manually curated local hardware profile and displays a one-time read-only inventory snapshot when opened: operating system, processor label and logical thread count, installed memory, and primary filesystem capacity.

GameDeck does not sample CPU/GPU utilization, temperatures, processes, or per-session resource usage. The snapshot is not persisted automatically. GPU and motherboard fields remain manual because dependable vendor-neutral Windows discovery would require broader WMI permissions and fragile hardware-specific parsing.

Acceptance requires singleton persistence, positive memory validation, stable inventory output, editable optional fields, and no background collection.
