import {useEffect,useState} from "react";
import api from "../services/api";
import {CHANNEL_UI} from "../components/channels";
import {Check,Plug} from "lucide-react";

export default function Settings(){
 const [channels,setChannels]=useState([]),[error,setError]=useState("");
 useEffect(()=>{
  api.get("/api/campaigns/channels").then(({data})=>setChannels(data.channels))
   .catch(e=>setError(e.response?.data?.detail||e.message));
 },[]);
 return <>
  <div className="page-heading"><div><p className="eyebrow">WORKSPACE</p><h1>Settings</h1>
   <p className="muted">Connect the channels you use to reach customers.</p></div></div>
  <section className="panel">
   <h3>Integrations</h3>
   {error&&<div className="error">{error}</div>}
   <div className="integrations">{channels.map(c=>{
    const ui=CHANNEL_UI[c.id]||{name:c.label,icon:Plug,color:"#999",blurb:"",provider:""};const Icon=ui.icon;
    return <article className="integration" key={c.id}>
     <div className="integration-head">
      <span className="channel-icon" style={{background:ui.color+"22",color:ui.color}}><Icon size={22}/></span>
      <div><b>{ui.name}</b><p className="muted">{ui.blurb}</p></div>
      <span className={`conn ${c.configured?"on":"off"}`}>{c.configured?<><Check size={11}/> Connected</>:"Not connected"}</span>
     </div>
     <p className="muted small">Provider: {ui.provider}</p>
     {c.configured?<p className="muted small">Ready to send. Choose {ui.name} on the Campaigns page.</p>:
      <div className="warn">To connect, add these settings to the backend <code>.env</code> file and restart the backend:
       <ul>{c.required_keys.map(k=><li key={k}><code>{k}</code>{c.missing_keys.includes(k)?" — missing":" — set"}</li>)}</ul></div>}
    </article>;
   })}</div>
  </section>
 </>;
}
