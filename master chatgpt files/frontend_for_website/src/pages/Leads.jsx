import {useEffect,useState} from "react";
import {Download} from "lucide-react";
import api from "../services/api";
import {downloadFile} from "../services/download";

const errText=err=>{const d=err.response?.data?.detail;return typeof d==="string"?d:err.message||"Request failed.";};

export default function Leads(){
 const [tab,setTab]=useState("deliveries");
 const [contacts,setContacts]=useState([]),[deliveries,setDeliveries]=useState([]);
 const [error,setError]=useState("");
 useEffect(()=>{
  api.get("/api/leads/contacts").then(({data})=>setContacts(data.items)).catch(e=>setError(errText(e)));
  api.get("/api/leads/deliveries").then(({data})=>setDeliveries(data.items)).catch(e=>setError(errText(e)));
 },[]);

 return <>
  <div className="page-heading"><div><p className="eyebrow">CUSTOMERS</p><h1>Leads & Customers</h1>
   <p className="muted">Everyone you have contacted, and exactly how each campaign message went.</p></div>
   <button className="primary dl" onClick={()=>downloadFile("/api/leads/export.xlsx","moseta_leads.xlsx").catch(e=>setError(errText(e)))}><Download size={15}/> Download Excel</button></div>
  <div className="tabs">
   <button className={tab==="deliveries"?"on":""} onClick={()=>setTab("deliveries")}>Campaign delivery log ({deliveries.length})</button>
   <button className={tab==="contacts"?"on":""} onClick={()=>setTab("contacts")}>Contacts ({contacts.length})</button>
  </div>
  <section className="panel">
   {error&&<div className="error">{error}</div>}
   <div style={{overflowX:"auto"}}>
   {tab==="deliveries"?
    (deliveries.length===0?<p className="muted">No campaign messages yet. Run a campaign from the Campaigns page.</p>:
    <table className="table"><thead><tr><th>Campaign</th><th>Name</th><th>Phone</th><th>Email</th><th>Channel</th><th>Status</th><th>Detail</th><th>Time (UTC)</th></tr></thead>
     <tbody>{deliveries.map(d=><tr key={d.id}><td>{d.campaign_name}</td><td>{d.name}</td><td>{d.phone}</td><td>{d.email}</td><td>{d.channel}</td>
      <td><span className={`badge ${d.status}`}>{d.status.replace("_"," ")}</span></td><td className="muted">{d.detail}</td><td>{d.sent_at}</td></tr>)}</tbody></table>)
   :
    (contacts.length===0?<p className="muted">No contacts yet. They are added automatically when you upload a contact sheet.</p>:
    <table className="table"><thead><tr><th>ID</th><th>Name</th><th>Phone</th><th>Email</th><th>Source</th><th>Added</th></tr></thead>
     <tbody>{contacts.map(c=><tr key={c.id}><td>{c.id}</td><td>{c.customer_name}</td><td>{c.phone}</td><td>{c.email}</td><td>{c.source}</td><td>{c.created_at}</td></tr>)}</tbody></table>)}
   </div>
  </section>
 </>;
}
