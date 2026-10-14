import { Link } from "react-router-dom";

export function LogoMark({ size = 22 }) {
  return (
    <svg className="logo-mark" viewBox="0 0 24 24" width={size} height={size} fill="none" aria-hidden="true">
      <rect x="3.5" y="2.5" width="17" height="19" rx="1.5" stroke="currentColor" strokeWidth="1.6" />
      <path d="M7.5 7.5h6M7.5 11h6M7.5 14.5h4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      <path d="M16.5 6.5v11" stroke="var(--rubric)" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

/** The wordmark. Pass `to` to make it a link (it is a plain label by default). */
export default function Brand({ to }) {
  const content = (
    <>
      <LogoMark />
      <span className="brand-name">Paper-Mind</span>
    </>
  );
  return to ? (
    <Link to={to} className="brand" aria-label="Paper-Mind home">
      {content}
    </Link>
  ) : (
    <span className="brand">{content}</span>
  );
}
