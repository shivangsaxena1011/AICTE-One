/**
 * Automated test suite for AICTE ONE frontend modules in headless environment
 */
const fs = require('fs');
const path = require('path');

// Mock browser globals
global.window = global;
global.localStorage = {
  store: {},
  getItem(k) { return this.store[k] || null; },
  setItem(k, v) { this.store[k] = String(v); },
  removeItem(k) { delete this.store[k]; },
  clear() { this.store = {}; }
};

global.document = {
  getElementById(id) {
    return {
      id,
      innerHTML: '',
      value: 'TEST_VAL',
      textContent: '',
      classList: {
        add() {},
        remove() {},
        contains() { return false; },
        toggle() {}
      },
      addEventListener() {},
      appendChild() {},
      querySelectorAll() { return []; }
    };
  },
  querySelectorAll() { return []; },
  createElement() {
    return {
      href: '',
      setAttribute() {},
      click() {},
      style: {},
      classList: { add() {}, remove() {} }
    };
  },
  body: {
    appendChild() {},
    removeChild() {},
    classList: { add() {}, remove() {} }
  },
  addEventListener() {}
};

global.location = {
  protocol: 'http:',
  origin: 'http://localhost:8000',
  hash: '#/overview'
};

global.URL = {
  createObjectURL() { return 'blob:mock-url'; },
  revokeObjectURL() {}
};

global.Blob = function(content, opts) { this.content = content; this.opts = opts; };

// Load modules in order
const basePath = path.join(__dirname, '..', 'aicte-one-prototype', 'assets', 'js');
require(path.join(basePath, 'data.js'));
require(path.join(basePath, 'utils', 'api.js'));
require(path.join(basePath, 'utils', 'csv.js'));

const modules = [
  'overview.js',
  'institutions.js',
  'digitalTwin.js',
  'applications.js',
  'scrutiny.js',
  'evc.js',
  'verification.js',
  'compliance.js',
  'complaints.js',
  'coordination.js',
  'tasks.js',
  'graph.js',
  'copilot.js',
  'reports.js',
  'notifications.js',
  'audit.js',
  'settings.js'
];

modules.forEach(m => {
  require(path.join(basePath, 'modules', m));
});

require(path.join(basePath, 'app.js'));

async function runTests() {
  console.log('--- Testing AICTE ONE Frontend Modules Execution ---');
  let passed = 0;
  let failed = 0;

  for (const key of Object.keys(App.modules)) {
    try {
      const modGetter = App.modules[key];
      const mod = modGetter();
      if (!mod || typeof mod.render !== 'function') {
        throw new Error(`Module '${key}' missing render function`);
      }
      const res = await mod.render('main-content', {});
      console.log(`[PASS] Module '${key}' rendered successfully.`);
      passed++;
    } catch (err) {
      console.error(`[FAIL] Module '${key}' failed with error:`, err);
      failed++;
    }
  }

  // Test CSV Utility
  try {
    const csvParsed = CSVUtil.parseCSV("Permanent ID,Institution Name,State\n1-100,Test Tech,Delhi");
    if (csvParsed.length !== 1 || csvParsed[0]['Institution Name'] !== 'Test Tech') {
      throw new Error('CSV parsing mismatch');
    }
    console.log('[PASS] CSV parser and validator verified.');
    passed++;
  } catch (e) {
    console.error('[FAIL] CSV parser error:', e);
    failed++;
  }

  console.log(`\nResults: ${passed} passed, ${failed} failed.`);
  if (failed > 0) process.exit(1);
}

runTests();
