import { useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { usePersonName, useCreateSpec, useSpecs } from '../api/hooks'
import type { Spec, SpecStatus } from '../api/types'
import { STATUS_LABEL } from '../api/types'
import { getAuthor, readUrlPersonId, relativeTime, setAuthor } from '../lib/author'
import './WorkbenchPage.css'

const SECTIONS: SpecStatus[] = ['draft', 'in_review', 'published']

/** The workbench — every spec you're working on, distinct from "my apps" in the Depot, which
 * are apps you *use*. All three states live right here, permanently — even a published spec
 * stays on this page (see its own SECTIONS below); it's just done, not gone.
 *
 * Authorship is picked up automatically, never typed in: a Launchpad "launch this app" link
 * carries `?person_id=` (same passthrough Task Master's own board uses), resolved here to a
 * real name via usePersonName and remembered (lib/author.ts) so it survives after the query
 * param is gone. Opened standalone with no persona to resolve, a spec just creates with no
 * author — same "no fake precision" restraint as everywhere else in this ecosystem, not a
 * fallback text field. */
export default function WorkbenchPage() {
  const { data: specs, isLoading } = useSpecs()
  const navigate = useNavigate()
  const createSpec = useCreateSpec()

  const urlPersonId = readUrlPersonId()
  const { data: personResult } = usePersonName(urlPersonId)
  useEffect(() => {
    if (personResult?.found && personResult.name) setAuthor(personResult.name)
  }, [personResult])

  const author = (personResult?.found && personResult.name) || getAuthor()

  function newSpec() {
    createSpec.mutate(
      { created_by: author || undefined },
      { onSuccess: (spec) => navigate(`/specs/${spec.id}`) },
    )
  }

  const groups: Record<SpecStatus, Spec[]> = { draft: [], in_review: [], published: [] }
  for (const s of specs ?? []) groups[s.status].push(s)

  return (
    <div className="workbench-page">
      <div className="workbench-page__toolbar">
        <h1 className="workbench-page__title">Your workbench</h1>
        <div className="workbench-page__new">
          {author && <span className="workbench-page__as">as {author}</span>}
          <button className="am-btn am-btn--primary" onClick={newSpec} disabled={createSpec.isPending}>
            + New spec
          </button>
        </div>
      </div>

      {isLoading ? (
        <p className="workbench-page__loading">Loading…</p>
      ) : (
        SECTIONS.map((status) => (
          <section className="workbench-section" key={status}>
            <div className="workbench-section__head">
              <span className="workbench-section__title">{STATUS_LABEL[status]}</span>
              <span className="workbench-section__count">{groups[status].length}</span>
            </div>
            {groups[status].length === 0 ? (
              <p className="workbench-section__empty">
                {status === 'draft' ? 'Nothing here yet — start a new spec above.' : 'Nothing here yet.'}
              </p>
            ) : (
              <div className="spec-grid">
                {groups[status].map((s) => (
                  <SpecCard spec={s} key={s.id} />
                ))}
              </div>
            )}
          </section>
        ))
      )}
    </div>
  )
}

function SpecCard({ spec }: { spec: Spec }) {
  return (
    <Link className="spec-card" to={`/specs/${spec.id}`}>
      <span className="spec-card__title">{spec.title || 'Untitled'}</span>
      {spec.problem_statement && <p className="spec-card__desc">{spec.problem_statement}</p>}
      <div className="spec-card__meta">
        {spec.created_by && <span className="spec-card__author">{spec.created_by}</span>}
        <span className="spec-card__time">{relativeTime(spec.updated_at)}</span>
      </div>
    </Link>
  )
}
