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

  // 4. Name2Email Interactive Permutator
  const inputFirst = document.getElementById('perm-first');
  const inputLast = document.getElementById('perm-last');
  const inputDomain = document.getElementById('perm-domain');
  const permsCount = document.getElementById('perms-count');
  const chipsContainer = document.getElementById('chips-container');
  const copyAllBtn = document.getElementById('btn-copy-all-perms');

  let currentPermutations = [];

  function generatePermutations() {
    const first = (inputFirst?.value || 'satya').trim().toLowerCase().replace(/[^a-z0-9]/g, '');
    const last = (inputLast?.value || 'nadella').trim().toLowerCase().replace(/[^a-z0-9]/g, '');
    const domain = (inputDomain?.value || 'microsoft.com').trim().toLowerCase().replace(/[^a-z0-9.-]/g, '');

    if (!first || !last || !domain) {
      if (chipsContainer) chipsContainer.innerHTML = '<p class="t-dim">Please enter a valid First Name, Last Name, and Domain.</p>';
      return;
    }

    const f = first[0];
    const l = last[0];

    const rawPatterns = [
      `${first}.${last}`,
      `${first}${last}`,
      `${f}.${last}`,
      `${f}${last}`,
      `${first}_${last}`,
      `${f}_${last}`,
      `${first}-${last}`,
      `${f}-${last}`,
      `${first}.${l}`,
      `${first}${l}`,
      `${first}_${l}`,
      `${first}-${l}`,
      `${first}`,
      `${last}`,
      `${last}.${first}`,
      `${last}${first}`,
      `${last}.${f}`,
      `${last}${f}`,
      `${last}_${first}`,
      `${last}_${f}`,
      `${last}-${first}`,
      `${last}-${f}`,
      `${l}.${first}`,
      `${l}${first}`,
      `${l}_${first}`,
      `${l}-${first}`,
      `${f}.${l}`,
      `${f}${l}`,
      `${first}.${last}1`,
      `${first}.${last}2`,
      `${first}${last}1`,
      `${first}${last}123`,
      `${first}${last}777`
    ];

    const uniqueEmails = [...new Set(rawPatterns.map(p => `${p}@${domain}`))];
    currentPermutations = uniqueEmails;

    if (permsCount) permsCount.textContent = `${uniqueEmails.length} Patterns`;

    if (chipsContainer) {
      chipsContainer.innerHTML = '';
      uniqueEmails.forEach((email, idx) => {
        const chip = document.createElement('div');
        const isTop = idx < 4;
        chip.className = `pattern-chip ${isTop ? 'top-choice' : ''}`;
        chip.innerHTML = `
          <span>${email}</span>
          <span style="font-size: 0.75rem; color: ${isTop ? 'var(--accent-emerald)' : 'var(--text-muted)'};">
            ${isTop ? '★ Top Pattern' : 'Candidate'}
          </span>
        `;
        chip.addEventListener('click', () => {
          navigator.clipboard.writeText(email).then(() => {
            showToast(`Copied candidate: ${email}`);
          });
        });
        chipsContainer.appendChild(chip);
      });
    }
  }

  [inputFirst, inputLast, inputDomain].forEach(inp => {
    if (inp) inp.addEventListener('input', generatePermutations);
  });

  if (copyAllBtn) {
    copyAllBtn.addEventListener('click', () => {
      if (currentPermutations.length > 0) {
        navigator.clipboard.writeText(currentPermutations.join('\n')).then(() => {
          showToast(`Copied all ${currentPermutations.length} permutations!`);
        });
      }
    });
  }

  // Quick Preset Samples
  document.querySelectorAll('.sample-perm-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      if (inputFirst) inputFirst.value = btn.getAttribute('data-first');
      if (inputLast) inputLast.value = btn.getAttribute('data-last');
      if (inputDomain) inputDomain.value = btn.getAttribute('data-domain');
      generatePermutations();
      showToast(`Loaded sample: ${inputFirst.value} ${inputLast.value}`);
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
      if (score >= 80) gaugeNumber.style.color = 'var(--accent-emerald)';
      else if (score >= 50) gaugeNumber.style.color = 'var(--accent-amber)';
      else gaugeNumber.style.color = 'var(--accent-rose)';
    }

    if (valMx) valMx.innerHTML = hasMx ? '<span style="color:var(--accent-emerald)">Active (Found)</span>' : '<span style="color:var(--accent-rose)">No MX Found</span>';
    if (valSpf) valSpf.innerHTML = hasMx ? '<span style="color:var(--accent-emerald)">Valid (v=spf1)</span>' : '<span style="color:var(--text-muted)">None</span>';
    if (valDmarc) valDmarc.innerHTML = hasMx ? '<span style="color:var(--accent-emerald)">Enforced (p=reject)</span>' : '<span style="color:var(--text-muted)">None</span>';
    if (valDisposable) valDisposable.innerHTML = isBurner ? '<span style="color:var(--accent-rose)">Flagged (Disposable)</span>' : '<span style="color:var(--accent-emerald)">Clean</span>';
    if (valFree) valFree.innerHTML = isFreeProv ? '<span style="color:var(--accent-amber)">Free Provider</span>' : '<span style="color:var(--accent-cyan)">Corporate / Custom</span>';
    if (valVerdict) {
      if (score >= 80) valVerdict.innerHTML = '<span class="badge-tag badge-free">DELIVERABLE</span>';
      else if (score >= 50) valVerdict.innerHTML = '<span class="badge-tag" style="background:rgba(245,158,11,0.2);color:var(--accent-amber)">RISKY / ROLE</span>';
      else valVerdict.innerHTML = '<span class="badge-tag" style="background:rgba(244,63,94,0.2);color:var(--accent-rose)">UNDELIVERABLE</span>';
    }

    showToast(`Calculated score for ${email}: ${score}%`);
  }

  if (verifyBtn) verifyBtn.addEventListener('click', runDeliverabilityCheck);

  // 6. Interactive Terminal Demonstration
  const termBody = document.getElementById('terminal-content');
  const termButtons = document.querySelectorAll('.term-action-btn');

  const termDemos = {
    scan: [
      '<span class="t-cyan">$ mailerone --scan admin@microsoft.com</span>',
      '<span class="t-dim">[*] Querying Google DoH & Active MX records...</span>',
      '<span class="t-green">[+] Active MX Records : Found (microsoft-com.mail.protection.outlook.com)</span>',
      '<span class="t-green">[+] SPF & DMARC       : Valid (v=spf1 / DMARC1 p=reject)</span>',
      '<span class="t-green">[+] Disposable Check  : Clean (Passed 8,800+ burner blocklist)</span>',
      '<span class="t-yellow">[*] OSINT Profiler    : Found GitHub Profile (@OWASP)</span>',
      '<span class="t-cyan">[+] ZeroBounce Check  : SMTP Provider Microsoft (invalid/role)</span>',
      '<span class="t-green">------------------------------------------------------------</span>',
      '<span class="t-green">>> COMPREHENSIVE SCAN SCORE: 85% [DELIVERABLE / ROLE]</span>'
    ],
    find: [
      '<span class="t-cyan">$ mailerone --find-b2b "Patrick" "Collison" "stripe.com"</span>',
      '<span class="t-dim">[*] Querying Hunter.io, ContactOut, SalesQL, FinalScout & Name2Email...</span>',
      '<span class="t-green">[+] Hunter.io Engine  : Found (patrick@stripe.com, Score: 96%)</span>',
      '<span class="t-green">[+] ContactOut Engine : Found (Work: patrick@stripe.com, Title: CEO)</span>',
      '<span class="t-green">[+] Name2Email Perms  : Generated 34 patterns -> Verified Top Candidate</span>',
      '<span class="t-green">------------------------------------------------------------</span>',
      '<span class="t-green">>> PRIMARY IDENTIFIED EMAIL: patrick@stripe.com [HIGH CONFIDENCE]</span>'
    ],
    quotas: [
      '<span class="t-cyan">$ mailerone --quotas --live</span>',
      '<span class="t-dim">[*] Querying real-time quota APIs & remaining balances...</span>',
      '<span class="t-green">[+] Hunter.io    : Free Plan (25 searches remaining, Reset: 2026-10-01)</span>',
      '<span class="t-green">[+] ZeroBounce   : 100 Credits Remaining</span>',
      '<span class="t-green">[+] DeBounce     : 100 Credits Remaining</span>',
      '<span class="t-green">[+] GitHub API   : 30 search req/min remaining (Token Mode)</span>',
      '<span class="t-green">[+] ContactOut   : 40 Free Work Emails / mo</span>',
      '<span class="t-green">[+] SalesQL      : 50 Free Credits / mo</span>',
      '<span class="t-green">[+] Name2Email   : 100% Free & Unlimited</span>'
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
});
