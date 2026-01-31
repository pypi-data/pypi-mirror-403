import{aV as l,aY as i,aX as m,aW as L,bQ as y,d as g,I as b,b7 as P,b8 as x,bR as T,b5 as j,aj as S,L as p,ba as E,r as I,o as $,by as w,bS as H,b1 as O,br as V}from"./index-DJskbzIk.js";const A=l("breadcrumb",`
 white-space: nowrap;
 cursor: default;
 line-height: var(--n-item-line-height);
`,[i("ul",`
 list-style: none;
 padding: 0;
 margin: 0;
 `),i("a",`
 color: inherit;
 text-decoration: inherit;
 `),l("breadcrumb-item",`
 font-size: var(--n-font-size);
 transition: color .3s var(--n-bezier);
 display: inline-flex;
 align-items: center;
 `,[l("icon",`
 font-size: 18px;
 vertical-align: -.2em;
 transition: color .3s var(--n-bezier);
 color: var(--n-item-text-color);
 `),i("&:not(:last-child)",[L("clickable",[m("link",`
 cursor: pointer;
 `,[i("&:hover",`
 background-color: var(--n-item-color-hover);
 `),i("&:active",`
 background-color: var(--n-item-color-pressed); 
 `)])])]),m("link",`
 padding: 4px;
 border-radius: var(--n-item-border-radius);
 transition:
 background-color .3s var(--n-bezier),
 color .3s var(--n-bezier);
 color: var(--n-item-text-color);
 position: relative;
 `,[i("&:hover",`
 color: var(--n-item-text-color-hover);
 `,[l("icon",`
 color: var(--n-item-text-color-hover);
 `)]),i("&:active",`
 color: var(--n-item-text-color-pressed);
 `,[l("icon",`
 color: var(--n-item-text-color-pressed);
 `)])]),m("separator",`
 margin: 0 8px;
 color: var(--n-separator-color);
 transition: color .3s var(--n-bezier);
 user-select: none;
 -webkit-user-select: none;
 `),i("&:last-child",[m("link",`
 font-weight: var(--n-font-weight-active);
 cursor: unset;
 color: var(--n-item-text-color-active);
 `,[l("icon",`
 color: var(--n-item-text-color-active);
 `)]),m("separator",`
 display: none;
 `)])])]),C=y("n-breadcrumb"),K=Object.assign(Object.assign({},x.props),{separator:{type:String,default:"/"}}),N=g({name:"Breadcrumb",props:K,setup(e){const{mergedClsPrefixRef:t,inlineThemeDisabled:o}=P(e),n=x("Breadcrumb","-breadcrumb",A,T,e,t);j(C,{separatorRef:S(e,"separator"),mergedClsPrefixRef:t});const c=p(()=>{const{common:{cubicBezierEaseInOut:d},self:{separatorColor:u,itemTextColor:a,itemTextColorHover:s,itemTextColorPressed:v,itemTextColorActive:h,fontSize:f,fontWeightActive:k,itemBorderRadius:R,itemColorHover:_,itemColorPressed:z,itemLineHeight:B}}=n.value;return{"--n-font-size":f,"--n-bezier":d,"--n-item-text-color":a,"--n-item-text-color-hover":s,"--n-item-text-color-pressed":v,"--n-item-text-color-active":h,"--n-separator-color":u,"--n-item-color-hover":_,"--n-item-color-pressed":z,"--n-item-border-radius":R,"--n-font-weight-active":k,"--n-item-line-height":B}}),r=o?E("breadcrumb",void 0,c,e):void 0;return{mergedClsPrefix:t,cssVars:o?void 0:c,themeClass:r==null?void 0:r.themeClass,onRender:r==null?void 0:r.onRender}},render(){var e;return(e=this.onRender)===null||e===void 0||e.call(this),b("nav",{class:[`${this.mergedClsPrefix}-breadcrumb`,this.themeClass],style:this.cssVars,"aria-label":"Breadcrumb"},b("ul",null,this.$slots))}});function M(e=H?window:null){const t=()=>{const{hash:c,host:r,hostname:d,href:u,origin:a,pathname:s,port:v,protocol:h,search:f}=(e==null?void 0:e.location)||{};return{hash:c,host:r,hostname:d,href:u,origin:a,pathname:s,port:v,protocol:h,search:f}},o=I(t()),n=()=>{o.value=t()};return $(()=>{e&&(e.addEventListener("popstate",n),e.addEventListener("hashchange",n))}),w(()=>{e&&(e.removeEventListener("popstate",n),e.removeEventListener("hashchange",n))}),o}const D={separator:String,href:String,clickable:{type:Boolean,default:!0},onClick:Function},Q=g({name:"BreadcrumbItem",props:D,slots:Object,setup(e,{slots:t}){const o=O(C,null);if(!o)return()=>null;const{separatorRef:n,mergedClsPrefixRef:c}=o,r=M(),d=p(()=>e.href?"a":"span"),u=p(()=>r.value.href===e.href?"location":null);return()=>{const{value:a}=c;return b("li",{class:[`${a}-breadcrumb-item`,e.clickable&&`${a}-breadcrumb-item--clickable`]},b(d.value,{class:`${a}-breadcrumb-item__link`,"aria-current":u.value,href:e.href,onClick:e.onClick},t),b("span",{class:`${a}-breadcrumb-item__separator`,"aria-hidden":"true"},V(t.separator,()=>{var s;return[(s=e.separator)!==null&&s!==void 0?s:n.value]})))}}});export{N as _,Q as a};
