import axios from "axios";
import {API_BASE_URL} from "../config";
const api=axios.create({baseURL:API_BASE_URL,headers:{"Content-Type":"application/json"},timeout:30000});
api.interceptors.request.use(config=>{const token=sessionStorage.getItem("moseta_access_token");if(token)config.headers.Authorization=`Bearer ${token}`;return config;});
// An expired or invalid session (401) sends the user back to the login page.
api.interceptors.response.use(r=>r,err=>{
 const url=err.config?.url||"";
 if(err.response?.status===401&&!url.includes("/auth/login")&&!url.includes("/auth/signup")){
  sessionStorage.removeItem("moseta_access_token");sessionStorage.removeItem("moseta_user");
  if(!location.pathname.startsWith("/login"))location.href="/login";
 }
 return Promise.reject(err);
});
export default api;