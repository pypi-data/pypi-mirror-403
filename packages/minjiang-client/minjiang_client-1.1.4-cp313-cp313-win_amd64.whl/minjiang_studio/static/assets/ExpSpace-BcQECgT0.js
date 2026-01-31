import{aV as u,aW as S,aX as i,aY as A,d as w,I as o,aZ as le,a_ as ae,a$ as ne,b0 as W,b1 as se,b2 as ie,r as P,b3 as ce,aj as U,L as I,b4 as de,b5 as pe,b6 as ue,b7 as ge,b8 as G,b9 as he,ba as me,bb as be,bc as N,e as j,f as C,bd as ve,h as v,J as fe,C as J,c as _e,b as Z,A as xe,ab as F,be as ye,l as b,w as _,i as g,s as O,t as E,as as we,aE as X,N as K,B as Q,j as Ce,a5 as Se,az as ke,bf as q,aR as Te,o as ze,a6 as Be,aI as Me,bg as Re,Y as $e,bh as Le,aJ as Ie,aK as Pe,bi as Ve}from"./index-DJskbzIk.js";import{u as ee}from"./groupDetail-grzpJhg1.js";import{S as te,_ as He}from"./SpaceTools-Ds6UqpWj.js";import{A as Ae}from"./AppsListDetail24Filled-BGRUPGEn.js";import{A as oe}from"./Add-B9E6ooHy.js";import{_ as Ee}from"./BackToOverview.vue_vue_type_script_setup_true_lang-C3Wp52Jq.js";import{E as je}from"./ExperimentTwotone-CUUKUJME.js";import"./exp-Dzc8nAzP.js";import"./json-editor-vue-cMpGPz9p.js";import"./index-CljUi5cZ.js";import"./params-elF_11QE.js";import"./PaginationView.vue_vue_type_script_setup_true_lang-C5I4MAUI.js";import"./Pagination-MzAc_u8k.js";import"./prop-NnGblK-3.js";import"./Popconfirm-DFFNKs94.js";import"./DataTable-BkhITQT9.js";import"./Checkbox-B0NmEvB4.js";import"./RadioGroup-DFjU_ho_.js";import"./download-C2161hUv.js";import"./Switch-BTGJkP8J.js";import"./DynamicForm-B5kgL0W4.js";import"./index-DDdGfEJ1.js";import"./InputNumber-CtZNiVVn.js";import"./FileSaver.min-CWr_Rv27.js";import"./ExitOutline-BbqKyaqz.js";const De=u("layout-sider",`
 flex-shrink: 0;
 box-sizing: border-box;
 position: relative;
 z-index: 1;
 color: var(--n-text-color);
 transition:
 color .3s var(--n-bezier),
 border-color .3s var(--n-bezier),
 min-width .3s var(--n-bezier),
 max-width .3s var(--n-bezier),
 transform .3s var(--n-bezier),
 background-color .3s var(--n-bezier);
 background-color: var(--n-color);
 display: flex;
 justify-content: flex-end;
`,[S("bordered",[i("border",`
 content: "";
 position: absolute;
 top: 0;
 bottom: 0;
 width: 1px;
 background-color: var(--n-border-color);
 transition: background-color .3s var(--n-bezier);
 `)]),i("left-placement",[S("bordered",[i("border",`
 right: 0;
 `)])]),S("right-placement",`
 justify-content: flex-start;
 `,[S("bordered",[i("border",`
 left: 0;
 `)]),S("collapsed",[u("layout-toggle-button",[u("base-icon",`
 transform: rotate(180deg);
 `)]),u("layout-toggle-bar",[A("&:hover",[i("top",{transform:"rotate(-12deg) scale(1.15) translateY(-2px)"}),i("bottom",{transform:"rotate(12deg) scale(1.15) translateY(2px)"})])])]),u("layout-toggle-button",`
 left: 0;
 transform: translateX(-50%) translateY(-50%);
 `,[u("base-icon",`
 transform: rotate(0);
 `)]),u("layout-toggle-bar",`
 left: -28px;
 transform: rotate(180deg);
 `,[A("&:hover",[i("top",{transform:"rotate(12deg) scale(1.15) translateY(-2px)"}),i("bottom",{transform:"rotate(-12deg) scale(1.15) translateY(2px)"})])])]),S("collapsed",[u("layout-toggle-bar",[A("&:hover",[i("top",{transform:"rotate(-12deg) scale(1.15) translateY(-2px)"}),i("bottom",{transform:"rotate(12deg) scale(1.15) translateY(2px)"})])]),u("layout-toggle-button",[u("base-icon",`
 transform: rotate(0);
 `)])]),u("layout-toggle-button",`
 transition:
 color .3s var(--n-bezier),
 right .3s var(--n-bezier),
 left .3s var(--n-bezier),
 border-color .3s var(--n-bezier),
 background-color .3s var(--n-bezier);
 cursor: pointer;
 width: 24px;
 height: 24px;
 position: absolute;
 top: 50%;
 right: 0;
 border-radius: 50%;
 display: flex;
 align-items: center;
 justify-content: center;
 font-size: 18px;
 color: var(--n-toggle-button-icon-color);
 border: var(--n-toggle-button-border);
 background-color: var(--n-toggle-button-color);
 box-shadow: 0 2px 4px 0px rgba(0, 0, 0, .06);
 transform: translateX(50%) translateY(-50%);
 z-index: 1;
 `,[u("base-icon",`
 transition: transform .3s var(--n-bezier);
 transform: rotate(180deg);
 `)]),u("layout-toggle-bar",`
 cursor: pointer;
 height: 72px;
 width: 32px;
 position: absolute;
 top: calc(50% - 36px);
 right: -28px;
 `,[i("top, bottom",`
 position: absolute;
 width: 4px;
 border-radius: 2px;
 height: 38px;
 left: 14px;
 transition: 
 background-color .3s var(--n-bezier),
 transform .3s var(--n-bezier);
 `),i("bottom",`
 position: absolute;
 top: 34px;
 `),A("&:hover",[i("top",{transform:"rotate(12deg) scale(1.15) translateY(-2px)"}),i("bottom",{transform:"rotate(-12deg) scale(1.15) translateY(2px)"})]),i("top, bottom",{backgroundColor:"var(--n-toggle-bar-color)"}),A("&:hover",[i("top, bottom",{backgroundColor:"var(--n-toggle-bar-color-hover)"})])]),i("border",`
 position: absolute;
 top: 0;
 right: 0;
 bottom: 0;
 width: 1px;
 transition: background-color .3s var(--n-bezier);
 `),u("layout-sider-scroll-container",`
 flex-grow: 1;
 flex-shrink: 0;
 box-sizing: border-box;
 height: 100%;
 opacity: 0;
 transition: opacity .3s var(--n-bezier);
 max-width: 100%;
 `),S("show-content",[u("layout-sider-scroll-container",{opacity:1})]),S("absolute-positioned",`
 position: absolute;
 left: 0;
 top: 0;
 bottom: 0;
 `)]),Ne=w({props:{clsPrefix:{type:String,required:!0},onClick:Function},render(){const{clsPrefix:e}=this;return o("div",{onClick:this.onClick,class:`${e}-layout-toggle-bar`},o("div",{class:`${e}-layout-toggle-bar__top`}),o("div",{class:`${e}-layout-toggle-bar__bottom`}))}}),qe=w({name:"LayoutToggleButton",props:{clsPrefix:{type:String,required:!0},onClick:Function},render(){const{clsPrefix:e}=this;return o("div",{class:`${e}-layout-toggle-button`,onClick:this.onClick},o(le,{clsPrefix:e},{default:()=>o(ae,null)}))}}),Fe={position:be,bordered:Boolean,collapsedWidth:{type:Number,default:48},width:{type:[Number,String],default:272},contentClass:String,contentStyle:{type:[String,Object],default:""},collapseMode:{type:String,default:"transform"},collapsed:{type:Boolean,default:void 0},defaultCollapsed:Boolean,showCollapsedContent:{type:Boolean,default:!0},showTrigger:{type:[Boolean,String],default:!1},nativeScrollbar:{type:Boolean,default:!0},inverted:Boolean,scrollbarProps:Object,triggerClass:String,triggerStyle:[String,Object],collapsedTriggerClass:String,collapsedTriggerStyle:[String,Object],"onUpdate:collapsed":[Function,Array],onUpdateCollapsed:[Function,Array],onAfterEnter:Function,onAfterLeave:Function,onExpand:[Function,Array],onCollapse:[Function,Array],onScroll:Function},Oe=w({name:"LayoutSider",props:Object.assign(Object.assign({},G.props),Fe),setup(e){const r=se(ie),t=P(null),c=P(null),p=P(e.defaultCollapsed),h=ce(U(e,"collapsed"),p),f=I(()=>W(h.value?e.collapsedWidth:e.width)),V=I(()=>e.collapseMode!=="transform"?{}:{minWidth:W(e.width)}),k=I(()=>r?r.siderPlacement:"left");function z(s,l){if(e.nativeScrollbar){const{value:n}=t;n&&(l===void 0?n.scrollTo(s):n.scrollTo(s,l))}else{const{value:n}=c;n&&n.scrollTo(s,l)}}function H(){const{"onUpdate:collapsed":s,onUpdateCollapsed:l,onExpand:n,onCollapse:D}=e,{value:L}=h;l&&N(l,!L),s&&N(s,!L),p.value=!L,L?n&&N(n):D&&N(D)}let m=0,a=0;const x=s=>{var l;const n=s.target;m=n.scrollLeft,a=n.scrollTop,(l=e.onScroll)===null||l===void 0||l.call(e,s)};de(()=>{if(e.nativeScrollbar){const s=t.value;s&&(s.scrollTop=a,s.scrollLeft=m)}}),pe(ue,{collapsedRef:h,collapseModeRef:U(e,"collapseMode")});const{mergedClsPrefixRef:B,inlineThemeDisabled:M}=ge(e),T=G("Layout","-layout-sider",De,he,e,B);function d(s){var l,n;s.propertyName==="max-width"&&(h.value?(l=e.onAfterLeave)===null||l===void 0||l.call(e):(n=e.onAfterEnter)===null||n===void 0||n.call(e))}const Y={scrollTo:z},R=I(()=>{const{common:{cubicBezierEaseInOut:s},self:l}=T.value,{siderToggleButtonColor:n,siderToggleButtonBorder:D,siderToggleBarColor:L,siderToggleBarColorHover:re}=l,y={"--n-bezier":s,"--n-toggle-button-color":n,"--n-toggle-button-border":D,"--n-toggle-bar-color":L,"--n-toggle-bar-color-hover":re};return e.inverted?(y["--n-color"]=l.siderColorInverted,y["--n-text-color"]=l.textColorInverted,y["--n-border-color"]=l.siderBorderColorInverted,y["--n-toggle-button-icon-color"]=l.siderToggleButtonIconColorInverted,y.__invertScrollbar=l.__invertScrollbar):(y["--n-color"]=l.siderColor,y["--n-text-color"]=l.textColor,y["--n-border-color"]=l.siderBorderColor,y["--n-toggle-button-icon-color"]=l.siderToggleButtonIconColor),y}),$=M?me("layout-sider",I(()=>e.inverted?"a":"b"),R,e):void 0;return Object.assign({scrollableElRef:t,scrollbarInstRef:c,mergedClsPrefix:B,mergedTheme:T,styleMaxWidth:f,mergedCollapsed:h,scrollContainerStyle:V,siderPlacement:k,handleNativeElScroll:x,handleTransitionend:d,handleTriggerClick:H,inlineThemeDisabled:M,cssVars:R,themeClass:$==null?void 0:$.themeClass,onRender:$==null?void 0:$.onRender},Y)},render(){var e;const{mergedClsPrefix:r,mergedCollapsed:t,showTrigger:c}=this;return(e=this.onRender)===null||e===void 0||e.call(this),o("aside",{class:[`${r}-layout-sider`,this.themeClass,`${r}-layout-sider--${this.position}-positioned`,`${r}-layout-sider--${this.siderPlacement}-placement`,this.bordered&&`${r}-layout-sider--bordered`,t&&`${r}-layout-sider--collapsed`,(!t||this.showCollapsedContent)&&`${r}-layout-sider--show-content`],onTransitionend:this.handleTransitionend,style:[this.inlineThemeDisabled?void 0:this.cssVars,{maxWidth:this.styleMaxWidth,width:W(this.width)}]},this.nativeScrollbar?o("div",{class:[`${r}-layout-sider-scroll-container`,this.contentClass],onScroll:this.handleNativeElScroll,style:[this.scrollContainerStyle,{overflow:"auto"},this.contentStyle],ref:"scrollableElRef"},this.$slots):o(ne,Object.assign({},this.scrollbarProps,{onScroll:this.onScroll,ref:"scrollbarInstRef",style:this.scrollContainerStyle,contentStyle:this.contentStyle,contentClass:this.contentClass,theme:this.mergedTheme.peers.Scrollbar,themeOverrides:this.mergedTheme.peerOverrides.Scrollbar,builtinThemeOverrides:this.inverted&&this.cssVars.__invertScrollbar==="true"?{colorHover:"rgba(255, 255, 255, .4)",color:"rgba(255, 255, 255, .3)"}:void 0}),this.$slots),c?c==="bar"?o(Ne,{clsPrefix:r,class:t?this.collapsedTriggerClass:this.triggerClass,style:t?this.collapsedTriggerStyle:this.triggerStyle,onClick:this.handleTriggerClick}):o(qe,{clsPrefix:r,class:t?this.collapsedTriggerClass:this.triggerClass,style:t?this.collapsedTriggerStyle:this.triggerStyle,onClick:this.handleTriggerClick}):null,this.bordered?o("div",{class:`${r}-layout-sider__border`}):null)}}),Ye={xmlns:"http://www.w3.org/2000/svg","xmlns:xlink":"http://www.w3.org/1999/xlink",viewBox:"0 0 32 32"},We=w({name:"LoadBalancerGlobal",render:function(r,t){return C(),j("svg",Ye,t[0]||(t[0]=[ve('<path d="M4 26h4v4H4z" fill="currentColor"></path><path d="M14 26h4v4h-4z" fill="currentColor"></path><path d="M24 26h4v4h-4z" fill="currentColor"></path><path d="M25 16h-8v-4h-2v4H7a2.002 2.002 0 0 0-2 2v6h2v-6h8v6h2v-6h8v6h2v-6a2.002 2.002 0 0 0-2-2z" fill="currentColor"></path><path d="M16 10a4 4 0 1 1 4-4a4.005 4.005 0 0 1-4 4zm0-6a2 2 0 1 0 2 2a2.002 2.002 0 0 0-2-2z" fill="currentColor"></path>',5)]))}}),Ke={xmlns:"http://www.w3.org/2000/svg","xmlns:xlink":"http://www.w3.org/1999/xlink",viewBox:"0 0 32 32"},Ue=w({name:"Parameter",render:function(r,t){return C(),j("svg",Ke,t[0]||(t[0]=[v("path",{d:"M28 13V8a2.002 2.002 0 0 0-2-2h-3v2h3v5a3.976 3.976 0 0 0 1.382 3A3.976 3.976 0 0 0 26 19v5h-3v2h3a2.002 2.002 0 0 0 2-2v-5a2.002 2.002 0 0 1 2-2v-2a2.002 2.002 0 0 1-2-2z",fill:"currentColor"},null,-1),v("path",{d:"M17 9l-.857 3h2L19 9h2l-.857 3H22v2h-2.428l-1.143 4H21v2h-3.143L17 23h-2l.857-3h-2L13 23h-2l.857-3H10v-2h2.429l1.143-4H11v-2h3.143L15 9zm.572 5h-2l-1.143 4h2z","fill-rule":"evenodd",fill:"currentColor"},null,-1),v("path",{d:"M6 13V8h3V6H6a2.002 2.002 0 0 0-2 2v5a2.002 2.002 0 0 1-2 2v2a2.002 2.002 0 0 1 2 2v5a2.002 2.002 0 0 0 2 2h3v-2H6v-5a3.976 3.976 0 0 0-1.382-3A3.976 3.976 0 0 0 6 13z",fill:"currentColor"},null,-1)]))}}),Ge={xmlns:"http://www.w3.org/2000/svg","xmlns:xlink":"http://www.w3.org/1999/xlink",viewBox:"0 0 24 24"},Xe=w({name:"FiberNewRound",render:function(r,t){return C(),j("svg",Ge,t[0]||(t[0]=[v("path",{d:"M20 4H4c-1.11 0-1.99.89-1.99 2L2 18c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V6c0-1.11-.89-2-2-2zM8.5 14.21c0 .43-.36.79-.79.79c-.25 0-.49-.12-.64-.33L4.75 11.5v2.88c0 .35-.28.62-.62.62s-.63-.28-.63-.62V9.79c0-.43.36-.79.79-.79h.05c.26 0 .5.12.65.33l2.26 3.17V9.62c0-.34.28-.62.63-.62s.62.28.62.62v4.59zm5-4.57c0 .35-.28.62-.62.62H11v1.12h1.88c.35 0 .62.28.62.62v.01c0 .35-.28.62-.62.62H11v1.11h1.88c.35 0 .62.28.62.62c0 .35-.28.62-.62.62h-2.53a.85.85 0 0 1-.85-.85v-4.3c0-.45.38-.83.85-.83h2.53c.35 0 .62.28.62.62v.02zm7 4.36c0 .55-.45 1-1 1h-4c-.55 0-1-.45-1-1V9.62c0-.34.28-.62.62-.62s.62.28.62.62v3.89h1.13v-2.9c0-.35.28-.62.62-.62s.62.28.62.62v2.89h1.12V9.62c0-.35.28-.62.62-.62s.62.28.62.62V14z",fill:"currentColor"},null,-1)]))}}),Je={xmlns:"http://www.w3.org/2000/svg","xmlns:xlink":"http://www.w3.org/1999/xlink",viewBox:"0 0 24 24"},Ze=w({name:"HistoryTwotone",render:function(r,t){return C(),j("svg",Je,t[0]||(t[0]=[v("path",{d:"M13 3a9 9 0 0 0-9 9H1l3.89 3.89l.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7s-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42A8.954 8.954 0 0 0 13 21a9 9 0 0 0 0-18zm-1 5v5l4.25 2.52l.77-1.28l-3.52-2.09V8z",fill:"currentColor"},null,-1)]))}}),Qe={xmlns:"http://www.w3.org/2000/svg","xmlns:xlink":"http://www.w3.org/1999/xlink",viewBox:"0 0 512 512"},et=w({name:"ExchangeAlt",render:function(r,t){return C(),j("svg",Qe,t[0]||(t[0]=[v("path",{d:"M0 168v-16c0-13.255 10.745-24 24-24h360V80c0-21.367 25.899-32.042 40.971-16.971l80 80c9.372 9.373 9.372 24.569 0 33.941l-80 80C409.956 271.982 384 261.456 384 240v-48H24c-13.255 0-24-10.745-24-24zm488 152H128v-48c0-21.314-25.862-32.08-40.971-16.971l-80 80c-9.372 9.373-9.372 24.569 0 33.941l80 80C102.057 463.997 128 453.437 128 432v-48h360c13.255 0 24-10.745 24-24v-16c0-13.255-10.745-24-24-24z",fill:"currentColor"},null,-1)]))}}),tt={class:"cursor-pointer !px-0 !py-4 space-s-a !mb-3 !mt-4 space-h-s",style:{padding:"0"},"show-icon":!1},ot={class:"mx-3 flex items-center justify-between"},rt={class:"flex items-center gap-1"},lt={class:"mx-3"},at=w({__name:"SpaceList",setup(e){fe(a=>({"72c404e2":b(p).dividerColor}));const r=J(),t=_e(),{t:c}=Z(),p=xe(),h=ee(),f=I(()=>{var a;return(a=h.spaceList)==null?void 0:a.find(x=>String(x.space_id)==r.query.space_id)}),V=a=>o("div",{class:"min-w-80 border-b hover:opacity-100 opacity-70 flex items-center gap-2 h-full",style:{color:p.value.textColor1,borderColor:p.value.dividerColor}},[o(K,{component:Ae}),o("span",{class:"font-bold text-base"},a.label),o("span",{class:"text-xs"},a.description)]),k=P(),z=()=>{var a;(a=k.value)==null||a.add()},H=()=>o("div",{class:"p-2 pb-0"},[o("div",{class:"flex justify-between item-center"},[o("span",{class:"font-bold leading-[28px] pl-1.5",style:{color:p.value.textColor1}},c("groupDetail.parameterManager.switchSpace")),o(Q,{onClick:z,type:"primary",size:"small"},{default:()=>c("groupDetail.parameterManager.createSpace"),icon:()=>o(oe)})]),o(Ce,{class:"!m-1 !mt-2"})]),m=(a,x)=>{t.push({name:r.name,query:{...r.query,space_id:x.value}})};return(a,x)=>{var T;const B=we,M=ye;return C(),F(M,{"render-label":V,"show-arrow":!0,options:[{key:"header",type:"render",render:H},...((T=b(h).spaceList)==null?void 0:T.map(d=>({...d,label:d.space_name,value:d.space_id})))||[]],onSelect:m,placement:"right-start",trigger:"click"},{default:_(()=>[v("div",tt,[v("div",ot,[v("div",rt,[g(B,{size:"tiny",type:"primary"},{default:_(()=>{var d;return[O(" #"+E((d=b(f))==null?void 0:d.space_id),1)]}),_:1}),g(b(X),{class:"font-bold max-w-[100px]","line-clamp":1},{default:_(()=>{var d;return[O(E((d=b(f))==null?void 0:d.space_name),1)]}),_:1})]),g(b(K),{component:b(et)},null,8,["component"])]),v("div",lt,[g(b(X),{"line-clamp":1,tooltip:!1,"expand-trigger":"click",class:"text-xs italic opacity-70 mt-2 pr-1"},{default:_(()=>{var d;return[O(E((d=b(f))==null?void 0:d.description),1)]}),_:1})]),g(te,{hidenbtns:!0,ref_key:"spaceToolsRef",ref:k},null,512)])]),_:1},8,["options"])}}}),nt=Se(at,[["__scopeId","data-v-5cc85506"]]),st={class:"m-3"},it={class:"font-bold text-lg"},ct={class:"pl-4"},Vt=w({__name:"ExpSpace",setup(e){const r=ee(),t=ke(),{t:c}=Z(),p=J(),h=P(),f=m=>()=>o(K,{size:16},{default:()=>o(m)}),V=[{label:()=>o(q,{to:{name:"exps",query:p.query}},{default:()=>c("groupDetail.parameterManager.tabExps")}),key:"exps",icon:f(je)},{icon:f(Ue),label:c("groupDetail.parameterManager.tabParams"),key:"params",children:[{label:()=>o(q,{to:{name:"poverview",query:p.query}},{default:()=>c("groupDetail.parameterManager.overview")}),key:"poverview",icon:f(We)},{label:()=>o(q,{to:{name:"platest",query:p.query}},{default:()=>c("groupDetail.parameterManager.globalLatest")}),key:"platest",icon:f(Xe)},{label:()=>o(q,{to:{name:"phistory",query:p.query}},{default:()=>c("groupDetail.parameterManager.globalHistory")}),key:"phistory",icon:f(Ze)}]}],k=()=>{["exps","poverview","platest","phistory"].includes(p.name)?h.value=p.name:h.value="exps"};Te(()=>{k()}),ze(()=>{k()}),Be(()=>t.groupDetailFetched,m=>{var a;m&&(r.curSpace=(a=r.spaceList)==null?void 0:a.find(x=>String(x.space_id)==p.query.space_id))},{immediate:!0});const z=P(),H=()=>{var m;(m=z.value)==null||m.add()};return(m,a)=>{const x=Re,B=Q,M=Oe,T=Me("router-view"),d=Le,Y=Ve;return C(),F(Y,{"has-sider":""},{default:_(()=>[g(M,{style:{height:"calc(100vh - 170px)"},width:"200px"},{default:_(()=>[v("div",st,[g(Ee,null,{default:_(()=>[v("span",it,E(b(c)("groupDetail.parameterManager.expSpace")),1)]),_:1})]),g(nt),g(x,{accordion:!1,collapsed:!1,"icon-size":0,options:V,indent:12,"root-indent":20,"default-expand-all":!0,value:b(h),"onUpdate:value":a[0]||(a[0]=R=>$e(h)?h.value=R:null),responsive:""},null,8,["value"]),g(B,{type:"primary",onClick:H,style:{width:"calc(100% - 16px)",position:"absolute",bottom:"8px",left:"8px"}},{icon:_(()=>[g(b(oe))]),default:_(()=>[O(" "+E(b(c)("groupDetail.parameterManager.createSpace")),1)]),_:1})]),_:1}),g(d,null,{default:_(()=>[v("div",ct,[g(He),g(T,null,{default:_(({Component:R})=>[(C(),F(Ie,null,[(C(),F(Pe(R),{key:m.$route.fullPath}))],1024))]),_:1})])]),_:1}),g(te,{hidenbtns:!0,ref_key:"spaceToolsRef",ref:z},null,512)]),_:1})}}});export{Vt as default};
