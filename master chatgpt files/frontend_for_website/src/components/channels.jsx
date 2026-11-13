import {MessageCircle,MessageSquare,Mail,Check,Plug} from "lucide-react";

// One place that defines how each sending channel looks. Backend ids: whatsapp, sms, email.
// When a provider is connected later, the "connected" state appears automatically - no design change.
export const CHANNEL_UI={
 whatsapp:{name:"WhatsApp",icon:MessageCircle,color:"#25D366",blurb:"Send promotions to customers' WhatsApp numbers.",provider:"Twilio WhatsApp"},
 sms:{name:"SMS",icon:MessageSquare,color:"#4DA3FF",blurb:"Text messages to mobile numbers.",provider:"Twilio SMS"},
 email:{name:"Gmail / Email",icon:Mail,color:"#EA4335",blurb:"Email campaigns through Gmail or any SMTP server.",provider:"Gmail / SMTP"},
};

export function ChannelPicker({channels,value,onChange}){
 return <div className="channel-grid">{channels.map(c=>{
  const ui=CHANNEL_UI[c.id]||{name:c.label,icon:Plug,color:"#999"};const Icon=ui.icon;
  return <button type="button" key={c.id} className={`channel-card ${value===c.id?"selected":""}`} onClick={()=>onChange(c.id)}>
   <span className="channel-icon" style={{background:ui.color+"22",color:ui.color}}><Icon size={22}/></span>
   <b>{ui.name}</b>
   <span className={`conn ${c.configured?"on":"off"}`}>{c.configured?<><Check size={11}/> Connected</>:"Not connected"}</span>
  </button>;
 })}</div>;
}
