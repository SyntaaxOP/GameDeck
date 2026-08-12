import type { ReactNode } from 'react'
import { BarChart3, CalendarHeart, ChartNoAxesCombined, CircleDollarSign, CloudDownload, Cpu, ExternalLink, Gamepad2, Library, ListTodo, Radio, ScanSearch, Settings } from 'lucide-react'
import { NavLink } from 'react-router-dom'

const navigation = [
  { label: 'Dashboard', icon: BarChart3, path: '/', available: true },
  { label: 'Analytics', icon: ChartNoAxesCombined, path: '/analytics', available: true },
  { label: 'Library', icon: Library, path: '/library', available: true },
  { label: 'Review detections', icon: ScanSearch, path: '/detections', available: true },
  { label: 'Sessions', icon: Gamepad2, path: '/sessions', available: true },
  { label: 'Backlog', icon: ListTodo, path: '/backlog', available: true },
  { label: 'Spending', icon: CircleDollarSign, path: '/spending', available: true },
  { label: 'FiveM', icon: Radio, path: '/fivem', available: true },
  { label: 'Game nights', icon: CalendarHeart, path: '/game-nights', available: true },
  { label: 'Steam library', icon: CloudDownload, path: '/steam-import', available: true },
  { label: 'PC profile', icon: Cpu, path: '/pc', available: true },
  { label: 'Settings', icon: Settings, path: '/settings', available: true },
]

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-background">
      <a href="#main-content" className="fixed left-3 top-3 z-50 -translate-y-20 rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground focus:translate-y-0">Skip to main content</a>
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r bg-card/50 p-5 lg:block">
        <div className="flex items-center gap-3 px-2 py-3">
          <div className="flex size-10 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Gamepad2 className="size-5" aria-hidden="true" />
          </div>
          <div>
            <p className="font-semibold tracking-tight">GameDeck</p>
            <p className="text-xs text-muted-foreground">Local gaming library</p>
          </div>
        </div>

        <nav className="mt-8 space-y-1" aria-label="Primary navigation">
          {navigation.map((item) => {
            const Icon = item.icon
            return (
              item.available ? (
                <NavLink
                  key={item.label}
                  to={item.path}
                  end={item.path === '/'}
                  className={({ isActive }) => isActive
                    ? 'flex items-center gap-3 rounded-md bg-accent px-3 py-2.5 text-sm font-medium'
                    : 'flex items-center gap-3 rounded-md px-3 py-2.5 text-sm text-muted-foreground hover:bg-accent/60 hover:text-foreground'}
                >
                  <Icon className="size-4" aria-hidden="true" />
                  {item.label}
                </NavLink>
              ) : (
                <div key={item.label} aria-disabled="true" className="flex items-center gap-3 rounded-md px-3 py-2.5 text-sm text-muted-foreground/55">
                  <Icon className="size-4" aria-hidden="true" />
                  {item.label}
                  <span className="ml-auto text-[10px] uppercase">Soon</span>
                </div>
              )
            )
          })}
        </nav>

        <div className="absolute inset-x-5 bottom-5 rounded-lg border bg-background/60 p-3">
          <p className="text-xs font-medium">Version 0.8.3</p>
          <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
            Complete local gaming workspace.
          </p>
        </div>
      </aside>

      <main id="main-content" tabIndex={-1} className="flex min-h-screen flex-col lg:pl-64">
        <div className="border-b bg-card/40 px-4 py-3 lg:hidden">
          <div className="mx-auto flex max-w-7xl flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <span className="flex items-center gap-2 font-semibold"><Gamepad2 className="size-5 text-primary" aria-hidden="true" /> GameDeck</span>
            <nav className="flex w-full gap-1 overflow-x-auto sm:w-auto" aria-label="Mobile navigation">
              <ButtonLink to="/" label="Dashboard" />
              <ButtonLink to="/library" label="Library" />
              <ButtonLink to="/detections" label="Detections" />
              <ButtonLink to="/analytics" label="Analytics" />
              <ButtonLink to="/backlog" label="Backlog" />
              <ButtonLink to="/sessions" label="Sessions" />
              <ButtonLink to="/spending" label="Spending" />
              <ButtonLink to="/fivem" label="FiveM" />
              <ButtonLink to="/game-nights" label="Game nights" />
              <ButtonLink to="/steam-import" label="Steam library" />
              <ButtonLink to="/pc" label="PC profile" />
              <ButtonLink to="/settings" label="Settings" />
            </nav>
          </div>
        </div>
        <div className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 sm:px-6 lg:px-8 lg:py-10">{children}</div>
        <footer className="flex justify-end px-4 pb-4 sm:px-6 lg:px-8">
          <a className="inline-flex items-center gap-1.5 text-xs text-muted-foreground transition-colors hover:text-primary" href="https://github.com/syntax-000" target="_blank" rel="noreferrer">Made by Syn <ExternalLink className="size-3.5" aria-hidden="true" /></a>
        </footer>
      </main>
    </div>
  )
}

function ButtonLink({ to, label }: { to: string; label: string }) {
  return <NavLink to={to} end={to === '/'} className={({ isActive }) => isActive ? 'shrink-0 rounded-md bg-accent px-3 py-1.5 text-sm font-medium' : 'shrink-0 rounded-md px-3 py-1.5 text-sm text-muted-foreground'}>{label}</NavLink>
}
