import {useEffect,useState} from "react";
import {Download} from "lucide-react";
import api from "../services/api";
import DropZone from "../components/DropZone";
import {downloadFile} from "../services/download";
import {ChannelPicker,CHANNEL_UI} from "../components/channels";
import {Link} from "react-router-dom";

const errText=err=>{const d=err.response?.data?.detail;return typeof d==="string"?d:Array.isArray(d)?d.map(x=>x.msg).join(" "):err.message||"Request failed.";};

export default function Campaigns(){
 const [channels,setChannels]=useState([]),[list,setList]=useState([]);
 const [name,setName]=useState(""),[channel,setChannel]=useState("whatsapp"),[subject,setSubject]=useState("");
 const [message,setMessage]=useState(""),[cc,setCc]=useState("+91"),[consent,setConsent]=useState(false);
 const [files,setFiles]=useState([]);
 const [busy,setBusy]=useState(false),[error,setError]=useState(""),[ok,setOk]=useState("");

 const load=()=>{
  api.get("/api/campaigns/channels").then(({data})=>setChannels(data.channels)).catch(()=>{});
  api.get("/api/campaigns").then(({data})=>setList(data.items)).catch(e=>setError(errText(e)));
 };
 useEffect(()=>{load();},[]);
 const current=channels.find(c=>c.id===channel);

 async function submit(e){
  e.preventDefault();setError("");setOk("");
  if(!files.length)return setError("Attach the Excel sheet with your contacts.");
  const form=new FormData();
  form.append("name",name);form.append("channel",channel);form.append("message",message);
  form.append("subject",subject);form.append("country_code",cc);form.append("consent",consent);
  form.append("file",files[0]);
  setBusy(true);
  try{
   const {data}=await api.post("/api/campaigns",form,{headers:{"Content-Type":"multipart/form-data"}});
   setOk(`${data.message} ${data.valid} valid contact(s), ${data.skipped} skipped.`);
   setName("");setMessage("");setSubject("");setFiles([]);setConsent(false);load();
  }catch(err){setError(errText(err));}finally{setBusy(false);}
 }

 return <>
  <div className="page-heading"><div><p className="eyebrow">MARKETING</p><h1>Campaigns</h1>
   <p className="muted">Upload your contact sheet, choose where to send, and run the campaign.</p></div></div>

  <section className="panel">
   <h3>New campaign</h3>
   <form onSubmit={submit} className="form-grid">
    <div className="field"><label>Campaign name</label>
     <input value={name} onChange={e=>setName(e.target.value)} required minLength={2} maxLength={120} placeholder="e.g. Diwali offer"/></div>
    <div className="field"><label>Send through</label>
     <ChannelPicker channels={channels} value={channel} onChange={setChannel}/></div>
    {current&&!current.configured&&<div className="warn">{CHANNEL_UI[current.id]?.name||current.label} is not connected yet. You can still save the campaign and contacts, but nothing will be sent until it is connected. See <Link to="/settings" className="link">Settings → Integrations</Link>.</div>}
    {channel==="email"&&<div className="field"><label>Email subject</label>
      <input value={subject} onChange={e=>setSubject(e.target.value)} maxLength={200} placeholder="Subject line"/></div>}
    <div className="field"><label>Message</label>
     <textarea rows={5} value={message} onChange={e=>setMessage(e.target.value)} required maxLength={1500} placeholder="Write the message your contacts will receive"/>
     <small className="muted">{message.length}/1500</small></div>
    <div className="field"><label>Contact sheet (Excel or CSV)</label>
     <DropZone accept=".xlsx,.csv" files={files} onFiles={setFiles} hint="First row must have headers: Name, Phone, Email · up to 1000 contacts"/></div>
    {channel!=="email"&&<div className="field short"><label>Default country code for numbers without one</label>
     <input value={cc} onChange={e=>setCc(e.target.value)} maxLength={6}/></div>}
    <label className="check"><input type="checkbox" checked={consent} onChange={e=>setConsent(e.target.checked)}/>
     <span>I confirm these contacts have agreed to receive marketing messages.</span></label>
    {error&&<div className="error">{error}</div>}
    {ok&&<div className="success">{ok}</div>}
    <button className="primary wide" disabled={busy||!consent}>{busy?"Starting…":"Run campaign"}</button>
   </form>
  </section>

  <section className="panel" style={{marginTop:16}}>
   <h3>Your campaigns</h3>
   {list.length===0?<p className="muted">No campaigns yet.</p>:
   <div style={{overflowX:"auto"}}><table className="table"><thead><tr><th>Name</th><th>Channel</th><th>Status</th><th>Contacts</th><th>Sent</th><th>Failed</th><th>Not sent</th><th>Created</th><th/></tr></thead>
    <tbody>{list.map(c=><tr key={c.id}>
     <td>{c.campaign_name}</td><td>{c.channel}</td><td><span className={`badge ${c.status}`}>{c.status.replace("_"," ")}</span></td>
     <td>{c.total_recipients}</td><td>{c.sent||0}</td><td>{c.failed||0}</td><td>{c.not_sent||0}</td><td>{c.created_at}</td>
     <td><button className="icon-btn" title="Download delivery report" onClick={()=>downloadFile(`/api/campaigns/${c.id}/export.xlsx`,`campaign_${c.id}.xlsx`).catch(e=>setError(errText(e)))}><Download size={15}/></button></td>
    </tr>)}</tbody></table></div>}
  </section>
 </>;
}
