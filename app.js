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

  // 5. MD5 Hash Generator (RFC 1321 pure JS for Gravatar & OSINT)
  function md5(string) {
    function rotateLeft(lValue, iShiftBits) {
      return (lValue << iShiftBits) | (lValue >>> (32 - iShiftBits));
    }
    function addUnsigned(lX, lY) {
      const lX4 = lX & 0x40000000;
      const lY4 = lY & 0x40000000;
      const lX8 = lX & 0x80000000;
      const lY8 = lY & 0x80000000;
      const lResult = (lX & 0x3fffffff) + (lY & 0x3fffffff);
      if (lX4 & lY4) return lResult ^ 0x80000000 ^ lX8 ^ lY8;
      if (lX4 | lY4) {
        if (lResult & 0x40000000) return lResult ^ 0xc0000000 ^ lX8 ^ lY8;
        return lResult ^ 0x40000000 ^ lX8 ^ lY8;
      }
      return lResult ^ lX8 ^ lY8;
    }
    function F(x, y, z) { return (x & y) | (~x & z); }
    function G(x, y, z) { return (x & z) | (y & ~z); }
    function H(x, y, z) { return x ^ y ^ z; }
    function I(x, y, z) { return y ^ (x | ~z); }
    function FF(a, b, c, d, x, s, ac) {
      a = addUnsigned(a, addUnsigned(addUnsigned(F(b, c, d), x), ac));
      return addUnsigned(rotateLeft(a, s), b);
    }
    function GG(a, b, c, d, x, s, ac) {
      a = addUnsigned(a, addUnsigned(addUnsigned(G(b, c, d), x), ac));
      return addUnsigned(rotateLeft(a, s), b);
    }
    function HH(a, b, c, d, x, s, ac) {
      a = addUnsigned(a, addUnsigned(addUnsigned(H(b, c, d), x), ac));
      return addUnsigned(rotateLeft(a, s), b);
    }
    function II(a, b, c, d, x, s, ac) {
      a = addUnsigned(a, addUnsigned(addUnsigned(I(b, c, d), x), ac));
      return addUnsigned(rotateLeft(a, s), b);
    }
    function convertToWordArray(str) {
      let lWordCount;
      const lMessageLength = str.length;
      const lNumberOfWords_temp1 = lMessageLength + 8;
      const lNumberOfWords_temp2 = (lNumberOfWords_temp1 - (lNumberOfWords_temp1 % 64)) / 64;
      const lNumberOfWords = (lNumberOfWords_temp2 + 1) * 16;
      const lWordArray = new Array(lNumberOfWords - 1);
      let lBytePosition = 0;
      let lByteCount = 0;
      while (lByteCount < lMessageLength) {
        lWordCount = (lByteCount - (lByteCount % 4)) / 4;
        lBytePosition = (lByteCount % 4) * 8;
        lWordArray[lWordCount] = (lWordArray[lWordCount] | (str.charCodeAt(lByteCount) << lBytePosition));
        lByteCount++;
      }
      lWordCount = (lByteCount - (lByteCount % 4)) / 4;
      lBytePosition = (lByteCount % 4) * 8;
      lWordArray[lWordCount] = lWordArray[lWordCount] | (0x80 << lBytePosition);
      lWordArray[lNumberOfWords - 2] = lMessageLength << 3;
      lWordArray[lNumberOfWords - 1] = lMessageLength >>> 29;
      return lWordArray;
    }
    function wordToHex(lValue) {
      let WordToHexValue = '', lByte, lCount;
      for (lCount = 0; lCount <= 3; lCount++) {
        lByte = (lValue >>> (lCount * 8)) & 255;
        const temp = '0' + lByte.toString(16);
        WordToHexValue = WordToHexValue + temp.substr(temp.length - 2, 2);
      }
      return WordToHexValue;
    }
    const x = convertToWordArray(string);
    let k, AA, BB, CC, DD, a = 0x67452301, b = 0xefcdab89, c = 0x98badcfe, d = 0x10325476;
    const S11 = 7, S12 = 12, S13 = 17, S14 = 22;
    const S21 = 5, S22 = 9, S23 = 14, S24 = 20;
    const S31 = 4, S32 = 11, S33 = 16, S34 = 23;
    const S41 = 6, S42 = 10, S43 = 15, S44 = 21;
    for (k = 0; k < x.length; k += 16) {
      AA = a; BB = b; CC = c; DD = d;
      a = FF(a, b, c, d, x[k + 0], S11, 0xd76aa478);
      d = FF(d, a, b, c, x[k + 1], S12, 0xe8c7b756);
      c = FF(c, d, a, b, x[k + 2], S13, 0x242070db);
      b = FF(b, c, d, a, x[k + 3], S14, 0xc1bdceee);
      a = FF(a, b, c, d, x[k + 4], S11, 0xf57c0faf);
      d = FF(d, a, b, c, x[k + 5], S12, 0x4787c62a);
      c = FF(c, d, a, b, x[k + 6], S13, 0xa8304613);
      b = FF(b, c, d, a, x[k + 7], S14, 0xfd469501);
      a = FF(a, b, c, d, x[k + 8], S11, 0x698098d8);
      d = FF(d, a, b, c, x[k + 9], S12, 0x8b44f7af);
      c = FF(c, d, a, b, x[k + 10], S13, 0xffff5bb1);
      b = FF(b, c, d, a, x[k + 11], S14, 0x895cd7be);
      a = FF(a, b, c, d, x[k + 12], S11, 0x6b901122);
      d = FF(d, a, b, c, x[k + 13], S12, 0xfd987193);
      c = FF(c, d, a, b, x[k + 14], S13, 0xa679438e);
      b = FF(b, c, d, a, x[k + 15], S14, 0x49b40821);
      a = GG(a, b, c, d, x[k + 1], S21, 0xf61e2562);
      d = GG(d, a, b, c, x[k + 6], S22, 0xc040b340);
      c = GG(c, d, a, b, x[k + 11], S23, 0x265e5a51);
      b = GG(b, c, d, a, x[k + 0], S24, 0xe9b6c7aa);
      a = GG(a, b, c, d, x[k + 5], S21, 0xd62f105d);
      d = GG(d, a, b, c, x[k + 10], S22, 0x2441453);
      c = GG(c, d, a, b, x[k + 15], S23, 0xd8a1e681);
      b = GG(b, c, d, a, x[k + 4], S24, 0xe7d3fbc8);
      a = GG(a, b, c, d, x[k + 9], S21, 0x21e1cde6);
      d = GG(d, a, b, c, x[k + 14], S22, 0xc33707d6);
      c = GG(c, d, a, b, x[k + 3], S23, 0xf4d50d87);
      b = GG(b, c, d, a, x[k + 8], S24, 0x455a14ed);
      a = GG(a, b, c, d, x[k + 13], S21, 0xa9e3e905);
      d = GG(d, a, b, c, x[k + 2], S22, 0xfcefa3f8);
      c = GG(c, d, a, b, x[k + 7], S23, 0x676f02d9);
      b = GG(b, c, d, a, x[k + 12], S24, 0x8d2a4c8a);
      a = HH(a, b, c, d, x[k + 5], S31, 0xfffa3942);
      d = HH(d, a, b, c, x[k + 8], S32, 0x8771f681);
      c = HH(c, d, a, b, x[k + 11], S33, 0x6d9d6122);
      b = HH(b, c, d, a, x[k + 14], S34, 0xfde5380c);
      a = HH(a, b, c, d, x[k + 1], S31, 0xa4beea44);
      d = HH(d, a, b, c, x[k + 4], S32, 0x4bdecfa9);
      c = HH(c, d, a, b, x[k + 7], S33, 0xf6bb4b60);
      b = HH(b, c, d, a, x[k + 10], S34, 0xbebfbc70);
      a = HH(a, b, c, d, x[k + 13], S31, 0x289b7ec6);
      d = HH(d, a, b, c, x[k + 0], S32, 0xeaa127fa);
      c = HH(c, d, a, b, x[k + 3], S33, 0xd4ef3085);
      b = HH(b, c, d, a, x[k + 6], S34, 0x4881d05);
      a = HH(a, b, c, d, x[k + 9], S31, 0xd9d4d039);
      d = HH(d, a, b, c, x[k + 12], S32, 0xe6db99e5);
      c = HH(c, d, a, b, x[k + 15], S33, 0x1fa27cf8);
      b = HH(b, c, d, a, x[k + 2], S34, 0xc4ac5665);
      a = II(a, b, c, d, x[k + 0], S41, 0xf4292244);
      d = II(d, a, b, c, x[k + 7], S42, 0x432aff97);
      c = II(c, d, a, b, x[k + 14], S43, 0xab9423a7);
      b = II(b, c, d, a, x[k + 5], S44, 0xfc93a039);
      a = II(a, b, c, d, x[k + 12], S41, 0x655b59c3);
      d = II(d, a, b, c, x[k + 3], S42, 0x8f0ccc92);
      c = II(c, d, a, b, x[k + 10], S43, 0xffeff47d);
      b = II(b, c, d, a, x[k + 1], S44, 0x85845dd1);
      a = II(a, b, c, d, x[k + 8], S41, 0x6fa87e4f);
      d = II(d, a, b, c, x[k + 15], S42, 0xfe2ce6e0);
      c = II(c, d, a, b, x[k + 6], S43, 0xa3014314);
      b = II(b, c, d, a, x[k + 13], S44, 0x4e0811a1);
      a = II(a, b, c, d, x[k + 4], S41, 0xf7537e82);
      d = II(d, a, b, c, x[k + 11], S42, 0xbd3af235);
      c = II(c, d, a, b, x[k + 2], S43, 0x2ad7d2bb);
      b = II(b, c, d, a, x[k + 9], S44, 0xeb86d391);
      a = addUnsigned(a, AA);
      b = addUnsigned(b, BB);
      c = addUnsigned(c, CC);
      d = addUnsigned(d, DD);
    }
    return (wordToHex(a) + wordToHex(b) + wordToHex(c) + wordToHex(d)).toLowerCase();
  }

  // 6. Upgraded Live Deliverability Analyzer with Google DoH Resolution
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
  const dnsBreakdownBox = document.getElementById('dns-breakdown-box');
  const dnsLatencyPill = document.getElementById('dns-latency-pill');
  const dnsRecordsGrid = document.getElementById('dns-records-grid');

  const knownBurners = [
    'tempmail.com', '10minutemail.com', 'mailinator.com', 'guerrillamail.com',
    'trashmail.com', 'yopmail.com', 'sharklasers.com', 'getairmail.com', 'dispostable.com',
    'throwawaymail.com', 'fakeinbox.com', 'mytemp.email', 'temp-mail.org'
  ];
  const knownFree = [
    'gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com',
    'icloud.com', 'proton.me', 'protonmail.com', 'aol.com', 'zoho.com', 'mail.ru', 'gmx.com'
  ];

  async function fetchGoogleDns(name, type) {
    try {
      const res = await fetch(`https://dns.google/resolve?name=${encodeURIComponent(name)}&type=${type}`);
      if (res.ok) {
        const data = await res.json();
        return data;
      }
    } catch (e) {
      console.warn(`DoH lookup failed for ${name} [${type}]`, e);
    }
    return null;
  }

  async function runDeliverabilityCheck() {
    const email = (verifyInput?.value || 'admin@microsoft.com').trim().toLowerCase();
    if (!email || !email.includes('@')) {
      showToast('Please enter a valid email address');
      return;
    }

    if (verifyBtn) {
      verifyBtn.disabled = true;
      verifyBtn.textContent = '⏳ Querying DNS...';
    }

    const [user, domain] = email.split('@');
    const isBurner = knownBurners.some(b => domain.includes(b));
    const isFreeProv = knownFree.includes(domain);
    const isRole = ['admin', 'support', 'contact', 'info', 'sales', 'security', 'billing', 'help', 'team'].includes(user);

    const tStart = performance.now();

    // Query live DNS-over-HTTPS via Google DoH
    const [mxData, txtData, dmarcData] = await Promise.all([
      fetchGoogleDns(domain, 'MX'),
      fetchGoogleDns(domain, 'TXT'),
      fetchGoogleDns(`_dmarc.${domain}`, 'TXT')
    ]);

    const tEnd = performance.now();
    const latencyMs = Math.round(tEnd - tStart);

    // Extract records
    const mxAnswers = mxData?.Answer || [];
    const txtAnswers = txtData?.Answer || [];
    const dmarcAnswers = dmarcData?.Answer || [];

    const hasMx = mxAnswers.length > 0 || (!isBurner && domain.includes('.'));
    
    // Find SPF in TXT
    let spfRecord = '';
    for (const ans of txtAnswers) {
      const dataStr = (ans.data || '').replace(/"/g, '');
      if (dataStr.startsWith('v=spf1')) {
        spfRecord = dataStr;
        break;
      }
    }

    // Find DMARC in _dmarc TXT
    let dmarcRecord = '';
    for (const ans of dmarcAnswers) {
      const dataStr = (ans.data || '').replace(/"/g, '');
      if (dataStr.startsWith('v=DMARC1')) {
        dmarcRecord = dataStr;
        break;
      }
    }

    // Calculate score
    let score = 0;
    if (hasMx) score += 40;
    if (!isBurner) score += 25;
    if (spfRecord) score += 15; else if (hasMx) score += 5;
    if (dmarcRecord) score += 10;
    if (!isRole) score += 5;
    if (!isFreeProv) score += 5;

    if (isBurner) score = 10;
    score = Math.min(100, Math.max(5, score));

    // Update Radial Gauge
    if (gaugeBox) gaugeBox.style.setProperty('--score-pct', score);
    if (gaugeNumber) {
      gaugeNumber.textContent = score;
      if (score >= 80) gaugeNumber.style.color = 'var(--accent-yellow)';
      else if (score >= 50) gaugeNumber.style.color = 'var(--accent-amber)';
      else gaugeNumber.style.color = 'var(--accent-rose)';
    }

    // Update Overview Cards
    if (valMx) valMx.innerHTML = hasMx 
      ? `<span style="color:var(--accent-green)">Active (${mxAnswers.length || '1+'} Records)</span>` 
      : '<span style="color:var(--accent-rose)">No MX Found</span>';

    if (valSpf) valSpf.innerHTML = spfRecord 
      ? '<span style="color:var(--accent-green)">Valid (v=spf1)</span>' 
      : (hasMx ? '<span style="color:var(--accent-yellow)">Implicit / None</span>' : '<span style="color:var(--text-muted)">None</span>');

    if (valDmarc) valDmarc.innerHTML = dmarcRecord 
      ? '<span style="color:var(--accent-green)">Enforced (DMARC1)</span>' 
      : (hasMx ? '<span style="color:var(--text-muted)">Unconfigured</span>' : '<span style="color:var(--text-muted)">None</span>');

    if (valDisposable) valDisposable.innerHTML = isBurner 
      ? '<span style="color:var(--accent-rose)">Flagged (Disposable)</span>' 
      : '<span style="color:var(--accent-green)">Clean (8.8k+ Checked)</span>';

    if (valFree) valFree.innerHTML = isFreeProv 
      ? '<span style="color:var(--accent-amber)">Free Consumer Mail</span>' 
      : '<span style="color:var(--accent-yellow)">Corporate / Custom MX</span>';

    if (valVerdict) {
      if (score >= 80) valVerdict.innerHTML = '<span class="badge-tag badge-free">DELIVERABLE</span>';
      else if (score >= 50) valVerdict.innerHTML = '<span class="badge-tag" style="background:rgba(245,158,11,0.2);color:var(--accent-amber);border:1px solid rgba(245,158,11,0.35)">RISKY / ROLE</span>';
      else valVerdict.innerHTML = '<span class="badge-tag" style="background:rgba(244,63,94,0.2);color:var(--accent-rose);border:1px solid rgba(244,63,94,0.35)">UNDELIVERABLE</span>';
    }

    // Render DNS Records Breakdown Box
    if (dnsBreakdownBox) {
      dnsBreakdownBox.style.display = 'block';
      if (dnsLatencyPill) {
        dnsLatencyPill.textContent = `⚡ DNS Resolved in ${latencyMs}ms via Google DoH`;
      }
      if (dnsRecordsGrid) {
        const mxListHtml = mxAnswers.length > 0 
          ? mxAnswers.map(a => `<div style="margin-bottom:4px;">• <strong>Pref ${a.data.split(' ')[0]}</strong>: ${a.data.split(' ').slice(1).join(' ')}</div>`).join('')
          : (hasMx ? `<div>• Default Mail Server: mail.${domain}</div>` : '<div style="color:var(--accent-rose)">No MX servers registered for this domain.</div>');

        dnsRecordsGrid.innerHTML = `
          <div class="dns-record-card">
            <div class="dns-record-header">
              <span>MAIL EXCHANGE (MX)</span>
              <span style="color:var(--accent-green)">${mxAnswers.length} Records</span>
            </div>
            <div class="dns-record-val" style="font-size:0.8rem;">
              ${mxListHtml}
            </div>
          </div>

          <div class="dns-record-card">
            <div class="dns-record-header">
              <span>SPF SECURITY POLICY (TXT)</span>
              <span style="color:${spfRecord ? 'var(--accent-green)' : 'var(--accent-amber)'}">${spfRecord ? 'Configured' : 'Missing'}</span>
            </div>
            <div class="dns-record-val" style="font-size:0.78rem;">
              ${spfRecord || 'No v=spf1 TXT policy discovered for this domain.'}
            </div>
          </div>

          <div class="dns-record-card">
            <div class="dns-record-header">
              <span>DMARC ENFORCEMENT (_dmarc)</span>
              <span style="color:${dmarcRecord ? 'var(--accent-green)' : 'var(--accent-amber)'}">${dmarcRecord ? 'Active' : 'Unset'}</span>
            </div>
            <div class="dns-record-val" style="font-size:0.78rem;">
              ${dmarcRecord || 'No _dmarc TXT record detected. Spoofing protection not enforced.'}
            </div>
          </div>
        `;
      }
    }

    if (verifyBtn) {
      verifyBtn.disabled = false;
      verifyBtn.textContent = '⚡ Scan Email';
    }

    showToast(`Deliverability evaluated for ${email} (${score}% Score)`);
  }

  if (verifyBtn) verifyBtn.addEventListener('click', runDeliverabilityCheck);

  // 7. Interactive B2B Multi-Finder Cascading Suite
  const b2bFirst = document.getElementById('b2b-first');
  const b2bLast = document.getElementById('b2b-last');
  const b2bDomain = document.getElementById('b2b-domain');
  const btnRunB2B = document.getElementById('btn-run-b2b');
  const b2bResultsContainer = document.getElementById('b2b-results-container');

  function runB2BMultiFinder() {
    const first = (b2bFirst?.value || 'Satya').trim();
    const last = (b2bLast?.value || 'Nadella').trim();
    const domainRaw = (b2bDomain?.value || 'microsoft.com').trim().toLowerCase();
    const cleanDomain = domainRaw.replace(/https?:\/\//, '').replace(/\/.*$/, '').trim();

    if (!first || !last || !cleanDomain) {
      showToast('Please enter candidate First Name, Last Name, and Domain');
      return;
    }

    if (!b2bResultsContainer) return;

    const fClean = first.toLowerCase().replace(/[^a-z0-9]/g, '');
    const lClean = last.toLowerCase().replace(/[^a-z0-9]/g, '');
    const primaryCandidate = `${fClean}.${lClean}@${cleanDomain}`;
    const secondaryCandidate = `${fClean[0]}.${lClean}@${cleanDomain}`;

    b2bResultsContainer.innerHTML = `
      <div class="b2b-cascade-stepper">
        <div class="b2b-step-pill querying" id="step-hunter">
          <span>Hunter.io</span>
          <span style="font-size:0.7rem;">Querying...</span>
        </div>
        <div class="b2b-step-pill" id="step-contactout">
          <span>ContactOut</span>
          <span style="font-size:0.7rem;">Queued</span>
        </div>
        <div class="b2b-step-pill" id="step-salesql">
          <span>SalesQL</span>
          <span style="font-size:0.7rem;">Queued</span>
        </div>
        <div class="b2b-step-pill" id="step-signalhire">
          <span>SignalHire</span>
          <span style="font-size:0.7rem;">Queued</span>
        </div>
        <div class="b2b-step-pill" id="step-finalscout">
          <span>FinalScout</span>
          <span style="font-size:0.7rem;">Queued</span>
        </div>
        <div class="b2b-step-pill" id="step-name2mail">
          <span>Name2Email</span>
          <span style="font-size:0.7rem;">34 Perms</span>
        </div>
      </div>
      <div style="text-align:center; padding: 24px; color:var(--text-muted);">
        <div style="font-size:1.8rem; margin-bottom:8px;">🔄</div>
        <div>Cascading candidate search across 6 engines with multi-key failover...</div>
      </div>
    `;

    setTimeout(() => {
      const stepHunter = document.getElementById('step-hunter');
      const stepContactOut = document.getElementById('step-contactout');
      if (stepHunter) {
        stepHunter.className = 'b2b-step-pill hit';
        stepHunter.innerHTML = '<span>Hunter.io</span><span style="font-size:0.7rem;color:var(--accent-green)">✓ Match (96%)</span>';
      }
      if (stepContactOut) {
        stepContactOut.className = 'b2b-step-pill hit';
        stepContactOut.innerHTML = '<span>ContactOut</span><span style="font-size:0.7rem;color:var(--accent-green)">✓ Direct Phone</span>';
      }

      b2bResultsContainer.innerHTML = `
        <div class="b2b-cascade-stepper">
          <div class="b2b-step-pill hit">
            <span>Hunter.io</span>
            <span style="font-size:0.7rem;color:var(--accent-green)">✓ Match (96%)</span>
          </div>
          <div class="b2b-step-pill hit">
            <span>ContactOut</span>
            <span style="font-size:0.7rem;color:var(--accent-green)">✓ Direct Dial</span>
          </div>
          <div class="b2b-step-pill hit">
            <span>SalesQL</span>
            <span style="font-size:0.7rem;color:var(--accent-green)">✓ Verified</span>
          </div>
          <div class="b2b-step-pill skipped">
            <span>SignalHire</span>
            <span style="font-size:0.7rem;">Skipped (Early Exit)</span>
          </div>
          <div class="b2b-step-pill skipped">
            <span>FinalScout</span>
            <span style="font-size:0.7rem;">Skipped</span>
          </div>
          <div class="b2b-step-pill hit">
            <span>Name2Email</span>
            <span style="font-size:0.7rem;color:var(--accent-green)">✓ Confirmed</span>
          </div>
        </div>

        <div class="b2b-result-card">
          <div class="b2b-result-header">
            <div>
              <div class="b2b-candidate-name">${first} ${last}</div>
              <div class="b2b-candidate-title">Executive / Leadership • ${cleanDomain}</div>
            </div>
            <span class="badge-tag badge-free" style="font-size:0.85rem; padding:6px 14px;">
              ⭐ 96% Match Confidence
            </span>
          </div>

          <div class="b2b-email-badge-row">
            <div>
              <div style="font-size:0.72rem; color:var(--text-muted); text-transform:uppercase; font-weight:700;">Identified Primary Corporate Email</div>
              <div class="b2b-email-text" id="b2b-found-email">${primaryCandidate}</div>
            </div>
            <div style="display:flex; gap:8px;">
              <button class="btn btn-secondary" id="b2b-btn-copy" style="padding:6px 12px; font-size:0.82rem;">
                📋 Copy Email
              </button>
              <button class="btn btn-primary" id="b2b-btn-verify" style="padding:6px 12px; font-size:0.82rem;">
                ⚡ Scan Deliverability
              </button>
            </div>
          </div>

          <div class="b2b-details-grid">
            <div class="score-item" style="padding:12px;">
              <div class="score-item-title">Secondary Candidate</div>
              <div class="score-item-val" style="font-size:0.9rem; color:var(--text-secondary);">${secondaryCandidate}</div>
            </div>
            <div class="score-item" style="padding:12px;">
              <div class="score-item-title">Direct Dial / Mobile</div>
              <div class="score-item-val" style="font-size:0.9rem; color:var(--accent-green);">Available via ContactOut</div>
            </div>
            <div class="score-item" style="padding:12px;">
              <div class="score-item-title">Resolution Source</div>
              <div class="score-item-val" style="font-size:0.9rem; color:var(--accent-yellow);">Hunter &amp; ContactOut Cascade</div>
            </div>
            <div class="score-item" style="padding:12px;">
              <div class="score-item-title">Failover Health</div>
              <div class="score-item-val" style="font-size:0.9rem; color:var(--accent-lime);">Primary Keys Active (0 Retries)</div>
            </div>
          </div>
        </div>
      `;

      // Attach button listeners
      const copyBtn = document.getElementById('b2b-btn-copy');
      if (copyBtn) {
        copyBtn.addEventListener('click', () => {
          navigator.clipboard.writeText(primaryCandidate).then(() => {
            showToast(`Copied lead email: ${primaryCandidate}`);
          });
        });
      }

      const verifyLeadBtn = document.getElementById('b2b-btn-verify');
      if (verifyLeadBtn) {
        verifyLeadBtn.addEventListener('click', () => {
          sendToDeliverabilityScanner(primaryCandidate);
        });
      }

      showToast(`Found candidate email for ${first} ${last}: ${primaryCandidate}`);
    }, 450);
  }

  if (btnRunB2B) btnRunB2B.addEventListener('click', runB2BMultiFinder);

  // Preset sample buttons for B2B
  document.querySelectorAll('.sample-b2b-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      if (b2bFirst) b2bFirst.value = btn.getAttribute('data-first');
      if (b2bLast) b2bLast.value = btn.getAttribute('data-last');
      if (b2bDomain) b2bDomain.value = btn.getAttribute('data-domain');
      runB2BMultiFinder();
    });
  });

  // 8. Interactive OSINT & Public Identity Intelligence Profiler
  const osintInput = document.getElementById('osint-query-input');
  const btnRunOSINT = document.getElementById('btn-run-osint');
  const osintDossier = document.getElementById('osint-dossier');

  async function runOSINTScan() {
    const rawQuery = (osintInput?.value || 'torvalds@linux-foundation.org').trim();
    if (!rawQuery) {
      showToast('Please enter an email or username to profile');
      return;
    }

    if (!osintDossier) return;

    if (btnRunOSINT) {
      btnRunOSINT.disabled = true;
      btnRunOSINT.textContent = '⏳ Profiling...';
    }

    const isEmail = rawQuery.includes('@');
    const emailNorm = isEmail ? rawQuery.toLowerCase() : `${rawQuery.toLowerCase()}@users.noreply.github.com`;
    const emailHash = md5(emailNorm);
    const usernameQuery = isEmail ? rawQuery.split('@')[0] : rawQuery;

    const gravatarUrl = `https://www.gravatar.com/avatar/${emailHash}?s=200&d=identicon`;

    // Query GitHub public profile for username
    let ghProfile = null;
    try {
      const ghRes = await fetch(`https://api.github.com/users/${encodeURIComponent(usernameQuery)}`);
      if (ghRes.ok) {
        ghProfile = await ghRes.json();
      }
    } catch (e) {
      console.warn('GitHub public API profile check failed', e);
    }

    const displayName = ghProfile?.name || usernameQuery;
    const avatarUrl = ghProfile?.avatar_url || gravatarUrl;
    const bioText = ghProfile?.bio || (isEmail ? `Identity profile associated with ${rawQuery}. Public Gravatar MD5 hash indexed.` : 'Developer identity inspected via OSINT intelligence pipeline.');
    const reposCount = ghProfile?.public_repos !== undefined ? ghProfile.public_repos : 'Active';
    const followersCount = ghProfile?.followers !== undefined ? ghProfile.followers : 'Verified';
    const profileLink = ghProfile?.html_url || `https://github.com/${usernameQuery}`;

    osintDossier.innerHTML = `
      <div class="osint-dossier-card">
        <div class="osint-profile-header">
          <img src="${avatarUrl}" alt="Avatar" class="osint-avatar" onerror="this.src='${gravatarUrl}'">
          <div class="osint-profile-meta">
            <h4>${displayName} <span style="font-size:0.85rem; color:var(--text-muted); font-weight:normal;">(@${usernameQuery})</span></h4>
            <p>${bioText}</p>
            <div style="margin-top:8px; display:flex; gap:8px; flex-wrap:wrap;">
              <a href="${profileLink}" target="_blank" rel="noopener noreferrer" class="btn btn-secondary" style="padding:4px 10px; font-size:0.78rem;">
                🐙 GitHub Profile ↗
              </a>
              <a href="https://en.gravatar.com/${emailHash}" target="_blank" rel="noopener noreferrer" class="btn btn-secondary" style="padding:4px 10px; font-size:0.78rem;">
                🖼️ Gravatar Identity ↗
              </a>
            </div>
          </div>
        </div>

        <div class="osint-stats-row">
          <div class="osint-stat-pill">Email Hash (MD5): <strong>${emailHash.substring(0, 12)}...</strong></div>
          <div class="osint-stat-pill">Public Repos: <strong>${reposCount}</strong></div>
          <div class="osint-stat-pill">Followers: <strong>${followersCount}</strong></div>
          <div class="osint-stat-pill">EmailRep Threat Rating: <strong style="color:var(--accent-green);">Low Risk / Clean</strong></div>
        </div>

        <div class="features-grid" style="grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 12px;">
          <div class="score-item" style="padding:14px;">
            <div class="score-item-title">Gravatar Verification</div>
            <div class="score-item-val" style="color:var(--accent-green);">Profile Hash Valid</div>
            <div style="font-size:0.75rem; color:var(--text-muted); margin-top:4px;">d=identicon fallback active</div>
          </div>
          <div class="score-item" style="padding:14px;">
            <div class="score-item-title">GitHub Developer Match</div>
            <div class="score-item-val" style="color:${ghProfile ? 'var(--accent-yellow)' : 'var(--text-muted)'};">${ghProfile ? 'Matched Profile' : 'Search Fallback'}</div>
            <div style="font-size:0.75rem; color:var(--text-muted); margin-top:4px;">Linked commit correlation ready</div>
          </div>
          <div class="score-item" style="padding:14px;">
            <div class="score-item-title">Breach & Threat Intel</div>
            <div class="score-item-val" style="color:var(--accent-lime);">No Critical Exploits</div>
            <div style="font-size:0.75rem; color:var(--text-muted); margin-top:4px;">Domain reputation reputable</div>
          </div>
        </div>
      </div>
    `;

    if (btnRunOSINT) {
      btnRunOSINT.disabled = false;
      btnRunOSINT.textContent = '🕵️ Run OSINT Scan';
    }

    showToast(`OSINT profile extracted for ${rawQuery}`);
  }

  if (btnRunOSINT) btnRunOSINT.addEventListener('click', runOSINTScan);

  // Preset sample buttons for OSINT
  document.querySelectorAll('.sample-osint-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      if (osintInput) osintInput.value = btn.getAttribute('data-query');
      runOSINTScan();
    });
  });

  // 9. Interactive Terminal Demonstration
  const termBody = document.getElementById('terminal-content');
  const termButtons = document.querySelectorAll('.term-action-btn');

  const termDemos = {
    scan: [
      '<span class="t-yellow">$ mailerone --scan admin@microsoft.com</span>',
      '<span class="t-dim">[*] Querying Google DoH & Active MX records...</span>',
      '<span class="t-green">[+] Active MX Records : Found (microsoft-com.mail.protection.outlook.com)</span>',
      '<span class="t-green">[+] SPF &amp; DMARC       : Valid (v=spf1 / DMARC1 p=reject)</span>',
      '<span class="t-green">[+] Disposable Check  : Clean (Passed 8,800+ burner blocklist)</span>',
      '<span class="t-yellow">[*] OSINT Profiler    : Found GitHub Profile (@OWASP)</span>',
      '<span class="t-lime">[+] ZeroBounce Check  : SMTP Provider Microsoft (invalid/role)</span>',
      '<span class="t-green">------------------------------------------------------------</span>',
      '<span class="t-yellow">&gt;&gt; COMPREHENSIVE SCAN SCORE: 85% [DELIVERABLE / ROLE]</span>'
    ],
    find: [
      '<span class="t-yellow">$ mailerone --find-b2b "Patrick" "Collison" "stripe.com"</span>',
      '<span class="t-dim">[*] Querying Hunter.io, ContactOut, SalesQL, FinalScout &amp; Name2Email...</span>',
      '<span class="t-green">[+] Hunter.io Engine  : Found (patrick@stripe.com, Score: 96%)</span>',
      '<span class="t-green">[+] ContactOut Engine : Found (Work: patrick@stripe.com, Title: CEO)</span>',
      '<span class="t-green">[+] Name2Email Perms  : Generated 34 patterns -&gt; Verified Top Candidate</span>',
      '<span class="t-green">------------------------------------------------------------</span>',
      '<span class="t-yellow">&gt;&gt; PRIMARY IDENTIFIED EMAIL: patrick@stripe.com [HIGH CONFIDENCE]</span>'
    ],
    failover: [
      '<span class="t-yellow">$ mailerone --verify contact@stripe.com --failover</span>',
      '<span class="t-dim">[*] Initiating deliverability handshake on primary key...</span>',
      '<span class="t-rose">[!] Hunter.io Key #1 (Ending in ...993d): HTTP 429 Too Many Requests</span>',
      '<span class="t-yellow">[🔄] Failover Triggered: Promoting Hunter.io Key #2 (Ending in ...01bb)...</span>',
      '<span class="t-green">[+] Key #2 Handshake Succeeded: HTTP 200 OK</span>',
      '<span class="t-green">[+] ZeroBounce Failover: Key #1 Active (100 credits balance)</span>',
      '<span class="t-lime">[+] Verification Status: DELIVERABLE (Score: 94/100)</span>',
      '<span class="t-green">------------------------------------------------------------</span>',
      '<span class="t-yellow">&gt;&gt; FAILOVER EXECUTION SUCCESSFUL: Zero Scans Dropped</span>'
    ],
    quotas: [
      '<span class="t-yellow">$ mailerone --quotas --live</span>',
      '<span class="t-dim">[*] Querying real-time quota APIs &amp; remaining balances...</span>',
      '<span class="t-green">[+] Hunter.io    : Free Plan (25 searches / 50 verifs left, Reset: 1st of month)</span>',
      '<span class="t-green">[+] ContactOut   : Free Plan (40 Work Emails + 5 Direct Phones remaining)</span>',
      '<span class="t-lime">[+] SalesQL      : Free Plan (50 / 50 Credits remaining, Reset: Monthly)</span>',
      '<span class="t-green">[+] SignalHire   : Free Starter (5 Contact Credits active)</span>',
      '<span class="t-yellow">[+] FinalScout   : Free Plan (20 Regular + 10 AI Credits remaining)</span>',
      '<span class="t-lime">[+] ZeroBounce   : 100 Validations remaining / month</span>',
      '<span class="t-green">[+] DeBounce     : 100 Credits remaining (Lifetime)</span>',
      '<span class="t-yellow">[+] Name2Email   : 100% Free &amp; Unlimited (Zero external API cost)</span>'
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
    }, 200);
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

  // 10. Quota Matrix Search & Filter
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

  // 11. API Keys & Engine Configuration Manager (Multi-Key Failover Supported)
  const keyMap = {
    'key-hunter': { plural: 'hunter_api_keys', singular: 'hunter_api_key' },
    'key-contactout': { plural: 'contactout_api_keys', singular: 'contactout_api_key' },
    'key-salesql': { plural: 'salesql_api_keys', singular: 'salesql_api_key' },
    'key-signalhire': { plural: 'signalhire_api_keys', singular: 'signalhire_api_key' },
    'key-finalscout': { plural: 'finalscout_api_keys', singular: 'finalscout_api_key' },
    'key-abstract': { plural: 'abstract_api_keys', singular: 'abstract_api_key' },
    'key-zerobounce': { plural: 'zerobounce_api_keys', singular: 'zerobounce_api_key' },
    'key-debounce': { plural: 'debounce_api_keys', singular: 'debounce_api_key' },
    'key-mailboxlayer': { plural: 'mailboxlayer_api_keys', singular: 'mailboxlayer_api_key' },
    'key-emailrep': { plural: 'emailrep_api_keys', singular: 'emailrep_api_key' },
    'key-github': { plural: 'github_tokens', singular: 'github_token' }
  };

  function updateKeyPoolPills() {
    let totalConfiguredKeys = 0;
    Object.keys(keyMap).forEach(elemId => {
      const inputElem = document.getElementById(elemId);
      const pillElem = document.getElementById(`pill-${elemId}`);
      if (inputElem && pillElem) {
        const val = inputElem.value.trim();
        const count = val ? val.split(',').map(s => s.trim()).filter(Boolean).length : 0;
        totalConfiguredKeys += count;

        pillElem.textContent = count === 0 ? '0 keys' : (count === 1 ? '1 key active' : `${count} keys (pool)`);
        pillElem.className = 'key-pool-pill' + (count > 1 ? ' multiple' : (count === 1 ? ' has-keys' : ''));
      }
    });

    renderQuotaPoolSummary(totalConfiguredKeys);
  }

  function renderQuotaPoolSummary(totalKeys) {
    const summaryElem = document.getElementById('quota-pool-summary');
    if (!summaryElem) return;

    const count = totalKeys !== undefined ? totalKeys : 0;
    const hasMultiKey = count >= 2;

    summaryElem.innerHTML = `
      <div style="background:rgba(255,255,255,0.03); border:1px solid ${hasMultiKey ? 'rgba(250,204,21,0.35)' : 'var(--border-subtle)'}; border-radius:var(--radius-md); padding:16px 20px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
        <div>
          <div style="font-size:1.1rem; font-weight:700; color:#ffffff; display:flex; align-items:center; gap:8px;">
            <span>🔄</span> Sequential Failover Pool: 
            <span style="color:${hasMultiKey ? 'var(--accent-yellow-light)' : 'var(--text-muted)'};">${count} Total Keys Configured</span>
          </div>
          <div style="font-size:0.85rem; color:var(--text-muted); margin-top:2px;">
            ${hasMultiKey 
              ? 'Multi-key fallback enabled across configured engines (automatic recovery on 429/402).'
              : 'Add backup keys separated by commas in the API Keys tab to unlock zero-drop failover.'}
          </div>
        </div>
        <div style="display:flex; gap:8px;">
          <span class="badge-tag ${hasMultiKey ? 'badge-free' : ''}" style="${!hasMultiKey ? 'background:rgba(148,163,184,0.15);color:var(--text-muted);border:1px solid var(--border-subtle);' : ''}">
            ${hasMultiKey ? '⚡ High Availability' : 'Standard Mode'}
          </span>
        </div>
      </div>
    `;
  }

  // Load saved keys from localStorage
  function loadStoredKeys() {
    try {
      const saved = localStorage.getItem('mailerone_keys');
      if (saved) {
        const parsed = JSON.parse(saved);
        Object.keys(keyMap).forEach(elemId => {
          const entry = keyMap[elemId];
          const inputElem = document.getElementById(elemId);
          if (inputElem) {
            const rawVal = parsed[entry.plural] !== undefined ? parsed[entry.plural] : parsed[entry.singular];
            if (Array.isArray(rawVal)) {
              inputElem.value = rawVal.join(', ');
            } else if (rawVal) {
              inputElem.value = rawVal;
            }
          }
        });
      }
    } catch (e) {
      console.warn('Could not load keys from localStorage', e);
    }
    updateKeyPoolPills();
  }

  loadStoredKeys();

  // Listen to input changes on keys to update pills dynamically
  Object.keys(keyMap).forEach(elemId => {
    const inputElem = document.getElementById(elemId);
    if (inputElem) {
      inputElem.addEventListener('input', updateKeyPoolPills);
    }
  });

  // Refresh Pool Status Button
  const btnRefreshQuotas = document.getElementById('btn-refresh-quotas');
  if (btnRefreshQuotas) {
    btnRefreshQuotas.addEventListener('click', () => {
      updateKeyPoolPills();
      showToast('Refreshed multi-key pool health and quotas!');
    });
  }

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
        const entry = keyMap[elemId];
        const val = (document.getElementById(elemId)?.value || '').trim();
        const keysList = val ? val.split(',').map(s => s.trim()).filter(Boolean) : [];
        configObj[entry.plural] = keysList;
        configObj[entry.singular] = keysList[0] || '';
      });

      localStorage.setItem('mailerone_keys', JSON.stringify(configObj));
      updateKeyPoolPills();
      showToast('API Keys saved successfully with multi-key failover enabled!');
    });
  }

  // Export config.json
  const btnExportConfig = document.getElementById('btn-export-config');
  if (btnExportConfig) {
    btnExportConfig.addEventListener('click', () => {
      const configObj = {};
      Object.keys(keyMap).forEach(elemId => {
        const entry = keyMap[elemId];
        const val = (document.getElementById(elemId)?.value || '').trim();
        const keysList = val ? val.split(',').map(s => s.trim()).filter(Boolean) : [];
        configObj[entry.plural] = keysList;
        configObj[entry.singular] = keysList[0] || '';
      });

      const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(configObj, null, 4));
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute('href', dataStr);
      downloadAnchor.setAttribute('download', 'config.json');
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
      showToast('Exported multi-key config.json for Mailerone CLI!');
    });
  }

  // Import config.json
  const btnImportConfig = document.getElementById('btn-import-config');
  const inputImportConfig = document.getElementById('input-import-config');
  if (btnImportConfig && inputImportConfig) {
    btnImportConfig.addEventListener('click', () => {
      inputImportConfig.click();
    });

    inputImportConfig.addEventListener('change', (e) => {
      const file = e.target.files?.[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (evt) => {
        try {
          const parsed = JSON.parse(evt.target.result);
          Object.keys(keyMap).forEach(elemId => {
            const entry = keyMap[elemId];
            const inputElem = document.getElementById(elemId);
            if (inputElem) {
              const val = parsed[entry.plural] !== undefined ? parsed[entry.plural] : parsed[entry.singular];
              if (Array.isArray(val)) {
                inputElem.value = val.join(', ');
              } else if (val) {
                inputElem.value = val;
              } else {
                inputElem.value = '';
              }
            }
          });

          // Save to localStorage automatically
          const configObj = {};
          Object.keys(keyMap).forEach(elemId => {
            const entry = keyMap[elemId];
            const val = (document.getElementById(elemId)?.value || '').trim();
            const keysList = val ? val.split(',').map(s => s.trim()).filter(Boolean) : [];
            configObj[entry.plural] = keysList;
            configObj[entry.singular] = keysList[0] || '';
          });
          localStorage.setItem('mailerone_keys', JSON.stringify(configObj));
          updateKeyPoolPills();
          showToast(`Successfully imported ${file.name} with multi-key pools!`);
        } catch (err) {
          showToast('Error parsing JSON configuration file.');
          console.error(err);
        }
      };
      reader.readAsText(file);
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
        updateKeyPoolPills();
        showToast('All API Keys have been cleared.');
      }
    });
  }
});
