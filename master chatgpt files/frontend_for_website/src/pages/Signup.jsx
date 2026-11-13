import {useState} from "react";
import {Link,useNavigate} from "react-router-dom";
import {Layers3,Mail,LockKeyhole,User} from "lucide-react";
import api from "../services/api";
import {useAuth} from "../context/AuthContext";

export default function Signup(){
 const {login}=useAuth(),navigate=useNavigate();
 const [name,setName]=useState(""),[email,setEmail]=useState(""),[password,setPassword]=useState(""),[confirm,setConfirm]=useState("");
 const [error,setError]=useState(""),[loading,setLoading]=useState(false);

 async function submit(e){
  e.preventDefault();setError("");
  if(password.length<8)return setError("Password must be at least 8 characters.");
  if(password!==confirm)return setError("Passwords do not match.");
  setLoading(true);
  try{
   await api.post("/api/auth/signup",{name:name.trim(),email:email.trim(),password});
   await login(email.trim(),password);
   navigate("/",{replace:true});
  }catch(err){
   const d=err.response?.data?.detail;
   setError(typeof d==="string"?d:Array.isArray(d)?d.map(x=>x.msg).join(" "):err.message||"Signup failed.");
  }finally{setLoading(false);}
 }

 return <div className="login-screen"><section className="login-card">
  <div className="login-brand"><div className="brand-mark big"><Layers3/></div><div><b>Dr AV Capstone</b><small>GROW YOUR BRAND WITH INTELLIGENCE</small></div></div>
  <p className="eyebrow">GET STARTED</p><h1>Create your account</h1>
  <p className="muted">Sign up your company to run AI-powered marketing campaigns.</p>
  <form onSubmit={submit}>
   <label>Full name</label>
   <div className="input-wrap"><User/><input value={name} onChange={e=>setName(e.target.value)} placeholder="Your name" required minLength={2}/></div>
   <label>Email address</label>
   <div className="input-wrap"><Mail/><input type="email" value={email} onChange={e=>setEmail(e.target.value)} placeholder="you@company.com" required/></div>
   <label>Password</label>
   <div className="input-wrap"><LockKeyhole/><input type="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="At least 8 characters" required minLength={8}/></div>
   <label>Confirm password</label>
   <div className="input-wrap"><LockKeyhole/><input type="password" value={confirm} onChange={e=>setConfirm(e.target.value)} placeholder="Re-enter password" required/></div>
   {error&&<div className="error">{error}</div>}
   <button className="primary" disabled={loading}>{loading?"Creating account...":"Create account"}</button>
  </form>
  <footer>Already have an account? <Link to="/login" className="link">Sign in</Link></footer>
 </section></div>;
}
