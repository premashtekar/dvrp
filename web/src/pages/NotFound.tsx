import { Link } from 'react-router-dom'; import { PageHead } from '../shared/Layout';
export function NotFound(){return <section className="panel empty"><PageHead title="Page not found"><p className="page-subtitle">This route is not part of the research interface.</p></PageHead><Link className="button primary" to="/overview">Return to overview</Link></section>}
