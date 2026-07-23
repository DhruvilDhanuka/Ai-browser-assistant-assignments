import {
  Link,
  Outlet,
  createRootRoute,
  useRouterState,
} from '@tanstack/react-router'
import {
  Bot,
  Command,
  FileText,
  Settings,
  Sparkles,
  UserRound,
} from 'lucide-react'

import '../styles.css'

export const Route = createRootRoute({ component: RootComponent })

const navigation = [
  { label: 'Profile', to: '/', icon: UserRound },
  { label: 'Resume', to: '/resume_upload', icon: FileText },
  { label: 'Command center', to: '/CommandsSection', icon: Command },
] as const

function RootComponent() {
  const pathname = useRouterState({
    select: (state) => state.location.pathname,
  })

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 selection:bg-indigo-500/30">
      <div className="fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute left-1/2 top-[-22rem] h-[42rem] w-[42rem] -translate-x-1/2 rounded-full bg-indigo-600/12 blur-3xl" />
        <div className="absolute right-[-14rem] top-1/3 h-80 w-80 rounded-full bg-blue-500/8 blur-3xl" />
      </div>

      <header className="border-b border-white/[0.07] bg-zinc-950/70 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-5 lg:px-8">
          <Link to="/" className="group flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl border border-indigo-400/25 bg-gradient-to-br from-indigo-500 to-violet-600 shadow-lg shadow-indigo-950/50 transition-transform duration-200 group-hover:scale-105">
              <Bot className="h-5 w-5 text-white" strokeWidth={2.2} />
            </span>
            <span>
              <span className="block text-sm font-semibold tracking-tight text-white">
                Nexus
              </span>
              <span className="block text-[10px] font-medium uppercase tracking-[0.16em] text-zinc-500">
                Browser assistant
              </span>
            </span>
          </Link>
          <div className="hidden items-center gap-2 text-xs text-zinc-500 sm:flex">
            <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_12px_rgba(52,211,153,0.8)]" />
            System online
          </div>
        </div>
      </header>

      <div className="mx-auto flex max-w-7xl gap-8 px-5 py-6 lg:px-8 lg:py-8">
        <aside className="hidden w-52 shrink-0 lg:block">
          <nav className="sticky top-8 space-y-1 rounded-2xl border border-white/[0.06] bg-zinc-900/40 p-2 shadow-2xl shadow-black/10">
            <p className="px-3 pb-2 pt-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-zinc-600">
              Workspace
            </p>
            {navigation.map(({ label, to, icon: Icon }) => {
              const active = pathname === to
              return (
                <Link
                  key={to}
                  to={to}
                  className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-colors ${active ? 'bg-indigo-500/12 text-indigo-200' : 'text-zinc-400 hover:bg-white/[0.04] hover:text-zinc-100'}`}
                >
                  <Icon className="h-4 w-4" />
                  {label}
                </Link>
              )
            })}
            <div className="my-2 border-t border-white/[0.06]" />
            <button
              type="button"
              className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm text-zinc-500 transition-colors hover:bg-white/[0.04] hover:text-zinc-300"
            >
              <Settings className="h-4 w-4" />
              Settings
            </button>
          </nav>
          <div className="mt-5 rounded-2xl border border-indigo-400/10 bg-indigo-500/[0.05] p-4">
            <Sparkles className="h-4 w-4 text-indigo-300" />
            <p className="mt-3 text-xs font-medium text-zinc-300">
              AI that works alongside you.
            </p>
            <p className="mt-1 text-xs leading-5 text-zinc-500">
              Set up your profile, then give Nexus a task.
            </p>
          </div>
        </aside>
        <main className="min-w-0 flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
