import {useEffect,useRef,useState} from "react";
import {Send,Sparkles} from "lucide-react";
import api from "../services/api";

export default function ContentStudio(){
 const [messages,setMessages]=useState([]);
 const [text,setText]=useState("");
 const [busy,setBusy]=useState(false);
 const [error,setError]=useState("");
 const end=useRef(null);

 useEffect(()=>{
  api.get("/api/chat/history?limit=30").then(({data})=>{
   const m=[];
   data.items.forEach(i=>{m.push({role:"user",text:i.question});m.push({role:"ai",text:i.answer,sources:JSON.parse(i.sources||"[]")});});
   setMessages(m);
  }).catch(()=>{});
 },[]);
 useEffect(()=>{end.current?.scrollIntoView({behavior:"smooth"});},[messages,busy]);

 async function send(e){
  e.preventDefault();
  const q=text.trim();if(!q||busy)return;
  setText("");setError("");setBusy(true);
  setMessages(m=>[...m,{role:"user",text:q}]);
  try{
   // Send the last few exchanges so follow-ups ("combine those", "add more info") have context.
   const pairs=[];
   for(let i=0;i+1<messages.length;i++){if(messages[i].role==="user"&&messages[i+1].role==="ai")pairs.push({question:messages[i].text,answer:messages[i+1].text});}
   const {data}=await api.post("/api/chat",{message:q,history:pairs.slice(-3)},{timeout:600000});
   setMessages(m=>[...m,{role:"ai",text:data.answer,sources:data.sources,campaign:data.is_campaign?data.platforms:null}]);
  }catch(err){
   const d=err.response?.data?.detail;
   setError(typeof d==="string"?d:err.message||"Request failed.");
  }finally{setBusy(false);}
 }

 return <>
  <div className="page-heading"><div><p className="eyebrow">GENERATIVE AI</p><h1>AI Content Studio</h1>
   <p className="muted">Ask about Moseta products or request Instagram, Facebook and WhatsApp campaigns. Answers use your product PDFs.</p></div>
   <div style={{display:"flex",gap:10,alignItems:"center"}}>
    {messages.length>0&&<button type="button" className="tabs-btn" onClick={()=>{setMessages([]);setError("");}}>New chat</button>}
    <span className="pill"><Sparkles size={12}/> Qwen2.5-0.5B (local)</span></div></div>
  <section className="panel chat">
   <div className="chat-log">
    {messages.length===0&&<p className="muted">Try: “What is the cooling capacity of Moto Pi?” or “Create an Instagram campaign for Moto Pi”, then follow up with “combine those two messages” or “add more information”.</p>}
    {messages.map((m,i)=><div key={i} className={`bubble ${m.role}`}>
     <div style={{whiteSpace:"pre-wrap"}}>{m.text}</div>
     {m.campaign&&<small>Campaign draft saved · {m.campaign.join(", ")}</small>}
     {m.sources&&m.sources.length>0&&<small>Sources: {m.sources.map(s=>`${s.source} #${s.chunk}`).join(" · ")}</small>}
    </div>)}
    {busy&&<div className="bubble ai"><span className="muted">Moseta AI is thinking… (CPU, can take a minute)</span></div>}
    <div ref={end}/>
   </div>
   {error&&<div className="error">{error}</div>}
   <form className="chat-form" onSubmit={send}>
    <input value={text} onChange={e=>setText(e.target.value)} placeholder="Ask Moseta AI…" disabled={busy}/>
    <button className="primary" disabled={busy||!text.trim()}><Send size={16}/></button>
   </form>
  </section>
 </>;
}
