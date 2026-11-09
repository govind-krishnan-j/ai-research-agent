import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import './style.css'
import './motion.css'
import './launchpad.css'

type ResearchResult = { topic: string; report: string; sources: string[] }
type View = 'home' | 'about'

const suggestions = [
  'The future of renewable energy',
  'AI in healthcare',
  'Ocean conservation',
]

const API = '/api'

function Icon({ name, size = 20 }: { name: string; size?: number }) {
  const common = { width: size, height: size, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 1.8, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const, 'aria-hidden': true as const }
  const paths: Record<string, React.ReactNode> = {
    search: <><circle cx="10.8" cy="10.8" r="6.8" /><path d="m16 16 4.7 4.7" /></>,
    arrow: <><path d="M4 12h16" /><path d="m14 6 6 6-6 6" /></>,
    document: <><path d="M6 3h9l4 4v14H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z" /><path d="M14 3v5h5M8 13h8M8 17h6" /></>,
    book: <><path d="M12 6C9.5 4.7 6.7 4.6 3 5v14c3.7-.4 6.5-.3 9 1 2.5-1.3 5.3-1.4 9-1V5c-3.7-.4-6.5-.3-9 1Z" /><path d="M12 6v14" /></>,
    spark: <><path d="m12 2 1.8 6.2L20 10l-6.2 1.8L12 18l-1.8-6.2L4 10l6.2-1.8L12 2ZM19 18l.6 1.4L21 20l-1.4.6L19 22l-.6-1.4L17 20l1.4-.6L19 18Z" /></>,
    clock: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
    external: <><path d="M13 5h6v6M19 5l-9 9" /><path d="M19 14v5H5V5h5" /></>,
    download: <><path d="M12 3v12m-4-4 4 4 4-4M4 18v3h16v-3" /></>,
    close: <><path d="M5 5 19 19M19 5 5 19" /></>,
    menu: <><path d="M4 7h16M4 12h16M4 17h16" /></>,
  }
  return <svg {...common}>{paths[name]}</svg>
}

function Logo() {
  return <div className="logo" aria-label="Research Atlas">
    <span className="logo-mark"><span className="logo-orbit" /><span className="logo-center" /></span>
    <span className="logo-word">research<span>atlas</span><span className="logo-dot">.</span></span>
  </div>
}

const researchTracks = [
  { name: 'Technology', symbol: '⌘', title: 'Beyond the next breakthrough.', question: 'How are AI agents changing the way software is built?', angles: ['Emerging tools', 'Practical applications', 'Current limitations'] },
  { name: 'Science', symbol: '✳', title: 'Big questions. New frontiers.', question: 'What are the biggest challenges in making fusion energy practical?', angles: ['Recent research', 'Engineering challenges', 'Future outlook'] },
  { name: 'Climate', symbol: '↗', title: 'A changing world, explained.', question: 'How can cities reduce the urban heat island effect?', angles: ['Causes and evidence', 'Real-world approaches', 'Trade-offs'] },
  { name: 'Business', symbol: '▥', title: 'Understand what moves markets.', question: 'How is the circular economy changing product design?', angles: ['Business models', 'Industry examples', 'Barriers to adoption'] },
]

function ResearchLaunchpad({ onChoose, disabled }: { onChoose: (question: string) => void; disabled: boolean }) {
  const [selected, setSelected] = useState(0)
  const track = researchTracks[selected]
  return <section className="launchpad reveal" aria-label="Research launchpad">
    <div className="launchpad-heading"><span>THE RESEARCH LAUNCHPAD</span><h2>Pick a direction.<br /><em>Go somewhere new.</em></h2><p>Start with a question worth exploring.</p></div>
    <div className="launchpad-layout">
      <div className="launchpad-tracks" aria-label="Choose a subject">{researchTracks.map((item, index) => <button key={item.name} className={selected === index ? 'selected' : ''} aria-pressed={selected === index} onClick={() => setSelected(index)}><span className="track-number">0{index + 1}</span><strong>{item.name}</strong><span className="track-arrow">↗</span></button>)}</div>
      <div className="launchpad-brief" aria-live="polite"><div className="brief-watermark" aria-hidden="true">{track.symbol}</div><div className="brief-label">{track.name.toUpperCase()} / QUESTION STARTER</div><h3>{track.title}</h3><div className="brief-question"><Icon name="search" size={20} /><p>{track.question}</p></div><div className="brief-angles">{track.angles.map(angle => <span key={angle}>{angle}</span>)}</div><button className="brief-cta" disabled={disabled} onClick={() => onChoose(track.question)}>Use this question <Icon name="arrow" size={19} /></button></div>
    </div>
  </section>
}

