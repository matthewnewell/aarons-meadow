import { Link } from 'react-router-dom'
import Nav from '../components/Nav'
import './SplashPage.css'

const FEATURES = [
  {
    title: 'A place, not a tool',
    body: "You walk into the meadow and work. No blank code editor, no framework to pick — just a conversation, one question at a time, that ends in something a developer can actually build from.",
  },
  {
    title: 'The spec assembles as you talk',
    body: 'Conversation on one side, the spec filling in on the other — you watch the artifact form instead of being handed one at the end. Nothing here writes code for you; the handoff to a developer is a human one.',
  },
  {
    title: 'Pushback is part of the interview',
    body: "If what you describe is really two apps, the meadow says so. And early on, once, it asks whether this needs to exist at all — or whether it's really a process that should just be deleted. An app store full of digitized bad processes is worse than an empty one.",
  },
]

export default function SplashPage() {
  return (
    <div className="splash-page">
      <Nav />
      <div className="splash-page__scroll">
        <div className="splash-page__content">
          <header className="splash-hero">
            <h1 className="splash-hero__title">Aaron's Meadow</h1>
            <p className="splash-hero__sub">
              Where you work out what you actually want to build, before anyone writes a line
              of code.
            </p>
            <div className="splash-hero__actions">
              <Link className="am-btn am-btn--primary" to="/">
                Go to the workbench →
              </Link>
            </div>
          </header>

          <section className="splash-features">
            {FEATURES.map((f) => (
              <article className="splash-feature" key={f.title}>
                <h3 className="splash-feature__title">{f.title}</h3>
                <p className="splash-feature__body">{f.body}</p>
              </article>
            ))}
          </section>

          <section className="splash-note">
            <p>
              A spec moves from <strong>Draft</strong> (still being interviewed) to{' '}
              <strong>In Review</strong> to <strong>Published</strong> — only a published spec
              shows up in Conway's Depot's own catalog, registered automatically the moment it
              publishes. The workbench, where drafts and in-review specs live, is yours alone;
              the Depot never sees anything short of finished.
            </p>
          </section>
        </div>
      </div>
    </div>
  )
}
