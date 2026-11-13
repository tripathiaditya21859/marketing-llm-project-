import {useRef,useState} from "react";
import {UploadCloud,X} from "lucide-react";

export default function DropZone({accept,multiple=false,files,onFiles,hint}){
 const input=useRef(null);
 const [over,setOver]=useState(false);
 const exts=accept.split(",").map(s=>s.trim().toLowerCase());

 function add(list){
  const picked=[...list].filter(f=>exts.some(e=>f.name.toLowerCase().endsWith(e)));
  if(!picked.length)return;
  onFiles(multiple?[...files,...picked]:[picked[0]]);
 }
 return <div>
  <div className={`dropzone ${over?"over":""}`}
   onClick={()=>input.current.click()}
   onDragOver={e=>{e.preventDefault();setOver(true);}}
   onDragLeave={()=>setOver(false)}
   onDrop={e=>{e.preventDefault();setOver(false);add(e.dataTransfer.files);}}>
   <UploadCloud size={28}/>
   <b>Drop {multiple?"files":"a file"} here or click to browse</b>
   <small>{hint}</small>
   <input ref={input} type="file" accept={accept} multiple={multiple} hidden
    onChange={e=>{add(e.target.files);e.target.value="";}}/>
  </div>
  {files.length>0&&<ul className="filelist">{files.map((f,i)=><li key={i}>
   <span>{f.name} <small>({Math.max(1,Math.round(f.size/1024))} KB)</small></span>
   <button type="button" className="icon-btn" onClick={()=>onFiles(files.filter((_,j)=>j!==i))}><X size={14}/></button>
  </li>)}</ul>}
 </div>;
}