function App() {
  const [topic, setTopic] = useState('')
  const [result, setResult] = useState<ResearchResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [pdfLoading, setPdfLoading] = useState(false)
  const [error, setError] = useState('')
  const [history, setHistory] = useState<string[]>(() => {
    try { return JSON.parse(localStorage.getItem('research-atlas-topics') || '[]') } catch { return [] }
  })
  const [view, setView] = useState<View>('home')
  const [menuOpen, setMenuOpen] = useState(false)
  const [workspaceCollapsed, setWorkspaceCollapsed] = useState(() => localStorage.getItem('research-atlas-workspace-collapsed') === 'true')

  useEffect(() => { localStorage.setItem('research-atlas-topics', JSON.stringify(history)) }, [history])
  useEffect(() => { localStorage.setItem('research-atlas-workspace-collapsed', String(workspaceCollapsed)) }, [workspaceCollapsed])
  useEffect(() => {
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (reduceMotion) return
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible')
          observer.unobserve(entry.target)
        }
      })
    }, { threshold: 0.12 })
    document.querySelectorAll('.reveal').forEach(element => observer.observe(element))
    return () => observer.disconnect()
  }, [view, result, loading])

  async function research(nextTopic = topic) {
    const clean = nextTopic.trim()
    if (clean.length < 2) { setError('Enter a topic with at least two characters.'); return }
    setTopic(clean)
    setView('home')
    setResult(null)
    setError('')
    setLoading(true)
    setMenuOpen(false)
    try {
      const response = await fetch(`${API}/research`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic: clean }),
      })
      const data = await response.json()
      if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Research failed. Please try again.')
      setResult(data as ResearchResult)
      setHistory(previous => [clean, ...previous.filter(item => item.toLowerCase() !== clean.toLowerCase())].slice(0, 6))
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not connect to the research server.')
    } finally { setLoading(false) }
  }

  async function downloadPdf() {
    if (!result) return
    setPdfLoading(true)
    setError('')
    try {
      const response = await fetch(`${API}/pdf`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic: result.topic, content: result.report, sources: result.sources }),
      })
      if (!response.ok) throw new Error('Could not create the PDF. Please try again.')
      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${result.topic.toLowerCase().replace(/[^a-z0-9]+/g, '_').slice(0, 60)}_report.pdf`
      link.click()
      URL.revokeObjectURL(url)
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Could not create the PDF.') }
    finally { setPdfLoading(false) }
  }

  function downloadText() {
    if (!result) return
    const sources = result.sources.length ? `\n\nSources\n${result.sources.map((url, i) => `${i + 1}. ${url}`).join('\n')}` : ''
    const blob = new Blob([`${result.topic}\n\n${result.report}${sources}`], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${result.topic.toLowerCase().replace(/[^a-z0-9]+/g, '_').slice(0, 60)}_report.txt`
    link.click()
    URL.revokeObjectURL(url)
  }

  const wordCount = result?.report.trim().split(/\s+/).length ?? 0

  return <div className={`app-shell ${workspaceCollapsed ? 'workspace-collapsed' : ''}`}>
    <aside className={`sidebar ${menuOpen ? 'sidebar-open' : ''}`} inert={workspaceCollapsed && !menuOpen}>
      <div className="sidebar-top">
        <Logo />
        <button className="mobile-close icon-button" onClick={() => setMenuOpen(false)} aria-label="Close menu"><Icon name="close" /></button>
      </div>
      <div className="workspace-label">WORKSPACE</div>
      <nav className="nav-list" aria-label="Main navigation">
        <button className={`nav-item ${view === 'home' ? 'active' : ''}`} onClick={() => { setView('home'); setMenuOpen(false) }}><Icon name="search" size={18} /> Research <span className="nav-arrow">↗</span></button>
        <button className={`nav-item ${view === 'about' ? 'active' : ''}`} onClick={() => { setView('about'); setMenuOpen(false) }}><Icon name="book" size={18} /> How it works</button>
      </nav>
      <div className="sidebar-divider" />
      <div className="history-heading"><span>RECENT TOPICS</span><span>{history.length ? String(history.length).padStart(2, '0') : ''}</span></div>
      {history.length ? <div className="history-list">{history.map(item => <button key={item} onClick={() => research(item)} disabled={loading} title={item}><Icon name="clock" size={16} /><span>{item}</span></button>)}</div> : <p className="history-empty">Your research topics will appear here.</p>}
      <div className="sidebar-bottom">
        <div className="sidebar-status"><span className="status-pulse" /> SYSTEM READY</div>
        <p>Curiosity deserves better answers.</p>
      </div>
    </aside>

    {menuOpen && <button className="mobile-scrim" aria-label="Close menu" onClick={() => setMenuOpen(false)} />}

    <main className="main-panel">
      <div className="page-grid" aria-hidden="true" />
      <div className="page-glow" aria-hidden="true" />
      <header className="topbar">
        <div className="topbar-left">
          <button className="mobile-menu icon-button" onClick={() => setMenuOpen(true)} aria-label="Open menu"><Icon name="menu" /></button>
          <button className="workspace-toggle icon-button" onClick={() => setWorkspaceCollapsed(value => !value)} aria-label={workspaceCollapsed ? 'Expand workspace' : 'Collapse workspace'} aria-expanded={!workspaceCollapsed} title={workspaceCollapsed ? 'Expand workspace' : 'Collapse workspace'}><Icon name="menu" size={20} /></button>
          <div className="breadcrumb"><span>WORKSPACE</span><span className="slash">/</span><strong>{view === 'about' ? 'How it works' : result ? 'Research report' : 'New research'}</strong></div>
        </div>
        <div className="topbar-right"><span className="topbar-indicator" /> AI RESEARCH ASSISTANT <span className="topbar-version">V1.0</span></div>
      </header>

      {view === 'about' ? <section className="about-page content-width">
        <div className="eyebrow"><span /> BEHIND THE RESEARCH</div>
        <h1>From question to <em>clarity.</em></h1>
        <p className="hero-copy">Research Atlas uses an AI agent to search the web, read relevant pages, and assemble a structured report. Sources appear alongside the finished work so you can inspect them yourself.</p>
        <div className="about-grid reveal">
          <div><span className="step-number">01</span><Icon name="search" /><h3>Search</h3><p>The agent looks for relevant pages on your topic.</p></div>
          <div><span className="step-number">02</span><Icon name="book" /><h3>Read</h3><p>It extracts text from selected sources.</p></div>
          <div><span className="step-number">03</span><Icon name="spark" /><h3>Synthesize</h3><p>It writes a report based on what it gathered.</p></div>
        </div>
        <button className="primary-button" onClick={() => setView('home')}>Start researching <Icon name="arrow" size={18} /></button>
      </section> : result ? <section className="result-page content-width">
        <div className="result-heading"><div><div className="eyebrow"><span /> RESEARCH COMPLETE</div><h1>{result.topic}</h1><div className="result-meta"><span><Icon name="document" size={16} /> {wordCount} words</span><span><Icon name="clock" size={16} /> ~{Math.max(1, Math.round(wordCount / 200))} min read</span><span><Icon name="book" size={16} /> {result.sources.length} sources</span></div></div></div>
        <div className="result-actions"><button className="subtle-button" onClick={() => { setResult(null); setTopic('') }}>+ New research</button><button className="subtle-button" onClick={downloadText}><Icon name="download" size={17} /> Text</button><button className="primary-button" onClick={downloadPdf} disabled={pdfLoading}><Icon name="download" size={17} /> {pdfLoading ? 'Preparing…' : 'Download PDF'}</button></div>
        {error && <div className="alert" role="alert">{error}</div>}
        <div className="report-grid reveal"><article className="report-card"><div className="card-overline">THE REPORT <span>✦</span></div><div className="markdown"><ReactMarkdown remarkPlugins={[remarkGfm]}>{result.report}</ReactMarkdown></div></article><aside className="sources-card"><div className="card-overline">SOURCE MATERIAL <span>{String(result.sources.length).padStart(2, '0')}</span></div>{result.sources.length ? result.sources.map((url, i) => { let host = url; try { host = new URL(url).hostname.replace(/^www\./, '') } catch { /* show original */ } return <a key={`${url}-${i}`} href={/^https?:\/\//i.test(url) ? url : '#'} target="_blank" rel="noopener noreferrer"><span className="source-number">{String(i + 1).padStart(2, '0')}</span><span className="source-info"><strong>{host}</strong><small>{url}</small></span><Icon name="external" size={16} /></a> }) : <p className="no-sources">No readable sources were returned. Review this report carefully.</p>}<p className="sources-note">Open the original pages to verify important claims.</p></aside></div>
      </section> : <section className="home-page content-width">
        <div className="hero-research" aria-hidden="true"><div className="hero-research-head"><span><span className="hero-research-live" /> AGENT WORKFLOW</span><span>RUN / 001</span></div><div className="hero-query"><Icon name="search" size={19} /><span>YOUR QUESTION</span><strong>Where could this lead?</strong></div><div className="hero-flow"><div className="hero-flow-line" /><div className="hero-flow-step"><span className="hero-flow-icon"><Icon name="search" size={17} /></span><div><small>01 / DISCOVER</small><strong>Search the web</strong><i className="hero-flow-bar bar-one" /></div><b>↗</b></div><div className="hero-flow-step"><span className="hero-flow-icon"><Icon name="book" size={17} /></span><div><small>02 / VERIFY</small><strong>Read source pages</strong><i className="hero-flow-bar bar-two" /></div><b>↗</b></div><div className="hero-flow-step"><span className="hero-flow-icon"><Icon name="spark" size={17} /></span><div><small>03 / CONNECT</small><strong>Synthesize findings</strong><i className="hero-flow-bar bar-three" /></div><b>↗</b></div></div><div className="hero-output"><div><span>✳ REPORT READY</span><strong>Answers with sources.</strong></div><Icon name="document" size={24} /></div><div className="hero-research-foot"><span>SEARCH → READ → WRITE</span><span>AI RESEARCH ASSISTANT</span></div></div>
        <div className="hero"><div className="eyebrow"><span /> RESEARCH WITHOUT LIMITS</div><h1>CHASE THE<br /><em>UNKNOWN.</em></h1><p className="hero-copy">One thought can take you anywhere. Give it a direction, and let the agent search, read, and connect the dots.</p><a className="scroll-cue" href="#research-input"><span>SCROLL TO EXPLORE</span><span className="scroll-cue-line" /></a></div>
        <div className="research-box reveal" id="research-input"><div className="research-box-top"><div><span className="input-kicker">01 / START WITH A QUESTION</span><h2>What’s on your mind?</h2></div><span className="box-spark">✳</span></div><form onSubmit={event => { event.preventDefault(); research() }}><label className="sr-only" htmlFor="topic">Research topic</label><div className="input-row"><Icon name="search" size={21} /><input id="topic" value={topic} onChange={event => setTopic(event.target.value)} placeholder="Enter a topic, question, or idea..." maxLength={300} disabled={loading} autoFocus /><button type="submit" disabled={loading || topic.trim().length < 2}><span>{loading ? 'Researching…' : 'Start research'}</span><Icon name="arrow" size={18} /></button></div></form>{error && <div className="alert" role="alert">{error}</div>}<div className="suggestion-row"><span>TRY AN IDEA</span>{suggestions.map(item => <button key={item} onClick={() => { setTopic(item); research(item) }} disabled={loading}>{item}<span>↗</span></button>)}</div></div>
        {loading ? <div className="working-card" role="status"><span className="working-spinner" /><div><strong>Research in progress</strong><p>The agent is searching and reading sources. This may take a minute.</p></div></div> : null}
        <ResearchLaunchpad disabled={loading} onChoose={question => { setTopic(question); document.getElementById('topic')?.focus({ preventScroll: true }); document.getElementById('research-input')?.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block: 'center' }) }} />
        <div className="feature-section" id="how-it-works"><div className="section-heading reveal"><span>02 / HOW IT WORKS</span><h2>More than a search.<br /><em>A clearer picture.</em></h2></div><div className="feature-grid"><div className="feature-card reveal"><div className="feature-icon"><Icon name="search" /></div><span>01 / DISCOVER</span><h3>Explore broadly</h3><p>Relevant web results give the agent a starting point for your topic.</p></div><div className="feature-card reveal"><div className="feature-icon"><Icon name="book" /></div><span>02 / UNDERSTAND</span><h3>Read the sources</h3><p>The agent extracts useful context from selected pages before writing.</p></div><div className="feature-card reveal"><div className="feature-icon"><Icon name="document" /></div><span>03 / CONNECT</span><h3>Get the full story</h3><p>Receive a structured report with source links and PDF export.</p></div></div></div>
      </section>}
      <footer className="footer"><span>© {new Date().getFullYear()} RESEARCH ATLAS</span><span>AN IDEA CAN TAKE YOU ANYWHERE <span className="footer-star">✳</span></span></footer>
    </main>
  </div>
}

createRoot(document.getElementById('root')!).render(<React.StrictMode><App /></React.StrictMode>)
