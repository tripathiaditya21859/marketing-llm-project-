import {createContext,useContext,useMemo,useState} from "react";
import api from "../services/api";
import {LOGIN_PATH,ME_PATH} from "../config";
const AuthContext=createContext(null);
export function AuthProvider({children}){
 const [user,setUser]=useState(()=>{const s=sessionStorage.getItem("moseta_user");return s?JSON.parse(s):null});
 const [token,setToken]=useState(()=>sessionStorage.getItem("moseta_access_token"));
 async function login(email,password){
  const {data}=await api.post(LOGIN_PATH,{email,password});
  const accessToken=data.access_token||data.token;
  if(!accessToken)throw new Error("No access_token/token found in login response. Check your backend response schema.");
  sessionStorage.setItem("moseta_access_token",accessToken);setToken(accessToken);
  let profile=data.user||data;
  try{const me=await api.get(ME_PATH);profile=me.data;}catch{}
  sessionStorage.setItem("moseta_user",JSON.stringify(profile));setUser(profile);return profile;
 }
 function logout(){sessionStorage.removeItem("moseta_access_token");sessionStorage.removeItem("moseta_user");setToken(null);setUser(null);}
 const value=useMemo(()=>({user,token,login,logout}),[user,token]);
 return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
export function useAuth(){const v=useContext(AuthContext);if(!v)throw new Error("useAuth must be inside AuthProvider");return v;}