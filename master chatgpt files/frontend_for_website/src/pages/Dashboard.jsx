import {useEffect,useState} from "react";
import {Link} from "react-router-dom";
import {Megaphone,Sparkles,Users,FileText,ArrowUpRight} from "lucide-react";
import api from "../services/api";

export default function Dashboard(){
 const [t,setT]=useState(null);
 useEffect(()=>{api.get("/api/analytics").then(({data})=>setT(data.totals)).catch(()=>{});},[]);
 const v=k=>t?t[k]:"—";
 const stats=[["Campaigns",v("campaigns"),"Campaigns you have run",Megaphone],["AI chats",v("ai_chats"),"Questions and drafts generated",Sparkles],["Contacts",v("contacts"),"People in your customer list",Users],["Knowledge items",v("knowledge_items"),"Files and notes the AI has studied",FileText]];
 return <><div className="page-heading"><div><p className="eyebrow">OVERVIEW</p><h1>Dashboard</h1><p className="muted">Welcome to Dr AV Capstone. Your marketing command centre.</p></div><span className="pill">Workspace overview</span></div><section className="stats">{stats.map(([label,value,note,Icon])=><article className="stat" key={label}><div>{label}<Icon size={18}/></div><strong>{value}</strong><small>{note}</small></article>)}</section><section className="dash-grid"><article className="panel hero"><p className="eyebrow">YOUR AI MARKETING ASSISTANT</p><h2>Make every campaign count.</h2><p className="muted">Use your product documents and brand knowledge to create consistent marketing content for your channels.</p><Link to="/content-studio">Open AI Content Studio <ArrowUpRight size={16}/></Link></article><article className="panel"><h3>Get started</h3>{[["01","Add product knowledge","Upload brochures or write notes in Knowledge Base."],["02","Ask the AI","Draft campaign messages in AI Content Studio."],["03","Run a campaign","Upload your contact sheet and send on WhatsApp, SMS or email."]].map(x=><div className="step" key={x[0]}><b>{x[0]}</b><div><strong>{x[1]}</strong><p className="muted">{x[2]}</p></div></div>)}</article></section></>;}
