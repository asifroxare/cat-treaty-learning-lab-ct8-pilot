import "./FoundationPage.css";

interface FoundationPageProps {
  eyebrow: string;
  title: string;
  description: string;
}

export function FoundationPage({ eyebrow, title, description }: FoundationPageProps) {
  return (
    <section className="foundation-page" aria-labelledby="foundation-title">
      <p className="page-eyebrow">{eyebrow}</p>
      <h1 id="foundation-title">{title}</h1>
      <p className="page-lede">{description}</p>
      <div className="checkpoint-note">
        <p className="checkpoint-label">Foundation checkpoint</p>
        <p>This destination is routed and ready. Its treaty workflow is intentionally deferred to the next frozen checkpoint.</p>
      </div>
    </section>
  );
}
