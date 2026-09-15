import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useCreateSpec, useSpecs } from '../api/hooks'
import type { Spec, SpecStatus } from '../api/types'
import { STATUS_LABEL } from '../api/types'
import { getAuthor, relativeTime, setAuthor } from '../lib/author'
import './WorkbenchPage.css'

const SECTIONS: SpecStatus[] = ['draft', 'in_review', 'published']

/** The workbench — every spec you're working on, distinct from "my apps" in the Depot, which
 * are apps you *use*. Only a published spec ever leaves here for the Depot's own catalog; a
 * draft or in-review one exists only on this page. */
export default function WorkbenchPage() {
  const { data: specs, isLoading } = useSpecs()
  const navigate = useNavigate()
  const createSpec = useCreateSpec()
  const [authorInput, setAuthorInput] = useState(getAuthor())

  function newSpec() {
    setAuthor(authorInput)
    createSpec.mutate(
      { created_by: authorInput.trim() || undefined },
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
          <input
            className="workbench-page__author"
            placeholder="Your name (optional)"
            value={authorInput}
            onChange={(e) => setAuthorInput(e.target.value)}
          />
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
