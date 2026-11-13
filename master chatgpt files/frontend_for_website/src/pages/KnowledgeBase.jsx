import {useEffect,useState} from "react";
import {Eye,FileText,StickyNote,Trash2} from "lucide-react";
import api from "../services/api";
import DropZone from "../components/DropZone";

const errText=err=>{const d=err.response?.data?.detail;return typeof d==="string"?d:Array.isArray(d)?d.map(x=>x.msg).join(" "):err.message||"Request failed.";};

export default function KnowledgeBase(){
 const [data,setData]=useState({items:[],chunks:null,scope:"company",using_base:false});
 const [files,setFiles]=useState([]);
 const [title,setTitle]=useState(""),[note,setNote]=useState("");
 const [busy,setBusy]=useState(false),[error,setError]=useState(""),[ok,setOk]=useState("");

 const load=()=>api.get("/api/knowledge").then(({data})=>setData(data)).catch(e=>setError(errText(e)));
 useEffect(()=>{load();},[]);

 async function submit(e){
  e.preventDefault();setError("");setOk("");
  if(!files.length&&!note.trim())return setError("Attach a file or write some information first.");
  const form=new FormData();
  files.forEach(f=>form.append("files",f));
  form.append("note_title",title);form.append("note_text",note);
  setBusy(true);
  try{
   const {data:r}=await api.post("/api/knowledge",form,{headers:{"Content-Type":"multipart/form-data"},timeout:600000});
   setOk(`${r.message} (${r.chunks} knowledge chunks indexed)`+(r.warnings?.length?` Warnings: ${r.warnings.join("; ")}`:""));
   setFiles([]);setTitle("");setNote("");load();
  }catch(err){setError(errText(err));}finally{setBusy(false);}
 }
 async function view(id){
  try{
   const res=await api.get(`/api/knowledge/${id}/file`,{responseType:"blob"});
   window.open(URL.createObjectURL(res.data),"_blank");
  }catch(err){setError(errText(err));}
 }
 async function remove(id){
  if(!confirm(data.scope==="platform"?"Remove this from the PLATFORM knowledge base? Companies without their own documents rely on it.":"Remove this item? The AI will stop using it. If you have no other documents, it will use Moseta's original base knowledge."))return;
  setError("");setOk("");setBusy(true);
  try{await api.delete(`/api/knowledge/${id}`,{timeout:600000});setOk("Item removed and knowledge updated.");load();}
  catch(err){setError(errText(err));}finally{setBusy(false);}
 }

 return <>
  <div className="page-heading"><div><p className="eyebrow">AI TRAINING</p><h1>Knowledge Base</h1>
   <p className="muted">Add product brochures, price lists and notes. Moseta AI studies them and uses them to answer questions and write campaigns.</p></div>
   <span className="pill">{data.scope==="platform"?"Platform knowledge":"Your company knowledge"}{data.chunks!=null?` · ${data.chunks} chunks`:""}</span></div>

  {data.using_base&&<div className="warn" style={{marginBottom:16}}>You have no documents of your own, so Moseta AI is answering from Moseta's original base knowledge. Add your own files or notes below to teach it your products.</div>}

  <section className="panel">
   <h3>Add knowledge</h3>
   <form onSubmit={submit} className="form-grid">
    <DropZone accept=".pdf,.txt,.md,.csv" multiple files={files} onFiles={setFiles} hint="PDF, TXT, MD or CSV · up to 10 files · 10 MB each"/>
    <div className="field"><label>Or write the information yourself (optional)</label>
     <input value={title} onChange={e=>setTitle(e.target.value)} placeholder="Title, e.g. Warranty details" maxLength={120}/>
     <textarea value={note} onChange={e=>setNote(e.target.value)} rows={7} maxLength={20000}
      placeholder="Type product details, offers, FAQs or brand guidelines here. You can attach files and write notes together."/></div>
    {error&&<div className="error">{error}</div>}
    {ok&&<div className="success">{ok}</div>}
    <button className="primary wide" disabled={busy}>{busy?"Studying your documents… (can take a minute)":"Save & train the AI"}</button>
   </form>
  </section>

  <section className="panel" style={{marginTop:16}}>
   <h3>Learned from ({data.items.length})</h3>
   {data.items.length===0?<p className="muted">Nothing added yet. Upload a file or write a note above.</p>:
   <table className="table"><thead><tr><th>Type</th><th>Name</th><th>Details</th><th>Added</th><th/></tr></thead>
    <tbody>{data.items.map(i=><tr key={i.id}>
     <td>{i.kind==="file"?<FileText size={15}/>:<StickyNote size={15}/>} {i.kind}</td>
     <td>{i.title}</td>
     <td className="muted">{i.kind==="note"?i.preview:`${Math.max(1,Math.round(i.size_bytes/1024))} KB`}</td>
     <td>{i.created_at}</td>
     <td style={{whiteSpace:"nowrap"}}>{i.kind==="file"&&<button className="icon-btn" title="View file" onClick={()=>view(i.id)}><Eye size={15}/></button>}<button className="icon-btn" title="Remove" disabled={busy} onClick={()=>remove(i.id)}><Trash2 size={15}/></button></td>
    </tr>)}</tbody></table>}
  </section>
 </>;
}
