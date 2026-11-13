import {useState} from "react";
import {Link,Navigate,useNavigate} from "react-router-dom";
import {Layers3,Mail,LockKeyhole} from "lucide-react";
import {useAuth} from "../context/AuthContext";
export default function Login(){
 const {login,token}=useAuth(),navigate=useNavigate();
 const [email,setEmail]=useState(""),[password,setPassword]=useState(""),[error,setError]=useState(""),[loading,setLoading]=useState(false);
 if(token)return <Navigate to="/" replace/>;
 async function submit(e){e.preventDefault();setError("");setLoading(true);try{await login(email.trim(),password);navigate("/",{replace:true});}catch(err){const d=err.response?.data?.detail;setError(typeof d==="string"?d:err.message||"Login failed.");}finally{setLoading(false);}}
 return <div className="login-screen"><section className="login-card"><div className="login-brand"><div className="brand-mark big"><Layers3/></div><div><b>Dr AV Capstone</b><small>GROW YOUR BRAND WITH INTELLIGENCE</small></div></div><p className="eyebrow">WELCOME BACK</p><h1>Sign in to your workspace</h1><p className="muted">Manage campaigns, content and customer growth from one place.</p><form onSubmit={submit}><label>Email address</label><div className="input-wrap"><Mail/><input type="email" value={email} onChange={e=>setEmail(e.target.value)} placeholder="you@company.com" required/></div><label>Password</label><div className="input-wrap"><LockKeyhole/><input type="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="Enter your password" required/></div>{error&&<div className="error">{error}</div>}<button className="primary" disabled={loading}>{loading?"Signing in...":"Sign in"}</button></form><footer>New here? <Link to="/signup" className="link">Create an account</Link></footer></section></div>;
}