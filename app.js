document.addEventListener('DOMContentLoaded', () => {
  // 1. Toast Notification Helper
  const toast = document.getElementById('toast');
  const toastMsg = document.getElementById('toast-msg');

  function showToast(message) {
    if (!toast) return;
    toastMsg.textContent = message;
    toast.classList.add('show');
    setTimeout(() => {
      toast.classList.remove('show');
    }, 2500);
  }

  // 2. Global Copy Button Listener
  document.querySelectorAll('[data-copy]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const textToCopy = btn.getAttribute('data-copy');
      if (textToCopy) {
        navigator.clipboard.writeText(textToCopy).then(() => {
          showToast(`Copied: ${textToCopy}`);
        });
      }
    });
  });

  // 3. Tab Switching Logic
  const tabButtons = document.querySelectorAll('.tab-btn');
  const tabPanes = document.querySelectorAll('.tab-pane');

  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      tabButtons.forEach(b => b.classList.remove('active'));
      tabPanes.forEach(p => p.classList.remove('active'));

      btn.classList.add('active');
      const targetTab = btn.getAttribute('data-tab');
      const pane = document.getElementById(targetTab);
      if (pane) pane.classList.add('active');
    });
  });

  // 4. Name2Email Interactive Permutator (Upgraded UI & Intelligence)
  const inputFirst = document.getElementById('perm-first');
  const inputLast = document.getElementById('perm-last');
  const inputDomain = document.getElementById('perm-domain');
  const chipsContainer = document.getElementById('chips-container');
  const tokensBar = document.getElementById('perm-tokens-bar');
  const permSearch = document.getElementById('perm-search');
  const copyAllBtn = document.getElementById('btn-copy-all-perms');
  const exportCsvBtn = document.getElementById('btn-export-csv');
  const exportJsonBtn = document.getElementById('btn-export-json');
  const filterButtons = document.querySelectorAll('.perm-filter-btn');

  let activeFilter = 'all';
  let searchQuery = '';
  let allPermutationsData = [];

  function buildPatternDefinitions(first, last, domain) {
    const f = first[0];
    const l = last[0];

    return [
      // Top / High Probability Corporate Patterns
      { pattern: `${first}.${last}`, formula: '{first}.{last}@{domain}', cat: 'top', prob: 98, badge: 'prob-high', desc: 'Standard Corporate' },
      { pattern: `${f}.${last}`, formula: '{f}.{last}@{domain}', cat: 'top', prob: 94, badge: 'prob-high', desc: 'First Initial + Last' },
      { pattern: `${first}${last}`, formula: '{first}{last}@{domain}', cat: 'top', prob: 91, badge: 'prob-high', desc: 'First + Last Name' },
      { pattern: `${first}`, formula: '{first}@{domain}', cat: 'top', prob: 88, badge: 'prob-high', desc: 'First Name Only' },
      { pattern: `${f}${last}`, formula: '{f}{last}@{domain}', cat: 'top', prob: 85, badge: 'prob-high', desc: 'Initial + Lastname' },

      // Dot, Dash & Hyphen Variants
      { pattern: `${first}_${last}`, formula: '{first}_{last}@{domain}', cat: 'dotdash', prob: 82, badge: 'prob-mid', desc: 'Underscore Delimiter' },
      { pattern: `${first}-${last}`, formula: '{first}-{last}@{domain}', cat: 'dotdash', prob: 79, badge: 'prob-mid', desc: 'Hyphen Delimiter' },
      { pattern: `${f}_${last}`, formula: '{f}_{last}@{domain}', cat: 'dotdash', prob: 76, badge: 'prob-mid', desc: 'Initial + Underscore' },
      { pattern: `${f}-${last}`, formula: '{f}-{last}@{domain}', cat: 'dotdash', prob: 74, badge: 'prob-mid', desc: 'Initial + Hyphen' },
      { pattern: `${first}.${l}`, formula: '{first}.{l}@{domain}', cat: 'dotdash', prob: 72, badge: 'prob-mid', desc: 'First + Last Initial' },
      { pattern: `${first}_${l}`, formula: '{first}_{l}@{domain}', cat: 'dotdash', prob: 68, badge: 'prob-mid', desc: 'First + Underscore Initial' },
      { pattern: `${first}-${l}`, formula: '{first}-{l}@{domain}', cat: 'dotdash', prob: 66, badge: 'prob-mid', desc: 'First + Hyphen Initial' },

      // Initials & Surnames
      { pattern: `${last}`, formula: '{last}@{domain}', cat: 'initials', prob: 65, badge: 'prob-mid', desc: 'Surname Only' },
      { pattern: `${last}.${first}`, formula: '{last}.{first}@{domain}', cat: 'initials', prob: 63, badge: 'prob-mid', desc: 'Surname + First' },
      { pattern: `${last}${first}`, formula: '{last}{first}@{domain}', cat: 'initials', prob: 60, badge: 'prob-mid', desc: 'Last + First' },
      { pattern: `${last}.${f}`, formula: '{last}.{f}@{domain}', cat: 'initials', prob: 58, badge: 'prob-mid', desc: 'Surname + First Initial' },
      { pattern: `${last}${f}`, formula: '{last}{f}@{domain}', cat: 'initials', prob: 56, badge: 'prob-mid', desc: 'Surname + Initial' },
      { pattern: `${last}_${first}`, formula: '{last}_{first}@{domain}', cat: 'initials', prob: 54, badge: 'prob-mid', desc: 'Surname + Underscore' },
      { pattern: `${last}_${f}`, formula: '{last}_{f}@{domain}', cat: 'initials', prob: 52, badge: 'prob-mid', desc: 'Last + Underscore Init' },
      { pattern: `${last}-${first}`, formula: '{last}-{first}@{domain}', cat: 'initials', prob: 50, badge: 'prob-low', desc: 'Last + Hyphen First' },
      { pattern: `${last}-${f}`, formula: '{last}-{f}@{domain}', cat: 'initials', prob: 48, badge: 'prob-low', desc: 'Last + Hyphen Init' },
      { pattern: `${l}.${first}`, formula: '{l}.{first}@{domain}', cat: 'initials', prob: 46, badge: 'prob-low', desc: 'Last Initial + First' },
      { pattern: `${l}${first}`, formula: '{l}{first}@{domain}', cat: 'initials', prob: 44, badge: 'prob-low', desc: 'Last Init + First' },
      { pattern: `${l}_${first}`, formula: '{l}_{first}@{domain}', cat: 'initials', prob: 42, badge: 'prob-low', desc: 'Last Init + Under' },
      { pattern: `${l}-${first}`, formula: '{l}-${first}@{domain}', cat: 'initials', prob: 40, badge: 'prob-low', desc: 'Last Init + Hyphen' },
      { pattern: `${f}.${l}`, formula: '{f}.{l}@{domain}', cat: 'initials', prob: 38, badge: 'prob-low', desc: 'Dual Initials Dot' },
      { pattern: `${f}${l}`, formula: '{f}{l}@{domain}', cat: 'initials', prob: 35, badge: 'prob-low', desc: 'Dual Initials Direct' },
      { pattern: `${first}${l}`, formula: '{first}{l}@{domain}', cat: 'initials', prob: 32, badge: 'prob-low', desc: 'First + Last Initial Direct' },

      // Tech & Numbered Suffixes
      { pattern: `${first}.${last}1`, formula: '{first}.{last}1@{domain}', cat: 'numeric', prob: 30, badge: 'prob-low', desc: 'Primary Suffix 1' },
      { pattern: `${first}.${last}2`, formula: '{first}.{last}2@{domain}', cat: 'numeric', prob: 25, badge: 'prob-low', desc: 'Secondary Suffix 2' },
      { pattern: `${first}${last}1`, formula: '{first}{last}1@{domain}', cat: 'numeric', prob: 22, badge: 'prob-low', desc: 'Concatenated 1' },
      { pattern: `${first}${last}123`, formula: '{first}{last}123@{domain}', cat: 'numeric', prob: 18, badge: 'prob-low', desc: 'Sequential 123' },
      { pattern: `${first}${last}777`, formula: '{first}{last}777@{domain}', cat: 'numeric', prob: 15, badge: 'prob-low', desc: 'Numeric Identifier' },
      { pattern: `${f}${last}1`, formula: '{f}{last}1@{domain}', cat: 'numeric', prob: 12, badge: 'prob-low', desc: 'Initial + Suffix 1' }
    ].map(item => ({
      ...item,
      email: `${item.pattern}@${domain}`
    }));
  }

  function formatHighlightedEmail(pattern, domain) {
    // Syntax highlight delimiters ., _, - and numbers in the username part
    const formattedUser = pattern.replace(/([._-])/g, '<span class="email-sep">$1</span>');
    return `<div class="pattern-email-box"><span class="email-user-part">${formattedUser}</span><span class="email-at">@</span><span class="email-domain-part">${domain}</span></div>`;
  }

  function formatHighlightedFormula(formula) {
    const rawPattern = formula.replace('@{domain}', '');
    const formatted = rawPattern.replace(/([._-])/g, '<span class="formula-sep">$1</span>');
    return `<span class="formula-prefix">RULE</span> <code>${formatted}</code>`;
  }

  function renderTokens(first, last, domain, totalCount, matchesCount) {
    if (!tokensBar) return;
    tokensBar.innerHTML = `
      <div class="perm-token-pill">First: <strong>${first}</strong></div>
      <div class="perm-token-pill">Last: <strong>${last}</strong></div>
      <div class="perm-token-pill">Domain: <strong>${domain}</strong></div>
      <div class="perm-token-pill">Initials: <strong>${first[0]}${last[0]}</strong></div>
      <div class="perm-token-pill" style="margin-left:auto; border-color:var(--accent-yellow); color:var(--accent-yellow-light);">
        Showing <strong>${matchesCount}</strong> of <strong>${totalCount}</strong> Patterns
      </div>
    `;
  }

  function sendToDeliverabilityScanner(email) {
    const tabVerifBtn = document.getElementById('tab-btn-deliverability');
    const verifInput = document.getElementById('verify-email-input');
    if (verifInput) verifInput.value = email;
    if (tabVerifBtn) tabVerifBtn.click();
    setTimeout(() => {
      runDeliverabilityCheck();
      showToast(`Transferred ${email} to Deliverability Analyzer!`);
    }, 150);
  }

  function generatePermutations() {
    const first = (inputFirst?.value || 'satya').trim().toLowerCase().replace(/[^a-z0-9]/g, '');
    const last = (inputLast?.value || 'nadella').trim().toLowerCase().replace(/[^a-z0-9]/g, '');
    const domain = (inputDomain?.value || 'microsoft.com').trim().toLowerCase().replace(/[^a-z0-9.-]/g, '');

    if (!first || !last || !domain) {
      if (chipsContainer) chipsContainer.innerHTML = '<p class="t-dim">Please enter a valid First Name, Last Name, and Domain.</p>';
      if (tokensBar) tokensBar.innerHTML = '';
      return;
    }

    allPermutationsData = buildPatternDefinitions(first, last, domain);

    // Apply Filter & Search
    const filtered = allPermutationsData.filter(item => {
      const matchCategory = (activeFilter === 'all') || (item.cat === activeFilter);
      const matchSearch = !searchQuery || item.email.includes(searchQuery) || item.desc.toLowerCase().includes(searchQuery);
      return matchCategory && matchSearch;
    });

    renderTokens(first, last, domain, allPermutationsData.length, filtered.length);

    if (chipsContainer) {
      chipsContainer.innerHTML = '';
      if (filtered.length === 0) {
        chipsContainer.innerHTML = '<p class="t-dim" style="padding:20px;">No patterns matched your search filter.</p>';
        return;
      }

      filtered.forEach((item, idx) => {
        const isTop = item.prob >= 85;
        const card = document.createElement('div');
        card.className = `pattern-card ${isTop ? 'top-choice' : ''}`;
        card.innerHTML = `
          <div class="pattern-card-header">
            ${formatHighlightedEmail(item.pattern, domain)}
            <button class="btn-card-action copy-single-btn" data-email="${item.email}" title="Copy email">
              📋 Copy
            </button>
          </div>
          <div class="pattern-meta-row">
            <div class="pattern-formula-tag">${formatHighlightedFormula(item.formula)}</div>
            <span class="pattern-prob-badge ${item.badge}">
              <span class="prob-dot"></span> ${item.prob}% Match
            </span>
          </div>
          <div class="pattern-actions-row">
            <span class="pattern-desc-tag">${item.desc}</span>
            <button class="btn-card-action btn-card-verify verify-single-btn" data-email="${item.email}">
              ⚡ Scan Deliverability
            </button>
          </div>
        `;

        // Copy single email
        const copyBtn = card.querySelector('.copy-single-btn');
        if (copyBtn) {
          copyBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            navigator.clipboard.writeText(item.email).then(() => {
              showToast(`Copied: ${item.email}`);
            });
          });
        }

        // Send to verify
        const verifyBtn = card.querySelector('.verify-single-btn');
        if (verifyBtn) {
          verifyBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            sendToDeliverabilityScanner(item.email);
          });
        }

        // Clicking whole card copies
        card.addEventListener('click', () => {
          navigator.clipboard.writeText(item.email).then(() => {
            showToast(`Copied: ${item.email}`);
          });
        });

        chipsContainer.appendChild(card);
      });
    }
  }

  [inputFirst, inputLast, inputDomain].forEach(inp => {
    if (inp) inp.addEventListener('input', generatePermutations);
  });

  if (permSearch) {
    permSearch.addEventListener('input', (e) => {
      searchQuery = e.target.value.trim().toLowerCase();
      generatePermutations();
    });
  }

  // Filter Buttons
  filterButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      filterButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeFilter = btn.getAttribute('data-filter') || 'all';
      generatePermutations();
    });
  });

  // Copy All Action
  if (copyAllBtn) {
    copyAllBtn.addEventListener('click', () => {
      const emails = allPermutationsData.map(p => p.email);
      if (emails.length > 0) {
        navigator.clipboard.writeText(emails.join('\n')).then(() => {
          showToast(`Copied all ${emails.length} permutations to clipboard!`);
        });
      }
    });
  }

  // Export CSV Action
  if (exportCsvBtn) {
    exportCsvBtn.addEventListener('click', () => {
      if (allPermutationsData.length === 0) return;
      let csvContent = 'Email,Pattern Formula,Category,Probability Match,Description\n';
      allPermutationsData.forEach(p => {
        csvContent += `"${p.email}","${p.formula}","${p.cat}","${p.prob}%","${p.desc}"\n`;
      });
      const dataStr = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csvContent);
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute('href', dataStr);
      downloadAnchor.setAttribute('download', `email_permutations_${inputDomain?.value || 'domain'}.csv`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
      showToast('Exported CSV with all 34 permutations!');
    });
  }

  // Export JSON Action
  if (exportJsonBtn) {
    exportJsonBtn.addEventListener('click', () => {
      if (allPermutationsData.length === 0) return;
      const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(allPermutationsData, null, 4));
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute('href', dataStr);
      downloadAnchor.setAttribute('download', `email_permutations_${inputDomain?.value || 'domain'}.json`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
      showToast('Exported JSON with all permutations!');
    });
  }

  // Preset sample buttons
  document.querySelectorAll('.sample-perm-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      if (inputFirst) inputFirst.value = btn.getAttribute('data-first');
      if (inputLast) inputLast.value = btn.getAttribute('data-last');
      if (inputDomain) inputDomain.value = btn.getAttribute('data-domain');
      if (permSearch) permSearch.value = '';
      searchQuery = '';
      activeFilter = 'all';
      filterButtons.forEach(b => b.classList.remove('active'));
      const allBtn = document.getElementById('perm-filter-all');
      if (allBtn) allBtn.classList.add('active');
      generatePermutations();
      showToast(`Loaded sample: ${inputFirst.value} ${inputLast.value} (${inputDomain.value})`);
    });
  });

  generatePermutations();

  // 5. Interactive Deliverability Analyzer Simulator
  const verifyInput = document.getElementById('verify-email-input');
  const verifyBtn = document.getElementById('btn-run-verify');
  const gaugeBox = document.getElementById('gauge-box');
  const gaugeNumber = document.getElementById('gauge-number');
  const valMx = document.getElementById('val-mx');
  const valSpf = document.getElementById('val-spf');
  const valDmarc = document.getElementById('val-dmarc');
  const valDisposable = document.getElementById('val-disposable');
  const valFree = document.getElementById('val-free');
  const valVerdict = document.getElementById('val-verdict');

  const knownBurners = ['tempmail.com', '10minutemail.com', 'mailinator.com', 'guerrillamail.com', 'trashmail.com', 'yopmail.com'];
  const knownFree = ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'icloud.com', 'proton.me', 'aol.com', 'zoho.com'];

  function runDeliverabilityCheck() {
    const email = (verifyInput?.value || 'admin@microsoft.com').trim().toLowerCase();
    if (!email || !email.includes('@')) {
      showToast('Please enter a valid email address');
      return;
    }

    const [user, domain] = email.split('@');
    const isBurner = knownBurners.some(b => domain.includes(b));
    const isFreeProv = knownFree.includes(domain);
    const hasMx = !isBurner && domain.includes('.');
    const isRole = ['admin', 'support', 'contact', 'info', 'sales', 'security', 'billing'].includes(user);

    let score = 0;
    if (hasMx) score += 40;
    if (!isBurner) score += 30;
    if (user.length > 2) score += 15;
    if (!isRole) score += 10;
    if (!isFreeProv) score += 5;

    if (isBurner) score = 10;

    if (gaugeBox) gaugeBox.style.setProperty('--score-pct', score);
    if (gaugeNumber) {
      gaugeNumber.textContent = score;
      if (score >= 80) gaugeNumber.style.color = 'var(--accent-yellow)';
      else if (score >= 50) gaugeNumber.style.color = 'var(--accent-amber)';
      else gaugeNumber.style.color = 'var(--accent-rose)';
    }

    if (valMx) valMx.innerHTML = hasMx ? '<span style="color:var(--accent-green)">Active (Found)</span>' : '<span style="color:var(--accent-rose)">No MX Found</span>';
    if (valSpf) valSpf.innerHTML = hasMx ? '<span style="color:var(--accent-green)">Valid (v=spf1)</span>' : '<span style="color:var(--text-muted)">None</span>';
    if (valDmarc) valDmarc.innerHTML = hasMx ? '<span style="color:var(--accent-green)">Enforced (p=reject)</span>' : '<span style="color:var(--text-muted)">None</span>';
    if (valDisposable) valDisposable.innerHTML = isBurner ? '<span style="color:var(--accent-rose)">Flagged (Disposable)</span>' : '<span style="color:var(--accent-green)">Clean</span>';
    if (valFree) valFree.innerHTML = isFreeProv ? '<span style="color:var(--accent-amber)">Free Provider</span>' : '<span style="color:var(--accent-yellow)">Corporate / Custom</span>';
    if (valVerdict) {
      if (score >= 80) valVerdict.innerHTML = '<span class="badge-tag badge-free">DELIVERABLE</span>';
      else if (score >= 50) valVerdict.innerHTML = '<span class="badge-tag" style="background:rgba(245,158,11,0.2);color:var(--accent-amber);border:1px solid rgba(245,158,11,0.35)">RISKY / ROLE</span>';
      else valVerdict.innerHTML = '<span class="badge-tag" style="background:rgba(244,63,94,0.2);color:var(--accent-rose);border:1px solid rgba(244,63,94,0.35)">UNDELIVERABLE</span>';
    }

    showToast(`Calculated score for ${email}: ${score}%`);
  }

  if (verifyBtn) verifyBtn.addEventListener('click', runDeliverabilityCheck);

  // 6. Interactive Terminal Demonstration
  const termBody = document.getElementById('terminal-content');
  const termButtons = document.querySelectorAll('.term-action-btn');

  const termDemos = {
    scan: [
      '<span class="t-yellow">$ mailerone --scan admin@microsoft.com</span>',
      '<span class="t-dim">[*] Querying Google DoH & Active MX records...</span>',
      '<span class="t-green">[+] Active MX Records : Found (microsoft-com.mail.protection.outlook.com)</span>',
      '<span class="t-green">[+] SPF & DMARC       : Valid (v=spf1 / DMARC1 p=reject)</span>',
      '<span class="t-green">[+] Disposable Check  : Clean (Passed 8,800+ burner blocklist)</span>',
      '<span class="t-yellow">[*] OSINT Profiler    : Found GitHub Profile (@OWASP)</span>',
      '<span class="t-lime">[+] ZeroBounce Check  : SMTP Provider Microsoft (invalid/role)</span>',
      '<span class="t-green">------------------------------------------------------------</span>',
      '<span class="t-yellow">>> COMPREHENSIVE SCAN SCORE: 85% [DELIVERABLE / ROLE]</span>'
    ],
    find: [
      '<span class="t-yellow">$ mailerone --find-b2b "Patrick" "Collison" "stripe.com"</span>',
      '<span class="t-dim">[*] Querying Hunter.io, ContactOut, SalesQL, FinalScout & Name2Email...</span>',
      '<span class="t-green">[+] Hunter.io Engine  : Found (patrick@stripe.com, Score: 96%)</span>',
      '<span class="t-green">[+] ContactOut Engine : Found (Work: patrick@stripe.com, Title: CEO)</span>',
      '<span class="t-green">[+] Name2Email Perms  : Generated 34 patterns -> Verified Top Candidate</span>',
      '<span class="t-green">------------------------------------------------------------</span>',
      '<span class="t-yellow">>> PRIMARY IDENTIFIED EMAIL: patrick@stripe.com [HIGH CONFIDENCE]</span>'
    ],
    quotas: [
      '<span class="t-yellow">$ mailerone --quotas --live</span>',
      '<span class="t-dim">[*] Querying real-time quota APIs & remaining balances...</span>',
      '<span class="t-green">[+] Hunter.io    : Free Plan (25 searches / 50 verifs left, Reset: 1st of month)</span>',
      '<span class="t-green">[+] ContactOut   : Free Plan (40 Work Emails + 5 Direct Phones remaining)</span>',
      '<span class="t-lime">[+] SalesQL      : Free Plan (50 / 50 Credits remaining, Reset: Monthly)</span>',
      '<span class="t-green">[+] SignalHire   : Free Starter (5 Contact Credits active)</span>',
      '<span class="t-yellow">[+] FinalScout   : Free Plan (20 Regular + 10 AI Credits remaining)</span>',
      '<span class="t-lime">[+] ZeroBounce   : 100 Validations remaining / month</span>',
      '<span class="t-green">[+] DeBounce     : 100 Credits remaining (Lifetime)</span>',
      '<span class="t-yellow">[+] Name2Email   : 100% Free & Unlimited (Zero external API cost)</span>'
    ]
  };

  function playTerminal(cmdKey) {
    if (!termBody) return;
    const lines = termDemos[cmdKey] || termDemos.scan;
    termBody.innerHTML = '';
    let idx = 0;
    const interval = setInterval(() => {
      if (idx < lines.length) {
        const p = document.createElement('div');
        p.innerHTML = lines[idx];
        termBody.appendChild(p);
        termBody.scrollTop = termBody.scrollHeight;
        idx++;
      } else {
        clearInterval(interval);
      }
    }, 220);
  }

  termButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      termButtons.forEach(b => b.classList.remove('btn-primary'));
      btn.classList.add('btn-primary');
      const action = btn.getAttribute('data-cmd');
      playTerminal(action);
    });
  });

  // Initial terminal animation
  playTerminal('scan');

  // 7. Quota Matrix Search & Filter
  const tableSearch = document.getElementById('table-search');
  const tableFilter = document.getElementById('table-filter');
  const matrixRows = document.querySelectorAll('.matrix-row');

  function filterMatrix() {
    const q = (tableSearch?.value || '').toLowerCase();
    const cat = (tableFilter?.value || 'all').toLowerCase();

    matrixRows.forEach(row => {
      const text = row.textContent.toLowerCase();
      const rowCat = (row.getAttribute('data-category') || '').toLowerCase();

      const matchesQuery = !q || text.includes(q);
      const matchesCat = cat === 'all' || rowCat === cat;

      if (matchesQuery && matchesCat) {
        row.style.display = '';
      } else {
        row.style.display = 'none';
      }
    });
  }

  if (tableSearch) tableSearch.addEventListener('input', filterMatrix);
  if (tableFilter) tableFilter.addEventListener('change', filterMatrix);

  // 8. API Keys & Engine Configuration Manager
  const keyMap = {
    'key-hunter': 'hunter_api_keys',
    'key-contactout': 'contactout_api_key',
    'key-salesql': 'salesql_api_key',
    'key-signalhire': 'signalhire_api_key',
    'key-finalscout': 'finalscout_api_key',
    'key-abstract': 'abstract_api_key',
    'key-zerobounce': 'zerobounce_api_key',
    'key-debounce': 'debounce_api_key',
    'key-mailboxlayer': 'mailboxlayer_api_key',
    'key-emailrep': 'emailrep_api_key',
    'key-github': 'github_token'
  };

  // Load saved keys from localStorage
  function loadStoredKeys() {
    try {
      const saved = localStorage.getItem('mailerone_keys');
      if (saved) {
        const parsed = JSON.parse(saved);
        Object.keys(keyMap).forEach(elemId => {
          const field = keyMap[elemId];
          const inputElem = document.getElementById(elemId);
          if (inputElem && parsed[field] !== undefined) {
            if (Array.isArray(parsed[field])) {
              inputElem.value = parsed[field].join(', ');
            } else {
              inputElem.value = parsed[field] || '';
            }
          }
        });
      }
    } catch (e) {
      console.warn('Could not load keys from localStorage', e);
    }
  }

  loadStoredKeys();

  // Show / Hide Key Visibility Toggle
  document.querySelectorAll('.toggle-key-visibility').forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-target');
      const targetInput = document.getElementById(targetId);
      if (targetInput) {
        if (targetInput.type === 'password') {
          targetInput.type = 'text';
          btn.textContent = '🔒';
        } else {
          targetInput.type = 'password';
          btn.textContent = '👁️';
        }
      }
    });
  });

  // Save Keys to Local Storage
  const btnSaveKeys = document.getElementById('btn-save-keys');
  if (btnSaveKeys) {
    btnSaveKeys.addEventListener('click', () => {
      const configObj = {};
      Object.keys(keyMap).forEach(elemId => {
        const field = keyMap[elemId];
        const val = (document.getElementById(elemId)?.value || '').trim();
        if (field === 'hunter_api_keys') {
          configObj[field] = val ? val.split(',').map(s => s.trim()).filter(Boolean) : [];
        } else {
          configObj[field] = val;
        }
      });

      localStorage.setItem('mailerone_keys', JSON.stringify(configObj));
      showToast('API Keys saved successfully to local storage!');
    });
  }

  // Export config.json
  const btnExportConfig = document.getElementById('btn-export-config');
  if (btnExportConfig) {
    btnExportConfig.addEventListener('click', () => {
      const configObj = {};
      Object.keys(keyMap).forEach(elemId => {
        const field = keyMap[elemId];
        const val = (document.getElementById(elemId)?.value || '').trim();
        if (field === 'hunter_api_keys') {
          configObj[field] = val ? val.split(',').map(s => s.trim()).filter(Boolean) : [];
        } else {
          configObj[field] = val;
        }
      });

      const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(configObj, null, 4));
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute('href', dataStr);
      downloadAnchor.setAttribute('download', 'config.json');
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
      showToast('Exported config.json for Mailerone CLI!');
    });
  }

  // Clear all keys
  const btnClearKeys = document.getElementById('btn-clear-keys');
  if (btnClearKeys) {
    btnClearKeys.addEventListener('click', () => {
      if (confirm('Are you sure you want to clear all entered API keys?')) {
        Object.keys(keyMap).forEach(elemId => {
          const inputElem = document.getElementById(elemId);
          if (inputElem) inputElem.value = '';
        });
        localStorage.removeItem('mailerone_keys');
        showToast('All API Keys have been cleared.');
      }
    });
  }
});
