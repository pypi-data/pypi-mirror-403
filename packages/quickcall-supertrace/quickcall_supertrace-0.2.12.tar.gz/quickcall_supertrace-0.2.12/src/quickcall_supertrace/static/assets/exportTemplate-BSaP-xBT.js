import{m as nt}from"./index-U_y88BhN.js";function rt(t){if(!t)return"";let o=t;return t.endsWith("+00:00")?o=t.replace("+00:00","Z"):t.endsWith("Z")||(o=t+"Z"),new Date(o).toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"})}function O(t){return t>=1e6?`${(t/1e6).toFixed(1)}M`:t>=1e3?`${(t/1e3).toFixed(1)}K`:t.toString()}function at(t){return t>=1e6?`${(t/1e6).toFixed(0)}M`:t>=1e3?`${(t/1e3).toFixed(0)}K`:t.toString()}function J(t){if(t===null||isNaN(t))return"-";if(t<60)return`${Math.round(t)}s`;const o=Math.floor(t/60),e=Math.round(t%60);return e>0?`${o}m ${e}s`:`${o}m`}function K(t,o={}){const{width:e=600,showCache:n=!0,isDark:a=!1}=o;if(!t||t.turns.length===0)return`<svg width="${e}" height="100" xmlns="http://www.w3.org/2000/svg">
      <text x="${e/2}" y="50" text-anchor="middle" fill="${a?"#9ca3af":"#6b7280"}" font-size="12">No prompt data</text>
    </svg>`;const{turns:r,maxTokens:M,maxTokensNoCache:x,maxTools:c,totals:C}=t,l=n?M:x,g=40,p=20,y=e-g-p,D=80,h=80,b=8,u=C.commits>0?16:0,$=C.thinking>0?16:0,v=20,S={top:8,bottom:4},d={top:4,bottom:4},_=D-S.top-S.bottom,z=h-d.top-d.bottom,I=D+b+h+u+$+v,H=a?"oklch(0.58 0.15 290)":"oklch(0.55 0.25 290)",w=a?"oklch(0.62 0.15 165)":"oklch(0.7 0.25 165)",L=a?"rgba(255,255,255,0.08)":"rgba(0,0,0,0.08)",i=a?"#9ca3af":"#6b7280",k=a?"oklch(0.70 0.12 85)":"oklch(0.8 0.15 85)",m=s=>r.length===1?g+y/2:g+12+s/(r.length-1)*(y-24),F=l||1,P=c||1,W=s=>{const T=s/F;return S.top+_-T*_},Z=s=>n?s.inputTokens:s.inputTokensNoCache??s.inputTokens,tt=r.map((s,T)=>`${m(T)},${W(Z(s))}`),et=r.map((s,T)=>`${m(T)},${W(s.outputTokens)}`),ot=`M ${tt.join(" L ")}`,st=`M ${et.join(" L ")}`,U=[0,.5,1].map(s=>({value:Math.round(F*s),y:W(F*s)})),V=[0,Math.ceil(P/2),P].map(s=>({value:s,y:d.top+z-s/P*z}));let f=`<svg width="${e}" height="${I}" xmlns="http://www.w3.org/2000/svg" style="font-family: ui-sans-serif, system-ui, sans-serif;">`;U.forEach(s=>{f+=`<text x="${g-4}" y="${s.y+3}" text-anchor="end" fill="${i}" font-size="9">${at(s.value)}</text>`}),U.forEach(s=>{f+=`<line x1="${g}" y1="${s.y}" x2="${e-p}" y2="${s.y}" stroke="${L}" stroke-dasharray="2,2"/>`}),f+=`<path d="${ot}" fill="none" stroke="${H}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>`,f+=`<path d="${st}" fill="none" stroke="${w}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>`,r.forEach((s,T)=>{const E=m(T),B=W(Z(s)),A=W(s.outputTokens);f+=`<circle cx="${E}" cy="${B}" r="4" fill="${H}"/>`,f+=`<circle cx="${E}" cy="${B}" r="2" fill="white"/>`,f+=`<circle cx="${E}" cy="${A}" r="4" fill="${w}"/>`,f+=`<circle cx="${E}" cy="${A}" r="2" fill="white"/>`});const j=D+b;if(V.forEach(s=>{f+=`<text x="${g-4}" y="${j+s.y+3}" text-anchor="end" fill="${i}" font-size="9">${s.value}</text>`}),V.forEach(s=>{f+=`<line x1="${g}" y1="${j+s.y}" x2="${e-p}" y2="${j+s.y}" stroke="${L}" stroke-dasharray="2,2"/>`}),r.forEach((s,T)=>{const E=m(T),B=20;let A=j+z+d.top;s.tools.forEach(R=>{const X=R.count/P*z;A-=X,f+=`<rect x="${E-B/2}" y="${A}" width="${B}" height="${X}" fill="${R.color}" rx="2" opacity="0.8"/>`})}),u>0){const s=j+h;f+=`<line x1="${g}" y1="${s+u/2}" x2="${e-p}" y2="${s+u/2}" stroke="${k}" stroke-opacity="0.3" stroke-dasharray="4,4"/>`,r.forEach((T,E)=>{T.hasCommit&&(f+=`<circle cx="${m(E)}" cy="${s+u/2}" r="4" fill="${k}"/>`)})}if($>0){const s=j+h+u;f+=`<line x1="${g}" y1="${s+$/2}" x2="${e-p}" y2="${s+$/2}" stroke="#a855f7" stroke-opacity="0.3" stroke-dasharray="4,4"/>`,r.forEach((T,E)=>{T.hasThinking&&(f+=`<circle cx="${m(E)}" cy="${s+$/2}" r="4" fill="#a855f7"/>`)})}const G=j+h+u+$;return f+=`<line x1="${g}" y1="${G}" x2="${e-p}" y2="${G}" stroke="${L}"/>`,r.forEach((s,T)=>{f+=`<text x="${m(T)}" y="${G+14}" text-anchor="middle" fill="${i}" font-size="9">${s.promptIndex}</text>`}),f+="</svg>",f}function Q(t,o={}){const{width:e=400,isDark:n=!1}=o;if(!t||t.toolLegend.length===0)return`<svg width="${e}" height="60" xmlns="http://www.w3.org/2000/svg">
      <text x="${e/2}" y="30" text-anchor="middle" fill="${n?"#9ca3af":"#6b7280"}" font-size="12">No tool usage data</text>
    </svg>`;const a=t.totals.tools,r=t.toolLegend,M=r.reduce((d,_)=>d+_.count,0),x=a-M,c=12,C=24,l=8,g=l+c+l+C+l,p=n?"#9ca3af":"#6b7280",y=n?"rgba(255,255,255,0.4)":"rgba(0,0,0,0.4)",D=n?"#374151":"#e5e7eb";let h=`<svg width="${e}" height="${g}" xmlns="http://www.w3.org/2000/svg" style="font-family: ui-sans-serif, system-ui, sans-serif;">`;h+=`<rect x="${l}" y="${l}" width="${e-l*2}" height="${c}" fill="${D}" rx="6"/>`;let b=l;const u=e-l*2;if(r.forEach((d,_)=>{const I=(a>0?d.count/a:0)*u,H=_===0,w=_===r.length-1&&x<=0;h+=`<rect x="${b}" y="${l}" width="${I}" height="${c}" fill="${d.color}" ${H?'rx="6" ry="6"':""} ${w?'rx="6" ry="6"':""}/>`,b+=I}),x>0){const _=x/a*u;h+=`<rect x="${b}" y="${l}" width="${_}" height="${c}" fill="${y}" rx="6" ry="6"/>`}const $=l+c+l+4;let v=l;const S=6;if(r.slice(0,S).forEach(d=>{const _=a>0?d.count/a*100:0;h+=`<rect x="${v}" y="${$}" width="8" height="8" fill="${d.color}" rx="2"/>`,v+=12;const z=d.name.length>8?d.name.slice(0,8)+"...":d.name;h+=`<text x="${v}" y="${$+7}" fill="${n?"#e5e7eb":"#374151"}" font-size="10">${z}</text>`,v+=z.length*6+4,h+=`<text x="${v}" y="${$+7}" fill="${p}" font-size="10">${d.count}</text>`,v+=String(d.count).length*6+4,h+=`<text x="${v}" y="${$+7}" fill="${y}" font-size="10">(${_.toFixed(0)}%)</text>`,v+=36}),r.length>S||x>0){const d=r.length>S?r.length-S+(x>0?1:0):1;h+=`<text x="${v}" y="${$+7}" fill="${p}" font-size="10">+${d} more</text>`}return h+="</svg>",h}function q(t,o={}){const{width:e=600,isDark:n=!1}=o;if(!t||t.turns.length===0)return`<svg width="${e}" height="80" xmlns="http://www.w3.org/2000/svg">
      <text x="${e/2}" y="40" text-anchor="middle" fill="${n?"#9ca3af":"#6b7280"}" font-size="12">No timing data</text>
    </svg>`;const{turns:a,maxDuration:r}=t,M=a.filter(i=>i.durationSeconds!==null);if(M.length===0)return`<svg width="${e}" height="80" xmlns="http://www.w3.org/2000/svg">
      <text x="${e/2}" y="40" text-anchor="middle" fill="${n?"#9ca3af":"#6b7280"}" font-size="12">No timing data available</text>
    </svg>`;const x=48,c=20,C=e-x-c,l=60,g=28,p={top:4,bottom:4},y=l-p.top-p.bottom,D=l+g,h=n?"#e5e7eb":"#1f2937",b=n?"rgba(255,255,255,0.08)":"rgba(0,0,0,0.08)",u=n?"#9ca3af":"#6b7280",$=i=>a.length===1?x+C/2:x+12+i/(a.length-1)*(C-24),v=M.map(i=>i.durationSeconds).filter(i=>i>0).sort((i,k)=>i-k),S=Math.floor(v.length*.9),d=v[S]||r||1,z=Math.max(d,(r||1)*.3)||1,I=i=>i===null?0:Math.min(i/z,1)*y,H=[0,.5,1].map(i=>({value:Math.round(z*i),y:p.top+y-i*y}));let w=`<svg width="${e}" height="${D}" xmlns="http://www.w3.org/2000/svg" style="font-family: ui-sans-serif, system-ui, sans-serif;">`;H.forEach(i=>{w+=`<text x="${x-4}" y="${i.y+3}" text-anchor="end" fill="${u}" font-size="9">${J(i.value)}</text>`}),H.forEach(i=>{w+=`<line x1="${x}" y1="${i.y}" x2="${e-c}" y2="${i.y}" stroke="${b}" stroke-dasharray="2,2"/>`});const L=16;return a.forEach((i,k)=>{const m=$(k),F=I(i.durationSeconds),P=p.top+y-F;w+=`<rect x="${m-L/2}" y="${P}" width="${L}" height="${F}" fill="${h}" opacity="0.6" rx="2"/>`}),w+=`<line x1="${x}" y1="${l}" x2="${e-c}" y2="${l}" stroke="${b}"/>`,a.forEach((i,k)=>{const m=$(k);w+=`<text x="${m}" y="${l+12}" text-anchor="middle" fill="${u}" font-size="8">${rt(i.startTime)}</text>`,w+=`<text x="${m}" y="${l+22}" text-anchor="middle" fill="${u}" font-size="8" opacity="0.6">#${i.promptIndex}</text>`}),w+="</svg>",w}function mt(t){const{session:o,metrics:e,chart_data:n,intents:a,metadata:r}=t,M=e?.by_category?.tokens||{},x=e?.by_category?.tools||{},c=e?.by_category?.timing||{},C=e?.by_category?.interaction||{},l=Y(M,"estimated_cost",0),g=Y(M,"cache_savings",0),p=n.prompt_turns,y=p?.totals?.inputTokens||0,D=p?.totals?.outputTokens||0,h=p?.totals?.cacheReadTokens||0,b=x?.tool_distribution?.value,u=b?Object.values(b).reduce((k,m)=>k+m,0):p?.totals?.tools||0,$=Y(c,"session_duration",0),v=Y(C,"prompt_count",0)||p?.turns?.length||0,S=v>0?u/v:0,d=o.project_path&&o.project_path.split("/").pop()||"Session",_=o.started_at?new Date(o.started_at.endsWith("Z")?o.started_at:o.started_at+"Z").toLocaleDateString(void 0,{month:"short",day:"numeric",year:"numeric"}):"Unknown date",z=n.prompt_turns?K(n.prompt_turns,{width:600,isDark:!1}):"",I=n.prompt_turns?K(n.prompt_turns,{width:600,isDark:!0}):"",H=n.prompt_turns?Q(n.prompt_turns,{width:500,isDark:!1}):"",w=n.prompt_turns?Q(n.prompt_turns,{width:500,isDark:!0}):"",L=n.prompt_turns?q(n.prompt_turns,{width:600,isDark:!1}):"",i=n.prompt_turns?q(n.prompt_turns,{width:600,isDark:!0}):"";return`<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${N(d)} - Session Dashboard</title>
  <style>${nt(it())}</style>
</head>
<body>
  <div class="container">
    <!-- Header -->
    <header class="header">
      <div class="header-content">
        <div class="header-left">
          <div class="brand">
            <svg class="brand-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
            </svg>
            <span class="brand-text">QuickCall SuperTrace</span>
          </div>
          <h1 class="title">${N(d)}</h1>
          <p class="subtitle">${N(_)} · ${v} prompts · ${r.export_level} export</p>
        </div>
        <div class="header-right">
          <button id="theme-toggle" class="theme-toggle" title="Toggle dark mode">
            <svg class="sun-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="5"/>
              <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
            </svg>
            <svg class="moon-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
            </svg>
          </button>
        </div>
      </div>
    </header>

    ${a&&a.length>0?`
    <!-- Session Intents -->
    <section class="intents-section">
      <div class="intents-container">
        <span class="intents-label">Session Goals:</span>
        <div class="intents-list">
          ${a.map(k=>`<span class="intent-tag">${N(k)}</span>`).join("")}
        </div>
      </div>
    </section>
    `:""}

    <!-- Metrics Grid -->
    <section class="metrics-grid">
      <div class="metric-card cost">
        <div class="metric-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 1v22M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
          </svg>
        </div>
        <div class="metric-content">
          <span class="metric-value">$${l.toFixed(4)}</span>
          <span class="metric-label">Estimated Cost</span>
        </div>
      </div>

      <div class="metric-card tokens">
        <div class="metric-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
        </div>
        <div class="metric-content">
          <span class="metric-value">${O(y+D)}</span>
          <span class="metric-label">Total Tokens</span>
          <span class="metric-detail">In: ${O(y)} · Out: ${O(D)}</span>
        </div>
      </div>

      <div class="metric-card tools">
        <div class="metric-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
          </svg>
        </div>
        <div class="metric-content">
          <span class="metric-value">${u}</span>
          <span class="metric-label">Tool Calls</span>
          <span class="metric-detail">${S.toFixed(1)} avg per prompt</span>
        </div>
      </div>

      <div class="metric-card duration">
        <div class="metric-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 6v6l4 2"/>
          </svg>
        </div>
        <div class="metric-content">
          <span class="metric-value">${J($)}</span>
          <span class="metric-label">Duration</span>
        </div>
      </div>

      ${g>0?`
      <div class="metric-card cache">
        <div class="metric-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 7V4a2 2 0 0 1 2-2h8.5L20 7.5V20a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-3"/>
            <path d="M14 2v6h6"/>
            <path d="M5 12h10"/>
            <path d="M5 15h10"/>
            <path d="M5 18h10"/>
          </svg>
        </div>
        <div class="metric-content">
          <span class="metric-value">$${g.toFixed(4)}</span>
          <span class="metric-label">Cache Savings</span>
          <span class="metric-detail">${O(h)} cached tokens</span>
        </div>
      </div>
      `:""}
    </section>

    <!-- Charts Section -->
    <section class="charts-section">
      ${z?`
      <div class="chart-card">
        <h2 class="chart-title">Token Usage & Tools per Prompt</h2>
        <div class="chart-container">
          <div class="chart-light">${z}</div>
          <div class="chart-dark">${I}</div>
        </div>
        <div class="chart-legend">
          <span class="legend-item">
            <span class="legend-dot" style="background: oklch(0.55 0.25 290)"></span>
            Input Tokens
          </span>
          <span class="legend-item">
            <span class="legend-dot" style="background: oklch(0.7 0.25 165)"></span>
            Output Tokens
          </span>
        </div>
      </div>
      `:""}

      ${H?`
      <div class="chart-card">
        <h2 class="chart-title">Tool Distribution</h2>
        <div class="chart-container">
          <div class="chart-light">${H}</div>
          <div class="chart-dark">${w}</div>
        </div>
      </div>
      `:""}

      ${L?`
      <div class="chart-card">
        <h2 class="chart-title">Turn Duration</h2>
        <div class="chart-container">
          <div class="chart-light">${L}</div>
          <div class="chart-dark">${i}</div>
        </div>
      </div>
      `:""}
    </section>

    ${b&&Object.keys(b).length>0?`
    <!-- Tool Breakdown -->
    <section class="tools-section">
      <h2 class="section-title">Tool Breakdown</h2>
      <div class="tools-grid">
        ${Object.entries(b).sort(([,k],[,m])=>m-k).slice(0,12).map(([k,m])=>`
            <div class="tool-item">
              <span class="tool-name">${N(k)}</span>
              <span class="tool-count">${m}</span>
              <span class="tool-percent">${(m/u*100).toFixed(1)}%</span>
            </div>
          `).join("")}
      </div>
    </section>
    `:""}

    ${lt(t.events,r.export_level)}

    <!-- Footer -->
    <footer class="footer">
      <p>Exported from <strong>QuickCall SuperTrace</strong> v${r.version}</p>
      <p class="footer-meta">
        Session ID: ${o.id.slice(0,12)}... ·
        Exported: ${new Date(r.exported_at).toLocaleString()} ·
        ${r.events_included} of ${r.events_total} events included
      </p>
    </footer>
  </div>

  <script>${ct()}<\/script>
</body>
</html>`}function it(){return`
    :root {
      --bg: #fafafa;
      --bg-card: #ffffff;
      --fg: #1f2937;
      --fg-muted: #6b7280;
      --border: #e5e7eb;
      --cost: oklch(0.75 0.15 55);
      --success: oklch(0.65 0.2 145);
      --info: oklch(0.6 0.15 250);
      --warning: oklch(0.8 0.15 85);
      --primary: #1f2937;
    }

    .dark {
      --bg: #111111;
      --bg-card: #1a1a1a;
      --fg: #f3f4f6;
      --fg-muted: #9ca3af;
      --border: #374151;
      --cost: oklch(0.65 0.12 55);
      --success: oklch(0.62 0.12 145);
      --info: oklch(0.60 0.10 250);
      --warning: oklch(0.70 0.12 85);
      --primary: #e5e7eb;
    }

    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      background: var(--bg);
      color: var(--fg);
      line-height: 1.5;
      min-height: 100vh;
    }

    .container {
      max-width: 900px;
      margin: 0 auto;
      padding: 24px 16px;
    }

    /* Header */
    .header {
      margin-bottom: 24px;
    }

    .header-content {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;
    }

    .brand-icon {
      width: 20px;
      height: 20px;
      color: var(--cost);
    }

    .brand-text {
      font-size: 12px;
      font-weight: 500;
      color: var(--fg-muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .title {
      font-size: 24px;
      font-weight: 600;
      margin-bottom: 4px;
    }

    .subtitle {
      font-size: 14px;
      color: var(--fg-muted);
    }

    .theme-toggle {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 8px;
      cursor: pointer;
      color: var(--fg);
    }

    .theme-toggle:hover {
      background: var(--border);
    }

    .theme-toggle svg {
      width: 20px;
      height: 20px;
    }

    .sun-icon { display: block; }
    .moon-icon { display: none; }
    .dark .sun-icon { display: none; }
    .dark .moon-icon { display: block; }

    /* Intents Section */
    .intents-section {
      margin-bottom: 20px;
    }

    .intents-container {
      display: flex;
      align-items: flex-start;
      gap: 12px;
      flex-wrap: wrap;
    }

    .intents-label {
      font-size: 13px;
      font-weight: 500;
      color: var(--fg-muted);
      white-space: nowrap;
      padding-top: 4px;
    }

    .intents-list {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .intent-tag {
      display: inline-block;
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 4px 12px;
      font-size: 13px;
      color: var(--fg);
    }

    /* Metrics Grid */
    .metrics-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }

    .metric-card {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 16px;
      display: flex;
      align-items: flex-start;
      gap: 12px;
    }

    .metric-icon {
      width: 40px;
      height: 40px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }

    .metric-icon svg {
      width: 20px;
      height: 20px;
    }

    .metric-card.cost .metric-icon { background: color-mix(in oklch, var(--cost) 15%, transparent); color: var(--cost); }
    .metric-card.tokens .metric-icon { background: color-mix(in oklch, var(--info) 15%, transparent); color: var(--info); }
    .metric-card.tools .metric-icon { background: color-mix(in oklch, var(--success) 15%, transparent); color: var(--success); }
    .metric-card.duration .metric-icon { background: color-mix(in oklch, var(--primary) 10%, transparent); color: var(--fg-muted); }
    .metric-card.cache .metric-icon { background: color-mix(in oklch, var(--warning) 15%, transparent); color: var(--warning); }

    .metric-content {
      display: flex;
      flex-direction: column;
      min-width: 0;
    }

    .metric-value {
      font-size: 20px;
      font-weight: 600;
      font-variant-numeric: tabular-nums;
    }

    .metric-label {
      font-size: 13px;
      color: var(--fg-muted);
    }

    .metric-detail {
      font-size: 11px;
      color: var(--fg-muted);
      opacity: 0.7;
      margin-top: 2px;
    }

    /* Charts Section */
    .charts-section {
      display: flex;
      flex-direction: column;
      gap: 20px;
      margin-bottom: 24px;
    }

    .chart-card {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 20px;
    }

    .chart-title {
      font-size: 14px;
      font-weight: 600;
      margin-bottom: 16px;
    }

    .chart-container {
      overflow-x: auto;
    }

    .chart-container svg {
      display: block;
      max-width: 100%;
      height: auto;
    }

    .chart-light { display: block; }
    .chart-dark { display: none; }
    .dark .chart-light { display: none; }
    .dark .chart-dark { display: block; }

    .chart-legend {
      display: flex;
      gap: 16px;
      margin-top: 12px;
      font-size: 12px;
      color: var(--fg-muted);
    }

    .legend-item {
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .legend-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
    }

    /* Section titles */
    .section-title {
      font-size: 14px;
      font-weight: 600;
      margin-bottom: 12px;
    }

    /* Tools Section */
    .tools-section {
      margin-bottom: 24px;
    }

    .tools-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
      gap: 8px;
    }

    .tool-item {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 10px 12px;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .tool-name {
      font-size: 13px;
      font-weight: 500;
      flex: 1;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .tool-count {
      font-size: 13px;
      font-weight: 600;
      font-variant-numeric: tabular-nums;
    }

    .tool-percent {
      font-size: 11px;
      color: var(--fg-muted);
    }

    /* Conversation Section */
    .conversation-section {
      margin-bottom: 24px;
    }

    .conversation-timeline {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .message {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 12px 16px;
    }

    .message-user {
      border-left: 3px solid var(--info);
    }

    .message-assistant {
      border-left: 3px solid var(--success);
    }

    .message-header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;
    }

    .message-index {
      font-size: 11px;
      font-weight: 600;
      padding: 2px 8px;
      border-radius: 10px;
      background: var(--border);
      color: var(--fg-muted);
    }

    .message-user .message-index {
      background: color-mix(in oklch, var(--info) 15%, transparent);
      color: var(--info);
    }

    .message-assistant .message-index {
      background: color-mix(in oklch, var(--success) 15%, transparent);
      color: var(--success);
    }

    .message-role {
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .message-user .message-role {
      color: var(--info);
    }

    .message-assistant .message-role {
      color: var(--success);
    }

    .message-time {
      font-size: 11px;
      color: var(--fg-muted);
    }

    .message-content {
      font-size: 14px;
      line-height: 1.6;
      white-space: pre-wrap;
      word-break: break-word;
    }

    .conversation-more {
      text-align: center;
      padding: 16px;
      background: var(--bg-card);
      border: 1px dashed var(--border);
      border-radius: 12px;
      color: var(--fg-muted);
      font-size: 13px;
    }

    .conversation-hint {
      display: block;
      font-size: 11px;
      margin-top: 4px;
      opacity: 0.7;
    }

    /* Footer */
    .footer {
      text-align: center;
      padding-top: 24px;
      border-top: 1px solid var(--border);
      font-size: 12px;
      color: var(--fg-muted);
    }

    .footer-meta {
      margin-top: 4px;
      font-size: 11px;
      opacity: 0.7;
    }

    /* Responsive */
    @media (max-width: 600px) {
      .container {
        padding: 16px 12px;
      }

      .header-content {
        flex-direction: column;
        gap: 12px;
      }

      .header-right {
        align-self: flex-end;
      }

      .title {
        font-size: 20px;
      }

      .metrics-grid {
        grid-template-columns: repeat(2, 1fr);
      }

      .metric-card {
        padding: 12px;
      }

      .metric-value {
        font-size: 16px;
      }

      .tools-grid {
        grid-template-columns: repeat(2, 1fr);
      }
    }

    @media print {
      .theme-toggle { display: none; }
      .container { max-width: none; }
    }
  `}function ct(){return`
    (function() {
      const toggle = document.getElementById('theme-toggle');
      const html = document.documentElement;

      // Check for saved preference or system preference
      const savedTheme = localStorage.getItem('theme');
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

      if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
        html.classList.add('dark');
      }

      toggle.addEventListener('click', function() {
        html.classList.toggle('dark');
        localStorage.setItem('theme', html.classList.contains('dark') ? 'dark' : 'light');
      });
    })();
  `}function Y(t,o,e){const n=t[o];if(!n||n.value===null||n.value===void 0)return e;const a=Number(n.value);return isNaN(a)?e:a}function N(t){return t.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#039;")}function lt(t,o){if(!t||t.length===0)return"";const e=t.filter(c=>c.event_type==="user_prompt"||c.event_type==="assistant_stop"||c.event_type==="assistant_response"||c.event_type==="user_message"||c.event_type==="assistant_message");if(e.length===0)return"";const n=o==="summary"?10:o==="full"?100:e.length,a=e.slice(0,n),r=e.length>n;let M=0;const x=a.map(c=>{const C=c.event_type==="user_prompt"||c.event_type==="user_message",l=dt(c),g=pt(l,o);if(!g.trim())return"";if(C&&c.data){const y=c.data;typeof y.promptIndex=="number"?M=y.promptIndex:M++}const p=C?`Prompt #${M}`:`Response #${M}`;return`
      <div class="message ${C?"message-user":"message-assistant"}">
        <div class="message-header">
          <span class="message-index">${p}</span>
          <span class="message-role">${C?"User":"Claude"}</span>
          ${c.timestamp?`<span class="message-time">${gt(c.timestamp)}</span>`:""}
        </div>
        <div class="message-content">${N(g)}</div>
      </div>
    `}).join("");return`
    <!-- Conversation Timeline -->
    <section class="conversation-section">
      <h2 class="section-title">Conversation (${e.length} messages)</h2>
      <div class="conversation-timeline">
        ${x}
        ${r?`
          <div class="conversation-more">
            <span>+ ${e.length-n} more messages</span>
            <span class="conversation-hint">Export with "Full" or "Archive" level to see all messages</span>
          </div>
        `:""}
      </div>
    </section>
  `}function dt(t){const o=t.data;if(!o)return"";if(typeof o=="object"){if("prompt"in o&&typeof o.prompt=="string")return o.prompt;if("transcript"in o&&Array.isArray(o.transcript)){const e=o.transcript,n=[];for(const a of e)if(a.type==="assistant"&&a.message?.content)for(const r of a.message.content)r.type==="text"&&r.text&&n.push(r.text);if(n.length>0)return n.join(`
`)}if("message"in o&&typeof o.message=="string")return o.message;if("content"in o&&Array.isArray(o.content))return o.content.filter(e=>e.type==="text"&&e.text).map(e=>e.text).join(`
`);if("text"in o&&typeof o.text=="string")return o.text;if("response"in o&&typeof o.response=="string")return o.response}return""}function pt(t,o){const e=o==="summary"?500:o==="full"?2e3:t.length;return t.length<=e?t:t.slice(0,e)+"..."}function gt(t){try{return new Date(t.endsWith("Z")?t:t+"Z").toLocaleTimeString(void 0,{hour:"2-digit",minute:"2-digit"})}catch{return""}}export{mt as generateDashboardHTML};
