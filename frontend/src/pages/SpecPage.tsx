import { useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  useChat,
  usePublish,
  useSpec,
  useSubmitForReview,
  useUpdateConformance,
} from '../api/hooks'
import type { DeclaredScope } from '../api/types'
import { DECLARED_SCOPE_LABEL, DECLARED_SCOPES, STATUS_LABEL } from '../api/types'
import './SpecPage.css'

/** The core screen — the interview on one side, the spec assembling itself on the other. A
 * draft is fully interactive (chat + editable conformance answers); in_review/published render
 * read-only, since the interview is over. A published spec stays right here — this page is its
 * permanent home, not a stand-in for a separate Depot catalog entry (see backend models.py's
 * own docstring for why publishing doesn't create one). */
export default function SpecPage() {
  const { specId } = useParams<{ specId: string }>()
  const { data: spec, isLoading } = useSpec(specId)
  const chat = useChat(specId ?? '')
  const updateConformance = useUpdateConformance(specId ?? '')
  const submitForReview = useSubmitForReview(specId ?? '')
  const publish = usePublish(specId ?? '')

  const [input, setInput] = useState('')
  const [chatError, setChatError] = useState<string | null>(null)
  const listRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    requestAnimationFrame(() => {
      listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' })
    })
  }, [spec?.messages.length])

  if (!specId) return null
  if (isLoading || !spec) return <div className="spec-page__loading">Loading…</div>

  const editable = spec.status === 'draft'

  function send() {
    const text = input.trim()
    if (!text || chat.isPending) return
    setInput('')
    setChatError(null)
    chat.mutate(text, {
      onSuccess: (result) => {
        if ('error' in result) setChatError(result.error)
      },
      onError: (err) => setChatError(err instanceof Error ? err.message : 'Something went wrong'),
    })
  }

  return (
    <div className="spec-page">
      <div className="spec-page__header">
        <h1 className="spec-page__title">{spec.title || 'Untitled spec'}</h1>
        <span className={`status-pill spec-page__status spec-page__status--${spec.status}`}>
          {STATUS_LABEL[spec.status]}
        </span>
      </div>

      <div className="spec-page__split">
        <section className="spec-page__chat">
          <div className="spec-page__chat-list" ref={listRef}>
            {spec.messages.length === 0 && (
              <p className="spec-page__chat-empty">
                Say what you're trying to build. One question at a time from here.
              </p>
            )}
            {spec.messages.map((m, i) => (
              <div key={i} className={`chat-bubble chat-bubble--${m.role}`}>
                {m.content}
              </div>
            ))}
            {chat.isPending && <div className="chat-bubble chat-bubble--assistant chat-bubble--pending">…</div>}
          </div>
          {chatError && <p className="spec-page__chat-error">{chatError}</p>}
          {editable ? (
            <div className="spec-page__chat-input">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    send()
                  }
                }}
                placeholder="Type here…"
                rows={2}
              />
              <button className="am-btn am-btn--primary" onClick={send} disabled={!input.trim() || chat.isPending}>
                Send
              </button>
            </div>
          ) : (
            <p className="spec-page__chat-closed">The interview is over — this spec is {STATUS_LABEL[spec.status].toLowerCase()}.</p>
          )}
        </section>

        <section className="spec-page__panel">
          <h2 className="spec-page__panel-title">The spec</h2>

          <SpecField label="Problem" value={spec.problem_statement} />
          <SpecField label="Who it's for" value={spec.who_its_for} />
          <SpecField label="Key features" value={spec.key_features} multiline />
          <SpecField label="Out of scope" value={spec.out_of_scope} multiline />
          <SpecField label="Open questions" value={spec.open_questions} multiline />

          {spec.deletion_question_conclusion && (
            <div className="spec-field spec-field--deletion">
              <span className="spec-field__label">Does this need to exist?</span>
              <p className="spec-field__value">{spec.deletion_question_conclusion}</p>
            </div>
          )}

          <div className="spec-page__conformance">
            <h3 className="spec-page__conformance-title">Conformance contract</h3>
            <label className="spec-page__conformance-field">
              <span>Who's this for?</span>
              <select
                value={spec.declared_scope ?? ''}
                disabled={!editable}
                onChange={(e) => updateConformance.mutate({ declared_scope: e.target.value as DeclaredScope })}
              >
                <option value="" disabled>Choose one…</option>
                {DECLARED_SCOPES.map((s) => (
                  <option key={s} value={s}>{DECLARED_SCOPE_LABEL[s]}</option>
                ))}
              </select>
            </label>
            <label className="spec-page__conformance-field">
              <span>What does it read from the digital thread?</span>
              <input
                defaultValue={spec.consumes ?? ''}
                disabled={!editable}
                placeholder="e.g. the project's phase and connected apps — or leave blank"
                onBlur={(e) => updateConformance.mutate({ consumes: e.target.value })}
              />
            </label>
            <label className="spec-page__conformance-field">
              <span>What does it write back? ("nothing" is fine)</span>
              <input
                defaultValue={spec.emits ?? ''}
                disabled={!editable}
                placeholder={'e.g. a status tile other apps can read — or "nothing"'}
                onBlur={(e) => updateConformance.mutate({ emits: e.target.value })}
              />
            </label>
          </div>

          <div className="spec-page__actions">
            {spec.status === 'draft' && (
              <button
                className="am-btn am-btn--primary"
                onClick={() => submitForReview.mutate()}
                disabled={submitForReview.isPending}
              >
                Submit for review
              </button>
            )}
            {spec.status === 'in_review' && (
              <button className="am-btn am-btn--primary" onClick={() => publish.mutate()} disabled={publish.isPending}>
                Publish
              </button>
            )}
            {submitForReview.isError && (
              <p className="spec-page__action-error">{(submitForReview.error as Error).message}</p>
            )}
          </div>
        </section>
      </div>
    </div>
  )
}

function SpecField({ label, value, multiline }: { label: string; value: string | null; multiline?: boolean }) {
  return (
    <div className="spec-field">
      <span className="spec-field__label">{label}</span>
      {value ? (
        <p className={`spec-field__value ${multiline ? 'spec-field__value--multiline' : ''}`}>{value}</p>
      ) : (
        <p className="spec-field__value spec-field__value--empty">not yet known</p>
      )}
    </div>
  )
}
