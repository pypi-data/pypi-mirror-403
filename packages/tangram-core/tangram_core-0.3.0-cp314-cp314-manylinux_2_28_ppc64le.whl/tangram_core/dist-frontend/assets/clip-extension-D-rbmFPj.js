import{L as c}from"./layer-extension-CYwTXf73.js";const l={clipBounds:[0,0,1,1],clipByInstance:void 0},t=`
uniform clipUniforms {
  vec4 bounds;
} clip;

bool clip_isInBounds(vec2 position) {
  return position.x >= clip.bounds[0] && position.y >= clip.bounds[1] && position.x < clip.bounds[2] && position.y < clip.bounds[3];
}
`,p={name:"clip",vs:t,uniformTypes:{bounds:"vec4<f32>"}},d={"vs:#decl":`
out float clip_isVisible;
`,"vs:DECKGL_FILTER_GL_POSITION":`
  clip_isVisible = float(clip_isInBounds(geometry.worldPosition.xy));
`,"fs:#decl":`
in float clip_isVisible;
`,"fs:DECKGL_FILTER_COLOR":`
  if (clip_isVisible < 0.5) discard;
`},a={name:"clip",fs:t,uniformTypes:{bounds:"vec4<f32>"}},r={"vs:#decl":`
out vec2 clip_commonPosition;
`,"vs:DECKGL_FILTER_GL_POSITION":`
  clip_commonPosition = geometry.position.xy;
`,"fs:#decl":`
in vec2 clip_commonPosition;
`,"fs:DECKGL_FILTER_COLOR":`
  if (!clip_isInBounds(clip_commonPosition)) discard;
`};class e extends c{getShaders(){let i="instancePositions"in this.getAttributeManager().attributes;return this.props.clipByInstance!==void 0&&(i=!!this.props.clipByInstance),this.state.clipByInstance=i,i?{modules:[p],inject:d}:{modules:[a],inject:r}}draw(){const{clipBounds:i}=this.props,n={};if(this.state.clipByInstance)n.bounds=i;else{const s=this.projectPosition([i[0],i[1],0]),o=this.projectPosition([i[2],i[3],0]);n.bounds=[Math.min(s[0],o[0]),Math.min(s[1],o[1]),Math.max(s[0],o[0]),Math.max(s[1],o[1])]}this.setShaderModuleProps({clip:n})}}e.defaultProps=l;e.extensionName="ClipExtension";export{e as C};
//# sourceMappingURL=clip-extension-D-rbmFPj.js.map
