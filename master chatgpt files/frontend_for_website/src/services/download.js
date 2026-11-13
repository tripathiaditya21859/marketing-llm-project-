import api from "./api";

// Downloads an authenticated file (Excel) from the backend.
export async function downloadFile(url,fallbackName){
 const res=await api.get(url,{responseType:"blob"});
 const cd=res.headers["content-disposition"]||"";
 const m=/filename\*?=(?:UTF-8'')?"?([^";]+)"?/i.exec(cd);
 const name=m?decodeURIComponent(m[1]):fallbackName;
 const href=URL.createObjectURL(res.data);
 const a=document.createElement("a");
 a.href=href;a.download=name;document.body.appendChild(a);a.click();a.remove();
 setTimeout(()=>URL.revokeObjectURL(href),1000);
}
