import{d as Ee,a0 as pt,aP as Pt,aE as Nt,G as P,aY as Wt,bb as Vt,bc as jt,bd as Zt,bg as Xt,bk as Gt,$ as $t,C as _t,Y as qt,a_ as Kt,aZ as Qt,S as xt,D as Jt,H as K,f as Lt,c2 as Yt,c3 as es,v as Te,V as D,w as Ve,o as Ie,c4 as ts,c as J,L as pe,c5 as Re,c6 as Oe,c7 as ss,u as q,c8 as rs,a as ne,g as Y,Q as os,b0 as we,y as he,R as oe,B as ns,c9 as Fe,p as is,aK as as}from"./index-C7ioxznG.js";import{_ as Ce}from"./index-BmJkaHuF.js";import{ShaderMaterial as mt}from"./shaderMaterial-CJtFf-M9.js";import"./clipPlaneFragment-De5ww3cH.js";import"./logDepthDeclaration-DsfLzvRF.js";import"./fogFragment-6nUqOaEp.js";import"./sceneUboDeclaration-Cl2yaWm5.js";import"./meshUboDeclaration-DRZ9rSBM.js";import"./clipPlaneVertex-CtJF83UU.js";import"./logDepthVertex-BgtVDjSs.js";import"./helperFunctions-B2fIE0QR.js";import"./clipPlaneFragment-Dj_n1rvQ.js";import"./logDepthDeclaration-DJ5VZ8Qf.js";import"./fogFragment-BAJ-Imxj.js";import"./sceneUboDeclaration-DbExGHC1.js";import"./meshUboDeclaration-DfeiWLXB.js";import"./helperFunctions-CFR2hQoc.js";import"./clipPlaneVertex-BFcaiwOj.js";import"./logDepthVertex-DG6UmMM-.js";import{R as be}from"./rawTexture-B_Rn1rXF.js";import"./thinInstanceMesh-ClAKTXM0.js";import{A as cs}from"./assetContainer-WmWzRef8.js";import{Ray as ls}from"./ray-CggSRU6m.js";import{S as hs}from"./standardMaterial-BUPzOZe7.js";class fs{constructor(){this.mm=new Map}get(e,t){const s=this.mm.get(e);if(s!==void 0)return s.get(t)}set(e,t,s){let n=this.mm.get(e);n===void 0&&this.mm.set(e,n=new Map),n.set(t,s)}}class us{get standalone(){var e;return((e=this._options)==null?void 0:e.standalone)??!1}get baseMaterial(){return this._baseMaterial}get doNotInjectCode(){var e;return((e=this._options)==null?void 0:e.doNotInjectCode)??!1}constructor(e,t,s){this._baseMaterial=e,this._scene=t??Ee.LastCreatedScene,this._options=s,this._subMeshToEffect=new Map,this._subMeshToDepthWrapper=new fs,this._meshes=new Map,this._onEffectCreatedObserver=this._baseMaterial.onEffectCreatedObservable.add(n=>{var i,c;const o=(i=n.subMesh)==null?void 0:i.getMesh();o&&!this._meshes.has(o)&&this._meshes.set(o,o.onDisposeObservable.add(d=>{const a=this._subMeshToEffect.keys();for(let _=a.next();_.done!==!0;_=a.next()){const u=_.value;(u==null?void 0:u.getMesh())===d&&(this._subMeshToEffect.delete(u),this._deleteDepthWrapperEffect(u))}})),((c=this._subMeshToEffect.get(n.subMesh))==null?void 0:c[0])!==n.effect&&(this._subMeshToEffect.set(n.subMesh,[n.effect,this._scene.getEngine().currentRenderPassId]),this._deleteDepthWrapperEffect(n.subMesh))})}_deleteDepthWrapperEffect(e){const t=this._subMeshToDepthWrapper.mm.get(e);t&&(t.forEach(s=>{var n;(n=s.mainDrawWrapper.effect)==null||n.dispose()}),this._subMeshToDepthWrapper.mm.delete(e))}getEffect(e,t,s){var i;const n=(i=this._subMeshToDepthWrapper.mm.get(e))==null?void 0:i.get(t);if(!n)return null;let o=n.drawWrapper[s];return o||(o=n.drawWrapper[s]=new pt(this._scene.getEngine()),o.setEffect(n.mainDrawWrapper.effect,n.mainDrawWrapper.defines)),o}isReadyForSubMesh(e,t,s,n,o){var i;return this.standalone&&!this._baseMaterial.isReadyForSubMesh(e.getMesh(),e,n)?!1:((i=this._makeEffect(e,t,s,o))==null?void 0:i.isReady())??!1}dispose(){this._baseMaterial.onEffectCreatedObservable.remove(this._onEffectCreatedObserver),this._onEffectCreatedObserver=null;const e=this._meshes.entries();for(let t=e.next();t.done!==!0;t=e.next()){const[s,n]=t.value;s.onDisposeObservable.remove(n)}}_makeEffect(e,t,s,n){var x,y;const o=this._scene.getEngine(),i=this._subMeshToEffect.get(e);if(!i)return null;const[c,d]=i;if(!c.isReady())return null;let a=this._subMeshToDepthWrapper.get(e,s);if(!a){const I=new pt(o);I.defines=((x=e._getDrawWrapper(d))==null?void 0:x.defines)??null,a={drawWrapper:[],mainDrawWrapper:I,depthDefines:"",token:Pt()},a.drawWrapper[n]=I,this._subMeshToDepthWrapper.set(e,s,a)}const _=t.join(`
`);if(a.mainDrawWrapper.effect&&_===a.depthDefines)return a.mainDrawWrapper.effect;a.depthDefines=_;const u=c.getUniformNames().slice();let f=c.vertexSourceCodeBeforeMigration,p=c.fragmentSourceCodeBeforeMigration;if(!f&&!p)return null;if(!this.doNotInjectCode){const I=this._options&&this._options.remappedVariables?`#include<shadowMapVertexNormalBias>(${this._options.remappedVariables.join(",")})`:"#include<shadowMapVertexNormalBias>",l=this._options&&this._options.remappedVariables?`#include<shadowMapVertexMetric>(${this._options.remappedVariables.join(",")})`:"#include<shadowMapVertexMetric>",g=this._options&&this._options.remappedVariables?`#include<shadowMapFragmentSoftTransparentShadow>(${this._options.remappedVariables.join(",")})`:"#include<shadowMapFragmentSoftTransparentShadow>",S="#include<shadowMapFragment>",C="#include<shadowMapVertexExtraDeclaration>";c.shaderLanguage===0?f=f.replace(/void\s+?main/g,`
${C}
void main`):f=f.replace(/@vertex/g,`
${C}
@vertex`),f=f.replace(/#define SHADOWDEPTH_NORMALBIAS|#define CUSTOM_VERTEX_UPDATE_WORLDPOS/g,I),f.indexOf("#define SHADOWDEPTH_METRIC")!==-1?f=f.replace(/#define SHADOWDEPTH_METRIC/g,l):f=f.replace(/}\s*$/g,l+`
}`),f=f.replace(/#define SHADER_NAME.*?\n|out vec4 glFragColor;\n/g,"");const w=p.indexOf("#define SHADOWDEPTH_SOFTTRANSPARENTSHADOW")>=0||p.indexOf("#define CUSTOM_FRAGMENT_BEFORE_FOG")>=0,m=p.indexOf("#define SHADOWDEPTH_FRAGMENT")!==-1;let h="";w?p=p.replace(/#define SHADOWDEPTH_SOFTTRANSPARENTSHADOW|#define CUSTOM_FRAGMENT_BEFORE_FOG/g,g):h=g+`
`,p=p.replace(/void\s+?main/g,Nt.IncludesShadersStore.shadowMapFragmentExtraDeclaration+`
void main`),m?p=p.replace(/#define SHADOWDEPTH_FRAGMENT/g,S):h+=S+`
`,h&&(p=p.replace(/}\s*$/g,h+"}")),u.push("biasAndScaleSM","depthValuesSM","lightDataSM","softTransparentShadowSM")}a.mainDrawWrapper.effect=o.createEffect({vertexSource:f,fragmentSource:p,vertexToken:a.token,fragmentToken:a.token},{attributes:c.getAttributesNames(),uniformsNames:u,uniformBuffersNames:c.getUniformBuffersNames(),samplers:c.getSamplers(),defines:_+`
`+c.defines.replace("#define SHADOWS","").replace(/#define SHADOW\d/g,""),indexParameters:c.getIndexParameters(),shaderLanguage:c.shaderLanguage},o);for(let I=0;I<a.drawWrapper.length;++I)I!==n&&((y=a.drawWrapper[I])==null||y.setEffect(a.mainDrawWrapper.effect,a.mainDrawWrapper.defines));return a.mainDrawWrapper.effect}}const vt="gaussianSplattingFragmentDeclaration",ds=`vec4 gaussianColor(vec4 inColor)
{float A=-dot(vPosition,vPosition);if (A<-4.0) discard;float B=exp(A)*inColor.a;
#include<logDepthFragment>
vec3 color=inColor.rgb;
#ifdef FOG
#include<fogFragment>
#endif
return vec4(color,B);}
`;P.IncludesShadersStore[vt]||(P.IncludesShadersStore[vt]=ds);const Ue="gaussianSplattingPixelShader",Ot=`#include<clipPlaneFragmentDeclaration>
#include<logDepthDeclaration>
#include<fogFragmentDeclaration>
varying vec4 vColor;varying vec2 vPosition;
#include<gaussianSplattingFragmentDeclaration>
void main () { 
#include<clipPlaneFragment>
gl_FragColor=gaussianColor(vColor);}
`;P.ShadersStore[Ue]||(P.ShadersStore[Ue]=Ot);const ps={name:Ue,shader:Ot},_s=Object.freeze(Object.defineProperty({__proto__:null,gaussianSplattingPixelShader:ps},Symbol.toStringTag,{value:"Module"})),gt="gaussianSplattingVertexDeclaration",xs="attribute vec3 position;attribute vec4 splatIndex0;attribute vec4 splatIndex1;attribute vec4 splatIndex2;attribute vec4 splatIndex3;uniform mat4 view;uniform mat4 projection;uniform mat4 world;uniform vec4 vEyePosition;";P.IncludesShadersStore[gt]||(P.IncludesShadersStore[gt]=xs);const St="gaussianSplattingUboDeclaration",ms=`#include<sceneUboDeclaration>
#include<meshUboDeclaration>
attribute vec3 position;attribute vec4 splatIndex0;attribute vec4 splatIndex1;attribute vec4 splatIndex2;attribute vec4 splatIndex3;
`;P.IncludesShadersStore[St]||(P.IncludesShadersStore[St]=ms);const yt="gaussianSplatting",vs=`#if !defined(WEBGL2) && !defined(WEBGPU) && !defined(NATIVE)
mat3 transpose(mat3 matrix) {return mat3(matrix[0][0],matrix[1][0],matrix[2][0],
matrix[0][1],matrix[1][1],matrix[2][1],
matrix[0][2],matrix[1][2],matrix[2][2]);}
#endif
vec2 getDataUV(float index,vec2 textureSize) {float y=floor(index/textureSize.x);float x=index-y*textureSize.x;return vec2((x+0.5)/textureSize.x,(y+0.5)/textureSize.y);}
#if SH_DEGREE>0
ivec2 getDataUVint(float index,vec2 textureSize) {float y=floor(index/textureSize.x);float x=index-y*textureSize.x;return ivec2(uint(x+0.5),uint(y+0.5));}
#endif
struct Splat {vec4 center;vec4 color;vec4 covA;vec4 covB;
#if SH_DEGREE>0
uvec4 sh0; 
#endif
#if SH_DEGREE>1
uvec4 sh1;
#endif
#if SH_DEGREE>2
uvec4 sh2;
#endif
};float getSplatIndex(int localIndex)
{float splatIndex;switch (localIndex)
{case 0: splatIndex=splatIndex0.x; break;case 1: splatIndex=splatIndex0.y; break;case 2: splatIndex=splatIndex0.z; break;case 3: splatIndex=splatIndex0.w; break;case 4: splatIndex=splatIndex1.x; break;case 5: splatIndex=splatIndex1.y; break;case 6: splatIndex=splatIndex1.z; break;case 7: splatIndex=splatIndex1.w; break;case 8: splatIndex=splatIndex2.x; break;case 9: splatIndex=splatIndex2.y; break;case 10: splatIndex=splatIndex2.z; break;case 11: splatIndex=splatIndex2.w; break;case 12: splatIndex=splatIndex3.x; break;case 13: splatIndex=splatIndex3.y; break;case 14: splatIndex=splatIndex3.z; break;case 15: splatIndex=splatIndex3.w; break;}
return splatIndex;}
Splat readSplat(float splatIndex)
{Splat splat;vec2 splatUV=getDataUV(splatIndex,dataTextureSize);splat.center=texture2D(centersTexture,splatUV);splat.color=texture2D(colorsTexture,splatUV);splat.covA=texture2D(covariancesATexture,splatUV)*splat.center.w;splat.covB=texture2D(covariancesBTexture,splatUV)*splat.center.w;
#if SH_DEGREE>0
ivec2 splatUVint=getDataUVint(splatIndex,dataTextureSize);splat.sh0=texelFetch(shTexture0,splatUVint,0);
#endif
#if SH_DEGREE>1
splat.sh1=texelFetch(shTexture1,splatUVint,0);
#endif
#if SH_DEGREE>2
splat.sh2=texelFetch(shTexture2,splatUVint,0);
#endif
return splat;}
#if defined(WEBGL2) || defined(WEBGPU) || defined(NATIVE)
vec3 computeColorFromSHDegree(vec3 dir,const vec3 sh[16])
{const float SH_C0=0.28209479;const float SH_C1=0.48860251;float SH_C2[5];SH_C2[0]=1.092548430;SH_C2[1]=-1.09254843;SH_C2[2]=0.315391565;SH_C2[3]=-1.09254843;SH_C2[4]=0.546274215;float SH_C3[7];SH_C3[0]=-0.59004358;SH_C3[1]=2.890611442;SH_C3[2]=-0.45704579;SH_C3[3]=0.373176332;SH_C3[4]=-0.45704579;SH_C3[5]=1.445305721;SH_C3[6]=-0.59004358;vec3 result=/*SH_C0**/sh[0];
#if SH_DEGREE>0
float x=dir.x;float y=dir.y;float z=dir.z;result+=- SH_C1*y*sh[1]+SH_C1*z*sh[2]-SH_C1*x*sh[3];
#if SH_DEGREE>1
float xx=x*x,yy=y*y,zz=z*z;float xy=x*y,yz=y*z,xz=x*z;result+=
SH_C2[0]*xy*sh[4] +
SH_C2[1]*yz*sh[5] +
SH_C2[2]*(2.0*zz-xx-yy)*sh[6] +
SH_C2[3]*xz*sh[7] +
SH_C2[4]*(xx-yy)*sh[8];
#if SH_DEGREE>2
result+=
SH_C3[0]*y*(3.0*xx-yy)*sh[9] +
SH_C3[1]*xy*z*sh[10] +
SH_C3[2]*y*(4.0*zz-xx-yy)*sh[11] +
SH_C3[3]*z*(2.0*zz-3.0*xx-3.0*yy)*sh[12] +
SH_C3[4]*x*(4.0*zz-xx-yy)*sh[13] +
SH_C3[5]*z*(xx-yy)*sh[14] +
SH_C3[6]*x*(xx-3.0*yy)*sh[15];
#endif
#endif
#endif
return result;}
vec4 decompose(uint value)
{vec4 components=vec4(
float((value ) & 255u),
float((value>>uint( 8)) & 255u),
float((value>>uint(16)) & 255u),
float((value>>uint(24)) & 255u));return components*vec4(2./255.)-vec4(1.);}
vec3 computeSH(Splat splat,vec3 dir)
{vec3 sh[16];sh[0]=vec3(0.,0.,0.);
#if SH_DEGREE>0
vec4 sh00=decompose(splat.sh0.x);vec4 sh01=decompose(splat.sh0.y);vec4 sh02=decompose(splat.sh0.z);sh[1]=vec3(sh00.x,sh00.y,sh00.z);sh[2]=vec3(sh00.w,sh01.x,sh01.y);sh[3]=vec3(sh01.z,sh01.w,sh02.x);
#endif
#if SH_DEGREE>1
vec4 sh03=decompose(splat.sh0.w);vec4 sh04=decompose(splat.sh1.x);vec4 sh05=decompose(splat.sh1.y);sh[4]=vec3(sh02.y,sh02.z,sh02.w);sh[5]=vec3(sh03.x,sh03.y,sh03.z);sh[6]=vec3(sh03.w,sh04.x,sh04.y);sh[7]=vec3(sh04.z,sh04.w,sh05.x);sh[8]=vec3(sh05.y,sh05.z,sh05.w);
#endif
#if SH_DEGREE>2
vec4 sh06=decompose(splat.sh1.z);vec4 sh07=decompose(splat.sh1.w);vec4 sh08=decompose(splat.sh2.x);vec4 sh09=decompose(splat.sh2.y);vec4 sh10=decompose(splat.sh2.z);vec4 sh11=decompose(splat.sh2.w);sh[9]=vec3(sh06.x,sh06.y,sh06.z);sh[10]=vec3(sh06.w,sh07.x,sh07.y);sh[11]=vec3(sh07.z,sh07.w,sh08.x);sh[12]=vec3(sh08.y,sh08.z,sh08.w);sh[13]=vec3(sh09.x,sh09.y,sh09.z);sh[14]=vec3(sh09.w,sh10.x,sh10.y);sh[15]=vec3(sh10.z,sh10.w,sh11.x); 
#endif
return computeColorFromSHDegree(dir,sh);}
#else
vec3 computeSH(Splat splat,vec3 dir)
{return vec3(0.,0.,0.);}
#endif
vec4 gaussianSplatting(vec2 meshPos,vec3 worldPos,vec2 scale,vec3 covA,vec3 covB,mat4 worldMatrix,mat4 viewMatrix,mat4 projectionMatrix)
{mat4 modelView=viewMatrix*worldMatrix;vec4 camspace=viewMatrix*vec4(worldPos,1.);vec4 pos2d=projectionMatrix*camspace;float bounds=1.2*pos2d.w;if (pos2d.z<-pos2d.w || pos2d.x<-bounds || pos2d.x>bounds
|| pos2d.y<-bounds || pos2d.y>bounds) {return vec4(0.0,0.0,2.0,1.0);}
mat3 Vrk=mat3(
covA.x,covA.y,covA.z,
covA.y,covB.x,covB.y,
covA.z,covB.y,covB.z
);bool isOrtho=abs(projectionMatrix[3][3]-1.0)<0.001;mat3 J;if (isOrtho) {J=mat3(
focal.x,0.,0.,
0.,focal.y,0.,
0.,0.,0.
);} else {J=mat3(
focal.x/camspace.z,0.,-(focal.x*camspace.x)/(camspace.z*camspace.z),
0.,focal.y/camspace.z,-(focal.y*camspace.y)/(camspace.z*camspace.z),
0.,0.,0.
);}
mat3 T=transpose(mat3(modelView))*J;mat3 cov2d=transpose(T)*Vrk*T;
#if COMPENSATION
float c00=cov2d[0][0];float c11=cov2d[1][1];float c01=cov2d[0][1];float detOrig=c00*c11-c01*c01;
#endif
cov2d[0][0]+=kernelSize;cov2d[1][1]+=kernelSize;
#if COMPENSATION
vec3 c2d=vec3(cov2d[0][0],c01,cov2d[1][1]);float detBlur=c2d.x*c2d.z-c2d.y*c2d.y;float compensation=sqrt(max(0.,detOrig/detBlur));vColor.w*=compensation;
#endif
float mid=(cov2d[0][0]+cov2d[1][1])/2.0;float radius=length(vec2((cov2d[0][0]-cov2d[1][1])/2.0,cov2d[0][1]));float epsilon=0.0001;float lambda1=mid+radius+epsilon,lambda2=mid-radius+epsilon;if (lambda2<0.0)
{return vec4(0.0,0.0,2.0,1.0);}
vec2 diagonalVector=normalize(vec2(cov2d[0][1],lambda1-cov2d[0][0]));vec2 majorAxis=min(sqrt(2.0*lambda1),1024.0)*diagonalVector;vec2 minorAxis=min(sqrt(2.0*lambda2),1024.0)*vec2(diagonalVector.y,-diagonalVector.x);vec2 vCenter=vec2(pos2d);float scaleFactor=isOrtho ? 1.0 : pos2d.w;return vec4(
vCenter 
+ ((meshPos.x*majorAxis
+ meshPos.y*minorAxis)*invViewport*scaleFactor)*scale,pos2d.zw);}`;P.IncludesShadersStore[yt]||(P.IncludesShadersStore[yt]=vs);const Pe="gaussianSplattingVertexShader",Ft=`#include<__decl__gaussianSplattingVertex>
#ifdef LOGARITHMICDEPTH
#extension GL_EXT_frag_depth : enable
#endif
#include<clipPlaneVertexDeclaration>
#include<fogVertexDeclaration>
#include<logDepthDeclaration>
#include<helperFunctions>
uniform vec2 invViewport;uniform vec2 dataTextureSize;uniform vec2 focal;uniform float kernelSize;uniform vec3 eyePosition;uniform float alpha;uniform sampler2D covariancesATexture;uniform sampler2D covariancesBTexture;uniform sampler2D centersTexture;uniform sampler2D colorsTexture;
#if SH_DEGREE>0
uniform highp usampler2D shTexture0;
#endif
#if SH_DEGREE>1
uniform highp usampler2D shTexture1;
#endif
#if SH_DEGREE>2
uniform highp usampler2D shTexture2;
#endif
varying vec4 vColor;varying vec2 vPosition;
#include<gaussianSplatting>
void main () {float splatIndex=getSplatIndex(int(position.z+0.5));Splat splat=readSplat(splatIndex);vec3 covA=splat.covA.xyz;vec3 covB=vec3(splat.covA.w,splat.covB.xy);vec4 worldPos=world*vec4(splat.center.xyz,1.0);vColor=splat.color;vPosition=position.xy;
#if SH_DEGREE>0
mat3 worldRot=mat3(world);mat3 normWorldRot=inverseMat3(worldRot);vec3 eyeToSplatLocalSpace=normalize(normWorldRot*(worldPos.xyz-eyePosition));vColor.xyz=splat.color.xyz+computeSH(splat,eyeToSplatLocalSpace);
#endif
vColor.w*=alpha;gl_Position=gaussianSplatting(position.xy,worldPos.xyz,vec2(1.,1.),covA,covB,world,view,projection);
#include<clipPlaneVertex>
#include<fogVertex>
#include<logDepthVertex>
}
`;P.ShadersStore[Pe]||(P.ShadersStore[Pe]=Ft);const gs={name:Pe,shader:Ft},Ss=Object.freeze(Object.defineProperty({__proto__:null,gaussianSplattingVertexShader:gs},Symbol.toStringTag,{value:"Module"})),wt="gaussianSplattingFragmentDeclaration",ys=`fn gaussianColor(inColor: vec4f,inPosition: vec2f)->vec4f
{var A : f32=-dot(inPosition,inPosition);if (A>-4.0)
{var B: f32=exp(A)*inColor.a;
#include<logDepthFragment>
var color: vec3f=inColor.rgb;
#ifdef FOG
#include<fogFragment>
#endif
return vec4f(color,B);} else {return vec4f(0.0);}}
`;P.IncludesShadersStoreWGSL[wt]||(P.IncludesShadersStoreWGSL[wt]=ys);const Ne="gaussianSplattingPixelShader",Bt=`#include<clipPlaneFragmentDeclaration>
#include<logDepthDeclaration>
#include<fogFragmentDeclaration>
varying vColor: vec4f;varying vPosition: vec2f;
#include<gaussianSplattingFragmentDeclaration>
@fragment
fn main(input: FragmentInputs)->FragmentOutputs {
#include<clipPlaneFragment>
fragmentOutputs.color=gaussianColor(input.vColor,input.vPosition);}
`;P.ShadersStoreWGSL[Ne]||(P.ShadersStoreWGSL[Ne]=Bt);const ws={name:Ne,shader:Bt},Cs=Object.freeze(Object.defineProperty({__proto__:null,gaussianSplattingPixelShaderWGSL:ws},Symbol.toStringTag,{value:"Module"})),Ct="gaussianSplatting",bs=`fn getDataUV(index: f32,dataTextureSize: vec2f)->vec2<f32> {let y: f32=floor(index/dataTextureSize.x);let x: f32=index-y*dataTextureSize.x;return vec2f((x+0.5),(y+0.5));}
struct Splat {center: vec4f,
color: vec4f,
covA: vec4f,
covB: vec4f,
#if SH_DEGREE>0
sh0: vec4<u32>,
#endif
#if SH_DEGREE>1
sh1: vec4<u32>,
#endif
#if SH_DEGREE>2
sh2: vec4<u32>,
#endif
};fn getSplatIndex(localIndex: i32,splatIndex0: vec4f,splatIndex1: vec4f,splatIndex2: vec4f,splatIndex3: vec4f)->f32 {var splatIndex: f32;switch (localIndex)
{case 0:
{splatIndex=splatIndex0.x;break;}
case 1:
{splatIndex=splatIndex0.y;break;}
case 2:
{splatIndex=splatIndex0.z;break;}
case 3:
{splatIndex=splatIndex0.w;break;}
case 4:
{splatIndex=splatIndex1.x;break;}
case 5:
{splatIndex=splatIndex1.y;break;}
case 6:
{splatIndex=splatIndex1.z;break;}
case 7:
{splatIndex=splatIndex1.w;break;}
case 8:
{splatIndex=splatIndex2.x;break;}
case 9:
{splatIndex=splatIndex2.y;break;}
case 10:
{splatIndex=splatIndex2.z;break;}
case 11:
{splatIndex=splatIndex2.w;break;}
case 12:
{splatIndex=splatIndex3.x;break;}
case 13:
{splatIndex=splatIndex3.y;break;}
case 14:
{splatIndex=splatIndex3.z;break;}
default:
{splatIndex=splatIndex3.w;break;}}
return splatIndex;}
fn readSplat(splatIndex: f32,dataTextureSize: vec2f)->Splat {var splat: Splat;let splatUV=getDataUV(splatIndex,dataTextureSize);let splatUVi32=vec2<i32>(i32(splatUV.x),i32(splatUV.y));splat.center=textureLoad(centersTexture,splatUVi32,0);splat.color=textureLoad(colorsTexture,splatUVi32,0);splat.covA=textureLoad(covariancesATexture,splatUVi32,0)*splat.center.w;splat.covB=textureLoad(covariancesBTexture,splatUVi32,0)*splat.center.w;
#if SH_DEGREE>0
splat.sh0=textureLoad(shTexture0,splatUVi32,0);
#endif
#if SH_DEGREE>1
splat.sh1=textureLoad(shTexture1,splatUVi32,0);
#endif
#if SH_DEGREE>2
splat.sh2=textureLoad(shTexture2,splatUVi32,0);
#endif
return splat;}
fn computeColorFromSHDegree(dir: vec3f,sh: array<vec3<f32>,16>)->vec3f
{let SH_C0: f32=0.28209479;let SH_C1: f32=0.48860251;var SH_C2: array<f32,5>=array<f32,5>(
1.092548430,
-1.09254843,
0.315391565,
-1.09254843,
0.546274215
);var SH_C3: array<f32,7>=array<f32,7>(
-0.59004358,
2.890611442,
-0.45704579,
0.373176332,
-0.45704579,
1.445305721,
-0.59004358
);var result: vec3f=/*SH_C0**/sh[0];
#if SH_DEGREE>0
let x: f32=dir.x;let y: f32=dir.y;let z: f32=dir.z;result+=-SH_C1*y*sh[1]+SH_C1*z*sh[2]-SH_C1*x*sh[3];
#if SH_DEGREE>1
let xx: f32=x*x;let yy: f32=y*y;let zz: f32=z*z;let xy: f32=x*y;let yz: f32=y*z;let xz: f32=x*z;result+=
SH_C2[0]*xy*sh[4] +
SH_C2[1]*yz*sh[5] +
SH_C2[2]*(2.0f*zz-xx-yy)*sh[6] +
SH_C2[3]*xz*sh[7] +
SH_C2[4]*(xx-yy)*sh[8];
#if SH_DEGREE>2
result+=
SH_C3[0]*y*(3.0f*xx-yy)*sh[9] +
SH_C3[1]*xy*z*sh[10] +
SH_C3[2]*y*(4.0f*zz-xx-yy)*sh[11] +
SH_C3[3]*z*(2.0f*zz-3.0f*xx-3.0f*yy)*sh[12] +
SH_C3[4]*x*(4.0f*zz-xx-yy)*sh[13] +
SH_C3[5]*z*(xx-yy)*sh[14] +
SH_C3[6]*x*(xx-3.0f*yy)*sh[15];
#endif
#endif
#endif
return result;}
fn decompose(value: u32)->vec4f
{let components : vec4f=vec4f(
f32((value ) & 255u),
f32((value>>u32( 8)) & 255u),
f32((value>>u32(16)) & 255u),
f32((value>>u32(24)) & 255u));return components*vec4f(2./255.)-vec4f(1.);}
fn computeSH(splat: Splat,dir: vec3f)->vec3f
{var sh: array<vec3<f32>,16>;sh[0]=vec3f(0.,0.,0.);
#if SH_DEGREE>0
let sh00: vec4f=decompose(splat.sh0.x);let sh01: vec4f=decompose(splat.sh0.y);let sh02: vec4f=decompose(splat.sh0.z);sh[1]=vec3f(sh00.x,sh00.y,sh00.z);sh[2]=vec3f(sh00.w,sh01.x,sh01.y);sh[3]=vec3f(sh01.z,sh01.w,sh02.x);
#endif
#if SH_DEGREE>1
let sh03: vec4f=decompose(splat.sh0.w);let sh04: vec4f=decompose(splat.sh1.x);let sh05: vec4f=decompose(splat.sh1.y);sh[4]=vec3f(sh02.y,sh02.z,sh02.w);sh[5]=vec3f(sh03.x,sh03.y,sh03.z);sh[6]=vec3f(sh03.w,sh04.x,sh04.y);sh[7]=vec3f(sh04.z,sh04.w,sh05.x);sh[8]=vec3f(sh05.y,sh05.z,sh05.w);
#endif
#if SH_DEGREE>2
let sh06: vec4f=decompose(splat.sh1.z);let sh07: vec4f=decompose(splat.sh1.w);let sh08: vec4f=decompose(splat.sh2.x);let sh09: vec4f=decompose(splat.sh2.y);let sh10: vec4f=decompose(splat.sh2.z);let sh11: vec4f=decompose(splat.sh2.w);sh[9]=vec3f(sh06.x,sh06.y,sh06.z);sh[10]=vec3f(sh06.w,sh07.x,sh07.y);sh[11]=vec3f(sh07.z,sh07.w,sh08.x);sh[12]=vec3f(sh08.y,sh08.z,sh08.w);sh[13]=vec3f(sh09.x,sh09.y,sh09.z);sh[14]=vec3f(sh09.w,sh10.x,sh10.y);sh[15]=vec3f(sh10.z,sh10.w,sh11.x); 
#endif
return computeColorFromSHDegree(dir,sh);}
fn gaussianSplatting(
meshPos: vec2<f32>,
worldPos: vec3<f32>,
scale: vec2<f32>,
covA: vec3<f32>,
covB: vec3<f32>,
worldMatrix: mat4x4<f32>,
viewMatrix: mat4x4<f32>,
projectionMatrix: mat4x4<f32>,
focal: vec2f,
invViewport: vec2f,
kernelSize: f32
)->vec4f {let modelView=viewMatrix*worldMatrix;let camspace=viewMatrix*vec4f(worldPos,1.0);let pos2d=projectionMatrix*camspace;let bounds=1.2*pos2d.w;if (pos2d.z<0. || pos2d.x<-bounds || pos2d.x>bounds || pos2d.y<-bounds || pos2d.y>bounds) {return vec4f(0.0,0.0,2.0,1.0);}
let Vrk=mat3x3<f32>(
covA.x,covA.y,covA.z,
covA.y,covB.x,covB.y,
covA.z,covB.y,covB.z
);let isOrtho=abs(projectionMatrix[3][3]-1.0)<0.001;var J: mat3x3<f32>;if (isOrtho) {J=mat3x3<f32>(
focal.x,0.0,0.0,
0.0,focal.y,0.0,
0.0,0.0,0.0
);} else {J=mat3x3<f32>(
focal.x/camspace.z,0.0,-(focal.x*camspace.x)/(camspace.z*camspace.z),
0.0,focal.y/camspace.z,-(focal.y*camspace.y)/(camspace.z*camspace.z),
0.0,0.0,0.0
);}
let T=transpose(mat3x3<f32>(
modelView[0].xyz,
modelView[1].xyz,
modelView[2].xyz))*J;var cov2d=transpose(T)*Vrk*T;
#if COMPENSATION
let c00: f32=cov2d[0][0];let c11: f32=cov2d[1][1];let c01: f32=cov2d[0][1];let detOrig: f32=c00*c11-c01*c01;
#endif
cov2d[0][0]+=kernelSize;cov2d[1][1]+=kernelSize;
#if COMPENSATION
let c2d: vec3f=vec3f(cov2d[0][0],c01,cov2d[1][1]);let detBlur: f32=c2d.x*c2d.z-c2d.y*c2d.y;let compensation: f32=sqrt(max(0.,detOrig/detBlur));vertexOutputs.vColor.w*=compensation;
#endif
let mid=(cov2d[0][0]+cov2d[1][1])/2.0;let radius=length(vec2<f32>((cov2d[0][0]-cov2d[1][1])/2.0,cov2d[0][1]));let lambda1=mid+radius;let lambda2=mid-radius;if (lambda2<0.0) {return vec4f(0.0,0.0,2.0,1.0);}
let diagonalVector=normalize(vec2<f32>(cov2d[0][1],lambda1-cov2d[0][0]));let majorAxis=min(sqrt(2.0*lambda1),1024.0)*diagonalVector;let minorAxis=min(sqrt(2.0*lambda2),1024.0)*vec2<f32>(diagonalVector.y,-diagonalVector.x);let vCenter=vec2<f32>(pos2d.x,pos2d.y);let scaleFactor=select(pos2d.w,1.0,isOrtho);return vec4f(
vCenter+((meshPos.x*majorAxis+meshPos.y*minorAxis)*invViewport*scaleFactor)*scale,
pos2d.z,
pos2d.w
);}`;P.IncludesShadersStoreWGSL[Ct]||(P.IncludesShadersStoreWGSL[Ct]=bs);const We="gaussianSplattingVertexShader",Ut=`#include<sceneUboDeclaration>
#include<meshUboDeclaration>
#include<helperFunctions>
#include<clipPlaneVertexDeclaration>
#include<fogVertexDeclaration>
#include<logDepthDeclaration>
attribute splatIndex0: vec4f;attribute splatIndex1: vec4f;attribute splatIndex2: vec4f;attribute splatIndex3: vec4f;attribute position: vec3f;uniform invViewport: vec2f;uniform dataTextureSize: vec2f;uniform focal: vec2f;uniform kernelSize: f32;uniform eyePosition: vec3f;uniform alpha: f32;var covariancesATexture: texture_2d<f32>;var covariancesBTexture: texture_2d<f32>;var centersTexture: texture_2d<f32>;var colorsTexture: texture_2d<f32>;
#if SH_DEGREE>0
var shTexture0: texture_2d<u32>;
#endif
#if SH_DEGREE>1
var shTexture1: texture_2d<u32>;
#endif
#if SH_DEGREE>2
var shTexture2: texture_2d<u32>;
#endif
varying vColor: vec4f;varying vPosition: vec2f;
#include<gaussianSplatting>
@vertex
fn main(input : VertexInputs)->FragmentInputs {let splatIndex: f32=getSplatIndex(i32(input.position.z+0.5),input.splatIndex0,input.splatIndex1,input.splatIndex2,input.splatIndex3);var splat: Splat=readSplat(splatIndex,uniforms.dataTextureSize);var covA: vec3f=splat.covA.xyz;var covB: vec3f=vec3f(splat.covA.w,splat.covB.xy);let worldPos: vec4f=mesh.world*vec4f(splat.center.xyz,1.0);vertexOutputs.vPosition=input.position.xy;
#if SH_DEGREE>0
let worldRot: mat3x3f= mat3x3f(mesh.world[0].xyz,mesh.world[1].xyz,mesh.world[2].xyz);let normWorldRot: mat3x3f=inverseMat3(worldRot);var eyeToSplatLocalSpace: vec3f=normalize(normWorldRot*(worldPos.xyz-uniforms.eyePosition.xyz));vertexOutputs.vColor=vec4f(splat.color.xyz+computeSH(splat,eyeToSplatLocalSpace),splat.color.w*uniforms.alpha);
#else
vertexOutputs.vColor=vec4f(splat.color.xyz,splat.color.w*uniforms.alpha);
#endif
vertexOutputs.position=gaussianSplatting(input.position.xy,worldPos.xyz,vec2f(1.0,1.0),covA,covB,mesh.world,scene.view,scene.projection,uniforms.focal,uniforms.invViewport,uniforms.kernelSize);
#include<clipPlaneVertex>
#include<fogVertex>
#include<logDepthVertex>
}
`;P.ShadersStoreWGSL[We]||(P.ShadersStoreWGSL[We]=Ut);const Is={name:We,shader:Ut},Es=Object.freeze(Object.defineProperty({__proto__:null,gaussianSplattingVertexShaderWGSL:Is},Symbol.toStringTag,{value:"Module"})),bt="gaussianSplattingDepthPixelShader",Ts=`precision highp float;varying vec2 vPosition;varying vec4 vColor;
#ifdef DEPTH_RENDER
varying float vDepthMetric;
#endif
void main(void) {float A=-dot(vPosition,vPosition);
#if defined(SM_SOFTTRANSPARENTSHADOW) && SM_SOFTTRANSPARENTSHADOW==1
float alpha=exp(A)*vColor.a;if (A<-4.) discard;
#else
if (A<-vColor.a) discard;
#endif
#ifdef DEPTH_RENDER
gl_FragColor=vec4(vDepthMetric,0.0,0.0,1.0);
#endif
}`;P.ShadersStore[bt]||(P.ShadersStore[bt]=Ts);const It="gaussianSplattingDepthVertexShader",Ds=`#include<__decl__gaussianSplattingVertex>
uniform vec2 invViewport;uniform vec2 dataTextureSize;uniform vec2 focal;uniform float kernelSize;uniform float alpha;uniform sampler2D covariancesATexture;uniform sampler2D covariancesBTexture;uniform sampler2D centersTexture;uniform sampler2D colorsTexture;varying vec2 vPosition;varying vec4 vColor;
#include<gaussianSplatting>
#ifdef DEPTH_RENDER
uniform vec2 depthValues;varying float vDepthMetric;
#endif
void main(void) {float splatIndex=getSplatIndex(int(position.z+0.5));Splat splat=readSplat(splatIndex);vec3 covA=splat.covA.xyz;vec3 covB=vec3(splat.covA.w,splat.covB.xy);vec4 worldPosGS=world*vec4(splat.center.xyz,1.0);vPosition=position.xy;vColor=splat.color;vColor.w*=alpha;gl_Position=gaussianSplatting(position.xy,worldPosGS.xyz,vec2(1.,1.),covA,covB,world,view,projection);
#ifdef DEPTH_RENDER
#ifdef USE_REVERSE_DEPTHBUFFER
vDepthMetric=((-gl_Position.z+depthValues.x)/(depthValues.y));
#else
vDepthMetric=((gl_Position.z+depthValues.x)/(depthValues.y));
#endif
#endif
}`;P.ShadersStore[It]||(P.ShadersStore[It]=Ds);const Et="gaussianSplattingDepthPixelShader",As=`#include<gaussianSplattingFragmentDeclaration>
varying vPosition: vec2f;varying vColor: vec4f;
#ifdef DEPTH_RENDER
varying vDepthMetric: f32;
#endif
fn checkDiscard(inPosition: vec2f,inColor: vec4f)->vec4f {var A : f32=-dot(inPosition,inPosition);var alpha : f32=exp(A)*inColor.a;
#if defined(SM_SOFTTRANSPARENTSHADOW) && SM_SOFTTRANSPARENTSHADOW==1
if (A<-4.) {discard;}
#else
if (A<-inColor.a) {discard;}
#endif
#ifdef DEPTH_RENDER
return vec4f(fragmentInputs.vDepthMetric,0.0,0.0,1.0);
#else
return vec4f(inColor.rgb,alpha);
#endif
}
#define CUSTOM_FRAGMENT_DEFINITIONS
@fragment
fn main(input: FragmentInputs)->FragmentOutputs {fragmentOutputs.color=checkDiscard(fragmentInputs.vPosition,fragmentInputs.vColor);
#if defined(SM_SOFTTRANSPARENTSHADOW) && SM_SOFTTRANSPARENTSHADOW==1
var alpha : f32=fragmentOutputs.color.a;
#endif
}
`;P.ShadersStoreWGSL[Et]||(P.ShadersStoreWGSL[Et]=As);const Tt="gaussianSplattingDepthVertexShader",Ms=`#include<sceneUboDeclaration>
#include<meshUboDeclaration>
attribute splatIndex0: vec4f;attribute splatIndex1: vec4f;attribute splatIndex2: vec4f;attribute splatIndex3: vec4f;attribute position: vec3f;uniform invViewport: vec2f;uniform dataTextureSize: vec2f;uniform focal: vec2f;uniform kernelSize: f32;uniform alpha: f32;var covariancesATexture: texture_2d<f32>;var covariancesBTexture: texture_2d<f32>;var centersTexture: texture_2d<f32>;var colorsTexture: texture_2d<f32>;varying vPosition: vec2f;varying vColor: vec4f;
#ifdef DEPTH_RENDER
uniform depthValues: vec2f;varying vDepthMetric: f32;
#endif
#include<gaussianSplatting>
@vertex
fn main(input : VertexInputs)->FragmentInputs {let splatIndex: f32=getSplatIndex(i32(input.position.z+0.5),input.splatIndex0,input.splatIndex1,input.splatIndex2,input.splatIndex3);var splat: Splat=readSplat(splatIndex,uniforms.dataTextureSize);var covA: vec3f=splat.covA.xyz;var covB: vec3f=vec3f(splat.covA.w,splat.covB.xy);let worldPos: vec4f=mesh.world*vec4f(splat.center.xyz,1.0);vertexOutputs.vPosition=input.position.xy;vertexOutputs.vColor=splat.color;vertexOutputs.vColor.w*=uniforms.alpha;vertexOutputs.position=gaussianSplatting(input.position.xy,worldPos.xyz,vec2f(1.0,1.0),covA,covB,mesh.world,scene.view,scene.projection,uniforms.focal,uniforms.invViewport,uniforms.kernelSize);
#ifdef DEPTH_RENDER
#ifdef USE_REVERSE_DEPTHBUFFER
vertexOutputs.vDepthMetric=((-vertexOutputs.position.z+uniforms.depthValues.x)/(uniforms.depthValues.y));
#else
vertexOutputs.vDepthMetric=((vertexOutputs.position.z+uniforms.depthValues.x)/(uniforms.depthValues.y));
#endif
#endif
}`;P.ShadersStoreWGSL[Tt]||(P.ShadersStoreWGSL[Tt]=Ms);class zs extends Jt{constructor(){super(),this.FOG=!1,this.THIN_INSTANCES=!0,this.LOGARITHMICDEPTH=!1,this.CLIPPLANE=!1,this.CLIPPLANE2=!1,this.CLIPPLANE3=!1,this.CLIPPLANE4=!1,this.CLIPPLANE5=!1,this.CLIPPLANE6=!1,this.SH_DEGREE=0,this.COMPENSATION=!1,this.rebuild()}}class M extends Wt{constructor(e,t){super(e,t),this.kernelSize=M.KernelSize,this._compensation=M.Compensation,this._isDirty=!1,this._sourceMesh=null,this.backFaceCulling=!1,this.shadowDepthWrapper=M._MakeGaussianSplattingShadowDepthWrapper(t,this.shaderLanguage)}set compensation(e){this._isDirty=this._isDirty!=e,this._compensation=e}get compensation(){return this._compensation}get hasRenderTargetTextures(){return!1}needAlphaTesting(){return!1}needAlphaBlending(){return!0}isReadyForSubMesh(e,t){const n=t._drawWrapper;let o=t.materialDefines;if(o&&this._isDirty&&o.markAsUnprocessed(),n.effect&&this.isFrozen&&n._wasPreviouslyReady&&n._wasPreviouslyUsingInstances===!0)return!0;t.materialDefines||(o=t.materialDefines=new zs);const i=this.getScene();if(this._isReadyForSubMesh(t))return!0;if(!this._sourceMesh)return!1;const c=i.getEngine(),d=this._sourceMesh;Vt(e,i,this._useLogarithmicDepth,this.pointsCloud,this.fogEnabled,!1,o,void 0,void 0,void 0,this._isVertexOutputInvariant),jt(i,c,this,o,!0,null,!0),Zt(e,o,!1,!1),(c.version>1||c.isWebGPU)&&(o.SH_DEGREE=d.shDegree);const a=d.material;if(o.COMPENSATION=a&&a.compensation?a.compensation:M.Compensation,o.isDirty){o.markAsProcessed(),i.resetCachedMaterial(),Xt(M._Attribs,o),Gt({uniformsNames:M._Uniforms,uniformBuffersNames:M._UniformBuffers,samplers:M._Samplers,defines:o}),$t(M._Uniforms);const _=o.toString(),u=i.getEngine().createEffect("gaussianSplatting",{attributes:M._Attribs,uniformsNames:M._Uniforms,uniformBuffersNames:M._UniformBuffers,samplers:M._Samplers,defines:_,onCompiled:this.onCompiled,onError:this.onError,indexParameters:{},shaderLanguage:this._shaderLanguage,extraInitializationsAsync:async()=>{this._shaderLanguage===1?await Promise.all([Ce(()=>Promise.resolve().then(()=>Cs),void 0),Ce(()=>Promise.resolve().then(()=>Es),void 0)]):await Promise.all([Ce(()=>Promise.resolve().then(()=>_s),void 0),Ce(()=>Promise.resolve().then(()=>Ss),void 0)])}},c);t.setEffect(u,o,this._materialContext)}return!t.effect||!t.effect.isReady()?!1:(o._renderId=i.getRenderId(),n._wasPreviouslyReady=!0,n._wasPreviouslyUsingInstances=!0,this._isDirty=!1,!0)}setSourceMesh(e){this._sourceMesh=e}static BindEffect(e,t,s){var f,p;const n=s.getEngine(),o=s.activeCamera,i=n.getRenderWidth()*o.viewport.width,c=n.getRenderHeight()*o.viewport.height,d=e.material;if(!d._sourceMesh)return;const a=d._sourceMesh,_=((f=o==null?void 0:o.rigParent)==null?void 0:f.rigCameras.length)||1;t.setFloat2("invViewport",1/(i/_),1/c);let u=1e3;if(o){const x=o.getProjectionMatrix().m[5];o.fovMode==_t.FOVMODE_VERTICAL_FIXED?u=c*x/2:u=i*x/2}if(t.setFloat2("focal",u,u),t.setFloat("kernelSize",d&&d.kernelSize?d.kernelSize:M.KernelSize),t.setFloat("alpha",d.alpha),s.bindEyePosition(t,"eyePosition",!0),a.covariancesATexture){const x=a.covariancesATexture.getSize();if(t.setFloat2("dataTextureSize",x.width,x.height),t.setTexture("covariancesATexture",a.covariancesATexture),t.setTexture("covariancesBTexture",a.covariancesBTexture),t.setTexture("centersTexture",a.centersTexture),t.setTexture("colorsTexture",a.colorsTexture),a.shTextures)for(let y=0;y<((p=a.shTextures)==null?void 0:p.length);y++)t.setTexture(`shTexture${y}`,a.shTextures[y])}}bindForSubMesh(e,t,s){const n=this.getScene(),o=s.materialDefines;if(!o)return;const i=s.effect;if(!i)return;this._activeEffect=i,t.getMeshUniformBuffer().bindToEffect(i,"Mesh"),t.transferToEffect(e),this._mustRebind(n,i,s,t.visibility)?(this.bindView(i),this.bindViewProjection(i),M.BindEffect(t,this._activeEffect,n),qt(i,this,n)):n.getEngine()._features.needToAlwaysBindUniformBuffers&&(this._needToBindSceneUbo=!0),Kt(n,t,i),this.useLogarithmicDepth&&Qt(o,i,n),this._afterBind(t,this._activeEffect,s)}static _BindEffectUniforms(e,t,s,n){const o=n.getEngine(),i=s.getEffect();e.getMeshUniformBuffer().bindToEffect(i,"Mesh"),s.bindView(i),s.bindViewProjection(i);const c=o.getRenderWidth(),d=o.getRenderHeight();i.setFloat2("invViewport",1/c,1/d);const _=n.getProjectionMatrix().m[5],u=c*_/2;i.setFloat2("focal",u,u),i.setFloat("kernelSize",t&&t.kernelSize?t.kernelSize:M.KernelSize),i.setFloat("alpha",t.alpha);let f,p;const x=n.activeCamera;if(!x)return;if(x.mode===_t.ORTHOGRAPHIC_CAMERA?(f=!o.useReverseDepthBuffer&&o.isNDCHalfZRange?0:1,p=o.useReverseDepthBuffer&&o.isNDCHalfZRange?0:1):(f=o.useReverseDepthBuffer&&o.isNDCHalfZRange?x.minZ:o.isNDCHalfZRange?0:x.minZ,p=o.useReverseDepthBuffer&&o.isNDCHalfZRange?0:x.maxZ),i.setFloat2("depthValues",f,f+p),e.covariancesATexture){const I=e.covariancesATexture.getSize();i.setFloat2("dataTextureSize",I.width,I.height),i.setTexture("covariancesATexture",e.covariancesATexture),i.setTexture("covariancesBTexture",e.covariancesBTexture),i.setTexture("centersTexture",e.centersTexture),i.setTexture("colorsTexture",e.colorsTexture)}}makeDepthRenderingMaterial(e,t){const s=new mt("gaussianSplattingDepthRender",e,{vertex:"gaussianSplattingDepth",fragment:"gaussianSplattingDepth"},{attributes:M._Attribs,uniforms:M._Uniforms,samplers:M._Samplers,uniformBuffers:M._UniformBuffers,shaderLanguage:t,defines:["#define DEPTH_RENDER"]});return s.onBindObservable.add(n=>{const o=n.material,i=n;M._BindEffectUniforms(i,o,s,e)}),s}static _MakeGaussianSplattingShadowDepthWrapper(e,t){const s=new mt("gaussianSplattingDepth",e,{vertex:"gaussianSplattingDepth",fragment:"gaussianSplattingDepth"},{attributes:M._Attribs,uniforms:M._Uniforms,samplers:M._Samplers,uniformBuffers:M._UniformBuffers,shaderLanguage:t}),n=new us(s,e,{standalone:!0});return s.onBindObservable.add(o=>{const i=o.material,c=o;M._BindEffectUniforms(c,i,s,e)}),n}clone(e){return xt.Clone(()=>new M(e,this.getScene()),this)}serialize(){const e=super.serialize();return e.customType="BABYLON.GaussianSplattingMaterial",e}getClassName(){return"GaussianSplattingMaterial"}static Parse(e,t,s){return xt.Parse(()=>new M(e.name,t),e,t,s)}}M.KernelSize=.3;M.Compensation=!1;M._Attribs=[K.PositionKind,"splatIndex0","splatIndex1","splatIndex2","splatIndex3"];M._Samplers=["covariancesATexture","covariancesBTexture","centersTexture","colorsTexture","shTexture0","shTexture1","shTexture2"];M._UniformBuffers=["Scene","Mesh"];M._Uniforms=["world","view","projection","vFogInfos","vFogColor","logarithmicDepthConstant","invViewport","dataTextureSize","focal","eyePosition","kernelSize","alpha","depthValues"];Lt("BABYLON.GaussianSplattingMaterial",M);const Hs=es,X={...Yt,TwoPi:Math.PI*2,Sign:Math.sign,Log2:Math.log2,HCF:Hs},L=(r,e)=>{const t=(1<<e)-1;return(r&t)/t},Dt=(r,e)=>{e.x=L(r>>>21,11),e.y=L(r>>>11,10),e.z=L(r,11)},ks=(r,e)=>{e[0]=L(r>>>24,8)*255,e[1]=L(r>>>16,8)*255,e[2]=L(r>>>8,8)*255,e[3]=L(r,8)*255},Rs=(r,e)=>{const t=1/(Math.sqrt(2)*.5),s=(L(r>>>20,10)-.5)*t,n=(L(r>>>10,10)-.5)*t,o=(L(r,10)-.5)*t,i=Math.sqrt(1-(s*s+n*n+o*o));switch(r>>>30){case 0:e.set(i,s,n,o);break;case 1:e.set(s,i,n,o);break;case 2:e.set(s,n,i,o);break;case 3:e.set(s,n,o,i);break}};var At;(function(r){r[r.FLOAT=0]="FLOAT",r[r.INT=1]="INT",r[r.UINT=2]="UINT",r[r.DOUBLE=3]="DOUBLE",r[r.UCHAR=4]="UCHAR",r[r.UNDEFINED=5]="UNDEFINED"})(At||(At={}));var Mt;(function(r){r[r.MIN_X=0]="MIN_X",r[r.MIN_Y=1]="MIN_Y",r[r.MIN_Z=2]="MIN_Z",r[r.MAX_X=3]="MAX_X",r[r.MAX_Y=4]="MAX_Y",r[r.MAX_Z=5]="MAX_Z",r[r.MIN_SCALE_X=6]="MIN_SCALE_X",r[r.MIN_SCALE_Y=7]="MIN_SCALE_Y",r[r.MIN_SCALE_Z=8]="MIN_SCALE_Z",r[r.MAX_SCALE_X=9]="MAX_SCALE_X",r[r.MAX_SCALE_Y=10]="MAX_SCALE_Y",r[r.MAX_SCALE_Z=11]="MAX_SCALE_Z",r[r.PACKED_POSITION=12]="PACKED_POSITION",r[r.PACKED_ROTATION=13]="PACKED_ROTATION",r[r.PACKED_SCALE=14]="PACKED_SCALE",r[r.PACKED_COLOR=15]="PACKED_COLOR",r[r.X=16]="X",r[r.Y=17]="Y",r[r.Z=18]="Z",r[r.SCALE_0=19]="SCALE_0",r[r.SCALE_1=20]="SCALE_1",r[r.SCALE_2=21]="SCALE_2",r[r.DIFFUSE_RED=22]="DIFFUSE_RED",r[r.DIFFUSE_GREEN=23]="DIFFUSE_GREEN",r[r.DIFFUSE_BLUE=24]="DIFFUSE_BLUE",r[r.OPACITY=25]="OPACITY",r[r.F_DC_0=26]="F_DC_0",r[r.F_DC_1=27]="F_DC_1",r[r.F_DC_2=28]="F_DC_2",r[r.F_DC_3=29]="F_DC_3",r[r.ROT_0=30]="ROT_0",r[r.ROT_1=31]="ROT_1",r[r.ROT_2=32]="ROT_2",r[r.ROT_3=33]="ROT_3",r[r.MIN_COLOR_R=34]="MIN_COLOR_R",r[r.MIN_COLOR_G=35]="MIN_COLOR_G",r[r.MIN_COLOR_B=36]="MIN_COLOR_B",r[r.MAX_COLOR_R=37]="MAX_COLOR_R",r[r.MAX_COLOR_G=38]="MAX_COLOR_G",r[r.MAX_COLOR_B=39]="MAX_COLOR_B",r[r.SH_0=40]="SH_0",r[r.SH_1=41]="SH_1",r[r.SH_2=42]="SH_2",r[r.SH_3=43]="SH_3",r[r.SH_4=44]="SH_4",r[r.SH_5=45]="SH_5",r[r.SH_6=46]="SH_6",r[r.SH_7=47]="SH_7",r[r.SH_8=48]="SH_8",r[r.SH_9=49]="SH_9",r[r.SH_10=50]="SH_10",r[r.SH_11=51]="SH_11",r[r.SH_12=52]="SH_12",r[r.SH_13=53]="SH_13",r[r.SH_14=54]="SH_14",r[r.SH_15=55]="SH_15",r[r.SH_16=56]="SH_16",r[r.SH_17=57]="SH_17",r[r.SH_18=58]="SH_18",r[r.SH_19=59]="SH_19",r[r.SH_20=60]="SH_20",r[r.SH_21=61]="SH_21",r[r.SH_22=62]="SH_22",r[r.SH_23=63]="SH_23",r[r.SH_24=64]="SH_24",r[r.SH_25=65]="SH_25",r[r.SH_26=66]="SH_26",r[r.SH_27=67]="SH_27",r[r.SH_28=68]="SH_28",r[r.SH_29=69]="SH_29",r[r.SH_30=70]="SH_30",r[r.SH_31=71]="SH_31",r[r.SH_32=72]="SH_32",r[r.SH_33=73]="SH_33",r[r.SH_34=74]="SH_34",r[r.SH_35=75]="SH_35",r[r.SH_36=76]="SH_36",r[r.SH_37=77]="SH_37",r[r.SH_38=78]="SH_38",r[r.SH_39=79]="SH_39",r[r.SH_40=80]="SH_40",r[r.SH_41=81]="SH_41",r[r.SH_42=82]="SH_42",r[r.SH_43=83]="SH_43",r[r.SH_44=84]="SH_44",r[r.UNDEFINED=85]="UNDEFINED"})(Mt||(Mt={}));class A extends Te{get disableDepthSort(){return this._disableDepthSort}set disableDepthSort(e){var t;!this._disableDepthSort&&e?((t=this._worker)==null||t.terminate(),this._worker=null,this._disableDepthSort=!0):this._disableDepthSort&&!e&&(this._disableDepthSort=!1,this._sortIsDirty=!0,this._instanciateWorker())}get viewDirectionFactor(){return D.OneReadOnly}get shDegree(){return this._shDegree}get splatCount(){var e;return(e=this._splatIndex)==null?void 0:e.length}get splatsData(){return this._splatsData}get covariancesATexture(){return this._covariancesATexture}get covariancesBTexture(){return this._covariancesBTexture}get centersTexture(){return this._centersTexture}get colorsTexture(){return this._colorsTexture}get shTextures(){return this._shTextures}get kernelSize(){return this._material instanceof M?this._material.kernelSize:0}get compensation(){return this._material instanceof M?this._material.compensation:!1}set material(e){this._material=e,this._material.backFaceCulling=!1,this._material.cullBackFaces=!1,e.resetDrawCache()}get material(){return this._material}static _MakeSplatGeometryForMesh(e){const t=new Ve,s=[-2,-2,0,2,-2,0,2,2,0,-2,2,0],n=[0,1,2,0,2,3],o=[],i=[];for(let c=0;c<A._BatchSize;c++){for(let d=0;d<12;d++)d==2||d==5||d==8||d==11?o.push(c):o.push(s[d]);i.push(n.map(d=>d+c*4))}t.positions=o,t.indices=i.flat(),t.applyToMesh(e)}constructor(e,t=null,s=null,n=!1){super(e,s),this._vertexCount=0,this._worker=null,this._modelViewProjectionMatrix=Ie.Identity(),this._canPostToWorker=!0,this._readyToDisplay=!1,this._covariancesATexture=null,this._covariancesBTexture=null,this._centersTexture=null,this._colorsTexture=null,this._splatPositions=null,this._splatIndex=null,this._shTextures=null,this._splatsData=null,this._keepInRam=!1,this._delayedTextureUpdate=null,this._useRGBACovariants=!1,this._material=null,this._tmpCovariances=[0,0,0,0,0,0],this._sortIsDirty=!1,this._shDegree=0,this._cameraViewInfos=new Map,this.viewUpdateThreshold=A._DefaultViewUpdateThreshold,this._disableDepthSort=!1,this._loadingPromise=null,this.subMeshes=[],new ts(0,0,4*A._BatchSize,0,6*A._BatchSize,this),this.setEnabled(!1),this._useRGBACovariants=!this.getEngine().isWebGPU&&this.getEngine().version===1,this._keepInRam=n,t&&(this._loadingPromise=this.loadFileAsync(t));const o=new M(this.name+"_material",this._scene);o.setSourceMesh(this),this._material=o,this._scene.onCameraRemovedObservable.add(i=>{const c=i.uniqueId;if(this._cameraViewInfos.has(c)){const d=this._cameraViewInfos.get(c);d==null||d.mesh.dispose(),this._cameraViewInfos.delete(c)}})}getLoadingPromise(){return this._loadingPromise}getClassName(){return"GaussianSplattingMesh"}getTotalVertices(){return this._vertexCount}isReady(e=!1){return super.isReady(e,!0)?this._readyToDisplay?!0:(this._postToWorker(!0),!1):!1}_getCameraDirection(e){const t=e.getViewMatrix(),s=e.getProjectionMatrix(),n=J.Matrix[0];t.multiplyToRef(s,n),this.getWorldMatrix().multiplyToRef(n,this._modelViewProjectionMatrix);const o=J.Vector3[1];return o.set(this._modelViewProjectionMatrix.m[8],this._modelViewProjectionMatrix.m[9],this._modelViewProjectionMatrix.m[10]),o.normalize(),o}_postToWorker(e=!1){var d,a;const s=this._scene.getFrameId();let n=!1;this._cameraViewInfos.forEach(_=>{_.frameIdLastUpdate!==s&&(n=!0)});const o=(d=this._scene.activeCameras)!=null&&d.length?this._scene.activeCameras:[this._scene.activeCamera],i=[];o.forEach(_=>{if(!_)return;const u=_.uniqueId,f=this._cameraViewInfos.get(u);if(f)i.push(f);else{const p=new Te(this.name+"_cameraMesh_"+u,this._scene);p.reservedDataStore={hidden:!0},p.setEnabled(!1),p.material=this.material,A._MakeSplatGeometryForMesh(p);const x={camera:_,cameraDirection:new D(0,0,0),mesh:p,frameIdLastUpdate:s,splatIndexBufferSet:!1};i.push(x),this._cameraViewInfos.set(u,x)}}),i.sort((_,u)=>_.frameIdLastUpdate-u.frameIdLastUpdate);const c=this._worker||_native&&_native.sortSplats||this._disableDepthSort;(e||n)&&c&&((a=this._scene.activeCameras)!=null&&a.length||this._scene.activeCamera)&&this._canPostToWorker?i.forEach(_=>{const u=_.camera,f=this._getCameraDirection(u),p=_.cameraDirection,x=D.Dot(f,p);(e||Math.abs(x-1)>=this.viewUpdateThreshold)&&this._canPostToWorker&&(_.cameraDirection.copyFrom(f),_.frameIdLastUpdate=s,this._canPostToWorker=!1,this._worker?this._worker.postMessage({modelViewProjection:this._modelViewProjectionMatrix.m,depthMix:this._depthMix,cameraId:u.uniqueId},[this._depthMix.buffer]):_native&&_native.sortSplats&&(_native.sortSplats(this._modelViewProjectionMatrix,this._splatPositions,this._splatIndex,this._scene.useRightHandedSystem),_.splatIndexBufferSet?_.mesh.thinInstanceBufferUpdated("splatIndex"):(_.mesh.thinInstanceSetBuffer("splatIndex",this._splatIndex,16,!1),_.splatIndexBufferSet=!0),this._canPostToWorker=!0,this._readyToDisplay=!0))}):this._disableDepthSort&&(i.forEach(_=>{_.splatIndexBufferSet||(_.mesh.thinInstanceSetBuffer("splatIndex",this._splatIndex,16,!1),_.splatIndexBufferSet=!0)}),this._canPostToWorker=!0,this._readyToDisplay=!0)}render(e,t,s){this._postToWorker(),!this._geometry&&this._cameraViewInfos.size&&(this._geometry=this._cameraViewInfos.values().next().value.mesh.geometry);const n=this._scene.activeCamera.uniqueId,o=this._cameraViewInfos.get(n);if(!o||!o.splatIndexBufferSet)return this;const i=o.mesh;return i.getWorldMatrix().copyFrom(this.getWorldMatrix()),i.render(e,t,s)}static _TypeNameToEnum(e){switch(e){case"float":return 0;case"int":return 1;case"uint":return 2;case"double":return 3;case"uchar":return 4}return 5}static _ValueNameToEnum(e){switch(e){case"min_x":return 0;case"min_y":return 1;case"min_z":return 2;case"max_x":return 3;case"max_y":return 4;case"max_z":return 5;case"min_scale_x":return 6;case"min_scale_y":return 7;case"min_scale_z":return 8;case"max_scale_x":return 9;case"max_scale_y":return 10;case"max_scale_z":return 11;case"packed_position":return 12;case"packed_rotation":return 13;case"packed_scale":return 14;case"packed_color":return 15;case"x":return 16;case"y":return 17;case"z":return 18;case"scale_0":return 19;case"scale_1":return 20;case"scale_2":return 21;case"diffuse_red":case"red":return 22;case"diffuse_green":case"green":return 23;case"diffuse_blue":case"blue":return 24;case"f_dc_0":return 26;case"f_dc_1":return 27;case"f_dc_2":return 28;case"f_dc_3":return 29;case"opacity":return 25;case"rot_0":return 30;case"rot_1":return 31;case"rot_2":return 32;case"rot_3":return 33;case"min_r":return 34;case"min_g":return 35;case"min_b":return 36;case"max_r":return 37;case"max_g":return 38;case"max_b":return 39;case"f_rest_0":return 40;case"f_rest_1":return 41;case"f_rest_2":return 42;case"f_rest_3":return 43;case"f_rest_4":return 44;case"f_rest_5":return 45;case"f_rest_6":return 46;case"f_rest_7":return 47;case"f_rest_8":return 48;case"f_rest_9":return 49;case"f_rest_10":return 50;case"f_rest_11":return 51;case"f_rest_12":return 52;case"f_rest_13":return 53;case"f_rest_14":return 54;case"f_rest_15":return 55;case"f_rest_16":return 56;case"f_rest_17":return 57;case"f_rest_18":return 58;case"f_rest_19":return 59;case"f_rest_20":return 60;case"f_rest_21":return 61;case"f_rest_22":return 62;case"f_rest_23":return 63;case"f_rest_24":return 64;case"f_rest_25":return 65;case"f_rest_26":return 66;case"f_rest_27":return 67;case"f_rest_28":return 68;case"f_rest_29":return 69;case"f_rest_30":return 70;case"f_rest_31":return 71;case"f_rest_32":return 72;case"f_rest_33":return 73;case"f_rest_34":return 74;case"f_rest_35":return 75;case"f_rest_36":return 76;case"f_rest_37":return 77;case"f_rest_38":return 78;case"f_rest_39":return 79;case"f_rest_40":return 80;case"f_rest_41":return 81;case"f_rest_42":return 82;case"f_rest_43":return 83;case"f_rest_44":return 84}return 85}static ParseHeader(e){const t=new Uint8Array(e),s=new TextDecoder().decode(t.slice(0,1024*10)),n=`end_header
`,o=s.indexOf(n);if(o<0||!s)return null;const i=parseInt(/element vertex (\d+)\n/.exec(s)[1]),c=/element chunk (\d+)\n/.exec(s);let d=0;c&&(d=parseInt(c[1]));let a=0,_=0;const u={double:8,int:4,uint:4,float:4,short:2,ushort:2,uchar:1,list:0};let f;(function(m){m[m.Vertex=0]="Vertex",m[m.Chunk=1]="Chunk",m[m.SH=2]="SH",m[m.Unused=3]="Unused"})(f||(f={}));let p=1;const x=[],y=[],I=s.slice(0,o).split(`
`);let l=0;for(const m of I)if(m.startsWith("property ")){const[,h,v]=m.split(" "),T=A._ValueNameToEnum(v);T!=85&&(T>=84?l=3:T>=64?l=Math.max(l,2):T>=48&&(l=Math.max(l,1)));const O=A._TypeNameToEnum(h);p==1?(y.push({value:T,type:O,offset:_}),_+=u[h]):p==0?(x.push({value:T,type:O,offset:a}),a+=u[h]):p==2&&x.push({value:T,type:O,offset:a}),u[h]||pe.Warn(`Unsupported property type: ${h}.`)}else if(m.startsWith("element ")){const[,h]=m.split(" ");h=="chunk"?p=1:h=="vertex"?p=0:h=="sh"?p=2:p=3}const g=new DataView(e,o+n.length),S=new ArrayBuffer(A._RowOutputLength*i);let C=null,w=0;return l&&(w=((l+1)*(l+1)-1)*3,C=new ArrayBuffer(w*i)),{vertexCount:i,chunkCount:d,rowVertexLength:a,rowChunkLength:_,vertexProperties:x,chunkProperties:y,dataView:g,buffer:S,shDegree:l,shCoefficientCount:w,shBuffer:C}}static _GetCompressedChunks(e,t){if(!e.chunkCount)return null;const s=e.dataView,n=new Array(e.chunkCount);for(let o=0;o<e.chunkCount;o++){const i={min:new D,max:new D,minScale:new D,maxScale:new D,minColor:new D(0,0,0),maxColor:new D(1,1,1)};n[o]=i;for(let c=0;c<e.chunkProperties.length;c++){const d=e.chunkProperties[c];let a;switch(d.type){case 0:a=s.getFloat32(d.offset+t.value,!0);break;default:continue}switch(d.value){case 0:i.min.x=a;break;case 1:i.min.y=a;break;case 2:i.min.z=a;break;case 3:i.max.x=a;break;case 4:i.max.y=a;break;case 5:i.max.z=a;break;case 6:i.minScale.x=a;break;case 7:i.minScale.y=a;break;case 8:i.minScale.z=a;break;case 9:i.maxScale.x=a;break;case 10:i.maxScale.y=a;break;case 11:i.maxScale.z=a;break;case 34:i.minColor.x=a;break;case 35:i.minColor.y=a;break;case 36:i.minColor.z=a;break;case 37:i.maxColor.x=a;break;case 38:i.maxColor.y=a;break;case 39:i.maxColor.z=a;break}}t.value+=e.rowChunkLength}return n}static _GetSplat(e,t,s,n){const o=J.Quaternion[0],i=J.Vector3[0],c=A._RowOutputLength,d=e.buffer,a=e.dataView,_=new Float32Array(d,t*c,3),u=new Float32Array(d,t*c+12,3),f=new Uint8ClampedArray(d,t*c+24,4),p=new Uint8ClampedArray(d,t*c+28,4);let x=null;e.shBuffer&&(x=new Uint8ClampedArray(e.shBuffer,t*e.shCoefficientCount,e.shCoefficientCount));const y=t>>8;let I=255,l=0,g=0,S=0;const C=[];for(let w=0;w<e.vertexProperties.length;w++){const m=e.vertexProperties[w];let h;switch(m.type){case 0:h=a.getFloat32(n.value+m.offset,!0);break;case 1:h=a.getInt32(n.value+m.offset,!0);break;case 2:h=a.getUint32(n.value+m.offset,!0);break;case 3:h=a.getFloat64(n.value+m.offset,!0);break;case 4:h=a.getUint8(n.value+m.offset);break;default:continue}switch(m.value){case 12:{const v=s[y];Dt(h,i),_[0]=X.Lerp(v.min.x,v.max.x,i.x),_[1]=X.Lerp(v.min.y,v.max.y,i.y),_[2]=X.Lerp(v.min.z,v.max.z,i.z)}break;case 13:Rs(h,o),I=o.x,l=o.y,g=o.z,S=o.w;break;case 14:{const v=s[y];Dt(h,i),u[0]=Math.exp(X.Lerp(v.minScale.x,v.maxScale.x,i.x)),u[1]=Math.exp(X.Lerp(v.minScale.y,v.maxScale.y,i.y)),u[2]=Math.exp(X.Lerp(v.minScale.z,v.maxScale.z,i.z))}break;case 15:{const v=s[y];ks(h,f),f[0]=X.Lerp(v.minColor.x,v.maxColor.x,f[0]/255)*255,f[1]=X.Lerp(v.minColor.y,v.maxColor.y,f[1]/255)*255,f[2]=X.Lerp(v.minColor.z,v.maxColor.z,f[2]/255)*255}break;case 16:_[0]=h;break;case 17:_[1]=h;break;case 18:_[2]=h;break;case 19:u[0]=Math.exp(h);break;case 20:u[1]=Math.exp(h);break;case 21:u[2]=Math.exp(h);break;case 22:f[0]=h;break;case 23:f[1]=h;break;case 24:f[2]=h;break;case 26:f[0]=(.5+A._SH_C0*h)*255;break;case 27:f[1]=(.5+A._SH_C0*h)*255;break;case 28:f[2]=(.5+A._SH_C0*h)*255;break;case 29:f[3]=(.5+A._SH_C0*h)*255;break;case 25:f[3]=1/(1+Math.exp(-h))*255;break;case 30:I=h;break;case 31:l=h;break;case 32:g=h;break;case 33:S=h;break}if(x&&m.value>=40&&m.value<=84){const v=m.value-40;if(m.type==4&&e.chunkCount){const T=a.getUint8(e.rowChunkLength*e.chunkCount+e.vertexCount*e.rowVertexLength+t*e.shCoefficientCount+v);C[v]=(T*(8/255)-4)*127.5+127.5}else{const T=X.Clamp(h*127.5+127.5,0,255);C[v]=T}}}if(x){const w=e.shDegree==1?3:e.shDegree==2?8:15;for(let m=0;m<w;m++)x[m*3+0]=C[m],x[m*3+1]=C[m+w],x[m*3+2]=C[m+w*2]}o.set(l,g,S,I),o.normalize(),p[0]=o.w*127.5+127.5,p[1]=o.x*127.5+127.5,p[2]=o.y*127.5+127.5,p[3]=o.z*127.5+127.5,n.value+=e.rowVertexLength}static*ConvertPLYWithSHToSplat(e,t=!1){const s=A.ParseHeader(e);if(!s)return{buffer:e};const n={value:0},o=A._GetCompressedChunks(s,n);for(let c=0;c<s.vertexCount;c++)A._GetSplat(s,c,o,n),c%A._PlyConversionBatchSize===0&&t&&(yield);let i=null;if(s.shDegree&&s.shBuffer){const c=Math.ceil(s.shCoefficientCount/16);let d=0;const a=new Uint8Array(s.shBuffer);i=[];const _=s.vertexCount,u=Ee.LastCreatedEngine;if(u){const f=u.getCaps().maxTextureSize,p=Math.ceil(_/f);for(let x=0;x<c;x++){const y=new Uint8Array(p*f*4*4);i.push(y)}for(let x=0;x<_;x++)for(let y=0;y<s.shCoefficientCount;y++){const I=a[d++],l=Math.floor(y/16),g=i[l],S=y%16,C=x*16;g[S+C]=I}}}return{buffer:s.buffer,sh:i}}static*ConvertPLYToSplat(e,t=!1){const s=A.ParseHeader(e);if(!s)return e;const n={value:0},o=A._GetCompressedChunks(s,n);for(let i=0;i<s.vertexCount;i++)A._GetSplat(s,i,o,n),i%A._PlyConversionBatchSize===0&&t&&(yield);return s.buffer}static async ConvertPLYToSplatAsync(e){return await Re(A.ConvertPLYToSplat(e,!0),Oe())}static async ConvertPLYWithSHToSplatAsync(e){return await Re(A.ConvertPLYWithSHToSplat(e,!0),Oe())}async loadDataAsync(e){return await this.updateDataAsync(e)}async loadFileAsync(e,t){await ss(e,t||Ee.LastCreatedScene,{pluginOptions:{splat:{gaussianSplattingMesh:this}}})}dispose(e){var t,s,n,o,i;if((t=this._covariancesATexture)==null||t.dispose(),(s=this._covariancesBTexture)==null||s.dispose(),(n=this._centersTexture)==null||n.dispose(),(o=this._colorsTexture)==null||o.dispose(),this._shTextures)for(const c of this._shTextures)c.dispose();this._covariancesATexture=null,this._covariancesBTexture=null,this._centersTexture=null,this._colorsTexture=null,this._shTextures=null,(i=this._worker)==null||i.terminate(),this._worker=null,this._cameraViewInfos.forEach(c=>{c.mesh.dispose()}),super.dispose(e,!0)}_copyTextures(e){var t,s,n,o,i;if(this._covariancesATexture=(t=e.covariancesATexture)==null?void 0:t.clone(),this._covariancesBTexture=(s=e.covariancesBTexture)==null?void 0:s.clone(),this._centersTexture=(n=e.centersTexture)==null?void 0:n.clone(),this._colorsTexture=(o=e.colorsTexture)==null?void 0:o.clone(),e._shTextures){this._shTextures=[];for(const c of this._shTextures)(i=this._shTextures)==null||i.push(c.clone())}}clone(e=""){const t=new A(e,void 0,this.getScene());t._copySource(this),t.makeGeometryUnique(),t._vertexCount=this._vertexCount,t._copyTextures(this),t._modelViewProjectionMatrix=Ie.Identity(),t._splatPositions=this._splatPositions,t._readyToDisplay=!1,t._disableDepthSort=this._disableDepthSort,t._instanciateWorker();const s=this.getBoundingInfo();return t.getBoundingInfo().reConstruct(s.minimum,s.maximum,this.getWorldMatrix()),t.forcedInstanceCount=this.forcedInstanceCount,t.setEnabled(!0),t}_makeEmptySplat(e,t,s,n){const o=this._useRGBACovariants?4:2;this._splatPositions[4*e+0]=0,this._splatPositions[4*e+1]=0,this._splatPositions[4*e+2]=0,t[e*4+0]=q(0),t[e*4+1]=q(0),t[e*4+2]=q(0),t[e*4+3]=q(0),s[e*o+0]=q(0),s[e*o+1]=q(0),n[e*4+3]=0}_makeSplat(e,t,s,n,o,i,c,d,a){const _=J.Matrix[0],u=J.Matrix[1],f=J.Quaternion[0],p=this._useRGBACovariants?4:2,x=t[8*e+0],y=t[8*e+1]*(a.flipY?-1:1),I=t[8*e+2];this._splatPositions[4*e+0]=x,this._splatPositions[4*e+1]=y,this._splatPositions[4*e+2]=I,c.minimizeInPlaceFromFloats(x,y,I),d.maximizeInPlaceFromFloats(x,y,I),f.set((s[32*e+28+1]-127.5)/127.5,(s[32*e+28+2]-127.5)/127.5,(s[32*e+28+3]-127.5)/127.5,-(s[32*e+28+0]-127.5)/127.5),f.normalize(),f.toRotationMatrix(_),Ie.ScalingToRef(t[8*e+3+0]*2,t[8*e+3+1]*2,t[8*e+3+2]*2,u);const l=_.multiplyToRef(u,J.Matrix[0]).m,g=this._tmpCovariances;g[0]=l[0]*l[0]+l[1]*l[1]+l[2]*l[2],g[1]=l[0]*l[4]+l[1]*l[5]+l[2]*l[6],g[2]=l[0]*l[8]+l[1]*l[9]+l[2]*l[10],g[3]=l[4]*l[4]+l[5]*l[5]+l[6]*l[6],g[4]=l[4]*l[8]+l[5]*l[9]+l[6]*l[10],g[5]=l[8]*l[8]+l[9]*l[9]+l[10]*l[10];let S=-1e4;for(let w=0;w<6;w++)S=Math.max(S,Math.abs(g[w]));this._splatPositions[4*e+3]=S;const C=S;n[e*4+0]=q(g[0]/C),n[e*4+1]=q(g[1]/C),n[e*4+2]=q(g[2]/C),n[e*4+3]=q(g[3]/C),o[e*p+0]=q(g[4]/C),o[e*p+1]=q(g[5]/C),i[e*4+0]=s[32*e+24+0],i[e*4+1]=s[32*e+24+1],i[e*4+2]=s[32*e+24+2],i[e*4+3]=s[32*e+24+3]}_updateTextures(e,t,s,n){const o=this._getTextureSize(this._vertexCount),i=(_,u,f,p)=>new be(_,u,f,p,this._scene,!1,!1,2,1),c=(_,u,f,p)=>new be(_,u,f,p,this._scene,!1,!1,2,0),d=(_,u,f,p)=>new be(_,u,f,p,this._scene,!1,!1,1,7),a=(_,u,f,p)=>new be(_,u,f,p,this._scene,!1,!1,2,2);if(this._covariancesATexture){this._delayedTextureUpdate={covA:e,covB:t,colors:s,centers:this._splatPositions,sh:n};const _=Float32Array.from(this._splatPositions),u=this._vertexCount;this._worker&&this._worker.postMessage({positions:_,vertexCount:u},[_.buffer]),this._postToWorker(!0)}else{if(this._covariancesATexture=a(e,o.x,o.y,5),this._covariancesBTexture=a(t,o.x,o.y,this._useRGBACovariants?5:7),this._centersTexture=i(this._splatPositions,o.x,o.y,5),this._colorsTexture=c(s,o.x,o.y,5),n){this._shTextures=[];for(const _ of n){const u=new Uint32Array(_.buffer),f=d(u,o.x,o.y,11);f.wrapU=0,f.wrapV=0,this._shTextures.push(f)}}this._instanciateWorker()}}*_updateData(e,t,s,n={flipY:!1}){this._covariancesATexture||(this._readyToDisplay=!1);const o=new Uint8Array(e),i=new Float32Array(o.buffer);this._keepInRam&&(this._splatsData=e);const c=o.length/A._RowOutputLength;c!=this._vertexCount&&this._updateSplatIndexBuffer(c),this._vertexCount=c,this._shDegree=s?s.length:0;const d=this._getTextureSize(c),a=d.x*d.y,_=A.ProgressiveUpdateAmount??d.y,u=d.x*_;this._splatPositions=new Float32Array(4*a);const f=new Uint16Array(a*4),p=new Uint16Array((this._useRGBACovariants?4:2)*a),x=new Uint8Array(a*4),y=new D(Number.MAX_VALUE,Number.MAX_VALUE,Number.MAX_VALUE),I=new D(-Number.MAX_VALUE,-Number.MAX_VALUE,-Number.MAX_VALUE);if(A.ProgressiveUpdateAmount){this._updateTextures(f,p,x,s),this.setEnabled(!0);const l=Math.ceil(d.y/_);for(let C=0;C<l;C++){const w=C*_,m=w*d.x;for(let h=0;h<u;h++)this._makeSplat(m+h,i,o,f,p,x,y,I,n);this._updateSubTextures(this._splatPositions,f,p,x,w,Math.min(_,d.y-w)),this.getBoundingInfo().reConstruct(y,I,this.getWorldMatrix()),t&&(yield)}const g=Float32Array.from(this._splatPositions),S=this._vertexCount;this._worker&&this._worker.postMessage({positions:g,vertexCount:S},[g.buffer]),this._sortIsDirty=!0}else{const l=c+15&-16;for(let g=0;g<c;g++)this._makeSplat(g,i,o,f,p,x,y,I,n),t&&g%A._SplatBatchSize===0&&(yield);for(let g=c;g<l;g++)this._makeEmptySplat(g,f,p,x);this._updateTextures(f,p,x,s),this.getBoundingInfo().reConstruct(y,I,this.getWorldMatrix()),this.setEnabled(!0),this._sortIsDirty=!0}this._postToWorker(!0)}async updateDataAsync(e,t){return await Re(this._updateData(e,!0,t),Oe())}updateData(e,t,s={flipY:!0}){rs(this._updateData(e,!1,t,s))}refreshBoundingInfo(){return this.thinInstanceRefreshBoundingInfo(!1),this}_updateSplatIndexBuffer(e){const t=e+15&-16;if(!this._splatIndex||e>this._splatIndex.length){this._splatIndex=new Float32Array(t);for(let s=0;s<t;s++)this._splatIndex[s]=s;this._cameraViewInfos.forEach(s=>{s.mesh.thinInstanceSetBuffer("splatIndex",this._splatIndex,16,!1)})}this.forcedInstanceCount=t>>4}_updateSubTextures(e,t,s,n,o,i,c){const d=(l,g,S,C,w)=>{this.getEngine().updateTextureData(l.getInternalTexture(),g,0,C,S,w,0,0,!1)},a=this._getTextureSize(this._vertexCount),_=this._useRGBACovariants?4:2,u=o*a.x,f=i*a.x,p=new Uint16Array(t.buffer,u*4*Uint16Array.BYTES_PER_ELEMENT,f*4),x=new Uint16Array(s.buffer,u*_*Uint16Array.BYTES_PER_ELEMENT,f*_),y=new Uint8Array(n.buffer,u*4,f*4),I=new Float32Array(e.buffer,u*4*Float32Array.BYTES_PER_ELEMENT,f*4);if(d(this._covariancesATexture,p,a.x,o,i),d(this._covariancesBTexture,x,a.x,o,i),d(this._centersTexture,I,a.x,o,i),d(this._colorsTexture,y,a.x,o,i),c)for(let l=0;l<c.length;l++){const S=new Uint32Array(c[l].buffer,u*4*4,f*4);d(this._shTextures[l],S,a.x,o,i)}}_instanciateWorker(){var s;if(!this._vertexCount||this._disableDepthSort||(this._updateSplatIndexBuffer(this._vertexCount),_native))return;(s=this._worker)==null||s.terminate(),this._worker=new Worker(URL.createObjectURL(new Blob(["(",A._CreateWorker.toString(),")(self)"],{type:"application/javascript"})));const e=this._vertexCount+15&-16;this._depthMix=new BigInt64Array(e);const t=Float32Array.from(this._splatPositions);this._worker.postMessage({positions:t},[t.buffer]),this._worker.onmessage=n=>{this._depthMix=n.data.depthMix;const o=n.data.cameraId,i=new Uint32Array(n.data.depthMix.buffer);if(this._splatIndex)for(let d=0;d<e;d++)this._splatIndex[d]=i[2*d];if(this._delayedTextureUpdate){const d=this._getTextureSize(e);this._updateSubTextures(this._delayedTextureUpdate.centers,this._delayedTextureUpdate.covA,this._delayedTextureUpdate.covB,this._delayedTextureUpdate.colors,0,d.y,this._delayedTextureUpdate.sh),this._delayedTextureUpdate=null}const c=this._cameraViewInfos.get(o);c&&(c.splatIndexBufferSet?c.mesh.thinInstanceBufferUpdated("splatIndex"):(c.mesh.thinInstanceSetBuffer("splatIndex",this._splatIndex,16,!1),c.splatIndexBufferSet=!0)),this._canPostToWorker=!0,this._readyToDisplay=!0,this._sortIsDirty&&(this._postToWorker(!0),this._sortIsDirty=!1)}}_getTextureSize(e){const t=this._scene.getEngine(),s=t.getCaps().maxTextureSize;let n=1;if(t.version===1&&!t.isWebGPU)for(;s*n<e;)n*=2;else n=Math.ceil(e/s);return n>s&&(pe.Error("GaussianSplatting texture size: ("+s+", "+n+"), maxTextureSize: "+s),n=s),new ne(s,n)}}A._RowOutputLength=32;A._SH_C0=.28209479177387814;A._SplatBatchSize=327680;A._PlyConversionBatchSize=32768;A._BatchSize=16;A._DefaultViewUpdateThreshold=1e-4;A.ProgressiveUpdateAmount=0;A._CreateWorker=function(r){let e,t,s,n;r.onmessage=o=>{if(o.data.positions)e=o.data.positions;else{const i=o.data.cameraId,c=o.data.modelViewProjection,d=e.length/4+15&-16;if(!e||!c)throw new Error("positions or modelViewProjection matrix is not defined!");t=o.data.depthMix,s=new Uint32Array(t.buffer),n=new Float32Array(t.buffer);for(let a=0;a<d;a++)s[2*a]=a;for(let a=0;a<d;a++)n[2*a+1]=1e4-(c[2]*e[4*a+0]+c[6]*e[4*a+1]+c[10]*e[4*a+2]);t.sort(),r.postMessage({depthMix:t,cameraId:i},[t.buffer])}}};class Os{constructor(e,t,s,n,o){this.idx=0,this.color=new Y(1,1,1,1),this.position=D.Zero(),this.rotation=D.Zero(),this.uv=new ne(0,0),this.velocity=D.Zero(),this.pivot=D.Zero(),this.translateFromPivot=!1,this._pos=0,this._ind=0,this.groupId=0,this.idxInGroup=0,this._stillInvisible=!1,this._rotationMatrix=[1,0,0,0,1,0,0,0,1],this.parentId=null,this._globalPosition=D.Zero(),this.idx=e,this._group=t,this.groupId=s,this.idxInGroup=n,this._pcs=o}get size(){return this.size}set size(e){this.size=e}get quaternion(){return this.rotationQuaternion}set quaternion(e){this.rotationQuaternion=e}intersectsMesh(e,t){if(!e.hasBoundingInfo)return!1;if(!this._pcs.mesh)throw new Error("Point Cloud System doesnt contain the Mesh");if(t)return e.getBoundingInfo().boundingSphere.intersectsPoint(this.position.add(this._pcs.mesh.position));const s=e.getBoundingInfo().boundingBox,n=s.maximumWorld.x,o=s.minimumWorld.x,i=s.maximumWorld.y,c=s.minimumWorld.y,d=s.maximumWorld.z,a=s.minimumWorld.z,_=this.position.x+this._pcs.mesh.position.x,u=this.position.y+this._pcs.mesh.position.y,f=this.position.z+this._pcs.mesh.position.z;return o<=_&&_<=n&&c<=u&&u<=i&&a<=f&&f<=d}getRotationMatrix(e){let t;if(this.rotationQuaternion)t=this.rotationQuaternion;else{t=J.Quaternion[0];const s=this.rotation;os.RotationYawPitchRollToRef(s.y,s.x,s.z,t)}t.toRotationMatrix(e)}}class Be{get groupID(){return this.groupId}set groupID(e){this.groupId=e}constructor(e,t){this.groupId=e,this._positionFunction=t}}var zt;(function(r){r[r.Color=2]="Color",r[r.UV=1]="UV",r[r.Random=0]="Random",r[r.Stated=3]="Stated"})(zt||(zt={}));class Fs{get positions(){return this._positions32}get colors(){return this._colors32}get uvs(){return this._uvs32}constructor(e,t,s,n){this.particles=new Array,this.nbParticles=0,this.counter=0,this.vars={},this._promises=[],this._positions=new Array,this._indices=new Array,this._normals=new Array,this._colors=new Array,this._uvs=new Array,this._updatable=!0,this._isVisibilityBoxLocked=!1,this._alwaysVisible=!1,this._groups=new Array,this._groupCounter=0,this._computeParticleColor=!0,this._computeParticleTexture=!0,this._computeParticleRotation=!0,this._computeBoundingBox=!1,this._isReady=!1,this.name=e,this._size=t,this._scene=s||Ee.LastCreatedScene,n&&n.updatable!==void 0?this._updatable=n.updatable:this._updatable=!0}async buildMeshAsync(e){return await Promise.all(this._promises),this._isReady=!0,await this._buildMeshAsync(e)}async _buildMeshAsync(e){this.nbParticles===0&&this.addPoints(1),this._positions32=new Float32Array(this._positions),this._uvs32=new Float32Array(this._uvs),this._colors32=new Float32Array(this._colors);const t=new Ve;t.set(this._positions32,K.PositionKind),this._uvs32.length>0&&t.set(this._uvs32,K.UVKind);let s=0;this._colors32.length>0&&(s=1,t.set(this._colors32,K.ColorKind));const n=new Te(this.name,this._scene);t.applyToMesh(n,this._updatable),this.mesh=n,this._positions=null,this._uvs=null,this._colors=null,this._updatable||(this.particles.length=0);let o=e;return o||(o=new hs("point cloud material",this._scene),o.emissiveColor=new we(s,s,s),o.disableLighting=!0,o.pointsCloud=!0,o.pointSize=this._size),n.material=o,n}_addParticle(e,t,s,n){const o=new Os(e,t,s,n,this);return this.particles.push(o),o}_randomUnitVector(e){e.position=new D(Math.random(),Math.random(),Math.random()),e.color=new Y(1,1,1,1)}_getColorIndicesForCoord(e,t,s,n){const o=e._groupImageData,i=s*(n*4)+t*4,c=[i,i+1,i+2,i+3],d=c[0],a=c[1],_=c[2],u=c[3],f=o[d],p=o[a],x=o[_],y=o[u];return new Y(f/255,p/255,x/255,y)}_setPointsColorOrUV(e,t,s,n,o,i,c,d){d=d??0,s&&e.updateFacetData();const _=2*e.getBoundingInfo().boundingSphere.radius;let u=e.getVerticesData(K.PositionKind);const f=e.getIndices(),p=e.getVerticesData(K.UVKind+(d?d+1:"")),x=e.getVerticesData(K.ColorKind),y=D.Zero();e.computeWorldMatrix();const I=e.getWorldMatrix();if(!I.isIdentity()){u=u.slice(0);for(let Z=0;Z<u.length/3;Z++)D.TransformCoordinatesFromFloatsToRef(u[3*Z],u[3*Z+1],u[3*Z+2],I,y),u[3*Z]=y.x,u[3*Z+1]=y.y,u[3*Z+2]=y.z}let l=0,g=0,S=0,C=0,w=0,m=0,h=0,v=0,T=0,O=0,k=0,b=0,B=0;const V=D.Zero(),z=D.Zero(),R=D.Zero(),W=D.Zero(),H=D.Zero();let j=0,G=0,Q=0,N=0,E=0,ee=0;const se=ne.Zero(),fe=ne.Zero(),_e=ne.Zero(),F=ne.Zero(),je=ne.Zero();let Ze=0,Xe=0,Ge=0,$e=0,qe=0,Ke=0,Qe=0,Je=0,Le=0,Ye=0,et=0,tt=0;const ue=he.Zero(),De=he.Zero(),st=he.Zero(),rt=he.Zero(),ot=he.Zero();let re=0,xe=0;c=c||0;let de,me,U=new he(0,0,0,0),Ae=D.Zero(),Me=D.Zero(),nt=D.Zero(),ie=0,it=D.Zero(),at=0,ct=0;const ve=new ls(D.Zero(),new D(1,0,0));let ze,ge=D.Zero();for(let Z=0;Z<f.length/3;Z++){g=f[3*Z],S=f[3*Z+1],C=f[3*Z+2],w=u[3*g],m=u[3*g+1],h=u[3*g+2],v=u[3*S],T=u[3*S+1],O=u[3*S+2],k=u[3*C],b=u[3*C+1],B=u[3*C+2],V.set(w,m,h),z.set(v,T,O),R.set(k,b,B),z.subtractToRef(V,W),R.subtractToRef(z,H),p&&(j=p[2*g],G=p[2*g+1],Q=p[2*S],N=p[2*S+1],E=p[2*C],ee=p[2*C+1],se.set(j,G),fe.set(Q,N),_e.set(E,ee),fe.subtractToRef(se,F),_e.subtractToRef(fe,je)),x&&n&&(Ze=x[4*g],Xe=x[4*g+1],Ge=x[4*g+2],$e=x[4*g+3],qe=x[4*S],Ke=x[4*S+1],Qe=x[4*S+2],Je=x[4*S+3],Le=x[4*C],Ye=x[4*C+1],et=x[4*C+2],tt=x[4*C+3],ue.set(Ze,Xe,Ge,$e),De.set(qe,Ke,Qe,Je),st.set(Le,Ye,et,tt),De.subtractToRef(ue,rt),st.subtractToRef(De,ot));let He,lt,ht,ft,ut,ae,ce,Se;const dt=new we(0,0,0),ye=new we(0,0,0);let le,$;for(let ke=0;ke<t._groupDensity[Z];ke++)l=this.particles.length,this._addParticle(l,t,this._groupCounter,Z+ke),$=this.particles[l],re=Math.sqrt(oe(0,1)),xe=oe(0,1),de=V.add(W.scale(re)).add(H.scale(re*xe)),s&&(Ae=e.getFacetNormal(Z).normalize().scale(-1),Me=W.clone().normalize(),nt=D.Cross(Ae,Me),ie=oe(0,2*Math.PI),it=Me.scale(Math.cos(ie)).add(nt.scale(Math.sin(ie))),ie=oe(.1,Math.PI/2),ge=it.scale(Math.cos(ie)).add(Ae.scale(Math.sin(ie))),ve.origin=de.add(ge.scale(1e-5)),ve.direction=ge,ve.length=_,ze=ve.intersectsMesh(e),ze.hit&&(ct=ze.pickedPoint.subtract(de).length(),at=oe(0,1)*ct,de.addInPlace(ge.scale(at)))),$.position=de.clone(),this._positions.push($.position.x,$.position.y,$.position.z),n!==void 0?p&&(me=se.add(F.scale(re)).add(je.scale(re*xe)),n?o&&t._groupImageData!==null?(He=t._groupImgWidth,lt=t._groupImgHeight,le=this._getColorIndicesForCoord(t,Math.round(me.x*He),Math.round(me.y*lt),He),$.color=le,this._colors.push(le.r,le.g,le.b,le.a)):x?(U=ue.add(rt.scale(re)).add(ot.scale(re*xe)),$.color=new Y(U.x,U.y,U.z,U.w),this._colors.push(U.x,U.y,U.z,U.w)):(U=ue.set(Math.random(),Math.random(),Math.random(),1),$.color=new Y(U.x,U.y,U.z,U.w),this._colors.push(U.x,U.y,U.z,U.w)):($.uv=me.clone(),this._uvs.push($.uv.x,$.uv.y))):(i?(dt.set(i.r,i.g,i.b),ht=oe(-c,c),ft=oe(-c,c),Se=dt.toHSV(),ut=Se.r,ae=Se.g+ht,ce=Se.b+ft,ae<0&&(ae=0),ae>1&&(ae=1),ce<0&&(ce=0),ce>1&&(ce=1),we.HSVtoRGBToRef(ut,ae,ce,ye),U.set(ye.r,ye.g,ye.b,1)):U=ue.set(Math.random(),Math.random(),Math.random(),1),$.color=new Y(U.x,U.y,U.z,U.w),this._colors.push(U.x,U.y,U.z,U.w))}}_colorFromTexture(e,t,s){if(e.material===null){pe.Warn(e.name+"has no material."),t._groupImageData=null,this._setPointsColorOrUV(e,t,s,!0,!1);return}const o=e.material.getActiveTextures();if(o.length===0){pe.Warn(e.name+"has no usable texture."),t._groupImageData=null,this._setPointsColorOrUV(e,t,s,!0,!1);return}const i=e.clone();i.setEnabled(!1),this._promises.push(new Promise(c=>{ns.WhenAllReady(o,()=>{let d=t._textureNb;d<0&&(d=0),d>o.length-1&&(d=o.length-1);const a=()=>{t._groupImgWidth=o[d].getSize().width,t._groupImgHeight=o[d].getSize().height,this._setPointsColorOrUV(i,t,s,!0,!0,void 0,void 0,o[d].coordinatesIndex),i.dispose(),c()};t._groupImageData=null;const _=o[d].readPixels();_?_.then(u=>{t._groupImageData=u,a()}):a()})}))}_calculateDensity(e,t,s){let n,o,i,c,d,a,_,u,f,p,x,y;const I=D.Zero(),l=D.Zero(),g=D.Zero(),S=D.Zero(),C=D.Zero(),w=D.Zero();let m;const h=[];let v=0;const T=s.length/3;for(let b=0;b<T;b++)n=s[3*b],o=s[3*b+1],i=s[3*b+2],c=t[3*n],d=t[3*n+1],a=t[3*n+2],_=t[3*o],u=t[3*o+1],f=t[3*o+2],p=t[3*i],x=t[3*i+1],y=t[3*i+2],I.set(c,d,a),l.set(_,u,f),g.set(p,x,y),l.subtractToRef(I,S),g.subtractToRef(l,C),D.CrossToRef(S,C,w),m=.5*w.length(),v+=m,h[b]=v;const O=new Array(T);let k=e;for(let b=T-1;b>0;b--){const B=h[b];if(B===0)O[b]=0;else{const z=(B-h[b-1])/B*k,R=Math.floor(z),W=z-R,H=+(Math.random()<W),j=R+H;O[b]=j,k-=j}}return O[0]=k,O}addPoints(e,t=this._randomUnitVector){const s=new Be(this._groupCounter,t);let n,o=this.nbParticles;for(let i=0;i<e;i++)n=this._addParticle(o,s,this._groupCounter,i),s&&s._positionFunction&&s._positionFunction(n,o,i),this._positions.push(n.position.x,n.position.y,n.position.z),n.color&&this._colors.push(n.color.r,n.color.g,n.color.b,n.color.a),n.uv&&this._uvs.push(n.uv.x,n.uv.y),o++;return this.nbParticles+=e,this._groupCounter++,this._groupCounter}addSurfacePoints(e,t,s,n,o){let i=s||0;(isNaN(i)||i<0||i>3)&&(i=0);const c=e.getVerticesData(K.PositionKind),d=e.getIndices();this._groups.push(this._groupCounter);const a=new Be(this._groupCounter,null);switch(a._groupDensity=this._calculateDensity(t,c,d),i===2?a._textureNb=n||0:n=n||new Y(1,1,1,1),i){case 2:this._colorFromTexture(e,a,!1);break;case 1:this._setPointsColorOrUV(e,a,!1,!1,!1);break;case 0:this._setPointsColorOrUV(e,a,!1);break;case 3:this._setPointsColorOrUV(e,a,!1,void 0,void 0,n,o);break}return this.nbParticles+=t,this._groupCounter++,this._groupCounter-1}addVolumePoints(e,t,s,n,o){let i=s||0;(isNaN(i)||i<0||i>3)&&(i=0);const c=e.getVerticesData(K.PositionKind),d=e.getIndices();this._groups.push(this._groupCounter);const a=new Be(this._groupCounter,null);switch(a._groupDensity=this._calculateDensity(t,c,d),i===2?a._textureNb=n||0:n=n||new Y(1,1,1,1),i){case 2:this._colorFromTexture(e,a,!0);break;case 1:this._setPointsColorOrUV(e,a,!0,!1,!1);break;case 0:this._setPointsColorOrUV(e,a,!0);break;case 3:this._setPointsColorOrUV(e,a,!0,void 0,void 0,n,o);break}return this.nbParticles+=t,this._groupCounter++,this._groupCounter-1}setParticles(e=0,t=this.nbParticles-1,s=!0){var S,C;if(!this._updatable||!this._isReady)return this;this.beforeUpdateParticles(e,t,s);const n=J.Matrix[0],o=this.mesh,i=this._colors32,c=this._positions32,d=this._uvs32,a=J.Vector3,_=a[5].copyFromFloats(1,0,0),u=a[6].copyFromFloats(0,1,0),f=a[7].copyFromFloats(0,0,1),p=a[8].setAll(Number.MAX_VALUE),x=a[9].setAll(-Number.MAX_VALUE);Ie.IdentityToRef(n);let y=0;if((S=this.mesh)!=null&&S.isFacetDataEnabled&&(this._computeBoundingBox=!0),t=t>=this.nbParticles?this.nbParticles-1:t,this._computeBoundingBox&&(e!=0||t!=this.nbParticles-1)){const w=(C=this.mesh)==null?void 0:C.getBoundingInfo();w&&(p.copyFrom(w.minimum),x.copyFrom(w.maximum))}y=0;let I=0,l=0,g=0;for(let w=e;w<=t;w++){const m=this.particles[w];y=m.idx,I=3*y,l=4*y,g=2*y,this.updateParticle(m);const h=m._rotationMatrix,v=m.position,T=m._globalPosition;if(this._computeParticleRotation&&m.getRotationMatrix(n),m.parentId!==null){const N=this.particles[m.parentId],E=N._rotationMatrix,ee=N._globalPosition,se=v.x*E[1]+v.y*E[4]+v.z*E[7],fe=v.x*E[0]+v.y*E[3]+v.z*E[6],_e=v.x*E[2]+v.y*E[5]+v.z*E[8];if(T.x=ee.x+fe,T.y=ee.y+se,T.z=ee.z+_e,this._computeParticleRotation){const F=n.m;h[0]=F[0]*E[0]+F[1]*E[3]+F[2]*E[6],h[1]=F[0]*E[1]+F[1]*E[4]+F[2]*E[7],h[2]=F[0]*E[2]+F[1]*E[5]+F[2]*E[8],h[3]=F[4]*E[0]+F[5]*E[3]+F[6]*E[6],h[4]=F[4]*E[1]+F[5]*E[4]+F[6]*E[7],h[5]=F[4]*E[2]+F[5]*E[5]+F[6]*E[8],h[6]=F[8]*E[0]+F[9]*E[3]+F[10]*E[6],h[7]=F[8]*E[1]+F[9]*E[4]+F[10]*E[7],h[8]=F[8]*E[2]+F[9]*E[5]+F[10]*E[8]}}else if(T.x=0,T.y=0,T.z=0,this._computeParticleRotation){const N=n.m;h[0]=N[0],h[1]=N[1],h[2]=N[2],h[3]=N[4],h[4]=N[5],h[5]=N[6],h[6]=N[8],h[7]=N[9],h[8]=N[10]}const k=a[11];m.translateFromPivot?k.setAll(0):k.copyFrom(m.pivot);const b=a[0];b.copyFrom(m.position);const B=b.x-m.pivot.x,V=b.y-m.pivot.y,z=b.z-m.pivot.z;let R=B*h[0]+V*h[3]+z*h[6],W=B*h[1]+V*h[4]+z*h[7],H=B*h[2]+V*h[5]+z*h[8];R+=k.x,W+=k.y,H+=k.z;const j=c[I]=T.x+_.x*R+u.x*W+f.x*H,G=c[I+1]=T.y+_.y*R+u.y*W+f.y*H,Q=c[I+2]=T.z+_.z*R+u.z*W+f.z*H;if(this._computeBoundingBox&&(p.minimizeInPlaceFromFloats(j,G,Q),x.maximizeInPlaceFromFloats(j,G,Q)),this._computeParticleColor&&m.color){const N=m.color,E=this._colors32;E[l]=N.r,E[l+1]=N.g,E[l+2]=N.b,E[l+3]=N.a}if(this._computeParticleTexture&&m.uv){const N=m.uv,E=this._uvs32;E[g]=N.x,E[g+1]=N.y}}return o&&(s&&(this._computeParticleColor&&o.updateVerticesData(K.ColorKind,i,!1,!1),this._computeParticleTexture&&o.updateVerticesData(K.UVKind,d,!1,!1),o.updateVerticesData(K.PositionKind,c,!1,!1)),this._computeBoundingBox&&(o.hasBoundingInfo?o.getBoundingInfo().reConstruct(p,x,o._worldMatrix):o.buildBoundingInfo(p,x,o._worldMatrix))),this.afterUpdateParticles(e,t,s),this}dispose(){var e;(e=this.mesh)==null||e.dispose(),this.vars=null,this._positions=null,this._indices=null,this._normals=null,this._uvs=null,this._colors=null,this._indices32=null,this._positions32=null,this._uvs32=null,this._colors32=null}refreshVisibleSize(){var e;return this._isVisibilityBoxLocked||(e=this.mesh)==null||e.refreshBoundingInfo(),this}setVisibilityBox(e){if(!this.mesh)return;const t=e/2;this.mesh.buildBoundingInfo(new D(-t,-t,-t),new D(t,t,t))}get isAlwaysVisible(){return this._alwaysVisible}set isAlwaysVisible(e){this.mesh&&(this._alwaysVisible=e,this.mesh.alwaysSelectAsActiveMesh=e)}set computeParticleRotation(e){this._computeParticleRotation=e}set computeParticleColor(e){this._computeParticleColor=e}set computeParticleTexture(e){this._computeParticleTexture=e}get computeParticleColor(){return this._computeParticleColor}get computeParticleTexture(){return this._computeParticleTexture}set computeBoundingBox(e){this._computeBoundingBox=e}get computeBoundingBox(){return this._computeBoundingBox}initParticles(){}recycleParticle(e){return e}updateParticle(e){return e}beforeUpdateParticles(e,t,s){}afterUpdateParticles(e,t,s){}}function Bs(r,e,t){const s=new Uint8Array(r),n=new Uint32Array(r.slice(0,12)),o=n[2],i=s[12],c=s[13],d=s[14],a=s[15],_=n[1];if(a||n[0]!=1347635022||_!=2&&_!=3)return new Promise(h=>{h({mode:3,data:f,hasVertexColors:!1})});const u=32,f=new ArrayBuffer(u*o),p=1/(1<<c),x=new Int32Array(1),y=new Uint8Array(x.buffer),I=function(h,v){return y[0]=h[v+0],y[1]=h[v+1],y[2]=h[v+2],y[3]=h[v+2]&128?255:0,x[0]*p};let l=16;const g=new Float32Array(f),S=new Float32Array(f),C=new Uint8ClampedArray(f),w=new Uint8ClampedArray(f);for(let h=0;h<o;h++)g[h*8+0]=I(s,l+0),g[h*8+1]=I(s,l+3),g[h*8+2]=I(s,l+6),l+=9;const m=.282;for(let h=0;h<o;h++){for(let v=0;v<3;v++){const O=(s[l+o+h*3+v]-127.5)/(.15*255);C[h*32+24+v]=X.Clamp((.5+m*O)*255,0,255)}C[h*32+24+3]=s[l+h]}l+=o*4;for(let h=0;h<o;h++)S[h*8+3+0]=Math.exp(s[l+0]/16-10),S[h*8+3+1]=Math.exp(s[l+1]/16-10),S[h*8+3+2]=Math.exp(s[l+2]/16-10),l+=3;if(_>=3){const h=Math.SQRT1_2;for(let v=0;v<o;v++){const T=[s[l+0],s[l+1],s[l+2],s[l+3]],O=T[0]+(T[1]<<8)+(T[2]<<16)+(T[3]<<24),k=511,b=[],B=O>>>30;let V=O,z=0;for(let H=3;H>=0;--H)if(H!==B){const j=V&k,G=V>>>9&1;V=V>>>10,b[H]=h*(j/k),G===1&&(b[H]=-b[H]),z+=b[H]*b[H]}const R=1-z;b[B]=Math.sqrt(Math.max(R,0));const W=[3,0,1,2];for(let H=0;H<4;H++)w[v*32+28+H]=Math.round(127.5+b[W[H]]*127.5);l+=4}}else for(let h=0;h<o;h++){const v=s[l+0],T=s[l+1],O=s[l+2],k=v/127.5-1,b=T/127.5-1,B=O/127.5-1;w[h*32+28+1]=v,w[h*32+28+2]=T,w[h*32+28+3]=O;const V=1-(k*k+b*b+B*B);w[h*32+28+0]=127.5+Math.sqrt(V<0?0:V)*127.5,l+=3}if(i){const v=((i+1)*(i+1)-1)*3,T=Math.ceil(v/16);let O=l;const k=[],B=e.getEngine().getCaps().maxTextureSize,V=Math.ceil(o/B);for(let z=0;z<T;z++){const R=new Uint8Array(V*B*4*4);k.push(R)}for(let z=0;z<o;z++)for(let R=0;R<v;R++){const W=s[O++],H=Math.floor(R/16),j=k[H],G=R%16,Q=z*16;j[G+Q]=W}return new Promise(z=>{z({mode:0,data:f,hasVertexColors:!1,sh:k,trainedWithAntialiasing:!!d})})}return new Promise(h=>{h({mode:0,data:f,hasVertexColors:!1,trainedWithAntialiasing:!!d})})}const Ht=.28209479177387814;async function kt(r,e,t){return await new Promise((n,o)=>{const i=t.createCanvasImage();if(!i)throw new Error("Failed to create ImageBitmap");i.onload=()=>{try{const d=t.createCanvas(i.width,i.height);if(!d)throw new Error("Failed to create canvas");const a=d.getContext("2d");if(!a)throw new Error("Failed to get 2D context");a.drawImage(i,0,0);const _=a.getImageData(0,0,d.width,d.height);n({bits:new Uint8Array(_.data.buffer),width:_.width})}catch(d){o(`Error loading image ${i.src} with exception: ${d}`)}},i.onerror=d=>{o(`Error loading image ${i.src} with exception: ${d}`)},i.crossOrigin="anonymous";let c;if(typeof r=="string"){if(!e)throw new Error("filename is required when using a URL");i.src=r+e}else{const d=new Blob([r],{type:"image/webp"});c=URL.createObjectURL(d),i.src=c}})}async function Us(r,e,t){const s=r.count?r.count:r.means.shape[0],n=32,o=new ArrayBuffer(n*s),i=new Float32Array(o),c=new Float32Array(o),d=new Uint8ClampedArray(o),a=new Uint8ClampedArray(o),_=l=>Math.sign(l)*(Math.exp(Math.abs(l))-1),u=e[0].bits,f=e[1].bits;if(!Array.isArray(r.means.mins)||!Array.isArray(r.means.maxs))throw new Error("Missing arrays in SOG data.");for(let l=0;l<s;l++){const g=l*4;for(let S=0;S<3;S++){const C=r.means.mins[S],w=r.means.maxs[S],m=f[g+S],h=u[g+S],v=m<<8|h,T=X.Lerp(C,w,v/65535);i[l*8+S]=_(T)}}const p=e[2].bits;if(r.version===2){if(!r.scales.codebook)throw new Error("Missing codebook in SOG version 2 scales data.");for(let l=0;l<s;l++){const g=l*4;for(let S=0;S<3;S++){const C=r.scales.codebook[p[g+S]],w=Math.exp(C);c[l*8+3+S]=w}}}else{if(!Array.isArray(r.scales.mins)||!Array.isArray(r.scales.maxs))throw new Error("Missing arrays in SOG scales data.");for(let l=0;l<s;l++){const g=l*4;for(let S=0;S<3;S++){const C=p[g+S],w=X.Lerp(r.scales.mins[S],r.scales.maxs[S],C/255),m=Math.exp(w);c[l*8+3+S]=m}}}const x=e[4].bits;if(r.version===2){if(!r.sh0.codebook)throw new Error("Missing codebook in SOG version 2 sh0 data.");for(let l=0;l<s;l++){const g=l*4;for(let S=0;S<3;S++){const C=.5+r.sh0.codebook[x[g+S]]*Ht;d[l*32+24+S]=Math.max(0,Math.min(255,Math.round(255*C)))}d[l*32+24+3]=x[g+3]}}else{if(!Array.isArray(r.sh0.mins)||!Array.isArray(r.sh0.maxs))throw new Error("Missing arrays in SOG sh0 data.");for(let l=0;l<s;l++){const g=l*4;for(let S=0;S<4;S++){const C=r.sh0.mins[S],w=r.sh0.maxs[S],m=x[g+S],h=X.Lerp(C,w,m/255);let v;S<3?v=.5+h*Ht:v=1/(1+Math.exp(-h)),d[l*32+24+S]=Math.max(0,Math.min(255,Math.round(255*v)))}}}const y=l=>(l/255-.5)*2/Math.SQRT2,I=e[3].bits;for(let l=0;l<s;l++){const g=I[l*4+0],S=I[l*4+1],C=I[l*4+2],w=I[l*4+3],m=y(g),h=y(S),v=y(C),T=w-252,O=m*m+h*h+v*v,k=Math.sqrt(Math.max(0,1-O));let b;switch(T){case 0:b=[k,m,h,v];break;case 1:b=[m,k,h,v];break;case 2:b=[m,h,k,v];break;case 3:b=[m,h,v,k];break;default:throw new Error("Invalid quaternion mode")}a[l*32+28+0]=b[0]*127.5+127.5,a[l*32+28+1]=b[1]*127.5+127.5,a[l*32+28+2]=b[2]*127.5+127.5,a[l*32+28+3]=b[3]*127.5+127.5}if(r.shN){const l=[0,3,8,15],g=r.shN.bands?l[r.shN.bands]:r.shN.shape[1]/3,S=e[5].bits,C=e[6].bits,w=e[5].width,m=g*3,h=Math.ceil(m/16),v=[],O=t.getEngine().getCaps().maxTextureSize,k=Math.ceil(s/O);for(let b=0;b<h;b++){const B=new Uint8Array(k*O*4*4);v.push(B)}if(r.version===2){if(!r.shN.codebook)throw new Error("Missing codebook in SOG version 2 shN data.");for(let b=0;b<s;b++){const B=C[b*4+0]+(C[b*4+1]<<8),V=B%64*g,z=Math.floor(B/64);for(let R=0;R<g;R++)for(let W=0;W<3;W++){const H=R*3+W,j=Math.floor(H/16),G=v[j],Q=H%16,N=b*16,E=r.shN.codebook[S[(V+R)*4+W+z*w*4]]*127.5+127.5;G[Q+N]=Math.max(0,Math.min(255,E))}}}else for(let b=0;b<s;b++){const B=C[b*4+0]+(C[b*4+1]<<8),V=B%64*g,z=Math.floor(B/64),R=r.shN.mins,W=r.shN.maxs;for(let H=0;H<3;H++)for(let j=0;j<g/3;j++){const G=j*3+H,Q=Math.floor(G/16),N=v[Q],E=G%16,ee=b*16,se=X.Lerp(R,W,S[(V+j)*4+H+z*w*4]/255)*127.5+127.5;N[E+ee]=Math.max(0,Math.min(255,se))}}return await new Promise(b=>{b({mode:0,data:o,hasVertexColors:!1,sh:v})})}return await new Promise(l=>{l({mode:0,data:o,hasVertexColors:!1})})}async function Rt(r,e,t){let s,n;if(r instanceof Map){n=r;const c=n.get("meta.json");if(!c)throw new Error("meta.json not found in files Map");s=JSON.parse(new TextDecoder().decode(c))}else s=r;const o=[...s.means.files,...s.scales.files,...s.quats.files,...s.sh0.files];s.shN&&o.push(...s.shN.files);const i=await Promise.all(o.map(async c=>{if(n&&n.has(c)){const d=n.get(c);return await kt(d,c,t.getEngine())}else return await kt(e,c,t.getEngine())}));return await Us(s,i,t)}class te{constructor(e=te._DefaultLoadingOptions){this.name=Fe.name,this._assetContainer=null,this.extensions=Fe.extensions,this._loadingOptions=e}createPlugin(e){return new te(e[Fe.name])}async importMeshAsync(e,t,s,n,o,i){return await this._parseAsync(e,t,s,n).then(c=>({meshes:c,particleSystems:[],skeletons:[],animationGroups:[],transformNodes:[],geometries:[],lights:[],spriteManagers:[]}))}static _BuildPointCloud(e,t){if(!t.byteLength)return!1;const s=new Uint8Array(t),n=new Float32Array(t),o=32,i=s.length/o,c=function(d,a){const _=n[8*a+0],u=n[8*a+1],f=n[8*a+2];d.position=new D(_,u,f);const p=s[o*a+24+0]/255,x=s[o*a+24+1]/255,y=s[o*a+24+2]/255;d.color=new Y(p,x,y,1)};return e.addPoints(i,c),!0}static _BuildMesh(e,t){const s=new Te("PLYMesh",e),n=new Uint8Array(t.data),o=new Float32Array(t.data),i=32,c=n.length/i,d=[],a=new Ve;for(let _=0;_<c;_++){const u=o[8*_+0],f=o[8*_+1],p=o[8*_+2];d.push(u,f,p)}if(t.hasVertexColors){const _=new Float32Array(c*4);for(let u=0;u<c;u++){const f=n[i*u+24+0]/255,p=n[i*u+24+1]/255,x=n[i*u+24+2]/255;_[u*4+0]=f,_[u*4+1]=p,_[u*4+2]=x,_[u*4+3]=1}a.colors=_}return a.positions=d,a.indices=t.faces,a.applyToMesh(s),s}async _unzipWithFFlateAsync(e){let t=this._loadingOptions.fflate;t||(typeof window.fflate>"u"&&await is.LoadScriptAsync(this._loadingOptions.deflateURL??"https://unpkg.com/fflate/umd/index.js"),t=window.fflate);const{unzipSync:s}=t,n=s(e),o=new Map;for(const[i,c]of Object.entries(n))o.set(i,c);return o}_parseAsync(e,t,s,n){const o=[],i=u=>{t._blockEntityCollection=!!this._assetContainer;const f=this._loadingOptions.gaussianSplattingMesh??new A("GaussianSplatting",null,t,this._loadingOptions.keepInRam);f._parentContainer=this._assetContainer,o.push(f),f.updateData(u.data,u.sh,{flipY:!1}),f.scaling.y*=-1,f.computeWorldMatrix(!0),t._blockEntityCollection=!1};if(typeof s=="string"){const u=JSON.parse(s);if(u&&u.means&&u.scales&&u.quats&&u.sh0)return new Promise(f=>{Rt(u,n,t).then(p=>{i(p),f(o)}).catch(()=>{throw new Error("Failed to parse SOG data.")})})}const c=s instanceof ArrayBuffer?new Uint8Array(s):s;if(c[0]===80&&c[1]===75)return new Promise(u=>{this._unzipWithFFlateAsync(c).then(f=>{Rt(f,n,t).then(p=>{i(p),u(o)}).catch(()=>{throw new Error("Failed to parse SOG zip data.")})})});const d=new ReadableStream({start(u){u.enqueue(new Uint8Array(s)),u.close()}}),a=new DecompressionStream("gzip"),_=d.pipeThrough(a);return new Promise(u=>{new Response(_).arrayBuffer().then(f=>{Bs(f,t,this._loadingOptions).then(p=>{t._blockEntityCollection=!!this._assetContainer;const x=this._loadingOptions.gaussianSplattingMesh??new A("GaussianSplatting",null,t,this._loadingOptions.keepInRam);if(p.trainedWithAntialiasing){const y=x.material;y.kernelSize=.1,y.compensation=!0}x._parentContainer=this._assetContainer,o.push(x),x.updateData(p.data,p.sh,{flipY:!1}),this._loadingOptions.flipY||(x.scaling.y*=-1,x.computeWorldMatrix(!0)),t._blockEntityCollection=!1,this.applyAutoCameraLimits(p,t),u(o)})}).catch(()=>{te._ConvertPLYToSplat(s).then(async f=>{switch(t._blockEntityCollection=!!this._assetContainer,f.mode){case 0:{const p=this._loadingOptions.gaussianSplattingMesh??new A("GaussianSplatting",null,t,this._loadingOptions.keepInRam);switch(p._parentContainer=this._assetContainer,o.push(p),p.updateData(f.data,f.sh,{flipY:!1}),p.scaling.y*=-1,f.chirality==="RightHanded"&&(p.scaling.y*=-1),f.upAxis){case"X":p.rotation=new D(0,0,Math.PI/2);break;case"Y":p.rotation=new D(0,0,Math.PI);break;case"Z":p.rotation=new D(-Math.PI/2,Math.PI,0);break}p.computeWorldMatrix(!0)}break;case 1:{const p=new Fs("PointCloud",1,t);te._BuildPointCloud(p,f.data)?await p.buildMeshAsync().then(x=>{o.push(x)}):p.dispose()}break;case 2:if(f.faces)o.push(te._BuildMesh(t,f));else throw new Error("PLY mesh doesn't contain face informations.");break;default:throw new Error("Unsupported Splat mode")}t._blockEntityCollection=!1,this.applyAutoCameraLimits(f,t),u(o)})})})}applyAutoCameraLimits(e,t){var s;if(!this._loadingOptions.disableAutoCameraLimits&&(e.safeOrbitCameraRadiusMin!==void 0||e.safeOrbitCameraElevationMinMax!==void 0)&&((s=t.activeCamera)==null?void 0:s.getClassName())==="ArcRotateCamera"){const n=t.activeCamera;e.safeOrbitCameraElevationMinMax&&(n.lowerBetaLimit=Math.PI*.5-e.safeOrbitCameraElevationMinMax[1],n.upperBetaLimit=Math.PI*.5-e.safeOrbitCameraElevationMinMax[0]),e.safeOrbitCameraRadiusMin&&(n.lowerRadiusLimit=e.safeOrbitCameraRadiusMin)}}loadAssetContainerAsync(e,t,s){const n=new cs(e);return this._assetContainer=n,this.importMeshAsync(null,e,t,s).then(o=>{for(const i of o.meshes)n.meshes.push(i);return this._assetContainer=null,n}).catch(o=>{throw this._assetContainer=null,o})}loadAsync(e,t,s){return this.importMeshAsync(null,e,t,s).then(()=>{})}static _ConvertPLYToSplat(e){const t=new Uint8Array(e),s=new TextDecoder().decode(t.slice(0,1024*10)),n=`end_header
`,o=s.indexOf(n);if(o<0||!s)return new Promise(w=>{w({mode:0,data:e,rawSplat:!0})});const i=parseInt(/element vertex (\d+)\n/.exec(s)[1]),c=/element face (\d+)\n/.exec(s);let d=0;c&&(d=parseInt(c[1]));const a=/element chunk (\d+)\n/.exec(s);let _=0;a&&(_=parseInt(a[1]));let u=0,f=0;const p={double:8,int:4,uint:4,float:4,short:2,ushort:2,uchar:1,list:0},x={Vertex:0,Chunk:1,SH:2,Float_Tuple:3,Float:4,Uchar:5};let y=x.Chunk;const I=[],l=s.slice(0,o).split(`
`),g={};for(const w of l)if(w.startsWith("property ")){const[,m,h]=w.split(" ");if(y==x.Chunk)f+=p[m];else if(y==x.Vertex)I.push({name:h,type:m,offset:u}),u+=p[m];else if(y==x.SH)I.push({name:h,type:m,offset:u});else if(y==x.Float_Tuple){const v=new DataView(e,f,p.float*2);g.safeOrbitCameraElevationMinMax=[v.getFloat32(0,!0),v.getFloat32(4,!0)]}else if(y==x.Float){const v=new DataView(e,f,p.float);g.safeOrbitCameraRadiusMin=v.getFloat32(0,!0)}else if(y==x.Uchar){const v=new DataView(e,f,p.uchar);h=="up_axis"?g.upAxis=v.getUint8(0)==0?"X":v.getUint8(0)==1?"Y":"Z":h=="chirality"&&(g.chirality=v.getUint8(0)==0?"LeftHanded":"RightHanded")}p[m]||pe.Warn(`Unsupported property type: ${m}.`)}else if(w.startsWith("element ")){const[,m]=w.split(" ");m=="chunk"?y=x.Chunk:m=="vertex"?y=x.Vertex:m=="sh"?y=x.SH:m=="safe_orbit_camera_elevation_min_max_radians"?y=x.Float_Tuple:m=="safe_orbit_camera_radius_min"?y=x.Float:(m=="up_axis"||m=="chirality")&&(y=x.Uchar)}const S=u,C=f;return A.ConvertPLYWithSHToSplatAsync(e).then(async w=>{const m=new DataView(e,o+n.length);let h=C*_+S*i;const v=[];if(d)for(let z=0;z<d;z++){const R=m.getUint8(h);if(R==3){h+=1;for(let W=0;W<R;W++){const H=m.getUint32(h+(2-W)*4,!0);v.push(H)}h+=12}}if(_)return await new Promise(z=>{z({mode:0,data:w.buffer,sh:w.sh,faces:v,hasVertexColors:!1,compressed:!0,rawSplat:!1})});let T=0,O=0;const k=["x","y","z","scale_0","scale_1","scale_2","opacity","rot_0","rot_1","rot_2","rot_3"],b=["red","green","blue","f_dc_0","f_dc_1","f_dc_2"];for(let z=0;z<I.length;z++){const R=I[z];k.includes(R.name)&&T++,b.includes(R.name)&&O++}const B=T==k.length&&O==3,V=d?2:B?0:1;return await new Promise(z=>{z({...g,mode:V,data:w.buffer,sh:w.sh,faces:v,hasVertexColors:!!O,compressed:!1,rawSplat:!1})})})}}te._DefaultLoadingOptions={keepInRam:!1,flipY:!1};as(new te);export{te as SPLATFileLoader};
