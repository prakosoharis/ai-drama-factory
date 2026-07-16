import Link from 'next/link'; import {api,Project} from '../lib/api';
export default async function Home(){const projects=await api<Project[]>('/api/projects');return <><p>Local control plane for project metadata, review, and deterministic assembly.</p><h2>Projects</h2>{projects.map(p=><div className="card" key={p.id}><Link href={`/projects/${p.id}`}>{p.name}</Link></div>)}</>}
