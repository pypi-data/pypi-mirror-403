import{m as nt}from"./index-B3w_787x.js";function rt(t){if(!t)return"";let o=t;return t.endsWith("+00:00")?o=t.replace("+00:00","Z"):t.endsWith("Z")||(o=t+"Z"),new Date(o).toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"})}function O(t){return t>=1e6?`${(t/1e6).toFixed(1)}M`:t>=1e3?`${(t/1e3).toFixed(1)}K`:t.toString()}function at(t){return t>=1e6?`${(t/1e6).toFixed(0)}M`:t>=1e3?`${(t/1e3).toFixed(0)}K`:t.toString()}function J(t){if(t===null||isNaN(t))return"-";if(t<60)return`${Math.round(t)}s`;const o=Math.floor(t/60),e=Math.round(t%60);return e>0?`${o}m ${e}s`:`${o}m`}function K(t,o={}){const{width:e=600,showCache:n=!0,isDark:a=!1}=o;if(!t||t.turns.length===0)return`<svg width="${e}" height="100" xmlns="http://www.w3.org/2000/svg">
      <text x="${e/2}" y="50" text-anchor="middle" fill="${a?"#9ca3af":"#6b7280"}" font-size="12">No prompt data</text>
    </svg>`;const{turns:r,maxTokens:w,maxTokensNoCache:f,maxTools:c,totals:T}=t,l=n?w:f,g=40,p=20,$=e-g-p,L=80,h=80,b=8,u=T.commits>0?16:0,v=T.thinking>0?16:0,x=20,D={top:8,bottom:4},d={top:4,bottom:4},M=L-D.top-D.bottom,z=h-d.top-d.bottom,E=L+b+h+u+v+x,I=a?"oklch(0.58 0.15 290)":"oklch(0.55 0.25 290)",k=a?"oklch(0.62 0.15 165)":"oklch(0.7 0.25 165)",F=a?"rgba(255,255,255,0.08)":"rgba(0,0,0,0.08)",i=a?"#9ca3af":"#6b7280",H=a?"oklch(0.70 0.12 85)":"oklch(0.8 0.15 85)",C=s=>r.length===1?g+$/2:g+12+s/(r.length-1)*($-24),_=l||1,S=c||1,N=s=>{const y=s/_;return D.top+M-y*M},Z=s=>n?s.inputTokens:s.inputTokensNoCache??s.inputTokens,tt=r.map((s,y)=>`${C(y)},${N(Z(s))}`),et=r.map((s,y)=>`${C(y)},${N(s.outputTokens)}`),ot=`M ${tt.join(" L ")}`,st=`M ${et.join(" L ")}`,U=[0,.5,1].map(s=>({value:Math.round(_*s),y:N(_*s)})),V=[0,Math.ceil(S/2),S].map(s=>({value:s,y:d.top+z-s/S*z}));let m=`<svg width="${e}" height="${E}" xmlns="http://www.w3.org/2000/svg" style="font-family: ui-sans-serif, system-ui, sans-serif;">`;U.forEach(s=>{m+=`<text x="${g-4}" y="${s.y+3}" text-anchor="end" fill="${i}" font-size="9">${at(s.value)}</text>`}),U.forEach(s=>{m+=`<line x1="${g}" y1="${s.y}" x2="${e-p}" y2="${s.y}" stroke="${F}" stroke-dasharray="2,2"/>`}),m+=`<path d="${ot}" fill="none" stroke="${I}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>`,m+=`<path d="${st}" fill="none" stroke="${k}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>`,r.forEach((s,y)=>{const j=C(y),B=N(Z(s)),A=N(s.outputTokens);m+=`<circle cx="${j}" cy="${B}" r="4" fill="${I}"/>`,m+=`<circle cx="${j}" cy="${B}" r="2" fill="white"/>`,m+=`<circle cx="${j}" cy="${A}" r="4" fill="${k}"/>`,m+=`<circle cx="${j}" cy="${A}" r="2" fill="white"/>`});const P=L+b;if(V.forEach(s=>{m+=`<text x="${g-4}" y="${P+s.y+3}" text-anchor="end" fill="${i}" font-size="9">${s.value}</text>`}),V.forEach(s=>{m+=`<line x1="${g}" y1="${P+s.y}" x2="${e-p}" y2="${P+s.y}" stroke="${F}" stroke-dasharray="2,2"/>`}),r.forEach((s,y)=>{const j=C(y),B=20;let A=P+z+d.top;s.tools.forEach(R=>{const X=R.count/S*z;A-=X,m+=`<rect x="${j-B/2}" y="${A}" width="${B}" height="${X}" fill="${R.color}" rx="2" opacity="0.8"/>`})}),u>0){const s=P+h;m+=`<line x1="${g}" y1="${s+u/2}" x2="${e-p}" y2="${s+u/2}" stroke="${H}" stroke-opacity="0.3" stroke-dasharray="4,4"/>`,r.forEach((y,j)=>{y.hasCommit&&(m+=`<circle cx="${C(j)}" cy="${s+u/2}" r="4" fill="${H}"/>`)})}if(v>0){const s=P+h+u;m+=`<line x1="${g}" y1="${s+v/2}" x2="${e-p}" y2="${s+v/2}" stroke="#a855f7" stroke-opacity="0.3" stroke-dasharray="4,4"/>`,r.forEach((y,j)=>{y.hasThinking&&(m+=`<circle cx="${C(j)}" cy="${s+v/2}" r="4" fill="#a855f7"/>`)})}const G=P+h+u+v;return m+=`<line x1="${g}" y1="${G}" x2="${e-p}" y2="${G}" stroke="${F}"/>`,r.forEach((s,y)=>{m+=`<text x="${C(y)}" y="${G+14}" text-anchor="middle" fill="${i}" font-size="9">${s.promptIndex}</text>`}),m+="</svg>",m}function Q(t,o={}){const{width:e=400,isDark:n=!1}=o;if(!t||t.toolLegend.length===0)return`<svg width="${e}" height="60" xmlns="http://www.w3.org/2000/svg">
      <text x="${e/2}" y="30" text-anchor="middle" fill="${n?"#9ca3af":"#6b7280"}" font-size="12">No tool usage data</text>
    </svg>`;const a=t.totals.tools,r=t.toolLegend,w=r.reduce((d,M)=>d+M.count,0),f=a-w,c=12,T=24,l=8,g=l+c+l+T+l,p=n?"#9ca3af":"#6b7280",$=n?"rgba(255,255,255,0.4)":"rgba(0,0,0,0.4)",L=n?"#374151":"#e5e7eb";let h=`<svg width="${e}" height="${g}" xmlns="http://www.w3.org/2000/svg" style="font-family: ui-sans-serif, system-ui, sans-serif;">`;h+=`<rect x="${l}" y="${l}" width="${e-l*2}" height="${c}" fill="${L}" rx="6"/>`;let b=l;const u=e-l*2;if(r.forEach((d,M)=>{const E=(a>0?d.count/a:0)*u,I=M===0,k=M===r.length-1&&f<=0;h+=`<rect x="${b}" y="${l}" width="${E}" height="${c}" fill="${d.color}" ${I?'rx="6" ry="6"':""} ${k?'rx="6" ry="6"':""}/>`,b+=E}),f>0){const M=f/a*u;h+=`<rect x="${b}" y="${l}" width="${M}" height="${c}" fill="${$}" rx="6" ry="6"/>`}const v=l+c+l+4;let x=l;const D=6;if(r.slice(0,D).forEach(d=>{const M=a>0?d.count/a*100:0;h+=`<rect x="${x}" y="${v}" width="8" height="8" fill="${d.color}" rx="2"/>`,x+=12;const z=d.name.length>8?d.name.slice(0,8)+"...":d.name;h+=`<text x="${x}" y="${v+7}" fill="${n?"#e5e7eb":"#374151"}" font-size="10">${z}</text>`,x+=z.length*6+4,h+=`<text x="${x}" y="${v+7}" fill="${p}" font-size="10">${d.count}</text>`,x+=String(d.count).length*6+4,h+=`<text x="${x}" y="${v+7}" fill="${$}" font-size="10">(${M.toFixed(0)}%)</text>`,x+=36}),r.length>D||f>0){const d=r.length>D?r.length-D+(f>0?1:0):1;h+=`<text x="${x}" y="${v+7}" fill="${p}" font-size="10">+${d} more</text>`}return h+="</svg>",h}function q(t,o={}){const{width:e=600,isDark:n=!1}=o;if(!t||t.turns.length===0)return`<svg width="${e}" height="80" xmlns="http://www.w3.org/2000/svg">
      <text x="${e/2}" y="40" text-anchor="middle" fill="${n?"#9ca3af":"#6b7280"}" font-size="12">No timing data</text>
    </svg>`;const{turns:a,maxDuration:r}=t,w=a.filter(i=>i.durationSeconds!==null);if(w.length===0)return`<svg width="${e}" height="80" xmlns="http://www.w3.org/2000/svg">
      <text x="${e/2}" y="40" text-anchor="middle" fill="${n?"#9ca3af":"#6b7280"}" font-size="12">No timing data available</text>
    </svg>`;const f=48,c=20,T=e-f-c,l=60,g=28,p={top:4,bottom:4},$=l-p.top-p.bottom,L=l+g,h=n?"#e5e7eb":"#1f2937",b=n?"rgba(255,255,255,0.08)":"rgba(0,0,0,0.08)",u=n?"#9ca3af":"#6b7280",v=i=>a.length===1?f+T/2:f+12+i/(a.length-1)*(T-24),x=w.map(i=>i.durationSeconds).filter(i=>i>0).sort((i,H)=>i-H),D=Math.floor(x.length*.9),d=x[D]||r||1,z=Math.max(d,(r||1)*.3)||1,E=i=>i===null?0:Math.min(i/z,1)*$,I=[0,.5,1].map(i=>({value:Math.round(z*i),y:p.top+$-i*$}));let k=`<svg width="${e}" height="${L}" xmlns="http://www.w3.org/2000/svg" style="font-family: ui-sans-serif, system-ui, sans-serif;">`;I.forEach(i=>{k+=`<text x="${f-4}" y="${i.y+3}" text-anchor="end" fill="${u}" font-size="9">${J(i.value)}</text>`}),I.forEach(i=>{k+=`<line x1="${f}" y1="${i.y}" x2="${e-c}" y2="${i.y}" stroke="${b}" stroke-dasharray="2,2"/>`});const F=16;return a.forEach((i,H)=>{const C=v(H),_=E(i.durationSeconds),S=p.top+$-_;k+=`<rect x="${C-F/2}" y="${S}" width="${F}" height="${_}" fill="${h}" opacity="0.6" rx="2"/>`}),k+=`<line x1="${f}" y1="${l}" x2="${e-c}" y2="${l}" stroke="${b}"/>`,a.forEach((i,H)=>{const C=v(H);k+=`<text x="${C}" y="${l+12}" text-anchor="middle" fill="${u}" font-size="8">${rt(i.startTime)}</text>`,k+=`<text x="${C}" y="${l+22}" text-anchor="middle" fill="${u}" font-size="8" opacity="0.6">#${i.promptIndex}</text>`}),k+="</svg>",k}function mt(t){const{session:o,metrics:e,chart_data:n,intents:a,metadata:r}=t,w=e?.by_category?.tokens||{},f=e?.by_category?.tools||{},c=e?.by_category?.timing||{},T=e?.by_category?.interaction||{},l=Y(w,"estimated_cost",0),g=Y(w,"cache_savings",0),p=n.prompt_turns,$=p?.totals?.inputTokens||0,L=p?.totals?.outputTokens||0,h=p?.totals?.cacheReadTokens||0,b=f?.tool_distribution?.value,u=b?Object.values(b).reduce((_,S)=>_+S,0):p?.totals?.tools||0,v=Y(c,"session_duration",0),x=Y(T,"prompt_count",0)||p?.turns?.length||0,D=x>0?u/x:0,d=o.project_path&&o.project_path.split("/").pop()||"Session",M=o.started_at?new Date(o.started_at.endsWith("Z")?o.started_at:o.started_at+"Z").toLocaleDateString(void 0,{month:"short",day:"numeric",year:"numeric"}):"Unknown date",z=n.prompt_turns?.turns?.length||0,E=Math.max(500,z*30+80),I=n.prompt_turns?K(n.prompt_turns,{width:E,isDark:!1}):"",k=n.prompt_turns?K(n.prompt_turns,{width:E,isDark:!0}):"",F=n.prompt_turns?Q(n.prompt_turns,{width:500,isDark:!1}):"",i=n.prompt_turns?Q(n.prompt_turns,{width:500,isDark:!0}):"",H=n.prompt_turns?q(n.prompt_turns,{width:E,isDark:!1}):"",C=n.prompt_turns?q(n.prompt_turns,{width:E,isDark:!0}):"";return`<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${W(d)} - Session Dashboard</title>
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
          <h1 class="title">${W(d)}</h1>
          <p class="subtitle">${W(M)} · ${x} prompts · ${r.export_level} export</p>
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
          ${a.map(_=>`<span class="intent-tag">${W(_)}</span>`).join("")}
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
          <span class="metric-value">${O($+L)}</span>
          <span class="metric-label">Total Tokens</span>
          <span class="metric-detail">In: ${O($)} · Out: ${O(L)}</span>
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
          <span class="metric-detail">${D.toFixed(1)} avg per prompt</span>
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
          <span class="metric-value">${J(v)}</span>
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
      ${I?`
      <div class="chart-card">
        <h2 class="chart-title">Token Usage & Tools per Prompt</h2>
        <div class="chart-container">
          <div class="chart-light">${I}</div>
          <div class="chart-dark">${k}</div>
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

      ${F?`
      <div class="chart-card">
        <h2 class="chart-title">Tool Distribution</h2>
        <div class="chart-container">
          <div class="chart-light">${F}</div>
          <div class="chart-dark">${i}</div>
        </div>
      </div>
      `:""}

      ${H?`
      <div class="chart-card">
        <h2 class="chart-title">Turn Duration</h2>
        <div class="chart-container">
          <div class="chart-light">${H}</div>
          <div class="chart-dark">${C}</div>
        </div>
      </div>
      `:""}
    </section>

    ${b&&Object.keys(b).length>0?`
    <!-- Tool Breakdown -->
    <section class="tools-section">
      <h2 class="section-title">Tool Breakdown</h2>
      <div class="tools-grid">
        ${Object.entries(b).sort(([,_],[,S])=>S-_).slice(0,12).map(([_,S])=>`
            <div class="tool-item">
              <span class="tool-name">${W(_)}</span>
              <span class="tool-count">${S}</span>
              <span class="tool-percent">${(S/u*100).toFixed(1)}%</span>
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
      overflow-y: hidden;
      -webkit-overflow-scrolling: touch;
      scrollbar-width: thin;
      scrollbar-color: var(--border) transparent;
    }

    .chart-container::-webkit-scrollbar {
      height: 6px;
    }

    .chart-container::-webkit-scrollbar-track {
      background: transparent;
    }

    .chart-container::-webkit-scrollbar-thumb {
      background: var(--border);
      border-radius: 3px;
    }

    .chart-container::-webkit-scrollbar-thumb:hover {
      background: var(--fg-muted);
    }

    .chart-container svg {
      display: block;
      height: auto;
    }

    .chart-light, .chart-dark {
      width: fit-content;
      min-width: 100%;
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
  `}function Y(t,o,e){const n=t[o];if(!n||n.value===null||n.value===void 0)return e;const a=Number(n.value);return isNaN(a)?e:a}function W(t){return t.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#039;")}function lt(t,o){if(!t||t.length===0)return"";const e=t.filter(c=>c.event_type==="user_prompt"||c.event_type==="assistant_stop"||c.event_type==="assistant_response"||c.event_type==="user_message"||c.event_type==="assistant_message");if(e.length===0)return"";const n=o==="summary"?10:o==="full"?100:e.length,a=e.slice(0,n),r=e.length>n;let w=0;const f=a.map(c=>{const T=c.event_type==="user_prompt"||c.event_type==="user_message",l=dt(c),g=pt(l,o);if(!g.trim())return"";if(T&&c.data){const $=c.data;typeof $.promptIndex=="number"?w=$.promptIndex:w++}const p=T?`Prompt #${w}`:`Response #${w}`;return`
      <div class="message ${T?"message-user":"message-assistant"}">
        <div class="message-header">
          <span class="message-index">${p}</span>
          <span class="message-role">${T?"User":"Claude"}</span>
          ${c.timestamp?`<span class="message-time">${gt(c.timestamp)}</span>`:""}
        </div>
        <div class="message-content">${W(g)}</div>
      </div>
    `}).join("");return`
    <!-- Conversation Timeline -->
    <section class="conversation-section">
      <h2 class="section-title">Conversation (${e.length} messages)</h2>
      <div class="conversation-timeline">
        ${f}
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
