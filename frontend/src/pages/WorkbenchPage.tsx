import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { usePersonName, useCreateSpec, useSpecs, useUpdateVisibility } from '../api/hooks'
import type { Spec, SpecStatus, SpecVisibility } from '../api/types'
import { STATUS_LABEL } from '../api/types'
import { getAuthor, getPersonId, readUrlPersonId, relativeTime, setAuthor, setPersonId } from '../lib/author'
import './WorkbenchPage.css'

const SECTIONS: SpecStatus[] = ['draft', 'in_review', 'published']

/** The workbench — every spec you're working on, distinct from "my apps" in the Depot, which
 * are apps you *use*. All three states live right here, permanently — even a published spec
 * stays on this page (see its own SECTIONS below); it's just done, not gone.
 *
 * Authorship and ownership are both picked up automatically, never typed in: a Launchpad
 * "launch this app" link carries `?person_id=` (same passthrough Task Master's own board uses),
 * resolved here to a real name (shown) and kept as the real id (used for ownership/filtering —
 * see models.Spec.person_id) — both remembered in lib/author.ts so they survive after the query
 * param is gone, since client-side navigation drops it from the URL. Opened standalone with no
 * persona to resolve, a spec just creates with no owner — same "no fake precision" restraint as
 * everywhere else in this ecosystem, not a fallback text field.
 *
 * "My workbench" / "Public" is the split that makes a still-in-progress draft reviewable by
 * someone else, not just a finished spec — see models.py's own VISIBILITIES note on why private
 * is the default. Without a known person_id there's no "mine" to show, so Public is the only
 * real option (My workbench still renders, just explains why it's empty). */
export default function WorkbenchPage() {
  const navigate = useNavigate()
  const createSpec = useCreateSpec()

  const urlPersonId = readUrlPersonId()
  const personId = urlPersonId || getPersonId()
  const { data: personResult } = usePersonName(urlPersonId)
  useEffect(() => {
    if (personResult?.found && personResult.name) {
      setAuthor(personResult.name)
      if (urlPersonId) setPersonId(urlPersonId)
    }
  }, [personResult, urlPersonId])

  const author = (personResult?.found && personResult.name) || getAuthor()

  const [view, setView] = useState<'mine' | 'public'>(personId ? 'mine' : 'public')
  const { data: specs, isLoading } = useSpecs(
    view === 'mine' ? { person_id: personId ?? undefined } : { visibility: 'public' },
  )

  function newSpec() {
    createSpec.mutate(
      { created_by: author || undefined, person_id: personId ?? undefined },
      { onSuccess: (spec) => navigate(`/specs/${spec.id}`) },
    )
  }

  const groups: Record<SpecStatus, Spec[]> = { draft: [], in_review: [], published: [] }
  for (const s of specs ?? []) groups[s.status].push(s)

  return (
    <div className="workbench-page">
      <div className="workbench-page__toolbar">
        <div>
          <h1 className="workbench-page__title">Your workbench</h1>
          <div className="workbench-page__tabs">
            <button
              className={`workbench-page__tab ${view === 'mine' ? 'workbench-page__tab--active' : ''}`}
              onClick={() => setView('mine')}
            >
              My workbench
            </button>
            <button
              className={`workbench-page__tab ${view === 'public' ? 'workbench-page__tab--active' : ''}`}
              onClick={() => setView('public')}
            >
              Public
            </button>
          </div>
        </div>
        <div className="workbench-page__new">
          {author && <span className="workbench-page__as">as {author}</span>}
          <button className="am-btn am-btn--primary" onClick={newSpec} disabled={createSpec.isPending}>
            + New spec
          </button>
        </div>
      </div>

      {view === 'mine' && !personId ? (
        <p className="workbench-page__loading">
          Open this from your Depot Launchpad to see your own workbench — without a persona
          there's no "mine" to show. Browsing <strong>Public</strong> in the meantime.
        </p>
      ) : isLoading ? (
        <p className="workbench-page__loading">Loading…</p>
      ) : (specs ?? []).length === 0 ? (
        <p className="workbench-page__loading">
          {view === 'mine'
            ? 'Nothing here yet — start a new spec above.'
            : "Nothing's been made public yet."}
        </p>
      ) : (
        SECTIONS.map((status) => (
          <section className="workbench-section" key={status}>
            <div className="workbench-section__head">
              <span className="workbench-section__title">{STATUS_LABEL[status]}</span>
              <span className="workbench-section__count">{groups[status].length}</span>
            </div>
            {groups[status].length === 0 ? (
              <p className="workbench-section__empty">Nothing here yet.</p>
            ) : (
              <div className="spec-grid">
                {groups[status].map((s) => (
                  <SpecCard spec={s} isMine={view === 'mine'} key={s.id} />
                ))}
              </div>
            )}
          </section>
        ))
      )}
    </div>
  )
}

function SpecCard({ spec, isMine }: { spec: Spec; isMine: boolean }) {
  return (
    <div className="spec-card">
      <Link className="spec-card__link" to={`/specs/${spec.id}`}>
        <span className="spec-card__title">{spec.title || 'Untitled'}</span>
        {spec.problem_statement && <p className="spec-card__desc">{spec.problem_statement}</p>}
        <div className="spec-card__meta">
          {spec.created_by && <span className="spec-card__author">{spec.created_by}</span>}
          <span className="spec-card__time">{relativeTime(spec.updated_at)}</span>
        </div>
      </Link>
      {isMine ? (
        <VisibilityToggle spec={spec} />
      ) : (
        spec.visibility === 'public' && <span className="spec-card__visibility">Public</span>
      )}
    </div>
  )
}

/** Only rendered for a spec's own owner (see SpecCard above) — no real access control behind
 * this either way (models.py's own note), but a stranger browsing Public shouldn't see a
 * clickable toggle on someone else's draft even though the backend wouldn't stop them. */
function VisibilityToggle({ spec }: { spec: Spec }) {
  const updateVisibility = useUpdateVisibility(spec.id)
  const next: SpecVisibility = spec.visibility === 'public' ? 'private' : 'public'
  return (
    <button
      className={`spec-card__visibility-toggle spec-card__visibility-toggle--${spec.visibility}`}
      onClick={(e) => {
        e.preventDefault()
        updateVisibility.mutate(next)
      }}
      disabled={updateVisibility.isPending}
      title={spec.visibility === 'public' ? 'Public — click to make private' : 'Private — click to make public'}
    >
      {spec.visibility === 'public' ? '🌐 Public' : '🔒 Private'}
    </button>
  )
}
