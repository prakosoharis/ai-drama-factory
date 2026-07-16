export type Project={id:string;name:string};
const base=process.env.DRAMA_FACTORY_API_INTERNAL_URL || process.env.NEXT_PUBLIC_DRAMA_FACTORY_API_URL || 'http://localhost:8000';
export async function api<T>(path:string, init?:RequestInit):Promise<T>{const r=await fetch(base+path,{...init,cache:'no-store',headers:{'content-type':'application/json',...(init?.headers||{})}});if(!r.ok)throw new Error(await r.text());return r.json()}
