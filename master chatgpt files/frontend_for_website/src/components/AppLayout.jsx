import {Outlet} from "react-router-dom";
import Sidebar from "./Sidebar";
export default function AppLayout(){return <div className="app-shell"><Sidebar/><main className="main-area"><header className="topbar"><div><small>DR AV CAPSTONE</small><b>Marketing intelligence workspace</b></div><span><i/> Backend workspace</span></header><div className="page-content"><Outlet/></div></main></div>;}