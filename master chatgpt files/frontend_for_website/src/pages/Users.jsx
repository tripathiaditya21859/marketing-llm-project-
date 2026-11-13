import {useEffect,useState} from "react";
import {Download} from "lucide-react";
import api from "../services/api";
import {downloadFile} from "../services/download";

export default function Users(){
 const [rows,setRows]=useState([]),[error,setError]=useState(""),[loading,setLoading]=useState(true);
 useEffect(()=>{
  api.get("/api/admin/users").then(({data})=>setRows(data.items))
   .catch(err=>{const d=err.response?.data?.detail;setError(typeof d==="string"?d:err.message);})
   .finally(()=>setLoading(false));
 },[]);
 return <>
  <div className="page-heading"><div><p className="eyebrow">ACCOUNTS</p><h1>Users</h1>
   <p className="muted">Everyone registered on the portal. Passwords are stored encrypted and never shown.</p></div>
   <div style={{display:"flex",gap:10,alignItems:"center"}}>
    <span className="pill">{rows.length} user{rows.length===1?"":"s"}</span>
    <button className="primary dl" onClick={()=>downloadFile("/api/admin/export.xlsx","moseta_accounts.xlsx").catch(e=>setError(e.response?.statusText||e.message))}><Download size={15}/> Download Excel</button>
   </div></div>
  <section className="panel">
   {error&&<div className="error">{error}</div>}
   {loading?<p className="muted">Loading…</p>:
   <div style={{overflowX:"auto"}}><table className="table">
    <thead><tr><th>ID</th><th>Name</th><th>Email</th><th>Password</th><th>Role</th><th>Company</th><th>Status</th><th>Joined</th></tr></thead>
    <tbody>{rows.map(u=><tr key={u.id}>
     <td>{u.id}</td><td>{u.full_name}</td><td>{u.email}</td><td>••••••••</td><td>{u.role}</td><td>{u.company_name||"—"}</td><td>{u.status}</td><td>{u.created_at}</td>
    </tr>)}</tbody>
   </table></div>}
  </section>
 </>;
}
