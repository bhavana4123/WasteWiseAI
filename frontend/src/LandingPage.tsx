import { useEffect, useState } from 'react'
import { ArrowDown, ArrowUpRight, BarChart3, Check, Cog, Leaf, Menu, Recycle, X } from 'lucide-react'
import './landing.css'

const features = [
  { icon: Recycle, title: 'Explore Materials', description: 'Discover waste sources and their locations throughout the circular city.' },
  { icon: Cog, title: 'Understand Pathways', description: 'Explore documented conversion technologies and scientific operating studies.' },
  { icon: BarChart3, title: 'See the Evidence', description: 'Understand supported numerical results, source references and limitations.' },
]
const pathways = [
  { label: 'PYROLYSIS', primary: 'Wood to', highlight: 'liquid product.', description: 'Published reference liquid-product yields, including water where documented.', footer: 'Reference mass accounting' },
  { label: 'GASIFICATION', primary: 'Wood chips to', highlight: 'producer gas.', description: 'Reference gas volume and chemical energy before any conversion to electricity.', footer: 'Reference energy accounting' },
  { label: 'SCIENTIFIC EVIDENCE', primary: 'Evidence before', highlight: 'estimates.', description: 'Published operating conditions, source traceability and transparent limitations.', footer: 'Traceable scientific references' },
]
const steps = [
  ['Discover', 'Explore waste locations across the miniature circular city.'],
  ['Select Waste', 'Choose a published waste subtype and enter the quantity.'],
  ['Choose a Study', 'Review available operating conditions and scientific references.'],
  ['Calculate', 'Run a supported reference calculation through the scientific engine.'],
  ['Understand Results', 'Inspect product quantity, units, sources and important limitations.'],
]
function Brand() {
  return <span className="ww-brand"><span className="ww-brand-icon"><Leaf size={23} strokeWidth={1.7} /></span><span>WasteWise<span className="ww-ai"> AI</span></span></span>
}
function ExploreLink({ children = 'Explore WasteWise', className = '' }: { children?: string; className?: string }) {
  return <a href="/simulation" className={`ww-button ${className}`}>{children}<ArrowUpRight size={19} aria-hidden="true" /></a>
}
function Heading({ primary, highlight, hero = false }: { primary: string; highlight: string; hero?: boolean }) {
  const content = <><span className="ww-primary">{primary}</span><span className="ww-highlight">{highlight}</span></>
  return hero ? <h1 className="ww-heading">{content}</h1> : <h2 className="ww-heading">{content}</h2>
}
export default function LandingPage() {
  const [menuOpen, setMenuOpen] = useState(false)
  useEffect(() => {
    // Optional typography enhancement: a failed external font request must
    // never prevent Vite from loading the landing page's local stylesheet.
    const font = document.createElement('link')
    font.rel = 'stylesheet'
    font.href = 'https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700&display=swap'
    document.head.appendChild(font)
    return () => font.remove()
  }, [])
  return <div className="ww-landing">
    <a className="ww-skip" href="#ww-main">Skip to content</a>
    <header className="ww-nav ww-container">
      <a href="/#home" aria-label="WasteWise AI home"><Brand /></a>
      <button className="ww-menu-toggle" aria-label={menuOpen ? 'Close navigation' : 'Open navigation'} aria-expanded={menuOpen} aria-controls="ww-navigation" onClick={() => setMenuOpen(!menuOpen)}>{menuOpen ? <X /> : <Menu />}</button>
      <nav id="ww-navigation" aria-label="Landing navigation" className={menuOpen ? 'is-open' : ''}>
        {[['Home', '#home'], ['3D City', '#city'], ['Pathways', '#pathways'], ['How It Works', '#how-it-works']].map(([label, href]) => <a key={href} href={href} onClick={() => setMenuOpen(false)}>{label}</a>)}
        <ExploreLink>Explore</ExploreLink>
      </nav>
    </header>
    <main id="ww-main" className="ww-main">
      <section id="home" className="ww-hero ww-container">
        <span className="ww-eyebrow"><span className="ww-dot" />THE CIRCULAR CITY LAB</span>
        <Heading hero primary="Waste is not the end." highlight="It's the beginning." />
        <p className="ww-hero-description">Discover how everyday waste can become valuable resources through interactive 3D exploration and evidence-backed scientific reference calculations.</p>
        <div className="ww-actions"><ExploreLink /><a href="#how-it-works" className="ww-button ww-secondary">How It Works<ArrowDown size={18} aria-hidden="true" /></a></div>
        <div className="ww-trust">{['Interactive 3D', 'Published Research', 'Traceable Results'].map(text => <span key={text}><Check size={14} aria-hidden="true" />{text}</span>)}</div>
        <div className="ww-hero-coordinate" aria-hidden="true">A BETTER WAY TO SEE WASTE / EST. 2026</div>
      </section>
      <section className="ww-features ww-container" aria-label="Explore, understand, and see the evidence">
        {features.map(({ icon: Icon, title, description }, i) => <article className="ww-card ww-feature" key={title}><span className={`ww-sticker ww-sticker-${i}`}><Icon size={60} strokeWidth={1.7} aria-hidden="true" /></span><h3 className="ww-highlight">{title}</h3><p>{description}</p><span className="ww-card-index" aria-hidden="true">0{i + 1}</span></article>)}
      </section>
      <section id="city" className="ww-section ww-container">
        <div className="ww-section-top"><div><span className="ww-eyebrow">01 / INTERACTIVE CITY</span><Heading primary="A whole city." highlight="A new perspective." /></div><p className="ww-section-description">Explore waste sources and follow their conceptual journey from collection to conversion.</p></div>
        <a href="/simulation" className="ww-city-preview" aria-label="Open the existing interactive 3D circular city"><img src="/city-preview.png" width="1280" height="720" alt="The real WasteWise miniature city with paddy fields, a food market, warehouses, timber yard and central processing hub" loading="lazy" /><span className="ww-preview-label"><span className="ww-dot" />YOUR NEXT PERSPECTIVE</span><span className="ww-preview-open"><ArrowUpRight size={25} /></span></a>
        <div className="ww-city-caption"><p>A miniature world. Real scientific references.<span>Preview of the existing city · Open the simulation to interact</span></p><ExploreLink className="ww-secondary">Explore the 3D City</ExploreLink></div>
      </section>
      <section id="pathways" className="ww-section ww-container">
        <span className="ww-eyebrow">02 / CONVERSION PATHWAYS</span><Heading primary="Different technologies." highlight="Documented possibilities." />
        <div className="ww-pathways">{pathways.map((pathway, i) => <article className="ww-card ww-pathway" key={pathway.label}><div className="ww-pathway-label"><span className="ww-eyebrow">{pathway.label}</span><span aria-hidden="true">0{i + 1}</span></div><h3><span className="ww-primary">{pathway.primary}</span><span className="ww-highlight">{pathway.highlight}</span></h3><p>{pathway.description}</p><a href="/simulation" className="ww-pathway-footer">{pathway.footer}<ArrowUpRight size={17} aria-hidden="true" /></a></article>)}</div>
      </section>
      <section id="how-it-works" className="ww-section ww-container ww-process">
        <span className="ww-eyebrow">03 / HOW IT WORKS</span><Heading primary="From curiosity" highlight="to understanding." />
        <ol className="ww-steps">{steps.map(([title, description], i) => <li key={title}><span className="ww-step-number">0{i + 1}</span><h3 className="ww-highlight">{title}</h3><p>{description}</p><ArrowUpRight className="ww-step-arrow" size={23} aria-hidden="true" /></li>)}</ol>
      </section>
      <section className="ww-container ww-cta-wrap"><div className="ww-cta"><span className="ww-eyebrow">READY TO EXPLORE?</span><Heading primary="Give waste" highlight="a new beginning." /><p>Discover what published scientific evidence can tell us about waste conversion.</p><ExploreLink /><span className="ww-cta-orbit" aria-hidden="true"><Recycle /></span></div></section>
    </main>
    <footer className="ww-footer ww-container"><div className="ww-footer-top"><div><a href="#home" aria-label="WasteWise AI home"><Brand /></a><p>The Circular City Lab</p><p>Explore. Simulate. Understand.</p></div><p>Interactive 3D · Scientific references · Transparent results</p></div><div className="ww-footer-bottom"><span>© {new Date().getFullYear()} WasteWise AI</span><p>Reference calculations are not validated plant-performance predictions.</p><a href="#home">Back to top ↑</a></div></footer>
  </div>
}
