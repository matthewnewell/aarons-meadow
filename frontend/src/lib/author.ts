// No auth here, same as every sibling app's journal — "who" is just a name, plus (unlike a
// plain journal) a real Depot persona id when one's known, since specs now have real ownership
// (person_id — see models.py) that "My workbench" filters by. Two sources for each, in order of
// preference: the Depot persona a "?person_id=" query param points at (see hooks.ts's
// usePersonName — resolved once, remembered here so both survive client-side navigation, which
// drops the query param, and future visits) and, failing that, whatever was remembered last
// time. Ported from Value Stream's / WinMax's lib/journal.ts, extended with the persona lookup.

const AUTHOR_KEY = 'am:author'
const PERSON_ID_KEY = 'am:person_id'

export function getAuthor(): string {
  try {
    return localStorage.getItem(AUTHOR_KEY) ?? ''
  } catch {
    return ''
  }
}

export function setAuthor(name: string): void {
  try {
    const trimmed = name.trim()
    if (trimmed) localStorage.setItem(AUTHOR_KEY, trimmed)
  } catch {
    // private window / storage blocked — specs just get created without an author
  }
}

export function getPersonId(): string | null {
  try {
    return localStorage.getItem(PERSON_ID_KEY)
  } catch {
    return null
  }
}

export function setPersonId(id: string): void {
  try {
    localStorage.setItem(PERSON_ID_KEY, id)
  } catch {
    // private window / storage blocked — no "My workbench" across visits, same degrade as author
  }
}

/** The `?person_id=` a Launchpad "launch this app" link carries (see conways-depot's
 * LaunchpadPage.tsx) — read once per page load, same pattern as Task Master's own
 * readUrlPersonId. `null` when opened standalone (bookmarked, typed in directly). */
export function readUrlPersonId(): string | null {
  try {
    return new URLSearchParams(window.location.search).get('person_id')
  } catch {
    return null
  }
}

/** "just now" / "6m ago" / "3h ago" / "yesterday" / "Sep 8" / "Sep 8, 2025". */
export function relativeTime(iso: string): string {
  const then = new Date(iso).getTime()
  if (Number.isNaN(then)) return ''
  const secs = Math.round((Date.now() - then) / 1000)
  if (secs < 45) return 'just now'
  if (secs < 3600) return `${Math.round(secs / 60)}m ago`
  if (secs < 86400) return `${Math.round(secs / 3600)}h ago`
  const days = Math.round(secs / 86400)
  if (days === 1) return 'yesterday'
  if (days < 7) return `${days}d ago`
  const d = new Date(iso)
  const sameYear = d.getFullYear() === new Date().getFullYear()
  return d.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    ...(sameYear ? {} : { year: 'numeric' }),
  })
}
