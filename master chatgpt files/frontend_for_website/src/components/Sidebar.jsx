import {NavLink} from "react-router-dom";
import {Users as UsersIcon,LayoutDashboard,Megaphone,Sparkles,BookOpen,Users,ChartNoAxesCombined,Settings,LogOut,Layers3} from "lucide-react";
import {useAuth} from "../context/AuthContext";
const links=[["/","Dashboard",LayoutDashboard,true],["/campaigns","Campaigns",Megaphone],["/content-studio","AI Content Studio",Sparkles],["/knowledge-base","Knowledge Base",BookOpen],["/leads","Leads & Customers",Users],["/analytics","Analytics",ChartNoAxesCombined],["/settings","Settings",Settings]];
export default function Sidebar(){
 const {logout,user}=useAuth();const name=user?.full_name||user?.name||user?.email||"Workspace user";
 return <aside className="sidebar"><div className="brand"><div className="brand-mark"><Layers3/></div><div><b>Dr AV Capstone</b></div></div><p className="section-label">WORKSPACE</p><nav>{(user?.is_superadmin?[...links.slice(0,-1),["/users","Users",UsersIcon],links[links.length-1]]:links).map(([to,label,Icon,end])=><NavLink key={to} to={to} end={end} className={({isActive})=>`nav-link ${isActive?"active":""}`}><Icon size={18}/><span>{label}</span></NavLink>)}</nav><div className="sidebar-bottom"><div className="user-name">{name}</div><button className="logout" onClick={logout}><LogOut size={16}/> Sign out</button></div></aside>;
}