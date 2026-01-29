"""
HELIX SDK Documentation Page
Matches the main HELIX UI exactly - same fonts, colors, glass cards, AIBlob, and animations.

Design System Analysis:
- Fonts: Silkscreen (logo), Bricolage Grotesque (headings), Poppins (body), JetBrains Mono (code)
- Colors: Pure black (#000) / white (#fff) with neutral grays (neutral-100 to neutral-900)
- Glass: backdrop-blur-lg, rgba backgrounds, subtle borders
- Animations: spring stiffness 100, y:-2 hover, scale 1.02/0.98 tap
- AIBlob: Golden ratio sphere distribution, 300-400 particles
- Buttons: rounded-2xl, solid black/white with inverse text
"""

SDK_DOCS_HTML = '''
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HELIX SDK Documentation</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Silkscreen:wght@400;700&family=Bricolage+Grotesque:wght@400;600;700&family=Poppins:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        /* === EXACT COLORS FROM MAIN APP === */
        :root {
            --bg: #000000;
            --fg: #ededed;
            --neutral-100: #f5f5f5;
            --neutral-200: #e5e5e5;
            --neutral-300: #d4d4d4;
            --neutral-400: #a3a3a3;
            --neutral-500: #737373;
            --neutral-600: #525252;
            --neutral-700: #404040;
            --neutral-800: #262626;
            --neutral-900: #171717;
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        html { scroll-behavior: smooth; }
        
        body {
            font-family: 'Poppins', system-ui, sans-serif;
            background-color: var(--bg);
            color: var(--fg);
            line-height: 1.7;
            transition: background-color 0.3s ease, color 0.3s ease;
        }
        
        /* === GLASS EFFECT FROM globals.css === */
        .glass-dark {
            background: rgba(0, 0, 0, 0.4);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        /* === GLASS CARD FROM GlassCard.tsx === */
        .glass-card {
            position: relative;
            overflow: hidden;
            border-radius: 1.5rem;
            padding: 2rem;
            background: rgba(255, 255, 255, 0.04);
            backdrop-filter: blur(24px) saturate(180%);
            -webkit-backdrop-filter: blur(24px) saturate(180%);
            border: 1px solid rgba(255, 255, 255, 0.12);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), 
                        inset 0 1px 0 rgba(255, 255, 255, 0.08), 
                        inset 0 -1px 0 rgba(255, 255, 255, 0.02);
            transition: transform 0.25s ease, box-shadow 0.25s ease;
        }
        
        .glass-card:hover {
            transform: translateY(-4px);
        }
        
        /* Top shine line - liquid glass highlight */
        .glass-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.25), transparent);
        }
        
        /* === GRID OVERLAY FROM HeroSection.tsx === */
        .grid-overlay {
            position: fixed;
            inset: 0;
            opacity: 0.1;
            background-image: 
                linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px);
            background-size: 50px 50px;
            pointer-events: none;
            z-index: 0;
        }
        
        .container { max-width: 1200px; margin: 0 auto; padding: 0 1rem; position: relative; z-index: 1; }
        
        /* === NAVBAR FROM Navbar.tsx === */
        nav {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 50;
            padding: 1rem 0;
        }
        
        .nav-inner {
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-radius: 1rem;
            padding: 0.75rem 1.5rem;
            background: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(20px);
            border: 1px solid var(--neutral-800);
        }
        
        .logo {
            font-family: 'Silkscreen', cursive;
            font-size: 1.5rem;
            font-weight: bold;
            color: white;
            text-decoration: none;
        }
        
        .nav-links {
            display: flex;
            align-items: center;
            gap: 2rem;
        }
        
        .nav-links a {
            color: var(--neutral-400);
            text-decoration: none;
            font-size: 0.875rem;
            font-weight: 500;
            transition: color 0.2s, transform 0.2s;
        }
        
        .nav-links a:hover {
            color: white;
            transform: translateY(-2px);
        }
        
        /* === HERO WITH AI BLOB === */
        .hero {
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            overflow: hidden;
            padding-top: 5rem;
        }
        
        .hero-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 3rem;
            align-items: center;
            width: 100%;
        }
        
        @media (max-width: 900px) {
            .hero-grid { grid-template-columns: 1fr; text-align: center; }
            .hero-blob { order: -1; }
        }
        
        .hero-content { max-width: 600px; }
        
        .hero-badge {
            display: inline-block;
            padding: 0.5rem 1rem;
            border-radius: 9999px;
            background: var(--neutral-900);
            border: 1px solid var(--neutral-800);
            font-size: 0.875rem;
            color: var(--neutral-400);
            margin-bottom: 1.5rem;
        }
        
        .hero h1 {
            font-family: 'Bricolage Grotesque', sans-serif;
            font-size: 3.5rem;
            font-weight: 700;
            line-height: 1.1;
            margin-bottom: 1.5rem;
        }
        
        .hero h1 .muted { color: var(--neutral-400); }
        
        .hero p {
            font-size: 1.125rem;
            color: var(--neutral-400);
            margin-bottom: 2rem;
        }
        
        .hero p .helix-text {
            font-family: 'Silkscreen', cursive;
        }
        
        .hero p .highlight {
            color: white;
            font-weight: 600;
        }
        
        /* === BUTTONS FROM HeroSection.tsx === */
        .btn-group {
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
        }
        
        @media (max-width: 900px) {
            .btn-group { justify-content: center; }
        }
        
        .btn {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 1rem 2rem;
            border-radius: 1rem;
            font-size: 1rem;
            font-weight: 600;
            text-decoration: none;
            border: none;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .btn:hover {
            transform: scale(1.02);
        }
        
        .btn:active {
            transform: scale(0.98);
        }
        
        .btn-primary {
            background: white;
            color: black;
        }
        
        .btn-secondary {
            background: transparent;
            color: white;
            border: 1px solid var(--neutral-700);
        }
        
        /* === STATS FROM HeroSection.tsx === */
        .stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 2rem;
            margin-top: 3rem;
        }
        
        .stat-value {
            font-size: 1.75rem;
            font-weight: 700;
            color: white;
        }
        
        .stat-label {
            font-size: 0.875rem;
            color: var(--neutral-500);
        }
        
        /* === AI BLOB CANVAS === */
        .hero-blob {
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        #ai-blob {
            width: 400px;
            height: 400px;
        }
        
        /* === MAIN CONTENT === */
        main {
            padding: 5rem 0;
        }
        
        section {
            margin-bottom: 5rem;
            scroll-margin-top: 6rem;
        }
        
        h2 {
            font-family: 'Bricolage Grotesque', sans-serif;
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 1.5rem;
            color: white;
        }
        
        h3 {
            font-size: 1.25rem;
            font-weight: 600;
            margin: 2rem 0 1rem;
            color: white;
        }
        
        p, li {
            color: var(--neutral-400);
            font-size: 1rem;
            margin-bottom: 1rem;
        }
        
        /* === FEATURE GRID === */
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
        }
        
        .feature-card {
            padding: 1.5rem;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 1rem;
            transition: transform 0.25s, border-color 0.25s;
        }
        
        .feature-card:hover {
            transform: translateY(-4px);
            border-color: rgba(255, 255, 255, 0.2);
        }
        
        .feature-card .icon {
            font-size: 2rem;
            margin-bottom: 1rem;
        }
        
        .feature-card h4 {
            font-size: 1.125rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: white;
        }
        
        .feature-card p {
            font-size: 0.875rem;
            margin: 0;
        }
        
        /* === CODE BLOCKS === */
        pre {
            background: #0d1117;
            border: 1px solid var(--neutral-800);
            border-radius: 1rem;
            padding: 1.5rem;
            overflow-x: auto;
            margin: 1.5rem 0;
        }
        
        code {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.875rem;
            line-height: 1.8;
        }
        
        .inline-code {
            font-family: 'JetBrains Mono', monospace;
            background: var(--neutral-900);
            padding: 0.125rem 0.5rem;
            border-radius: 0.375rem;
            font-size: 0.8125rem;
            color: white;
        }
        
        /* Syntax colors */
        .kw { color: #ff79c6; }
        .str { color: #f1fa8c; }
        .cmt { color: #6272a4; }
        .fn { color: #50fa7b; }
        .num { color: #bd93f9; }
        
        /* === TABLES === */
        .table-wrap {
            overflow-x: auto;
            margin: 1.5rem 0;
            border-radius: 1rem;
            border: 1px solid var(--neutral-800);
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th, td {
            text-align: left;
            padding: 1rem 1.25rem;
            border-bottom: 1px solid var(--neutral-800);
        }
        
        th {
            background: rgba(255, 255, 255, 0.03);
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--neutral-500);
        }
        
        td {
            font-size: 0.875rem;
            color: var(--neutral-400);
        }
        
        tr:last-child td { border-bottom: none; }
        
        /* === INSTALL BOX === */
        .install-box {
            display: inline-flex;
            align-items: center;
            gap: 1rem;
            background: var(--neutral-900);
            border: 1px solid var(--neutral-800);
            border-radius: 1rem;
            padding: 1rem 1.5rem;
            margin-top: 2rem;
        }
        
        .install-box code {
            font-family: 'JetBrains Mono', monospace;
            color: white;
        }
        
        .install-box button {
            background: var(--neutral-800);
            border: none;
            padding: 0.5rem;
            border-radius: 0.5rem;
            cursor: pointer;
            color: var(--neutral-400);
            transition: color 0.2s, background 0.2s;
        }
        
        .install-box button:hover {
            color: white;
            background: var(--neutral-700);
        }
        
        /* === FOOTER FROM Footer.tsx === */
        footer {
            padding: 4rem 0;
            border-top: 1px solid var(--neutral-800);
        }
        
        .footer-grid {
            display: grid;
            grid-template-columns: 2fr 1fr 1fr 1fr;
            gap: 3rem;
        }
        
        @media (max-width: 768px) {
            .footer-grid { grid-template-columns: 1fr; }
        }
        
        .footer-brand .logo {
            font-family: 'Silkscreen', cursive;
            font-size: 1.5rem;
            font-weight: bold;
            color: white;
        }
        
        .footer-brand p {
            font-size: 0.875rem;
            margin-top: 1rem;
            max-width: 300px;
        }
        
        .footer-social {
            display: flex;
            gap: 1rem;
            margin-top: 1.5rem;
        }
        
        .footer-social a {
            width: 2.5rem;
            height: 2.5rem;
            border-radius: 9999px;
            background: var(--neutral-800);
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--neutral-500);
            transition: color 0.2s, transform 0.2s;
        }
        
        .footer-social a:hover {
            color: white;
            transform: scale(1.1);
        }
        
        .footer-links h4 {
            color: white;
            font-weight: 600;
            margin-bottom: 1rem;
        }
        
        .footer-links ul {
            list-style: none;
        }
        
        .footer-links li {
            margin-bottom: 0.75rem;
        }
        
        .footer-links a {
            color: var(--neutral-500);
            text-decoration: none;
            font-size: 0.875rem;
            transition: color 0.2s;
        }
        
        .footer-links a:hover {
            color: white;
        }
        
        .footer-bottom {
            margin-top: 3rem;
            padding-top: 2rem;
            border-top: 1px solid var(--neutral-800);
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 1rem;
        }
        
        .footer-bottom p, .footer-bottom a {
            font-size: 0.875rem;
            color: var(--neutral-500);
        }
        
        .footer-bottom a:hover {
            color: white;
        }
        
        /* === SCROLLBAR FROM globals.css === */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track { background: transparent; }
        
        ::-webkit-scrollbar-thumb {
            background: rgba(128, 128, 128, 0.3);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(128, 128, 128, 0.5);
        }
        
        ::selection {
            background: rgba(255, 255, 255, 0.2);
        }
    </style>
</head>
<body>
    <div class="grid-overlay"></div>
    
    <nav>
        <div class="container">
            <div class="nav-inner">
                <a href="/" class="logo">HELIX</a>
                <div class="nav-links">
                    <a href="#installation">Installation</a>
                    <a href="#quickstart">Quick Start</a>
                    <a href="#api">API</a>
                    <a href="https://github.com/DB0SZ1/PROJECT-HELIX" target="_blank">GitHub →</a>
                </div>
            </div>
        </div>
    </nav>
    
    <section class="hero">
        <div class="container">
            <div class="hero-grid">
                <div class="hero-content">
                    <div class="hero-badge">🚀 SDK v1.0.0 — Ready for Production</div>
                    <h1>
                        <span>Compress</span> <span class="muted">Smarter</span><br>
                        <span>Train</span> <span class="muted">Faster</span>
                    </h1>
                    <p>
                        <span class="helix-text">HELIX</span> SDK enables <span class="highlight">10x dataset compression</span> 
                        for AI training. Store blueprints, materialize at any resolution.
                    </p>
                    <div class="btn-group">
                        <a href="#quickstart" class="btn btn-primary">Get Started</a>
                        <a href="#api" class="btn btn-secondary">API Reference</a>
                    </div>
                    <div class="install-box">
                        <code>pip install helix-sdk</code>
                        <button onclick="navigator.clipboard.writeText('pip install helix-sdk')" title="Copy">📋</button>
                    </div>
                    <div class="stats">
                        <div>
                            <div class="stat-value">10x</div>
                            <div class="stat-label">Compression</div>
                        </div>
                        <div>
                            <div class="stat-value">< 3s</div>
                            <div class="stat-label">Materialize</div>
                        </div>
                        <div>
                            <div class="stat-value">∞</div>
                            <div class="stat-label">Resolutions</div>
                        </div>
                    </div>
                </div>
                <div class="hero-blob">
                    <canvas id="ai-blob" width="400" height="400"></canvas>
                </div>
            </div>
        </div>
    </section>
    
    <main>
        <div class="container">
            <section id="overview">
                <h2>Why HELIX SDK?</h2>
                <div class="feature-grid">
                    <div class="feature-card">
                        <div class="icon">📦</div>
                        <h4>10x Compression</h4>
                        <p>Reduce 100GB datasets to 10GB. Store blueprints, not pixels.</p>
                    </div>
                    <div class="feature-card">
                        <div class="icon">🚀</div>
                        <h4>PyTorch Ready</h4>
                        <p>Drop-in DataLoader replacement. Works with existing pipelines.</p>
                    </div>
                    <div class="feature-card">
                        <div class="icon">🔄</div>
                        <h4>Dynamic Resolution</h4>
                        <p>Same HLX file materializes from 256p to 8K on demand.</p>
                    </div>
                    <div class="feature-card">
                        <div class="icon">♾️</div>
                        <h4>Free Augmentation</h4>
                        <p>Generate infinite variants per image. Multiplies your dataset.</p>
                    </div>
                </div>
            </section>
            
            <section id="installation">
                <h2>Installation</h2>
                <h3>From PyPI</h3>
                <pre><code><span class="cmt"># Basic install</span>
pip install helix-sdk

<span class="cmt"># With PyTorch support</span>
pip install helix-sdk[ml]

<span class="cmt"># Full install (all extras)</span>
pip install helix-sdk[all]</code></pre>
                
                <h3>From Source</h3>
                <pre><code>git clone https://github.com/DB0SZ1/PROJECT-HELIX.git
cd PROJECT-HELIX
pip install -e .</code></pre>

                <h3>Environment</h3>
                <pre><code><span class="cmt"># Set your Gemini API key</span>
export GEMINI_API_KEY=<span class="str">"your-key"</span></code></pre>
            </section>
            
            <section id="quickstart">
                <h2>Quick Start</h2>
                
                <h3>Basic Usage</h3>
                <pre><code><span class="kw">from</span> helix_sdk <span class="kw">import</span> HelixSDK

sdk = HelixSDK()

<span class="cmt"># Compress image to HLX</span>
result = sdk.compress(<span class="str">"photo.jpg"</span>, <span class="str">"photo.hlx"</span>)
<span class="kw">print</span>(<span class="str">f"Compression: {result.compression_ratio:.1f}x"</span>)

<span class="cmt"># Materialize at 4K</span>
result = sdk.materialize(<span class="str">"photo.hlx"</span>, <span class="str">"photo_4k.png"</span>, resolution=<span class="str">"4K"</span>)</code></pre>

                <h3>ML Training</h3>
                <pre><code><span class="kw">from</span> helix_sdk <span class="kw">import</span> HelixDataset, HelixLoader

dataset = HelixDataset(<span class="str">"/data/hlx/"</span>, target_resolution=<span class="str">"512p"</span>)
loader = HelixLoader(dataset, batch_size=<span class="num">64</span>, num_workers=<span class="num">4</span>)

<span class="kw">for</span> batch <span class="kw">in</span> loader:
    images = torch.from_numpy(batch)
    model.train_step(images)</code></pre>

                <h3>CLI</h3>
                <pre><code>helix compress photo.jpg              <span class="cmt"># → photo.hlx</span>
helix materialize photo.hlx -r 4K     <span class="cmt"># → photo.4K.png</span>
helix batch /images/ /hlx/ -w 8       <span class="cmt"># Parallel compression</span>
helix info photo.hlx                  <span class="cmt"># Show metadata</span></code></pre>
            </section>
            
            <section id="api">
                <h2>API Reference</h2>
                
                <h3>HelixSDK</h3>
                <div class="table-wrap">
                    <table>
                        <thead>
                            <tr><th>Method</th><th>Description</th></tr>
                        </thead>
                        <tbody>
                            <tr><td><span class="inline-code">compress(input, output)</span></td><td>Compress image to HLX</td></tr>
                            <tr><td><span class="inline-code">materialize(input, output, resolution)</span></td><td>Reconstruct from HLX</td></tr>
                            <tr><td><span class="inline-code">compress_directory(in_dir, out_dir)</span></td><td>Batch compression</td></tr>
                            <tr><td><span class="inline-code">get_info(hlx_path)</span></td><td>Get HLX metadata</td></tr>
                        </tbody>
                    </table>
                </div>
                
                <h3>HelixDataset</h3>
                <pre><code>dataset = HelixDataset(
    path=<span class="str">"/data/hlx/"</span>,
    target_resolution=<span class="str">"512p"</span>,
    enable_variants=<span class="kw">True</span>,
    cache_materializations=<span class="kw">True</span>
)</code></pre>

                <h3>HelixLoader</h3>
                <pre><code>loader = HelixLoader(
    dataset,
    batch_size=<span class="num">64</span>,
    shuffle=<span class="kw">True</span>,
    num_workers=<span class="num">4</span>,
    variants_per_image=<span class="num">3</span>  <span class="cmt"># 3x dataset!</span>
)</code></pre>
                
                <h3>REST Endpoints</h3>
                <div class="table-wrap">
                    <table>
                        <thead>
                            <tr><th>Endpoint</th><th>Method</th><th>Description</th></tr>
                        </thead>
                        <tbody>
                            <tr><td><span class="inline-code">/api/encode</span></td><td>POST</td><td>Encode to HLX v1</td></tr>
                            <tr><td><span class="inline-code">/api/encode/v2</span></td><td>POST</td><td>Encode to HLX v2</td></tr>
                            <tr><td><span class="inline-code">/api/materialize</span></td><td>POST</td><td>Reconstruct image</td></tr>
                            <tr><td><span class="inline-code">/api/hlx/preview</span></td><td>POST</td><td>Extract JPEG preview</td></tr>
                        </tbody>
                    </table>
                </div>
            </section>
        </div>
    </main>
    
    <footer>
        <div class="container">
            <div class="footer-grid">
                <div class="footer-brand">
                    <div class="logo">HELIX</div>
                    <p>Identity-preserving AI compression. Store the essence, regenerate the rest.</p>
                    <div class="footer-social">
                        <a href="https://github.com/DB0SZ1/PROJECT-HELIX" title="GitHub">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
                        </a>
                    </div>
                </div>
                <div class="footer-links">
                    <h4>Product</h4>
                    <ul>
                        <li><a href="#installation">Installation</a></li>
                        <li><a href="#api">API Reference</a></li>
                        <li><a href="/">Demo</a></li>
                    </ul>
                </div>
                <div class="footer-links">
                    <h4>Resources</h4>
                    <ul>
                        <li><a href="https://github.com/DB0SZ1/PROJECT-HELIX">GitHub</a></li>
                        <li><a href="https://github.com/DB0SZ1/PROJECT-HELIX/issues">Issues</a></li>
                    </ul>
                </div>
                <div class="footer-links">
                    <h4>Company</h4>
                    <ul>
                        <li><a href="/">About</a></li>
                        <li><a href="/">Contact</a></li>
                    </ul>
                </div>
            </div>
            <div class="footer-bottom">
                <p>© 2026 Project HELIX. Built for Gemini API Developer Competition.</p>
                <div>
                    <a href="#">Privacy</a> · <a href="#">Terms</a>
                </div>
            </div>
        </div>
    </footer>
    
    <script>
        // === AI BLOB FROM AIBlob.tsx - EXACT IMPLEMENTATION ===
        const canvas = document.getElementById('ai-blob');
        const ctx = canvas.getContext('2d');
        const size = 400;
        const centerX = size / 2;
        const centerY = size / 2;
        const radius = size * 0.36;
        const particleCount = 300;
        
        // Golden ratio distribution for even spacing
        const goldenRatio = (1 + Math.sqrt(5)) / 2;
        const particles = [];
        
        for (let i = 0; i < particleCount; i++) {
            const theta = 2 * Math.PI * i / goldenRatio;
            const phi = Math.acos(1 - 2 * (i + 0.5) / particleCount);
            particles.push({
                x: radius * Math.sin(phi) * Math.cos(theta),
                y: radius * Math.sin(phi) * Math.sin(theta),
                z: radius * Math.cos(phi),
                baseSize: 1.8 + Math.random() * 1.2
            });
        }
        
        let rotation = 0;
        
        function animate() {
            ctx.clearRect(0, 0, size, size);
            rotation += 0.003;
            
            // Sort by Z for depth
            const sorted = [...particles].sort((a, b) => {
                const az = a.x * Math.sin(rotation) + a.z * Math.cos(rotation);
                const bz = b.x * Math.sin(rotation) + b.z * Math.cos(rotation);
                return az - bz;
            });
            
            sorted.forEach(p => {
                const cosR = Math.cos(rotation);
                const sinR = Math.sin(rotation);
                
                // Rotate around Y
                const rotatedX = p.x * cosR - p.z * sinR;
                const rotatedZ = p.x * sinR + p.z * cosR;
                
                // Slight X rotation for 3D
                const cosRx = Math.cos(rotation * 0.25);
                const sinRx = Math.sin(rotation * 0.25);
                const rotatedY = p.y * cosRx - rotatedZ * sinRx;
                const finalZ = p.y * sinRx + rotatedZ * cosRx;
                
                // Perspective projection
                const perspective = 500;
                const scale = perspective / (perspective + finalZ);
                const projectedX = centerX + rotatedX * scale;
                const projectedY = centerY + rotatedY * scale;
                
                // Depth-based opacity
                const normalizedZ = (finalZ + radius) / (radius * 2);
                const opacity = 0.25 + normalizedZ * 0.7;
                
                // Draw white particle (dark mode)
                ctx.fillStyle = `rgba(255, 255, 255, ${opacity})`;
                ctx.beginPath();
                ctx.arc(projectedX, projectedY, p.baseSize * scale, 0, Math.PI * 2);
                ctx.fill();
            });
            
            requestAnimationFrame(animate);
        }
        
        animate();
    </script>
</body>
</html>
'''
