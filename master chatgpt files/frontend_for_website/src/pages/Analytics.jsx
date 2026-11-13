import {useEffect,useState} from "react";
import api from "../services/api";

export default function Analytics(){
 const [d,setD]=useState(null),[error,setError]=useState("");
 useEffect(()=>{api.get("/api/analytics").then(({data})=>setD(data)).catch(e=>setError(e.response?.data?.detail||e.message));},[]);
 if(error)return <div className="error">{error}</div>;
 if(!d)return <p className="muted">Loading…</p>;
 const t=d.totals,max=Math.max(1,...d.per_day.map(x=>x.messages));
 const cards=[["Campaigns",t.campaigns],["Contacts",t.contacts],["Messages sent",t.messages_sent],["Failed",t.messages_failed],
  ["Delivery rate",t.delivery_rate==null?"—":`${t.delivery_rate}%`],["AI chats",t.ai_chats],["Knowledge items",t.knowledge_items]];
 return <>
  <div className="page-heading"><div><p className="eyebrow">PERFORMANCE</p><h1>Analytics</h1>
   <p className="muted">{d.scope==="platform"?"Platform-wide numbers across all companies.":`Your company's numbers, ${d.user}.`}</p></div></div>
  <section className="stats" style={{gridTemplateColumns:"repeat(4,1fr)"}}>
   {cards.map(([l,v])=><article className="stat" key={l}><div>{l}</div><strong>{v}</strong></article>)}
  </section>
  <section className="dash-grid">
   <article className="panel"><h3>Messages per day (last 14 days)</h3>
    {d.per_day.length===0?<p className="muted">No messages sent yet.</p>:
     <div className="bars">{d.per_day.map(x=><div key={x.day} className="bar-col" title={`${x.day}: ${x.messages}`}>
      <div className="bar" style={{height:`${Math.round(100*x.messages/max)}%`}}/><small>{x.day.slice(5)}</small></div>)}</div>}
   </article>
   <article className="panel"><h3>By channel</h3>
    {d.by_channel.length===0?<p className="muted">No campaigns yet.</p>:
     <table className="table"><thead><tr><th>Channel</th><th>Sent</th><th>Failed</th><th>Not sent</th></tr></thead>
      <tbody>{d.by_channel.map(c=><tr key={c.channel}><td>{c.channel}</td><td>{c.sent||0}</td><td>{c.failed||0}</td><td>{c.not_sent||0}</td></tr>)}</tbody></table>}
   </article>
  </section>
  <section className="panel" style={{marginTop:16}}><h3>Recent campaigns</h3>
   {d.recent_campaigns.length===0?<p className="muted">Nothing yet.</p>:
    <table className="table"><thead><tr><th>Name</th><th>Channel</th><th>Status</th><th>Contacts</th><th>Sent</th><th>Failed</th><th>Created</th></tr></thead>
     <tbody>{d.recent_campaigns.map(c=><tr key={c.id}><td>{c.campaign_name}</td><td>{c.channel}</td><td><span className={`badge ${c.status}`}>{c.status.replace("_"," ")}</span></td>
      <td>{c.total_recipients}</td><td>{c.sent||0}</td><td>{c.failed||0}</td><td>{c.created_at}</td></tr>)}</tbody></table>}
  </section>
 </>;
}
