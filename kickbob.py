"""
קיקבוב (KickBob) - PRE ALPHA 0.0.4
תוכנת שולחן עבודה לצפייה בסטרימים העבריים של Kick:
דפדפן קטן בסגנון Chrome (סימניות, ערוצים מועדפים, התראות שידור, היסטוריית צפייה עם ייצוא, עדכון אוטומטי, מד רמות, סמן ניאון, כולל מסגרת חלון משלו במקום זו של Windows), עם Kick בעברית (תרגום הממשק): חיפוש קליפים, כרטיסיות, סרגל עליון (ניווט + שורת כתובת עם חיפוש בגוגל), גלישה לכל אתר, כניסה דרך קיק,
סמן מותאם, רמות (XP לפי זמן צפייה), עיצוב אתר Kick (צבעים, גופן, CSS מותאם, שיתוף עיצובים בקוד), זמן שידור של סטרימר,
הגדרות בסגנון Chrome (מראה, פרטיות, מנוע חיפוש, הפעלה, רמות) ואודות.
"""
import ast
import csv
import html as htmllib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import webbrowser

APP_NAME = "קיקבוב"
VERSION = "PRE ALPHA 0.0.4"
HOME_URL = "https://kick.com/browse?sort=featured&languages=he"
FOLLOWING_URL = "https://kick.com/following"
ABOUT_TEXT = "התוכנה עשה EMUIO הסטרימר בקיק"
ABOUT_LINK = "https://kick.com/emuio"

# ---------------------------------------------------------------------------
# מה חדש / מה בדרך - אפשר לערוך כאן בחופשיות (מוצג בתוכנה ב"מה חדש ומה בדרך")
# ---------------------------------------------------------------------------
CHANGELOG = [
    {"v": "PRE ALPHA 0.0.4", "items": [
        "סימניות (Ctrl+D) ודף בית עם ערוצים מועדפים וסימניות",
        "התראות כשערוץ מועדף (או ערוץ שאתה עוקב אחריו) עולה לשידור",
        "היסטוריית צפייה מלאה עם ייצוא ל-CSV ול-JSON",
        "תרגום מורחב של Kick לעברית",
        "עדכון אוטומטי מ-GitHub, ותהליך שבונה EXE אוטומטית"]},
    {"v": "PRE ALPHA 0.0.3_3", "items": [
        "הצפייה שלי: כמה סטרימרים צפית בהם, כמה זמן, ומי המובילים",
        "מסך \"מה חדש ומה בדרך\" עם היסטוריית גרסאות ותוכניות לגרסה הבאה",
        "מסך אודות מורחב עם יכולות, קיצורי מקלדת ומידע על ההפעלה"]},
    {"v": "PRE ALPHA 0.0.3_2", "items": [
        "תפריט קיקבוב שנפתח מהאות K",
        "מסגרת כהה לכפתורי החלון (מזעור, הגדלה, סגירה)",
        "אייקון בית חדש"]},
    {"v": "PRE ALPHA 0.0.3_1", "items": ["מד רמות בסרגל ובחלון הרמות", "סמן ניאון עם כוונת, שובל ואפקט לחיצה"]},
    {"v": "PRE ALPHA 0.0.3", "items": ["חלון בסגנון Chrome במקום המסגרת של Windows", "אתר עם הורדה"]},
    {"v": "PRE ALPHA 0.0.2_3", "items": ["Kick בעברית: תרגום הממשק, מילון אישי ו\"טקסטים שעוד לא תורגמו\""]},
    {"v": "PRE ALPHA 0.0.2_2", "items": ["הגדרות בסגנון Chrome, בחירת מנוע חיפוש ודף פתיחה"]},
    {"v": "PRE ALPHA 0.0.2_1", "items": ["חיפוש קליפים", "מראה בסגנון Chrome"]},
    {"v": "PRE ALPHA 0.0.2", "items": ["כרטיסיות וגלישה לכל אתר", "חיפוש בגוגל", "מספר צופים בשידור"]},
    {"v": "PRE ALPHA 0.0.1_x", "items": ["עיצוב חופשי ל-Kick וקודי שיתוף", "זמן שידור של סטרימר"]},
    {"v": "PRE ALPHA 0.0.1", "items": ["סרגל עליון, חיפוש, רמות וסמן מותאם"]},
    {"v": "PRE ALPHA 0.0.0", "items": ["הגרסה הראשונה: Kick בחלון משלו עם כניסה לחשבון"]},
]
ROADMAP = {
    "next": "PRE ALPHA 0.0.5",
    "items": [
        "מצב תמונה בתוך תמונה",
        "הורדת קליפים",
        "גלריית עיצובים משותפת",
        "סנכרון הגדרות וסימניות בין מחשבים",
        "ערוצים מועדפים בקבוצות וסדר אישי"],
    "later": ["תוספים קטנים לקיקבוב", "מצב בהיר"],
}
INFO = {"changelog": CHANGELOG, "roadmap": ROADMAP}
TITLE = f"{APP_NAME} - {VERSION}"
DATA_DIR = os.path.join(os.path.expanduser("~"), ".kickbob")
WIPE_FLAG = os.path.join(os.path.expanduser("~"), ".kickbob_wipe")
LOG_FILE = os.path.join(os.path.expanduser("~"), "kickbob.log")
PROGRESS_FILE = os.path.join(DATA_DIR, "progress.json")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")
STYLE_FILE = os.path.join(DATA_DIR, "style.json")
# מצב בטוח: python kickbob.py --safe  (בלי חוסם פרסומות ובלי סמן מותאם)
SAFE_MODE = "--safe" in sys.argv
# מסגרת חלון רגילה של Windows במקום המסגרת בסגנון Chrome: python kickbob.py --framed
FRAMELESS = {"v": "--framed" not in sys.argv}


def log(msg):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# חסימת פרסומות/מעקבים + הגדרות פרטיות (רץ אחרי טעינת הדף)
# ---------------------------------------------------------------------------
BLOCKER_JS = r"""
(function () {
  if (window.__kbBlock) return;
  window.__kbBlock = true;

  var S = { adblock: true, privacy: true };
  try {
    var r = __SETTINGS__;
    if (r.adblock === false) S.adblock = false;
    if (r.privacy === false) S.privacy = false;
  } catch (e) {}

  var HOSTS = [
    'doubleclick.net', 'googlesyndication.com', 'googleadservices.com',
    'adservice.google.com', 'google-analytics.com', 'googletagmanager.com',
    'facebook.net', 'hotjar.com', 'segment.io', 'segment.com', 'mixpanel.com',
    'amplitude.com', 'taboola.com', 'outbrain.com', 'adnxs.com',
    'scorecardresearch.com', 'criteo.com', 'quantserve.com'
  ];
  function blocked(u) {
    try {
      var h = new URL(u, location.href).hostname;
      return HOSTS.some(function (x) { return h === x || h.slice(-(x.length + 1)) === '.' + x; });
    } catch (e) { return false; }
  }

  if (S.adblock) {
    // בקשות רשת עתידיות לדומיינים של פרסום/מעקב
    try {
      var of = window.fetch;
      window.fetch = function (input) {
        var u = (typeof input === 'string') ? input : (input && input.url);
        if (u && blocked(u)) return Promise.resolve(new Response('', { status: 204 }));
        return of.apply(this, arguments);
      };
    } catch (e) {}
    try {
      var oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send;
      XMLHttpRequest.prototype.open = function (m, u) { this.__kbBlocked = blocked(u); return oo.apply(this, arguments); };
      XMLHttpRequest.prototype.send = function () { if (this.__kbBlocked) return; return os.apply(this, arguments); };
    } catch (e) {}
    try {
      var ob = navigator.sendBeacon && navigator.sendBeacon.bind(navigator);
      if (ob) navigator.sendBeacon = function (u) { return blocked(u) ? true : ob.apply(null, arguments); };
    } catch (e) {}

    // הסרת סקריפטים/פריימים/תמונות שנוספים לדף
    try {
      var queue = [], timer = null;
      function flush() {
        timer = null;
        var batch = queue; queue = [];
        for (var i = 0; i < batch.length; i++) {
          var n = batch[i];
          if (n.src && blocked(n.src)) n.remove();
        }
      }
      new MutationObserver(function (muts) {
        for (var i = 0; i < muts.length; i++) {
          var added = muts[i].addedNodes;
          for (var j = 0; j < added.length; j++) {
            var n = added[j];
            if (n.nodeType === 1 && (n.tagName === 'SCRIPT' || n.tagName === 'IFRAME' || n.tagName === 'IMG')) queue.push(n);
          }
        }
        if (queue.length && !timer) timer = setTimeout(flush, 300);
      }).observe(document, { childList: true, subtree: true });
    } catch (e) {}

    // הסתרה קוסמטית של אלמנטי פרסומת מוכרים
    try {
      var css = 'ins.adsbygoogle, .adsbygoogle, iframe[src*="doubleclick"], iframe[src*="googlesyndication"], ' +
                'iframe[src*="adservice"], [id^="google_ads"], [data-ad-slot], [aria-label="Advertisement"], ' +
                '[aria-label="advertisement"] { display: none !important; }';
      var sh = new CSSStyleSheet(); sh.replaceSync(css);
      document.adoptedStyleSheets = document.adoptedStyleSheets.concat([sh]);
    } catch (e) {}
  }

  if (S.privacy) {
    // Do Not Track + Global Privacy Control
    try { Object.defineProperty(Navigator.prototype, 'doNotTrack', { get: function () { return '1'; }, configurable: true }); } catch (e) {}
    try { Object.defineProperty(Navigator.prototype, 'globalPrivacyControl', { get: function () { return true; }, configurable: true }); } catch (e) {}
  }
})();
"""

# ---------------------------------------------------------------------------
# הממשק: סרגל עליון בסגנון דפדפן - מוזרק אחרי טעינת כל דף
# ---------------------------------------------------------------------------
INJECT_JS = r"""
(function () {
  if (document.getElementById('kickbob-bar')) return;

  var BAR_H = 80, TAB_H = 38;
  var INFO = __INFO__;
  var CFG = __CFG__;   // הגדרות/עיצוב/התקדמות - נטענים מקבצים ב-Python, משותפים לכל האתרים והכרטיסיות
  function api() { try { return window.pywebview && window.pywebview.api; } catch (e) { return null; } }
  function persist(name, obj) {
    var str = JSON.stringify(obj);
    try { var a = api(); if (a && a.save_cfg) a.save_cfg(name, str); } catch (e) {}
    try { localStorage.setItem('kickbob_' + name, str); } catch (e) {}
  }
  function isKick() { return /(^|\.)kick\.com$/.test(location.hostname); }
  var THEMES = {
    green:  { name: 'ירוק Kick', c: '#53fc18' },
    purple: { name: 'סגול',      c: '#a970ff' },
    blue:   { name: 'כחול',      c: '#3b9cff' },
    red:    { name: 'אדום',      c: '#ff4d5e' },
    gold:   { name: 'זהב',       c: '#ffc400' }
  };
  var SET = Object.assign({ theme: 'green', adblock: true, privacy: true, cursor: true, startPage: 'kick', search: 'google', hebrew: false, hebrewAsked: false, rtl: false, dict: '', nativeFrame: false, cursorStyle: 'neon', cursorTrail: true, cursorRipple: true,
    notify: true, notifyFollowed: true, notifySound: true, homeButton: 'kick', autoUpdate: true, updateRepo: '' }, CFG.settings || {});
  if (!THEMES[SET.theme]) SET.theme = 'green';
  function saveSet() { persist('settings', SET); }
  var ENGINES = {
    google: { name: 'גוגל', url: 'https://www.google.com/search?hl=iw&q=' },
    bing:   { name: 'Bing', url: 'https://www.bing.com/search?setlang=he&q=' },
    ddg:    { name: 'DuckDuckGo', url: 'https://duckduckgo.com/?kl=il-he&q=' }
  };
  function engine() { return ENGINES[SET.search] || ENGINES.google; }

  var GREEN = THEMES[SET.theme].c;           // צבע הדגש הנוכחי
  var BORDER = '#2a2a2e';
  var HOME = '__HOME__', FOLLOWING = '__FOLLOWING__';
  var SAFE = __SAFE__;
  var FRAMELESS = CFG.frameless === true;   // מסגרת החלון מצוירת על ידי קיקבוב (כמו Chrome)

  // ---------- עזר: גיליונות סגנון (עובדים גם תחת CSP) ----------
  function addSheet(css) {
    try {
      var sh = new CSSStyleSheet(); sh.replaceSync(css);
      document.adoptedStyleSheets = document.adoptedStyleSheets.concat([sh]);
      return { remove: function () {
        document.adoptedStyleSheets = document.adoptedStyleSheets.filter(function (x) { return x !== sh; });
      } };
    } catch (e) {
      var st = document.createElement('style'); st.textContent = css;
      document.documentElement.appendChild(st);
      return { remove: function () { st.remove(); } };
    }
  }

  function mk(label, title, fn, accent) {
    var b = document.createElement('button');
    b.textContent = label; b.title = title || label;
    Object.assign(b.style, {
      background: accent ? GREEN : '#3c4043', color: accent ? '#000' : '#e8eaed',
      border: 'none', borderRadius: '16px',
      padding: '0 14px', height: '32px', cursor: 'pointer', fontWeight: '600', fontSize: '13px',
      fontFamily: 'inherit', whiteSpace: 'nowrap', flex: '0 0 auto'
    });
    b.onmouseenter = function () { if (!accent) b.style.background = '#4a4d51'; };
    b.onmouseleave = function () { if (!accent) b.style.background = '#3c4043'; };
    b.onclick = fn;
    return b;
  }
  // כפתור עגול שטוח כמו בכרום
  function flat(label, title, fn) {
    var b = document.createElement('button');
    b.textContent = label; b.title = title || label;
    Object.assign(b.style, {
      background: 'transparent', color: '#e8eaed', border: 'none', borderRadius: '50%',
      width: '32px', height: '32px', padding: '0', cursor: 'pointer', fontSize: '16px',
      display: 'inline-flex', alignItems: 'center', justifyContent: 'center', flex: '0 0 auto', fontFamily: 'inherit'
    });
    b.onmouseenter = function () { b.style.background = '#4a4d51'; };
    b.onmouseleave = function () { b.style.background = 'transparent'; };
    b.onclick = fn;
    return b;
  }
  function icoBtn(d, title, fn) {
    var b = flat('', title, fn);
    var NS = 'http://www.w3.org/2000/svg';
    var svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('viewBox', '0 0 24 24'); svg.setAttribute('width', '20'); svg.setAttribute('height', '20');
    var pth = document.createElementNS(NS, 'path'); pth.setAttribute('d', d); pth.setAttribute('fill', '#e8eaed');
    svg.appendChild(pth); b.appendChild(svg);
    return b;
  }

  // ---------- חלון קופץ כללי ----------
  function openModal(id, build) {
    if (document.getElementById(id)) return;
    var ov = document.createElement('div');
    ov.id = id; ov.setAttribute('dir', 'rtl');
    Object.assign(ov.style, {
      position: 'fixed', inset: '0', background: 'rgba(0,0,0,0.7)', zIndex: '2147483647',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontFamily: 'Segoe UI, Arial, sans-serif'
    });
    var box = document.createElement('div');
    Object.assign(box.style, {
      background: '#0e0e10', color: '#fff', border: '2px solid ' + GREEN,
      borderRadius: '16px', padding: '24px 30px', width: '460px', maxWidth: '92vw',
      maxHeight: '90vh', overflowY: 'auto', textAlign: 'center',
      boxShadow: '0 10px 40px rgba(0,0,0,0.6)'
    });
    function line(txt, css) {
      var d = document.createElement('div'); d.textContent = txt;
      Object.assign(d.style, css || {}); box.appendChild(d); return d;
    }
    build(box, line, function () { ov.remove(); });
    ov.appendChild(box);
    ov.onclick = function (e) { if (e.target === ov) ov.remove(); };
    document.documentElement.appendChild(ov);
  }

  // ---------- אודות ----------
  function showAbout() {
    openModal('kickbob-about', function (box, line, close) {
      box.style.width = '520px';
      line('קיקבוב', { color: GREEN, fontSize: '32px', fontWeight: '800' });
      var vp = line('__VERSION__', { display: 'inline-block', border: '1px solid ' + GREEN, color: GREEN, borderRadius: '12px', padding: '2px 12px', fontSize: '12px', direction: 'ltr', margin: '6px 0 12px' });
      line('דפדפן קטן לצפייה בסטרימים העבריים של Kick', { fontSize: '15px', color: '#d6d6da', marginBottom: '14px' });
      line('__ABOUT_TEXT__', { fontSize: '15px', fontWeight: '700', marginBottom: '4px' });
      var a = document.createElement('a');
      a.textContent = '__ABOUT_LINK__'; a.href = '__ABOUT_LINK__';
      Object.assign(a.style, { color: GREEN, direction: 'ltr', display: 'inline-block', marginBottom: '16px' });
      box.appendChild(a);

      function sec(title) { line(title, { fontWeight: '700', textAlign: 'right', margin: '12px 0 6px', borderTop: '1px solid #26262c', paddingTop: '12px' }); }
      sec('מה יש בפנים');
      ['כרטיסיות, שורת כתובת וחיפוש בגוגל', 'מספר צופים וזמן שידור של סטרימר', 'חיפוש קליפים', 'רמות, מד התקדמות ו"הצפייה שלי"',
       'עיצוב חופשי ל-Kick וקודי שיתוף', 'Kick בעברית (תרגום הממשק)', 'חסימת פרסומות והגדרות פרטיות', 'חלון וסמן בסגנון Chrome וניאון'].forEach(function (t) {
        line('• ' + t, { fontSize: '13px', color: '#b9b9c0', textAlign: 'right', margin: '2px 0' });
      });
      sec('קיצורי מקלדת');
      line('Ctrl+T כרטיסייה חדשה · Ctrl+W סגירה · Ctrl+Tab מעבר · Ctrl+L שורת כתובת · Ctrl+Shift+Z כיבוי חירום של עיצוב Kick',
           { fontSize: '12px', color: '#9aa0a6', textAlign: 'right', lineHeight: '1.7' });
      sec('מידע על ההפעלה');
      var info = [['מסגרת החלון', FRAMELESS ? 'בסגנון Chrome' : 'רגילה של Windows'], ['תרגום Kick לעברית', heOn ? 'פעיל' : 'כבוי'],
                  ['מצב בטוח', SAFE ? 'כן' : 'לא'], ['צבע דגש', THEMES[SET.theme].name], ['מנוע חיפוש', engine().name]];
      info.forEach(function (kv) {
        var r = document.createElement('div'); Object.assign(r.style, { display: 'flex', justifyContent: 'space-between', fontSize: '13px', margin: '3px 0' });
        var k = document.createElement('span'); k.textContent = kv[0]; k.style.color = '#9aa0a6';
        var v = document.createElement('span'); v.textContent = kv[1];
        r.appendChild(k); r.appendChild(v); box.appendChild(r);
      });
      line('זו גרסת PRE ALPHA: יכולים להיות באגים. קובץ הלוג: kickbob.log בתיקיית המשתמש.', { fontSize: '11px', color: '#777', margin: '14px 0' });
      var row = document.createElement('div'); Object.assign(row.style, { display: 'flex', gap: '8px', justifyContent: 'center', flexWrap: 'wrap' });
      row.appendChild(mk('מה חדש ומה בדרך', 'היסטוריית גרסאות ותוכניות', function () { close(); showRoadmap('new'); }));
      row.appendChild(mk('הצפייה שלי', 'סטטיסטיקות צפייה', function () { close(); showWatched(); }));
      row.appendChild(mk('סגור', 'סגור', close, true));
      box.appendChild(row);
    });
  }

  // ---------- הגדרות: דף מלא בסגנון הגדרות של Chrome ----------
  function showSettings(restoreScroll) {
    if (document.getElementById('kickbob-settings')) return;
    var C = { bg: '#202124', card: '#292a2d', line: '#3c4043', text: '#e8eaed', sub: '#9aa0a6' };
    function h(tag, css, text) {
      var e = document.createElement(tag);
      if (css) Object.assign(e.style, css);
      if (text !== undefined) e.textContent = text;
      return e;
    }
    function reloadKeepOpen() {
      try { sessionStorage.setItem('kb_reopen', String(ov.scrollTop || 0)); } catch (e) {}
      location.reload();
    }
    var ov = h('div', { position: 'fixed', top: BAR_H + 'px', left: '0', right: '0', bottom: '0', background: C.bg, color: C.text,
      zIndex: '2147483645', overflow: 'auto', fontFamily: "'Segoe UI', Arial, sans-serif", fontSize: '14px' });
    ov.id = 'kickbob-settings'; ov.setAttribute('dir', 'rtl');
    function modalOpen() {
      return ['kickbob-style', 'kickbob-levels', 'kickbob-clips', 'kickbob-stream', 'kickbob-about', 'kickbob-dict', 'kickbob-untr', 'kickbob-lang', 'kickbob-watched', 'kickbob-roadmap', 'kickbob-bm', 'kickbob-fav', 'kickbob-hist', 'kickbob-upd'].some(function (i) { return document.getElementById(i); });
    }
    function closeAll() { ov.remove(); document.removeEventListener('keydown', onKey, true); }
    function onKey(e) {
      if (e.key === 'Escape' && !modalOpen() && !(e.target && e.target.tagName === 'INPUT' && e.target.value)) closeAll();
    }
    document.addEventListener('keydown', onKey, true);

    // ----- רכיבים -----
    function toggle(on, fn) {
      var t = h('div', { width: '36px', height: '14px', borderRadius: '7px', position: 'relative', cursor: 'pointer', flex: '0 0 auto', transition: 'background .15s' });
      t.setAttribute('dir', 'ltr');
      var k = h('div', { position: 'absolute', top: '-3px', width: '20px', height: '20px', borderRadius: '50%', transition: 'left .15s', boxShadow: '0 1px 3px rgba(0,0,0,0.6)' });
      t.appendChild(k);
      function paint() { t.style.background = on ? GREEN + '88' : '#5f6368'; k.style.background = on ? GREEN : '#bdc1c6'; k.style.left = on ? '16px' : '0px'; }
      paint();
      t.onclick = function () { on = !on; paint(); fn(on); };
      return t;
    }
    function obtn(label, fn, danger) {
      var col = danger ? '#f28b82' : GREEN;
      var b = h('button', { background: 'transparent', color: col, border: '1px solid #5f6368', borderRadius: '18px', padding: '0 16px', height: '36px',
        cursor: 'pointer', fontSize: '14px', fontFamily: 'inherit', fontWeight: '500', whiteSpace: 'nowrap', flex: '0 0 auto' }, label);
      b.onmouseenter = function () { b.style.background = col + '1a'; };
      b.onmouseleave = function () { b.style.background = 'transparent'; };
      b.onclick = fn;
      return b;
    }
    function radio(selected) {
      var o = h('div', { width: '18px', height: '18px', borderRadius: '50%', boxSizing: 'border-box', flex: '0 0 auto',
        border: '2px solid ' + (selected ? GREEN : C.sub), display: 'flex', alignItems: 'center', justifyContent: 'center' });
      if (selected) o.appendChild(h('div', { width: '8px', height: '8px', borderRadius: '50%', background: GREEN }));
      return o;
    }
    function row(title, desc, control, onClick) {
      var r = h('div', { display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '16px', padding: '14px 20px',
        borderTop: '1px solid ' + C.line, minHeight: '28px', cursor: onClick ? 'pointer' : 'default' });
      var left = h('div', { flex: '1', minWidth: '0' });
      left.appendChild(h('div', null, title));
      if (desc) left.appendChild(h('div', { fontSize: '12px', color: C.sub, marginTop: '3px', lineHeight: '1.5' }, desc));
      r.appendChild(left);
      if (control) r.appendChild(control);
      if (onClick) {
        r.onclick = onClick;
        r.onmouseenter = function () { r.style.background = 'rgba(255,255,255,0.04)'; };
        r.onmouseleave = function () { r.style.background = 'transparent'; };
      }
      r.kbText = (title + ' ' + (desc || '')).toLowerCase();
      return r;
    }

    // ----- מבנה הדף -----
    var head = h('div', { position: 'sticky', top: '0', zIndex: '3', background: C.card, borderBottom: '1px solid ' + C.line,
      display: 'flex', alignItems: 'center', gap: '24px', padding: '0 24px', height: '64px', boxSizing: 'border-box' });
    head.appendChild(h('div', { fontSize: '22px', fontWeight: '500', flex: '0 0 auto' }, 'הגדרות'));
    var search = h('input', { flex: '1', maxWidth: '560px', height: '40px', boxSizing: 'border-box', background: C.bg, color: C.text,
      border: '1px solid transparent', borderRadius: '20px', padding: '0 18px', outline: 'none', fontSize: '14px', fontFamily: 'inherit' });
    search.type = 'text'; search.placeholder = 'חפש בהגדרות';
    search.onfocus = function () { search.style.borderColor = GREEN; };
    search.onblur = function () { search.style.borderColor = 'transparent'; };
    ['keydown', 'keypress', 'keyup'].forEach(function (ev) { search.addEventListener(ev, function (e) { e.stopPropagation(); }); });
    head.appendChild(search);
    var xb = flat('✕', 'סגור (Esc)', closeAll); xb.style.marginInlineStart = 'auto';
    head.appendChild(xb);
    ov.appendChild(head);

    var layout = h('div', { display: 'flex', gap: '32px', maxWidth: '1100px', margin: '0 auto', padding: '24px', alignItems: 'flex-start', boxSizing: 'border-box' });
    var side = h('div', { width: '230px', flex: '0 0 auto', position: 'sticky', top: '88px' });
    var main = h('div', { flex: '1', minWidth: '0', maxWidth: '720px' });
    layout.appendChild(side); layout.appendChild(main); ov.appendChild(layout);

    var secs = [];
    function section(id, label, icon) {
      var wrap = h('div', { marginBottom: '28px' });
      wrap.appendChild(h('div', { fontSize: '14px', fontWeight: '500', margin: '0 4px 10px' }, label));
      var card = h('div', { background: C.card, borderRadius: '10px', overflow: 'hidden' });
      wrap.appendChild(card);
      var s = { id: id, label: label, icon: icon, wrap: wrap, rows: [] };
      s.add = function (r) { if (!s.rows.length) r.style.borderTop = 'none'; s.rows.push(r); card.appendChild(r); };
      secs.push(s); main.appendChild(wrap);
      return s;
    }

    // ===== מראה =====
    var sA = section('appearance', 'מראה', '🎨');
    var swWrap = h('div', { display: 'flex', gap: '10px', flex: '0 0 auto' });
    Object.keys(THEMES).forEach(function (k) {
      var sw = h('div', { width: '26px', height: '26px', borderRadius: '50%', background: THEMES[k].c, cursor: 'pointer', boxSizing: 'border-box',
        border: k === SET.theme ? '3px solid #fff' : '3px solid transparent' });
      sw.title = THEMES[k].name;
      sw.onclick = function () { SET.theme = k; saveSet(); reloadKeepOpen(); };
      swWrap.appendChild(sw);
    });
    sA.add(row('צבע דגש של קיקבוב', 'משנה את צבעי הסרגל, הסמן והחלונות של קיקבוב (לא של אתר Kick עצמו).', swWrap));
    sA.add(row('מסגרת חלון בסגנון Chrome', 'כשהאפשרות פעילה, קיקבוב מצייר בעצמו את שורת הכותרת וכפתורי החלון במקום המסגרת הרגילה של Windows. נכנס לתוקף בהפעלה הבאה. אם יש בעיה בגרירה או בשינוי גודל, כבה את זה.',
      toggle(SET.nativeFrame !== true, function (v) { SET.nativeFrame = !v; saveSet(); toast('יחול בהפעלה הבאה של קיקבוב'); })));
    [['neon', 'סמן ניאון (חדש)', 'חץ זוהר עם כוונת מעל כפתורים וקישורים.'], ['classic', 'סמן קלאסי', 'החץ הפשוט מהגרסאות הקודמות.']].forEach(function (o) {
      var r = row(o[1], o[2], radio(CUR_STYLE === o[0]), function () { SET.cursorStyle = o[0]; saveSet(); reloadKeepOpen(); });
      r.insertBefore(r.lastChild, r.firstChild);
      sA.add(r);
    });
    sA.add(row('שובל אחרי הסמן', 'קו זוהר שנמשך אחרי העכבר (כשסמן קיקבוב פעיל).', toggle(SET.cursorTrail !== false, function (v) { SET.cursorTrail = v; saveSet(); })));
    sA.add(row('אפקט לחיצה', 'גל זוהר קטן בכל לחיצה (כשסמן קיקבוב פעיל).', toggle(SET.cursorRipple !== false, function (v) { SET.cursorRipple = v; saveSet(); })));
    sA.add(row('סמן עכבר של קיקבוב', 'חץ בצבע הדגש שהופך ללבן מעל כפתורים וקישורים.', toggle(cursorOn, function (v) {
      cursorOn = v; SET.cursor = v; saveSet(); applyCursor();
    })));

    // ===== עיצוב Kick =====
    var sK = section('kickstyle', 'עיצוב Kick', '🖌️');
    sK.add(row('עיצוב אתר Kick פעיל', 'מפעיל או מכבה את כל ההתאמות של צבעים, גופן ו-CSS באתר Kick.', toggle(STY.on, function (v) {
      STY.on = v; saveSty(); applyStyle();
    })));
    var summary = [];
    if (STY.bg) summary.push('רקע ' + STY.bg);
    if (STY.accent) summary.push('דגש ' + STY.accent);
    if (STY.css) summary.push('CSS מותאם');
    sK.add(row('עורך העיצוב', summary.length ? 'כרגע: ' + summary.join(' · ') : 'סגנונות מוכנים, צבעים, גופן, CSS וקוד עיצוב לשיתוף עם חברים.',
      obtn('פתח עורך', function () { showStyle(); })));

    // ===== סימניות ומועדפים =====
    var sBm = section('bookmarks', 'סימניות ומועדפים', '🔖');
    sBm.add(row('סימניות', 'נשמרות עם Ctrl+D או בכוכב בשורת הכתובת. כרגע: ' + BM.length, obtn('נהל', function () { showBookmarks(); })));
    sBm.add(row('ערוצים מועדפים', 'מוצגים בדף הבית ומשמשים להתראות. כרגע: ' + FAV.length, obtn('נהל', function () { showFavorites(); })));
    sBm.add(row('כפתור הבית פותח', 'מה ייפתח כשלוחצים על אייקון הבית בסרגל.',
      obtn(SET.homeButton === 'mine' ? 'דף הבית שלי' : 'Kick בעברית', function () { SET.homeButton = SET.homeButton === 'mine' ? 'kick' : 'mine'; saveSet(); reloadKeepOpen(); })));

    // ===== התראות שידור =====
    var sNt = section('notify', 'התראות שידור', '🔔');
    sNt.add(row('התראה כשערוץ מועדף עולה לשידור', 'חלון רקע מוסתר בודק אחת לדקה. התראת Windows + צליל + הבהוב בשורת המשימות.',
      toggle(SET.notify !== false, function (v) { SET.notify = v; saveSet(); })));
    sNt.add(row('כולל ערוצים שאני עוקב אחריהם ב-Kick (ניסיוני)', 'משתמש ברשימת המעקב של החשבון שלך. אם Kick ישנה את הממשק שלו, זה עלול להפסיק לעבוד.',
      toggle(SET.notifyFollowed !== false, function (v) { SET.notifyFollowed = v; saveSet(); })));
    sNt.add(row('צליל התראה', '', toggle(SET.notifySound !== false, function (v) { SET.notifySound = v; saveSet(); })));
    sNt.add(row('בדיקת התראה', 'שולח עכשיו התראת ניסיון.', obtn('שלח', function () {
      var a = api(); if (a && a.notify) a.notify(JSON.stringify({ key: 'test:' + Date.now(), title: '🔔 בדיקת התראה', body: 'ככה ייראו ההתראות של קיקבוב', url: '' }));
    })));

    // ===== היסטוריית צפייה =====
    var sHs = section('history', 'היסטוריית צפייה', '🕘');
    sHs.add(row('היסטוריית צפייה', 'לפי יום וערוץ, עם חיפוש וייצוא ל-CSV ול-JSON. קיצור: Ctrl+H.', obtn('פתח', function () { showHistory(); })));

    // ===== עדכונים =====
    var sUp = section('updates', 'עדכונים', '⬆️');
    var srcIn = fieldCss(h('input')); srcIn.type = 'text'; srcIn.setAttribute('dir', 'ltr'); srcIn.value = SET.updateRepo || ''; srcIn.placeholder = 'owner/repo'; srcIn.style.width = '210px';
    ['keydown', 'keypress', 'keyup'].forEach(function (ev) { srcIn.addEventListener(ev, function (e) { e.stopPropagation(); }); });
    srcIn.onchange = function () { SET.updateRepo = srcIn.value.trim(); saveSet(); };
    sUp.add(row('מקור העדכונים', 'מאגר GitHub בצורה owner/repo (העדכון נלקח מ-Releases) או קישור לקובץ JSON. הגדר רק מקור שאתה סומך עליו.', srcIn));
    sUp.add(row('בדוק עדכונים אוטומטית', 'בדיקה ברקע כל כמה שעות. עדכון מתבצע רק באישור שלך.', toggle(SET.autoUpdate !== false, function (v) { SET.autoUpdate = v; saveSet(); })));
    var upMsg = h('div', { fontSize: '12px', color: '#fdd663', marginTop: '6px' });
    var upRow = row('הגרסה שלך', '__VERSION__', obtn('בדוק עכשיו', function () {
      SET.updateRepo = srcIn.value.trim(); saveSet(); upMsg.textContent = 'בודק...';
      setTimeout(function () {
        var a = api(); if (!a || !a.check_update) { upMsg.textContent = 'זמין רק בתוך התוכנה.'; return; }
        a.check_update().then(function (s) {
          var r = {}; try { r = JSON.parse(s); } catch (e) {}
          upMsg.textContent = !r.ok ? (r.error === 'no_source' ? 'לא הוגדר מקור עדכונים.' : 'הבדיקה נכשלה: ' + (r.error || ''))
            : (r.newer ? 'יש גרסה חדשה: ' + r.latest : 'אתה על הגרסה העדכנית.');
          if (r.ok && r.newer) showUpdate(r);
        });
      }, 700);
    }));
    upRow.firstChild.appendChild(upMsg);
    sUp.add(upRow);

    // ===== שפה =====
    var sLg = section('language', 'שפה: Kick בעברית', '🌐');
    sLg.add(row('תרגם את הממשק של Kick לעברית', 'תרגום אוטומטי של כפתורים, תפריטים וכותרות נפוצים באתר. הצ׳אט ושמות הסטרימרים לא מתורגמים.',
      toggle(SET.hebrew === true, function (v) { SET.hebrew = v; SET.hebrewAsked = true; saveSet(); reloadKeepOpen(); })));
    sLg.add(row('פריסה מימין לשמאל (ניסיוני)', 'הופך את כיוון הטקסט באתר. ייתכן שחלק מהאלמנטים לא יסתדרו יפה.',
      toggle(SET.rtl === true, function (v) { SET.rtl = v; saveSet(); reloadKeepOpen(); })));
    sLg.add(row('מילון תרגומים אישי', 'הוסף או תקן תרגומים בעצמך. כל שורה: English = עברית.', obtn('פתח עורך', function () { showDict(); })));
    sLg.add(row('טקסטים שעוד לא תורגמו', 'רשימת טקסטים באנגלית שנמצאו באתר, שאפשר להעביר למילון האישי.', obtn('הצג', function () { showUntranslated(); })));

    // ===== מנוע חיפוש =====
    var sS = section('search', 'מנוע חיפוש', '🔍');
    Object.keys(ENGINES).forEach(function (k) {
      var r = row(ENGINES[k].name, k === 'google' ? 'ברירת המחדל. הקלדה של @ערוץ בשורת הכתובת פותחת ערוץ ב-Kick.' : '', radio(SET.search === k || (!SET.search && k === 'google')), function () {
        SET.search = k; saveSet(); reloadKeepOpen();
      });
      r.insertBefore(r.lastChild, r.firstChild);   // הרדיו בצד ההתחלה, כמו ב-Chrome
      sS.add(r);
    });

    // ===== בעת ההפעלה =====
    var sO = section('startup', 'בעת ההפעלה', '⏻');
    [['newtab', 'דף הבית שלי', 'חיפוש, ערוצים מועדפים וסימניות.'], ['kick', 'פתח את Kick בעברית', 'סטרימים בעברית שמוצגים עכשיו באתר.']].forEach(function (o) {
      var r = row(o[1], o[2], radio(SET.startPage === o[0]), function () { SET.startPage = o[0]; saveSet(); reloadKeepOpen(); });
      r.insertBefore(r.lastChild, r.firstChild);
      sO.add(r);
    });

    // ===== פרטיות ואבטחה =====
    var sP = section('privacy', 'פרטיות ואבטחה', '🔒');
    sP.add(row('חסימת פרסומות ומעקבים', 'חוסם בקשות לדומיינים מוכרים של פרסום ומעקב ומסתיר אלמנטי פרסומת. עובד על מה שנטען אחרי שהממשק עלה.',
      toggle(SET.adblock, function (v) { SET.adblock = v; saveSet(); reloadKeepOpen(); })));
    sP.add(row('שלח בקשת "אל תעקוב"', 'שולח לאתרים אות Do Not Track ו-Global Privacy Control.',
      toggle(SET.privacy, function (v) { SET.privacy = v; saveSet(); reloadKeepOpen(); })));
    var clrMsg = h('div', { fontSize: '12px', color: '#fdd663', marginTop: '6px' });
    var armed = false, clrTimer = null;
    var clrBtn = obtn('מחק נתוני גלישה...', function () {
      if (!armed) {
        armed = true; clrBtn.textContent = 'לחץ שוב לאישור';
        clrTimer = setTimeout(function () { armed = false; clrBtn.textContent = 'מחק נתוני גלישה...'; }, 3500);
        return;
      }
      clearTimeout(clrTimer); armed = false; clrBtn.textContent = 'מחק נתוני גלישה...';
      try { localStorage.clear(); sessionStorage.clear(); } catch (e) {}
      try {
        document.cookie.split(';').forEach(function (c) {
          var n = c.split('=')[0].trim();
          document.cookie = n + '=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/';
        });
      } catch (e) {}
      var ok = false;
      try { var a = api(); if (a && a.clear_data) { a.clear_data(); ok = true; } } catch (e) {}
      clrMsg.textContent = ok ? 'העוגיות, החיבור לחשבון וההתקדמות ברמות יימחקו סופית. סגור את קיקבוב והפעל מחדש.'
                              : 'נוקו הנתונים הגלויים לדף. סגור והפעל מחדש כדי לנקות הכול.';
    }, true);
    var clrRow = row('מחק נתוני גלישה', 'עוגיות, חיבור שמור ל-Kick והתקדמות ברמות.', clrBtn);
    clrRow.firstChild.appendChild(clrMsg);
    sP.add(clrRow);

    // ===== רמות =====
    var sL = section('levels', 'רמות', '⭐');
    var lv = levelFor(P.xp), lo = need(lv), hi = need(lv + 1);
    var lvInfo = h('div', { flex: '1', minWidth: '0' });
    var barBg = h('div', { height: '8px', background: C.line, borderRadius: '4px', overflow: 'hidden', margin: '10px 0 6px' });
    barBg.appendChild(h('div', { height: '100%', width: Math.min(100, Math.round((P.xp - lo) / (hi - lo) * 100)) + '%', background: GREEN }));
    var mins = Math.floor(P.seconds / 60);
    var lrow = row('רמה ' + lv + ' - ' + rankFor(lv), P.xp + ' / ' + hi + ' XP · זמן צפייה: ' + Math.floor(mins / 60) + ' שעות ו-' + (mins % 60) + ' דקות',
      obtn('פרטים', function () { showLevels(); }));
    lrow.firstChild.appendChild(barBg);
    sL.add(lrow);
    var wl = watchedList();
    sL.add(row('הצפייה שלי', 'צפית ב-' + wl.length + ' סטרימרים' + (wl[0] ? ' · המוביל: ' + wl[0].name : ''), obtn('פתח', function () { showWatched(); })));

    // ===== אודות =====
    var sAb = section('about', 'אודות קיקבוב', 'ℹ️');
    var ver = h('div', { color: C.sub, direction: 'ltr', textAlign: 'right', fontSize: '13px' }, '__VERSION__');
    sAb.add(row('קיקבוב', 'דפדפן קטן לצפייה בסטרימים העבריים של Kick.', ver));
    sAb.add(row('מה חדש ומה בדרך', 'היסטוריית גרסאות ותוכניות לגרסה הבאה (' + ((INFO.roadmap && INFO.roadmap.next) || '') + ').', obtn('פתח', function () { showRoadmap('new'); })));
    sAb.add(row('מידע על התוכנה', 'יכולות, קיצורי מקלדת ופרטי ההפעלה.', obtn('אודות', function () { showAbout(); })));
    sAb.add(row('__ABOUT_TEXT__', '__ABOUT_LINK__', obtn('פתח את הערוץ', function () { location.href = '__ABOUT_LINK__'; })));
    sAb.add(row('קיצורי מקלדת', 'Ctrl+T כרטיסייה חדשה · Ctrl+W סגירה · Ctrl+Tab מעבר · Ctrl+L שורת כתובת · Ctrl+Shift+Z כיבוי חירום של עיצוב Kick'));

    // ----- סרגל צד -----
    var sideItems = [];
    secs.forEach(function (s, i) {
      var it = h('div', { display: 'flex', alignItems: 'center', gap: '14px', padding: '10px 16px', borderRadius: '0 22px 22px 0', cursor: 'pointer', marginBottom: '2px' });
      it.appendChild(h('span', { fontSize: '15px', width: '20px', textAlign: 'center' }, s.icon));
      it.appendChild(h('span', null, s.label));
      function mark(on) { it.style.background = on ? GREEN + '26' : 'transparent'; it.style.color = on ? GREEN : C.text; }
      it.onclick = function () {
        sideItems.forEach(function (x) { x.mark(false); }); mark(true);
        s.wrap.scrollIntoView({ block: 'start', behavior: 'smooth' });
      };
      it.onmouseenter = function () { if (it.style.color !== GREEN) it.style.background = 'rgba(255,255,255,0.06)'; };
      it.onmouseleave = function () { if (it.style.color !== GREEN) it.style.background = 'transparent'; };
      it.mark = mark; mark(i === 0); sideItems.push(it); side.appendChild(it);
    });

    // ----- חיפוש בהגדרות -----
    var empty = h('div', { display: 'none', color: C.sub, textAlign: 'center', padding: '40px 0' }, 'לא נמצאו הגדרות תואמות');
    main.appendChild(empty);
    search.oninput = function () {
      var q = search.value.trim().toLowerCase(), any = false;
      secs.forEach(function (s) {
        var vis = 0, secHit = q && s.label.toLowerCase().indexOf(q) >= 0;
        s.rows.forEach(function (r) {
          var show = !q || secHit || r.kbText.indexOf(q) >= 0;
          r.style.display = show ? 'flex' : 'none'; if (show) vis++;
        });
        s.wrap.style.display = vis ? '' : 'none'; if (vis) any = true;
      });
      empty.style.display = any ? 'none' : 'block';
    };

    document.documentElement.appendChild(ov);
    if (typeof restoreScroll === 'number' && restoreScroll > 0) ov.scrollTop = restoreScroll;
  }


  // =====================================================================
  //  רמות (XP לפי זמן צפייה בפועל)
  // =====================================================================
  var RANKS = [
    { from: 1,  name: 'מתחיל' },
    { from: 3,  name: 'צופה' },
    { from: 5,  name: 'חבר קבוע' },
    { from: 10, name: 'מומחה' },
    { from: 15, name: 'אגדה' },
    { from: 25, name: 'אלוף הסטרימים' }
  ];
  var XP_PER_TICK = 2, TICK_MS = 15000, DAILY_BONUS = 50;   // 2 XP כל 15 שניות צפייה (8 לדקה)
  function need(l) { return 50 * l * (l - 1); }              // סה"כ XP שנדרש כדי להגיע לרמה l
  function levelFor(xp) { var l = 1; while (xp >= need(l + 1)) l++; return l; }
  function rankFor(l) {
    var r = RANKS[0];
    RANKS.forEach(function (x) { if (l >= x.from) r = x; });
    return r.name;
  }
  var P = Object.assign({ xp: 0, seconds: 0, daily: '', streamers: {}, names: {} }, CFG.progress || {});
  if (!P.streamers || typeof P.streamers !== 'object') P.streamers = {};
  if (!P.names || typeof P.names !== 'object') P.names = {};
  function saveP() { persist('progress', P); }

  var levelBtn = mk('', 'רמות - לחץ לפרטים', function () { showLevels(); });
  // מד רמות: טבעת התקדמות קטנה בסרגל, ומד גדול בחלון הרמות
  function ringSvg(size, pct, label) {
    var NS = 'http://www.w3.org/2000/svg', r = size / 2 - 3, c = size / 2, C = 2 * Math.PI * r;
    var svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('viewBox', '0 0 ' + size + ' ' + size); svg.setAttribute('width', String(size)); svg.setAttribute('height', String(size));
    function circ(stroke, dash) {
      var e = document.createElementNS(NS, 'circle');
      e.setAttribute('cx', String(c)); e.setAttribute('cy', String(c)); e.setAttribute('r', String(r)); e.setAttribute('fill', 'none');
      e.setAttribute('stroke', stroke); e.setAttribute('stroke-width', '3');
      if (dash) { e.setAttribute('stroke-dasharray', dash + ' ' + C); e.setAttribute('stroke-linecap', 'round'); e.setAttribute('transform', 'rotate(-90 ' + c + ' ' + c + ')'); }
      return e;
    }
    svg.appendChild(circ('#4a4d51'));
    svg.appendChild(circ(GREEN, Math.max(0.001, Math.min(1, pct)) * C));
    var t = document.createElementNS(NS, 'text');
    t.setAttribute('x', String(c)); t.setAttribute('y', String(c + 3.5)); t.setAttribute('text-anchor', 'middle');
    t.setAttribute('font-size', label.length > 2 ? '8' : '10'); t.setAttribute('font-weight', '700'); t.setAttribute('fill', '#e8eaed');
    t.textContent = label;
    svg.appendChild(t);
    return svg;
  }
  function bigGauge(pct, level) {
    var NS = 'http://www.w3.org/2000/svg', cx = 120, cy = 118, r = 92;
    var svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('viewBox', '0 0 240 142'); svg.setAttribute('width', '240'); svg.setAttribute('height', '142');
    function pt(p, rad) { var a = Math.PI * (1 - p); return [cx + rad * Math.cos(a), cy - rad * Math.sin(a)]; }
    function arc(p, color, w) {
      var e = document.createElementNS(NS, 'path'), a = pt(0, r), b = pt(p, r);
      e.setAttribute('d', 'M ' + a[0] + ' ' + a[1] + ' A ' + r + ' ' + r + ' 0 0 1 ' + b[0] + ' ' + b[1]);
      e.setAttribute('fill', 'none'); e.setAttribute('stroke', color); e.setAttribute('stroke-width', String(w)); e.setAttribute('stroke-linecap', 'round');
      return e;
    }
    svg.appendChild(arc(0.999, '#2e2f33', 16));
    if (pct > 0.004) svg.appendChild(arc(Math.min(pct, 0.999), GREEN, 16));
    [0, 0.25, 0.5, 0.75, 1].forEach(function (p) {
      var a = pt(p, r + 14), b = pt(p, r + 22), l = document.createElementNS(NS, 'line');
      l.setAttribute('x1', String(a[0])); l.setAttribute('y1', String(a[1])); l.setAttribute('x2', String(b[0])); l.setAttribute('y2', String(b[1]));
      l.setAttribute('stroke', '#5f6368'); l.setAttribute('stroke-width', '2'); svg.appendChild(l);
    });
    var n = pt(Math.min(pct, 0.999), r - 22), nd = document.createElementNS(NS, 'line');
    nd.setAttribute('x1', String(cx)); nd.setAttribute('y1', String(cy)); nd.setAttribute('x2', String(n[0])); nd.setAttribute('y2', String(n[1]));
    nd.setAttribute('stroke', '#ffffff'); nd.setAttribute('stroke-width', '3'); nd.setAttribute('stroke-linecap', 'round'); svg.appendChild(nd);
    var hub = document.createElementNS(NS, 'circle');
    hub.setAttribute('cx', String(cx)); hub.setAttribute('cy', String(cy)); hub.setAttribute('r', '7'); hub.setAttribute('fill', GREEN); svg.appendChild(hub);
    var t = document.createElementNS(NS, 'text');
    t.setAttribute('x', String(cx)); t.setAttribute('y', '98'); t.setAttribute('text-anchor', 'middle');
    t.setAttribute('font-size', '34'); t.setAttribute('font-weight', '800'); t.setAttribute('fill', '#ffffff'); t.textContent = String(level);
    svg.appendChild(t);
    return svg;
  }
  function refreshLevel() {
    var l = levelFor(P.xp), lo = need(l), hi = need(l + 1), pct = (P.xp - lo) / (hi - lo);
    while (levelBtn.firstChild) levelBtn.removeChild(levelBtn.firstChild);
    Object.assign(levelBtn.style, { display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '0 12px 0 6px' });
    levelBtn.appendChild(ringSvg(26, pct, String(l)));
    var tx = document.createElement('span'); tx.textContent = 'רמה ' + l;
    levelBtn.appendChild(tx);
    levelBtn.title = 'רמה ' + l + ' · ' + P.xp + ' / ' + hi + ' XP (' + Math.round(pct * 100) + '%) - לחץ לפרטים';
  }

  function toast(text) {
    var t = document.createElement('div');
    t.textContent = text; t.setAttribute('dir', 'rtl');
    Object.assign(t.style, {
      position: 'fixed', top: (BAR_H + 10) + 'px', left: '50%', transform: 'translateX(-50%)',
      background: GREEN, color: '#000', fontWeight: '800', padding: '10px 20px',
      borderRadius: '12px', zIndex: '2147483647', fontFamily: 'Segoe UI, Arial, sans-serif',
      boxShadow: '0 6px 24px rgba(0,0,0,0.5)', fontSize: '15px'
    });
    document.documentElement.appendChild(t);
    setTimeout(function () { t.remove(); }, 4500);
  }

  function addXP(n, why) {
    var before = levelFor(P.xp);
    P.xp += n;
    var after = levelFor(P.xp);
    saveP(); refreshLevel();
    if (after > before) toast('🎉 עלית לרמה ' + after + ' - ' + rankFor(after) + '!');
    else if (why) toast(why);
  }

  function today() { var d = new Date(); return d.getFullYear() + '-' + (d.getMonth() + 1) + '-' + d.getDate(); }
  function videoPlaying() {
    var vs = document.querySelectorAll('video');
    for (var i = 0; i < vs.length; i++) {
      var v = vs[i];
      if (!v.paused && !v.ended && v.readyState > 2) return true;
    }
    return false;
  }
  setInterval(function () {
    if (document.hidden || !document.hasFocus()) return;
    if (!videoPlaying()) return;
    P.seconds += TICK_MS / 1000;
    try {
      var wsl = channelSlug();
      if (wsl) {   // סופרים סטרימרים שצפית בהם (רק כשסרטון מנגן בדף הערוץ)
        var wk = wsl.toLowerCase();
        P.streamers[wk] = (P.streamers[wk] || 0) + TICK_MS / 1000;
        if (SI && SI.slug === wsl && SI.loaded && SI.name) P.names[wk] = SI.name;
        histNote(wsl, TICK_MS / 1000);   // רק אחרי שהשם האמיתי נטען מ-Kick
        var wks = Object.keys(P.streamers);
        if (wks.length > 500) {
          wks.sort(function (a, b) { return P.streamers[a] - P.streamers[b]; });
          wks.slice(0, wks.length - 400).forEach(function (k) { delete P.streamers[k]; delete P.names[k]; });
        }
      }
    } catch (e) {}
    addXP(XP_PER_TICK);
  }, TICK_MS);

  function showLevels() {
    openModal('kickbob-levels', function (box, line, close) {
      var l = levelFor(P.xp), lo = need(l), hi = need(l + 1);
      line('⭐ הרמה שלך', { color: GREEN, fontSize: '22px', fontWeight: '800', marginBottom: '6px' });
      var gWrap = document.createElement('div'); Object.assign(gWrap.style, { display: 'flex', justifyContent: 'center' });
      gWrap.appendChild(bigGauge((P.xp - lo) / (hi - lo), l)); box.appendChild(gWrap);
      line('רמה ' + l + ' - ' + rankFor(l), { fontSize: '22px', fontWeight: '800', margin: '0 0 14px' });

      var barBg = document.createElement('div');
      Object.assign(barBg.style, { height: '16px', background: '#1c1c20', borderRadius: '8px', overflow: 'hidden', border: '1px solid ' + BORDER });
      var barFg = document.createElement('div');
      Object.assign(barFg.style, { height: '100%', width: Math.min(100, Math.round((P.xp - lo) / (hi - lo) * 100)) + '%', background: GREEN });
      barBg.appendChild(barFg); box.appendChild(barBg);
      line(P.xp + ' / ' + hi + ' XP (עוד ' + (hi - P.xp) + ' לרמה ' + (l + 1) + ')', { fontSize: '12px', color: '#aaa', margin: '6px 0 14px' });

      var mins = Math.floor(P.seconds / 60);
      line('זמן צפייה כולל: ' + Math.floor(mins / 60) + ' שעות ו-' + (mins % 60) + ' דקות', { fontSize: '14px', marginBottom: '14px' });
      line('סטרימרים שצפית בהם: ' + watchedList().length, { fontSize: '14px', marginBottom: '14px' });

      line('איך מרוויחים XP?', { fontWeight: '700', textAlign: 'right', marginBottom: '4px' });
      line('• צפייה בסרטון/סטרים שמנגן בפועל: 8 XP לדקה (רק כשהחלון פעיל)', { fontSize: '12px', color: '#aaa', textAlign: 'right' });
      line('• בונוס יומי: ' + DAILY_BONUS + ' XP בפעם הראשונה בכל יום', { fontSize: '12px', color: '#aaa', textAlign: 'right', marginBottom: '14px' });

      line('דרגות', { fontWeight: '700', textAlign: 'right', marginBottom: '4px' });
      RANKS.forEach(function (r) {
        line('רמה ' + r.from + '+  -  ' + r.name, { fontSize: '12px', textAlign: 'right', color: l >= r.from ? GREEN : '#777' });
      });
      var sp = document.createElement('div'); sp.style.height = '16px'; box.appendChild(sp);
      var lr = document.createElement('div'); Object.assign(lr.style, { display: 'flex', gap: '8px', justifyContent: 'center' });
      lr.appendChild(mk('הצפייה שלי', 'סטטיסטיקות צפייה', function () { close(); showWatched(); }));
      lr.appendChild(mk('סגור', 'סגור', close, true));
      box.appendChild(lr);
    });
  }

  // =====================================================================
  //  סמן עכבר מותאם (CSS native, עם גיבוי JS)
  // =====================================================================
  var cursorOn = !SAFE && SET.cursor !== false;
  var cursorSheet = null, jsCur = null, jsMode = null, jsSheet = null, cursorModeDecided = null;
  var HOVER_SEL = 'a,button,[role="button"],[role="link"],[role="tab"],label,select,summary,[onclick],[tabindex]:not([tabindex="-1"])';

  // ----- צורות הסמן: תיאור אחד משמש גם ל-CSS וגם לגיבוי ב-DOM -----
  var CUR_STYLE = SET.cursorStyle === 'classic' ? 'classic' : 'neon';
  var NEON_ARROW = 'M4 3 L4 25 L10 19.6 L14.4 29 L18.4 27.2 L14 17.8 L22 17.8 Z';
  function curShapes(hover) {
    var A = GREEN;
    if (CUR_STYLE === 'classic') {
      return { size: 26, hx: 2, hy: 2, paths: [{ d: 'M2 2 L2 21 L7.5 16 L11.5 24.5 L15 23 L11 14.8 L18.5 14.8 Z', fill: hover ? '#ffffff' : A, stroke: '#000000', sw: 1.6 }] };
    }
    if (hover) {   // כוונת (כמו במשחקים) מעל כפתורים וקישורים
      return { size: 32, hx: 16, hy: 16, paths: [
        { c: [16, 16, 10], fill: 'none', stroke: A, sw: 6, op: 0.25 },
        { c: [16, 16, 10], fill: 'none', stroke: A, sw: 2.2 },
        { d: 'M16 1.5V7 M16 25V30.5 M1.5 16H7 M25 16H30.5', fill: 'none', stroke: A, sw: 2.2 },
        { c: [16, 16, 2.6], fill: '#ffffff', stroke: '#07130a', sw: 1 } ] };
    }
    return { size: 32, hx: 4, hy: 3, paths: [     // חץ ניאון עם הילה
      { d: NEON_ARROW, fill: 'none', stroke: A, sw: 6, op: 0.28 },
      { d: NEON_ARROW, fill: A, stroke: '#07130a', sw: 1.8 },
      { d: 'M6.6 7.4 L6.6 19.6 L9.8 16.6', fill: 'none', stroke: '#ffffff', sw: 1.4, op: 0.6 } ] };
  }
  function shapeSvg(sh) {
    var out = '<svg xmlns="http://www.w3.org/2000/svg" width="' + sh.size + '" height="' + sh.size + '" viewBox="0 0 ' + sh.size + ' ' + sh.size + '">';
    sh.paths.forEach(function (p) {
      var at = ' fill="' + (p.fill || 'none') + '"' + (p.stroke ? ' stroke="' + p.stroke + '" stroke-width="' + p.sw + '" stroke-linejoin="round" stroke-linecap="round"' : '') + (p.op ? ' opacity="' + p.op + '"' : '');
      out += p.c ? '<circle cx="' + p.c[0] + '" cy="' + p.c[1] + '" r="' + p.c[2] + '"' + at + '/>' : '<path d="' + p.d + '"' + at + '/>';
    });
    return out + '</svg>';
  }
  function shapeUri(sh) { return 'url("data:image/svg+xml,' + encodeURIComponent(shapeSvg(sh)) + '") ' + sh.hx + ' ' + sh.hy; }
  function shapeEl(sh) {
    var NS = 'http://www.w3.org/2000/svg', svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('viewBox', '0 0 ' + sh.size + ' ' + sh.size); svg.setAttribute('width', String(sh.size)); svg.setAttribute('height', String(sh.size));
    sh.paths.forEach(function (p) {
      var e = document.createElementNS(NS, p.c ? 'circle' : 'path');
      if (p.c) { e.setAttribute('cx', String(p.c[0])); e.setAttribute('cy', String(p.c[1])); e.setAttribute('r', String(p.c[2])); } else e.setAttribute('d', p.d);
      e.setAttribute('fill', p.fill || 'none');
      if (p.stroke) { e.setAttribute('stroke', p.stroke); e.setAttribute('stroke-width', String(p.sw)); e.setAttribute('stroke-linejoin', 'round'); e.setAttribute('stroke-linecap', 'round'); }
      if (p.op) e.setAttribute('opacity', String(p.op));
      svg.appendChild(e);
    });
    return svg;
  }

  function clearCursor() {
    if (cursorSheet) { cursorSheet.remove(); cursorSheet = null; }
    if (jsSheet) { jsSheet.remove(); jsSheet = null; }
    if (jsCur) { jsCur.style.display = 'none'; }
  }
  function useCssCursor() {
    clearCursor();
    cursorSheet = addSheet(
      'html, body, * { cursor: ' + shapeUri(curShapes(false)) + ', auto !important; } ' +
      'a, a *, button, button *, [role="button"], [role="link"], [role="tab"], label, select, summary, [onclick], ' +
      '[tabindex]:not([tabindex="-1"]) { cursor: ' + shapeUri(curShapes(true)) + ', pointer !important; } ' +
      'input:not([type]), input[type="text"], input[type="search"], input[type="email"], input[type="password"], ' +
      'input[type="url"], textarea, [contenteditable="true"] { cursor: text !important; }'
    );
  }
  // גיבוי: אלמנט שעוקב אחרי העכבר (אם ה-CSP חוסם תמונות data:)
  function buildJsCursor() {
    var shN = curShapes(false), shH = curShapes(true);
    jsCur = document.createElement('div');
    jsCur.id = 'kickbob-cursor';
    Object.assign(jsCur.style, { position: 'fixed', left: '0', top: '0', width: '32px', height: '32px', pointerEvents: 'none',
      zIndex: '2147483647', display: 'none', willChange: 'transform' });
    var eN = shapeEl(shN), eH = shapeEl(shH); eH.style.display = 'none';
    jsCur.appendChild(eN); jsCur.appendChild(eH);
    document.documentElement.appendChild(jsCur);
    var hoverPending = false, lastT = null, hovering = false, mx = 0, my = 0;
    function paint() {
      var sh = hovering ? shH : shN;
      jsCur.style.transform = 'translate(' + (mx - sh.hx) + 'px,' + (my - sh.hy) + 'px)';
      eN.style.display = hovering ? 'none' : ''; eH.style.display = hovering ? '' : 'none';
    }
    window.addEventListener('mousemove', function (e) {
      if (!cursorOn || jsMode !== true) return;
      mx = e.clientX; my = e.clientY;
      if (!jsSheet) jsSheet = addSheet('*, *::before, *::after { cursor: none !important; }');   // רק אחרי התזוזה הראשונה
      jsCur.style.display = 'block';
      paint();
      lastT = e.target;
      if (hoverPending) return;
      hoverPending = true;
      requestAnimationFrame(function () {
        hoverPending = false;
        var h = !!(lastT && lastT.closest && lastT.closest(HOVER_SEL));
        if (h !== hovering) { hovering = h; paint(); }
      });
    }, { capture: true, passive: true });
    document.documentElement.addEventListener('mouseleave', function () { jsCur.style.display = 'none'; });
  }
  function useJsCursor() {
    clearCursor();
    jsMode = true;
    if (!jsCur) buildJsCursor();
  }

  // ----- אפקטים: שובל וגל לחיצה (קנבס שקוף מעל הדף) -----
  var fxCv = null, fxCtx = null, fxPts = [], fxRip = [], fxRun = false, fxBound = false;
  function fxSize() {
    if (!fxCv) return;
    var d = window.devicePixelRatio || 1;
    fxCv.width = Math.round(window.innerWidth * d); fxCv.height = Math.round(window.innerHeight * d);
    if (fxCtx) fxCtx.setTransform(d, 0, 0, d, 0, 0);
  }
  function fxEnsure() {
    if (fxCv) return true;
    try {
      fxCv = document.createElement('canvas'); fxCv.id = 'kickbob-fx';
      Object.assign(fxCv.style, { position: 'fixed', left: '0', top: '0', width: '100vw', height: '100vh', pointerEvents: 'none', zIndex: '2147483640' });
      document.documentElement.appendChild(fxCv);
      fxCtx = fxCv.getContext('2d'); fxSize();
      window.addEventListener('resize', fxSize);
      return !!fxCtx;
    } catch (e) { fxCv = null; return false; }
  }
  function fxFrame() {
    if (!fxCtx) { fxRun = false; return; }
    var now = Date.now(), W = window.innerWidth, H = window.innerHeight, rgb = hex2rgb(GREEN) || [83, 252, 24];
    function col(a) { return 'rgba(' + rgb[0] + ',' + rgb[1] + ',' + rgb[2] + ',' + a.toFixed(3) + ')'; }
    fxCtx.clearRect(0, 0, W, H);
    fxPts = fxPts.filter(function (q) { return now - q.t < 450; });
    fxCtx.lineCap = 'round';
    for (var i = 1; i < fxPts.length; i++) {
      var a = 1 - (now - fxPts[i].t) / 450;
      fxCtx.strokeStyle = col(a * 0.75); fxCtx.lineWidth = 1 + 6 * a;
      fxCtx.beginPath(); fxCtx.moveTo(fxPts[i - 1].x, fxPts[i - 1].y); fxCtx.lineTo(fxPts[i].x, fxPts[i].y); fxCtx.stroke();
    }
    fxRip = fxRip.filter(function (q) { return now - q.t < 520; });
    fxRip.forEach(function (q) {
      var t = (now - q.t) / 520;
      fxCtx.strokeStyle = col(1 - t); fxCtx.lineWidth = 2.5 * (1 - t) + 0.5;
      fxCtx.beginPath(); fxCtx.arc(q.x, q.y, 6 + 34 * t, 0, Math.PI * 2); fxCtx.stroke();
    });
    if (fxPts.length > 1 || fxRip.length) requestAnimationFrame(fxFrame); else { fxRun = false; fxCtx.clearRect(0, 0, W, H); fxPts = []; }
  }
  function fxKick() { if (!fxRun) { fxRun = true; requestAnimationFrame(fxFrame); } }
  function fxBind() {
    if (fxBound) return; fxBound = true;
    window.addEventListener('mousemove', function (e) {
      if (!cursorOn || SET.cursorTrail === false || document.hidden || !fxEnsure()) return;
      fxPts.push({ x: e.clientX, y: e.clientY, t: Date.now() });
      if (fxPts.length > 60) fxPts.shift();
      fxKick();
    }, { capture: true, passive: true });
    window.addEventListener('mousedown', function (e) {
      if (!cursorOn || SET.cursorRipple === false || e.button !== 0 || !fxEnsure()) return;
      fxRip.push({ x: e.clientX, y: e.clientY, t: Date.now() });
      fxKick();
    }, { capture: true, passive: true });
  }

  function applyCursor() {
    clearCursor();
    jsMode = null;
    if (cursorOn) {
      fxBind();
      if (cursorModeDecided === 'css') useCssCursor();
      else if (cursorModeDecided === 'js') useJsCursor();
      else {
        // בדיקה: האם הדף מרשה תמונות data: (אחרת נשתמש בגיבוי)
        var decided = false;
        var t = new Image();
        t.onload = function () { if (!decided) { decided = true; cursorModeDecided = 'css'; if (cursorOn) useCssCursor(); } };
        t.onerror = function () { if (!decided) { decided = true; cursorModeDecided = 'js'; if (cursorOn) useJsCursor(); } };
        t.src = 'data:image/svg+xml,' + encodeURIComponent(shapeSvg(curShapes(false)));
        setTimeout(function () { if (!decided) { decided = true; cursorModeDecided = 'js'; if (cursorOn) useJsCursor(); } }, 1500);
      }
    }
    cursorBtn.style.opacity = cursorOn ? '1' : '0.45';
    cursorBtn.title = cursorOn ? 'סמן קיקבוב: פעיל (לחץ לכיבוי)' : 'סמן קיקבוב: כבוי (לחץ להפעלה)';
  }
  var cursorBtn = flat('🖱️', '', function () {
    cursorOn = !cursorOn;
    SET.cursor = cursorOn; saveSet();
    applyCursor();
  });

  // =====================================================================
  //  עיצוב קיק: צבעים, גופן, CSS מותאם
  // =====================================================================
  var STY = Object.assign({ on: true, bg: '', accent: '', font: '', size: 100, css: '' }, CFG.style || {});
  var FONTS = [
    ['', 'ברירת מחדל של Kick'], ["'Segoe UI', Tahoma, sans-serif", 'Segoe UI'], ['Arial, sans-serif', 'Arial'],
    ['Tahoma, sans-serif', 'Tahoma'], ["'Comic Sans MS', cursive", 'Comic Sans'], ['Georgia, serif', 'Georgia'],
    ["'Courier New', monospace", 'Courier New'], ['Impact, sans-serif', 'Impact']
  ];
  var PRESETS = [
    { n: 'ברירת מחדל', bg: '', accent: '', font: '' },
    { n: 'שחור AMOLED', bg: '#000000', accent: '', font: '' },
    { n: 'סגול ניאון', bg: '#0d0716', accent: '#b36bff', font: '' },
    { n: 'אוקיינוס', bg: '#06141f', accent: '#3bb7ff', font: '' },
    { n: 'אש', bg: '#140607', accent: '#ff4d4d', font: '' },
    { n: 'קנדי', bg: '#1a0a14', accent: '#ff6ec7', font: "'Comic Sans MS', cursive" },
    { n: 'יער', bg: '#07140a', accent: '#7dffa8', font: '' },
    { n: 'שקיעה', bg: '#1a0d06', accent: '#ff9a3c', font: '' },
    { n: 'מונוכרום', bg: '#101010', accent: '#ffffff', font: '' },
    { n: 'רטרו', bg: '#14110a', accent: '#ffd400', font: "'Courier New', monospace" },
    { n: 'ורוד-סגול', bg: '#12081a', accent: '#e86bff', font: '' },
    { n: 'קרח', bg: '#08121a', accent: '#8fe3ff', font: '' }
  ];
  var styleSheets = [], painted = [], scanTimer = null, scanEpoch = 0;

  function saveSty() { persist('style', STY); }
  // כשעוברים בין כרטיסיות: מושכים את העיצוב העדכני (אולי שונה בכרטיסייה אחרת)
  function resyncStyle() {
    var a = api(); if (!a || !a.get_cfg) return;
    a.get_cfg('style').then(function (str) {
      try {
        var o = JSON.parse(str || '{}');
        if (JSON.stringify(Object.assign({}, STY, o)) !== JSON.stringify(STY)) { Object.assign(STY, o); applyStyle(); }
      } catch (e) {}
    });
  }
  document.addEventListener('visibilitychange', function () { if (!document.hidden) resyncStyle(); });
  window.addEventListener('focus', resyncStyle);

  function hex2rgb(h) {
    var m = /^#?([0-9a-f]{6})$/i.exec(h || '');
    if (!m) return null;
    var n = parseInt(m[1], 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  }
  function parseCol(c) {
    var m = /rgba?\(([^)]+)\)/.exec(c || '');
    if (!m) return null;
    var p = m[1].split(/[ ,\/]+/).filter(Boolean).map(parseFloat);
    return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 };
  }
  function isKickGreen(c) { return c && c.a > 0.5 && c.g >= 200 && c.r <= 130 && c.b <= 80 && (c.g - c.r) > 90; }
  function isDarkNeutral(c) {
    return c && c.a === 1 && c.r <= 70 && c.g <= 70 && c.b <= 70 &&
      (Math.max(c.r, c.g, c.b) - Math.min(c.r, c.g, c.b)) <= 14;
  }
  function clamp(v) { return Math.max(0, Math.min(255, Math.round(v))); }
  function paint(el, prop, val) { el.style.setProperty(prop, val, 'important'); painted.push([el, prop]); }

  function scanEl(el, base) {
    var tag = el.tagName;
    if (tag === 'SCRIPT' || tag === 'STYLE' || tag === 'VIDEO' || tag === 'CANVAS' || tag === 'IMG') return;
    if (el.closest && el.closest('[id^="kickbob"]')) return;
    var cs = getComputedStyle(el);
    if (STY.accent) {
      if (isKickGreen(parseCol(cs.color))) paint(el, 'color', STY.accent);
      if (isKickGreen(parseCol(cs.backgroundColor))) paint(el, 'background-color', STY.accent);
      if (parseFloat(cs.borderTopWidth) > 0 && isKickGreen(parseCol(cs.borderTopColor))) paint(el, 'border-color', STY.accent);
      if (el instanceof SVGElement) {
        if (isKickGreen(parseCol(cs.fill))) paint(el, 'fill', STY.accent);
        if (isKickGreen(parseCol(cs.stroke))) paint(el, 'stroke', STY.accent);
      }
    }
    if (base) {
      var bc = parseCol(cs.backgroundColor);
      if (isDarkNeutral(bc)) {
        var d = ((bc.r + bc.g + bc.b) / 3 - 12) * 1.2;   // שומר על ההפרש בין לוחות כהים שונים
        paint(el, 'background-color', 'rgb(' + clamp(base[0] + d) + ',' + clamp(base[1] + d) + ',' + clamp(base[2] + d) + ')');
      }
    }
  }
  function startScan() {
    var ep = scanEpoch;
    function cycle() {
      if (ep !== scanEpoch) return;
      if (document.hidden || !document.body) { scanTimer = setTimeout(cycle, 4000); return; }
      if (painted.length > 20000) painted = painted.filter(function (p) { return p[0].isConnected; });
      var base = STY.bg ? hex2rgb(STY.bg) : null;
      var list = document.body.querySelectorAll('*'), i = 0;
      (function step() {
        if (ep !== scanEpoch) return;
        var end = Math.min(i + 250, list.length);
        for (; i < end; i++) { try { scanEl(list[i], base); } catch (e) {} }
        scanTimer = setTimeout(i < list.length ? step : cycle, i < list.length ? 30 : 4000);
      })();
    }
    cycle();
  }

  function applyStyle() {
    styleSheets.forEach(function (x) { x.remove(); }); styleSheets = [];
    painted.forEach(function (p) { try { p[0].style.removeProperty(p[1]); } catch (e) {} }); painted = [];
    scanEpoch++; clearTimeout(scanTimer);
    if (STY.on && isKick()) {   // העיצוב חל רק על kick.com
      var css = '';
      if (STY.bg) css += 'html, body, #__next, #__next > div, main { background-color: ' + STY.bg + ' !important; } ';
      if (STY.font) css += 'body, body * { font-family: ' + STY.font + ' !important; } ';
      if (STY.size && STY.size !== 100) css += 'html { font-size: ' + STY.size + '% !important; } ';
      if (STY.css) css += '\n' + STY.css + '\n';
      if (css) styleSheets.push(addSheet(css));
      if (STY.accent || STY.bg) startScan();
    }
    // הגנה: CSS מותאם לא יכול להסתיר את הסרגל של קיקבוב
    styleSheets.push(addSheet('#kickbob-bar { display: flex !important; visibility: visible !important; opacity: 1 !important; }'));
  }
  // כיבוי חירום של העיצוב: Ctrl+Shift+Z
  document.addEventListener('keydown', function (e) {
    if (e.ctrlKey && e.shiftKey && (e.key === 'Z' || e.key === 'z')) {
      STY.on = false; saveSty(); applyStyle(); toast('העיצוב כובה. אפשר להפעיל מחדש דרך 🎨');
    }
  }, true);

  function showStyle() {
    openModal('kickbob-style', function (box, line, close) {
      box.style.width = '560px';
      function stop(el) { ['keydown', 'keypress', 'keyup'].forEach(function (ev) { el.addEventListener(ev, function (e) { e.stopPropagation(); }); }); }
      var timer = null;
      function change() { clearTimeout(timer); timer = setTimeout(function () { saveSty(); applyStyle(); }, 150); }

      line('🎨 עיצוב קיק', { color: GREEN, fontSize: '24px', fontWeight: '800', marginBottom: '4px' });
      line('משנה את המראה של אתר Kick עצמו. ניסיוני: ייתכן שחלק מהאלמנטים לא ישתנו.', { fontSize: '12px', color: '#888', marginBottom: '14px' });

      var onBtn = mk('', '', function () { STY.on = !STY.on; saveSty(); applyStyle(); syncFields(); });
      onBtn.style.width = '100%'; box.appendChild(onBtn);

      line('סגנונות מוכנים', { fontWeight: '700', textAlign: 'right', margin: '16px 0 8px' });
      var pr = document.createElement('div');
      Object.assign(pr.style, { display: 'flex', gap: '6px', flexWrap: 'wrap', justifyContent: 'center' });
      PRESETS.forEach(function (p) {
        var pb = mk(p.n, p.n, function () {
          STY.bg = p.bg; STY.accent = p.accent; STY.font = p.font; STY.on = true;
          saveSty(); applyStyle(); syncFields();
        });
        pb.style.borderRight = '5px solid ' + (p.accent || '#53fc18');
        pr.appendChild(pb);
      });
      box.appendChild(pr);

      function row(label, ctl) {
        var r = document.createElement('div');
        Object.assign(r.style, { display: 'flex', alignItems: 'center', gap: '10px', margin: '10px 0', textAlign: 'right' });
        var l = document.createElement('div'); l.textContent = label;
        Object.assign(l.style, { width: '110px', fontWeight: '600', flex: '0 0 auto' });
        r.appendChild(l);
        ctl.forEach(function (c) { r.appendChild(c); });
        box.appendChild(r);
      }
      function colorCtl(key) {
        var inp = document.createElement('input'); inp.type = 'color';
        Object.assign(inp.style, { width: '48px', height: '30px', background: 'none', border: '1px solid ' + BORDER, borderRadius: '6px' });
        inp.oninput = function () { STY[key] = inp.value; change(); lbl.textContent = inp.value; };
        var lbl = document.createElement('span'); Object.assign(lbl.style, { fontSize: '12px', color: '#aaa', direction: 'ltr', width: '70px' });
        var clr = mk('ללא', 'חזרה לברירת המחדל', function () { STY[key] = ''; saveSty(); applyStyle(); syncFields(); });
        return { els: [inp, lbl, clr], inp: inp, lbl: lbl };
      }
      var bgC = colorCtl('bg'), acC = colorCtl('accent');
      row('צבע רקע', bgC.els);
      row('צבע דגש', acC.els);

      var fontSel = document.createElement('select');
      Object.assign(fontSel.style, { background: '#1c1c20', color: '#fff', border: '1px solid ' + BORDER, borderRadius: '8px', padding: '6px', flex: '1' });
      FONTS.forEach(function (f, i) { var o = document.createElement('option'); o.value = i; o.textContent = f[1]; fontSel.appendChild(o); });
      fontSel.onchange = function () { STY.font = FONTS[fontSel.value][0]; change(); };
      row('גופן', [fontSel]);

      var sizeIn = document.createElement('input'); sizeIn.type = 'range'; sizeIn.min = 80; sizeIn.max = 130; sizeIn.step = 5;
      sizeIn.style.flex = '1';
      var sizeLbl = document.createElement('span'); Object.assign(sizeLbl.style, { width: '48px', direction: 'ltr', fontSize: '12px', color: '#aaa' });
      sizeIn.oninput = function () { STY.size = parseInt(sizeIn.value, 10); sizeLbl.textContent = STY.size + '%'; change(); };
      row('גודל כתב', [sizeIn, sizeLbl]);

      line('CSS מותאם אישית (עיצוב חופשי לאתר)', { fontWeight: '700', textAlign: 'right', margin: '14px 0 6px' });
      var ta = document.createElement('textarea'); ta.setAttribute('dir', 'ltr'); ta.spellcheck = false;
      ta.placeholder = '/* לדוגמה */\nbody { zoom: 1.05; }\nfooter { display: none !important; }';
      Object.assign(ta.style, { width: '100%', height: '130px', boxSizing: 'border-box', background: '#1c1c20', color: '#d6ffd0',
        border: '1px solid ' + BORDER, borderRadius: '8px', padding: '8px', fontFamily: 'Consolas, monospace', fontSize: '12px', resize: 'vertical' });
      ta.oninput = function () { STY.css = ta.value; change(); };
      stop(ta); box.appendChild(ta);
      line('חירום: Ctrl+Shift+Z מכבה את כל העיצוב אם משהו נשבר.', { fontSize: '11px', color: '#888', textAlign: 'right', margin: '4px 0 10px' });

      line('שיתוף עיצוב: קוד שכל אחד יכול להדביק אצלו', { fontWeight: '700', textAlign: 'right', margin: '8px 0 6px' });
      var ex = document.createElement('textarea'); ex.setAttribute('dir', 'ltr'); ex.spellcheck = false;
      ex.placeholder = 'הדבק כאן קוד עיצוב (KB1:...) ולחץ "החל קוד"';
      Object.assign(ex.style, { width: '100%', height: '56px', boxSizing: 'border-box', background: '#1c1c20', color: '#ccc',
        border: '1px solid ' + BORDER, borderRadius: '8px', padding: '8px', fontFamily: 'Consolas, monospace', fontSize: '11px' });
      stop(ex); box.appendChild(ex);
      var exRow = document.createElement('div'); Object.assign(exRow.style, { display: 'flex', gap: '8px', margin: '8px 0', justifyContent: 'center' });
      var exMsg = line('', { fontSize: '12px', color: '#aaa' });
      function sanitize(o) {
        if (!o || typeof o !== 'object') throw 0;
        var r = { on: true, bg: '', accent: '', font: '', size: 100, css: '', stripped: false };
        if (/^#[0-9a-f]{6}$/i.test(o.bg)) r.bg = o.bg;
        if (/^#[0-9a-f]{6}$/i.test(o.accent)) r.accent = o.accent;
        if (FONTS.some(function (f) { return f[0] === o.font; })) r.font = o.font;
        var sz = parseInt(o.size, 10); if (sz >= 80 && sz <= 130) r.size = sz;
        if (typeof o.css === 'string') {
          var c = o.css.slice(0, 20000);
          var clean = c.replace(/@import[^;]*;?/gi, '').replace(/url\s*\([^)]*\)/gi, '');   // מטעמי בטיחות
          r.stripped = clean !== c; r.css = clean;
        }
        return r;
      }
      function enc() {
        var j = JSON.stringify({ bg: STY.bg, accent: STY.accent, font: STY.font, size: STY.size, css: STY.css });
        return 'KB1:' + btoa(unescape(encodeURIComponent(j)));
      }
      function dec(t) {
        t = (t || '').trim();
        var j = /^KB1:/.test(t) ? decodeURIComponent(escape(atob(t.slice(4)))) : t;
        return sanitize(JSON.parse(j));
      }
      exRow.appendChild(mk('צור קוד', 'יוצר קוד מהעיצוב הנוכחי', function () {
        ex.value = enc(); ex.select();
        var copied = false;
        try { copied = document.execCommand('copy'); } catch (e) {}
        exMsg.textContent = copied ? 'הקוד נוצר והועתק. שלח אותו לחברים.' : 'הקוד נוצר. העתק אותו ושלח לחברים.';
      }));
      exRow.appendChild(mk('החל קוד', 'טוען עיצוב מקוד', function () {
        try {
          var r = dec(ex.value);
          var st = r.stripped; delete r.stripped;
          Object.assign(STY, r); saveSty(); applyStyle(); syncFields();
          exMsg.textContent = st ? 'העיצוב נטען. הוסרו @import ו-url() מטעמי בטיחות.' : 'העיצוב נטען.';
        } catch (e) { exMsg.textContent = 'הקוד לא תקין.'; }
      }));
      box.insertBefore(exRow, exMsg);

      function syncFields() {
        onBtn.textContent = STY.on ? '✔ העיצוב פעיל' : '✖ העיצוב כבוי';
        onBtn.style.background = STY.on ? GREEN : '#1c1c20'; onBtn.style.color = STY.on ? '#000' : '#fff';
        bgC.inp.value = STY.bg || '#000000'; bgC.lbl.textContent = STY.bg || 'ברירת מחדל';
        acC.inp.value = STY.accent || '#53fc18'; acC.lbl.textContent = STY.accent || 'ברירת מחדל';
        var fi = 0; FONTS.forEach(function (f, i) { if (f[0] === STY.font) fi = i; }); fontSel.value = fi;
        sizeIn.value = STY.size; sizeLbl.textContent = STY.size + '%';
        ta.value = STY.css || '';
      }
      syncFields();

      var rst = mk('🧹 איפוס עיצוב', 'מוחק את כל ההתאמות', function () {
        STY = { on: true, bg: '', accent: '', font: '', size: 100, css: '' };
        saveSty(); applyStyle(); syncFields();
      });
      rst.style.margin = '12px 8px 0 0';
      var btns = document.createElement('div'); Object.assign(btns.style, { display: 'flex', gap: '8px', justifyContent: 'center', marginTop: '10px' });
      btns.appendChild(rst); btns.appendChild(mk('סגור', 'סגור', close, true));
      box.appendChild(btns);
    });
  }

  // =====================================================================
  //  זמן שידור של סטרימר (מהנתונים של Kick)
  // =====================================================================
  var RESERVED = { 'browse': 1, 'categories': 1, 'category': 1, 'following': 1, 'search': 1, 'clips': 1, 'video': 1,
    'videos': 1, 'dashboard': 1, 'settings': 1, 'subscriptions': 1, 'help': 1, 'terms-of-service': 1, 'privacy-policy': 1,
    'community-guidelines': 1, 'leaderboard': 1, 'api': 1, 'login': 1, 'signup': 1, 'support': 1, 'about': 1, 'careers': 1,
    'creators': 1, 'drops': 1, 'gifts': 1, 'wallet': 1, 'notifications': 1, 'messages': 1, 'store': 1 };
  var SI = { slug: null, loaded: false, live: false, start: null, title: '', viewers: null, category: '', name: '', error: null };

  function channelSlug() {
    var segs = location.pathname.split('/').filter(Boolean);
    if (!isKick() || segs.length !== 1) return null;
    var sg = segs[0].toLowerCase();
    return RESERVED[sg] ? null : segs[0];
  }
  function parseTime(t) {
    if (!t) return null;
    if (typeof t === 'number') return t < 1e12 ? t * 1000 : t;
    var x = String(t).trim();
    if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}/.test(x)) x = x.replace(' ', 'T');
    if (/^\d{4}-\d{2}-\d{2}T[\d:.]+$/.test(x)) x += 'Z';   // Kick שולח זמן ב-UTC
    var ms = Date.parse(x);
    return isNaN(ms) ? null : ms;
  }
  function fmtDur(ms) {
    var t = Math.max(0, Math.floor(ms / 1000));
    var h = Math.floor(t / 3600), m = Math.floor((t % 3600) / 60), sc = t % 60;
    return h + ':' + (m < 10 ? '0' : '') + m + ':' + (sc < 10 ? '0' : '') + sc;
  }
  function refreshStream() {
    var slug = SI.slug;
    if (!slug) return;
    fetch('/api/v2/channels/' + encodeURIComponent(slug), { credentials: 'include', headers: { 'Accept': 'application/json' } })
      .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(function (d) {
        if (SI.slug !== slug) return;
        var ls = d && d.livestream;
        SI.name = (d && d.user && d.user.username) || slug;
        if (ls) {
          SI.live = true;
          SI.start = parseTime(ls.start_time || ls.created_at);
          SI.title = ls.session_title || '';
          SI.viewers = (ls.viewer_count !== undefined) ? ls.viewer_count : null;
          SI.category = (ls.categories && ls.categories[0] && ls.categories[0].name) || '';
        } else { SI.live = false; SI.start = null; SI.title = ''; SI.viewers = null; SI.category = ''; }
        SI.error = null; SI.loaded = true;
      })
      .catch(function (e) { if (SI.slug === slug) { SI.error = String(e); SI.loaded = true; } });
  }

  var streamBtn = mk('', 'זמן שידור של הסטרימר - לחץ לפרטים', function () { showStream(); });
  streamBtn.style.display = 'none';
  var viewerPill = document.createElement('span');
  viewerPill.title = 'מספר צופים כרגע';
  Object.assign(viewerPill.style, { display: 'none', background: '#1c1c20', border: '1px solid ' + BORDER, borderRadius: '8px',
    padding: '0 10px', height: '30px', lineHeight: '28px', boxSizing: 'border-box', fontWeight: '600', fontSize: '13px',
    whiteSpace: 'nowrap', flex: '0 0 auto' });
  function tickStream() {
    var slug = channelSlug();
    if (slug !== SI.slug) {
      SI = { slug: slug, loaded: false, live: false, start: null, title: '', viewers: null, category: '', name: slug || '', error: null };
      if (slug) refreshStream();
    }
    if (!slug) { streamBtn.style.display = 'none'; viewerPill.style.display = 'none'; return; }
    streamBtn.style.display = '';
    var txt;
    if (SI.live && SI.start) txt = '🔴 שודר ' + fmtDur(Date.now() - SI.start);
    else if (SI.live) txt = '🔴 משדר עכשיו';
    else if (SI.error) txt = '⏱ אין נתונים';
    else if (SI.loaded) txt = '⚫ לא משדר';
    else txt = '⏱ טוען...';
    if (streamBtn.textContent !== txt) streamBtn.textContent = txt;
    if (SI.live && SI.viewers !== null && SI.viewers !== undefined) {
      var vt = '👁 ' + Number(SI.viewers).toLocaleString('he-IL');
      viewerPill.style.display = '';
      if (viewerPill.textContent !== vt) viewerPill.textContent = vt;
    } else viewerPill.style.display = 'none';
  }

  function showStream() {
    openModal('kickbob-stream', function (box, line, close) {
      line('⏱ זמן שידור', { color: GREEN, fontSize: '22px', fontWeight: '800', marginBottom: '6px' });
      line(SI.name || '', { fontSize: '24px', fontWeight: '800', marginBottom: '12px', direction: 'ltr' });
      if (SI.error) {
        line('לא הצלחתי לקבל נתונים מ-Kick (' + SI.error + ').', { color: '#ff8080', fontSize: '13px', marginBottom: '8px' });
      } else if (!SI.loaded) {
        line('טוען נתונים...', { color: '#aaa', marginBottom: '8px' });
      } else if (!SI.live) {
        line('הסטרימר לא משדר כרגע.', { fontSize: '16px', marginBottom: '8px' });
      } else {
        line('משדר עכשיו', { color: '#ff5050', fontWeight: '800', marginBottom: '8px' });
        if (SI.start) {
          line('משך שידור: ' + fmtDur(Date.now() - SI.start), { fontSize: '30px', fontWeight: '800', direction: 'ltr', marginBottom: '6px' });
          line('התחיל ב-' + new Date(SI.start).toLocaleString('he-IL'), { fontSize: '13px', color: '#aaa', marginBottom: '10px' });
        } else {
          line('זמן ההתחלה לא זמין.', { fontSize: '13px', color: '#aaa', marginBottom: '10px' });
        }
        if (SI.title) line(SI.title, { fontSize: '14px', marginBottom: '4px' });
        if (SI.category) line('קטגוריה: ' + SI.category, { fontSize: '13px', color: '#aaa' });
        if (SI.viewers !== null) line('צופים: ' + SI.viewers, { fontSize: '13px', color: '#aaa' });
      }
      line('הנתונים מגיעים מ-Kick ומתעדכנים כל חצי דקה.', { fontSize: '11px', color: '#777', margin: '12px 0' });
      var row = document.createElement('div'); Object.assign(row.style, { display: 'flex', gap: '8px', justifyContent: 'center' });
      if (SI.slug) {
        var fsl = SI.slug.toLowerCase(), isFav = favIdx(fsl) >= 0;
        row.appendChild(mk(isFav ? '★ במועדפים' : '☆ הוסף למועדפים', 'ערוצים מועדפים והתראות שידור', function () {
          if (favIdx(fsl) >= 0) { FAV.splice(favIdx(fsl), 1); saveFav(); } else addFav(SI.slug, SI.name);
          close(); showStream();
        }));
      }
      row.appendChild(mk('רענן', 'רענון נתונים', function () { refreshStream(); close(); setTimeout(showStream, 900); }));
      row.appendChild(mk('סגור', 'סגור', close, true));
      box.appendChild(row);
    });
  }
  setInterval(tickStream, 1000);
  setInterval(function () { if (SI.slug && !document.hidden) refreshStream(); }, 30000);

  // =====================================================================
  //  חיפוש קליפים
  // =====================================================================
  function fmtClipDur(sec) { sec = Math.round(Number(sec) || 0); var m = Math.floor(sec / 60), sc = sec % 60; return m + ':' + (sc < 10 ? '0' : '') + sc; }
  function showClips() {
    openModal('kickbob-clips', function (box, line, close) {
      box.style.width = '740px';
      line('🎬 חיפוש קליפים', { color: GREEN, fontSize: '22px', fontWeight: '800', marginBottom: '12px' });
      function rowOf(list) {
        var r = document.createElement('div');
        Object.assign(r.style, { display: 'flex', gap: '8px', flexWrap: 'wrap', justifyContent: 'center', alignItems: 'center' });
        list.forEach(function (el) { r.appendChild(el); });
        return r;
      }
      if (!isKick()) {
        line('חיפוש קליפים עובד בתוך אתר Kick.', { marginBottom: '14px' });
        box.appendChild(rowOf([mk('פתח את Kick', 'פתח את Kick', function () { location.href = HOME; }, true), mk('סגור', 'סגור', close)]));
        return;
      }
      function field(el) {
        Object.assign(el.style, { background: '#1c1c20', color: '#fff', border: '1px solid ' + BORDER, borderRadius: '8px',
          padding: '7px 10px', fontSize: '13px', fontFamily: 'inherit', outline: 'none' });
        return el;
      }
      var inp = field(document.createElement('input')); inp.type = 'text'; inp.setAttribute('dir', 'auto');
      inp.placeholder = 'שם ערוץ (למשל emuio) או מילה לחיפוש בכותרות'; inp.style.flex = '1 1 260px';
      ['keydown', 'keypress', 'keyup'].forEach(function (ev) { inp.addEventListener(ev, function (e) { e.stopPropagation(); }); });
      function sel(opts) {
        var x = field(document.createElement('select'));
        opts.forEach(function (o) { var op = document.createElement('option'); op.value = o[0]; op.textContent = o[1]; x.appendChild(op); });
        return x;
      }
      var sortSel = sel([['view', 'הכי נצפים'], ['date', 'החדשים ביותר']]);
      var timeSel = sel([['all', 'כל הזמנים'], ['month', 'חודש אחרון'], ['week', 'שבוע אחרון'], ['day', '24 שעות']]);
      box.appendChild(rowOf([inp, sortSel, timeSel, mk('🔍 חפש', 'חפש', function () { run(false); }, true)]));
      var status = line('', { fontSize: '12px', color: '#aaa', margin: '10px 0' });
      var grid = document.createElement('div');
      Object.assign(grid.style, { display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(210px,1fr))', gap: '12px', textAlign: 'right' });
      box.appendChild(grid);
      var moreBtn = mk('טען עוד', 'טען עוד קליפים', function () { run(true); });
      moreBtn.style.display = 'none'; moreBtn.style.margin = '14px auto 0';
      box.appendChild(moreBtn);
      var st = { slug: '', q: '', cursor: null, global: true, busy: false };

      function getJson(u) {
        return fetch(u, { credentials: 'include', headers: { 'Accept': 'application/json' } })
          .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); });
      }
      function urlFor(slug, cursor) {
        var base = slug ? '/api/v2/channels/' + encodeURIComponent(slug) + '/clips' : '/api/v2/clips';
        var q = ['sort=' + sortSel.value, 'time=' + timeSel.value];
        if (cursor) q.push('cursor=' + encodeURIComponent(cursor));
        return base + '?' + q.join('&');
      }
      function pass(c) {
        if (!st.global || !st.q) return true;
        var hay = ((c.title || '') + ' ' + ((c.channel && (c.channel.slug || c.channel.username)) || '') + ' ' +
                   ((c.creator && c.creator.username) || '')).toLowerCase();
        return hay.indexOf(st.q.toLowerCase()) >= 0;
      }
      function card(c) {
        var cslug = (c.channel && (c.channel.slug || c.channel.username)) || st.slug || '';
        var href = (c.clip_url && /^https?:/i.test(c.clip_url)) ? c.clip_url : ('https://kick.com/' + cslug + '/clips/' + c.id);
        var a = document.createElement('a'); a.href = href;
        Object.assign(a.style, { display: 'block', background: '#16161a', border: '1px solid #26262c', borderRadius: '10px',
          overflow: 'hidden', color: '#fff', textDecoration: 'none' });
        a.onmouseenter = function () { a.style.borderColor = GREEN; };
        a.onmouseleave = function () { a.style.borderColor = '#26262c'; };
        a.addEventListener('click', function () {
          setTimeout(function () { var m = document.getElementById('kickbob-clips'); if (m) m.remove(); }, 60);
        });
        var th = document.createElement('div');
        Object.assign(th.style, { height: '118px', background: '#1c1c20', backgroundSize: 'cover', backgroundPosition: 'center', position: 'relative' });
        var turl = c.thumbnail_url || c.thumbnail || '';
        if (turl) th.style.backgroundImage = 'url(' + JSON.stringify(String(turl)) + ')';
        if (c.duration) {
          var du = document.createElement('span'); du.textContent = fmtClipDur(c.duration);
          Object.assign(du.style, { position: 'absolute', bottom: '6px', left: '6px', background: 'rgba(0,0,0,0.8)', borderRadius: '4px',
            padding: '1px 6px', fontSize: '11px', direction: 'ltr' });
          th.appendChild(du);
        }
        a.appendChild(th);
        var info = document.createElement('div'); info.style.padding = '8px 10px';
        var ti = document.createElement('div'); ti.textContent = c.title || 'קליפ';
        Object.assign(ti.style, { fontSize: '13px', fontWeight: '700', display: '-webkit-box', webkitLineClamp: '2', overflow: 'hidden', minHeight: '34px' });
        ti.style.webkitBoxOrient = 'vertical'; ti.style.setProperty('-webkit-line-clamp', '2'); ti.style.setProperty('-webkit-box-orient', 'vertical');
        var meta = document.createElement('div');
        var views = (c.view_count !== undefined ? c.view_count : c.views);
        var parts = [];
        if (cslug) parts.push(cslug);
        if (views !== undefined && views !== null) parts.push('👁 ' + Number(views).toLocaleString('he-IL'));
        if (c.created_at) { var dt = Date.parse(c.created_at); if (!isNaN(dt)) parts.push(new Date(dt).toLocaleDateString('he-IL')); }
        meta.textContent = parts.join(' · ');
        Object.assign(meta.style, { fontSize: '11px', color: '#9aa0a6', marginTop: '4px' });
        info.appendChild(ti); info.appendChild(meta); a.appendChild(info);
        return a;
      }
      function fetchPage(pagesLeft, found) {
        st.busy = true; status.textContent = 'טוען...';
        return getJson(urlFor(st.global ? '' : st.slug, st.cursor)).then(function (d) {
          var list = (d && (d.clips || d.data)) || [];
          st.cursor = (d && (d.nextCursor || d.next_cursor)) || null;
          var shown = 0;
          list.forEach(function (c) { if (pass(c)) { grid.appendChild(card(c)); shown++; } });
          found += shown;
          if (st.global && st.q && found < 8 && st.cursor && pagesLeft > 1) return fetchPage(pagesLeft - 1, found);
          st.busy = false;
          moreBtn.style.display = st.cursor ? '' : 'none';
          status.textContent = grid.children.length ? ('נמצאו ' + grid.children.length + ' קליפים') : 'לא נמצאו קליפים.';
        });
      }
      function fail(e) {
        st.busy = false;
        status.textContent = 'לא הצלחתי לטעון קליפים (' + ((e && e.message) || e) + '). אפשר לפתוח את דף הקליפים באתר.';
      }
      function run(more) {
        if (st.busy) return;
        if (!more) {
          grid.textContent = ''; moreBtn.style.display = 'none'; st.cursor = null;
          var q = inp.value.trim().replace(/^@/, ''); st.q = q;
          st.slug = /^[\w-]+$/.test(q) ? q : ''; st.global = !st.slug;
          if (st.slug) {   // קודם כערוץ; אם אין כזה - חיפוש בכותרות של קליפים פופולריים
            fetchPage(1, 0).catch(function () {
              st.busy = false; st.global = true; st.slug = ''; st.cursor = null; grid.textContent = '';
              return fetchPage(4, 0);
            }).catch(fail);
            return;
          }
          fetchPage(st.q ? 4 : 1, 0).catch(fail);
          return;
        }
        fetchPage(st.global && st.q ? 4 : 1, 0).catch(fail);
      }
      inp.addEventListener('keydown', function (e) { if (e.key === 'Enter') run(false); });
      var sp = document.createElement('div'); sp.style.height = '16px'; box.appendChild(sp);
      box.appendChild(rowOf([
        mk('פתח את דף הקליפים באתר', 'פתיחה באתר Kick', function () { location.href = st.slug ? 'https://kick.com/' + st.slug + '/clips' : 'https://kick.com/clips'; }),
        mk('סגור', 'סגור', close, true)
      ]));
      run(false);
    });
  }

  // =====================================================================
  //  Kick בעברית: תרגום הממשק של האתר (מילון + תבניות + מילון אישי)
  // =====================================================================
  var HE_DICT = {
 "browse": "עיון",
 "home": "בית",
 "following": "במעקב",
 "follow": "עקוב",
 "unfollow": "הפסק לעקוב",
 "followers": "עוקבים",
 "follower": "עוקב",
 "subscribe": "הירשם כמנוי",
 "subscribed": "מנוי",
 "subscribers": "מנויים",
 "subscriber": "מנוי",
 "subscriptions": "מנויים",
 "gift a sub": "תן מנוי במתנה",
 "gift sub": "מנוי במתנה",
 "gift subs": "מנויים במתנה",
 "gift": "מתנה",
 "log in": "התחברות",
 "login": "התחברות",
 "sign up": "הרשמה",
 "signup": "הרשמה",
 "log out": "התנתקות",
 "logout": "התנתקות",
 "sign out": "התנתקות",
 "search": "חיפוש",
 "search...": "חיפוש...",
 "categories": "קטגוריות",
 "category": "קטגוריה",
 "live": "שידור חי",
 "live now": "משדר עכשיו",
 "offline": "לא משדר",
 "live channels": "ערוצים בשידור חי",
 "recommended": "מומלצים",
 "recommended channels": "ערוצים מומלצים",
 "for you": "בשבילך",
 "show more": "הצג עוד",
 "show less": "הצג פחות",
 "see all": "הצג הכול",
 "view all": "הצג הכול",
 "load more": "טען עוד",
 "clips": "קליפים",
 "clip": "קליפ",
 "videos": "סרטונים",
 "video": "סרטון",
 "vods": "הקלטות",
 "about": "אודות",
 "schedule": "לוח שידורים",
 "featured": "מומלצים",
 "popular": "פופולרי",
 "trending": "פופולרי עכשיו",
 "top": "מובילים",
 "new": "חדש",
 "most viewed": "הכי נצפים",
 "send a message": "שלח הודעה",
 "send message": "שלח הודעה",
 "send": "שלח",
 "cancel": "ביטול",
 "save": "שמור",
 "save changes": "שמור שינויים",
 "close": "סגור",
 "back": "חזרה",
 "next": "הבא",
 "previous": "הקודם",
 "done": "סיום",
 "continue": "המשך",
 "confirm": "אישור",
 "ok": "אישור",
 "yes": "כן",
 "no": "לא",
 "edit": "עריכה",
 "delete": "מחיקה",
 "remove": "הסרה",
 "copy": "העתק",
 "copy link": "העתק קישור",
 "share": "שיתוף",
 "report": "דיווח",
 "reply": "תגובה",
 "replying to": "משיב ל",
 "mute": "השתק",
 "unmute": "בטל השתקה",
 "ban": "חסימה",
 "timeout": "הרחקה זמנית",
 "apply": "החל",
 "reset": "איפוס",
 "clear": "נקה",
 "upload": "העלאה",
 "download": "הורדה",
 "add": "הוסף",
 "create": "צור",
 "update": "עדכן",
 "settings": "הגדרות",
 "preferences": "העדפות",
 "account": "חשבון",
 "profile": "פרופיל",
 "my profile": "הפרופיל שלי",
 "security": "אבטחה",
 "privacy": "פרטיות",
 "notifications": "התראות",
 "connections": "חיבורים",
 "wallet": "ארנק",
 "dashboard": "לוח בקרה",
 "creator dashboard": "לוח בקרה ליוצרים",
 "go live": "התחל שידור",
 "stream manager": "מנהל שידור",
 "language": "שפה",
 "languages": "שפות",
 "email": "אימייל",
 "password": "סיסמה",
 "username": "שם משתמש",
 "forgot password?": "שכחת סיסמה?",
 "remember me": "זכור אותי",
 "or": "או",
 "continue with google": "המשך עם Google",
 "continue with apple": "המשך עם Apple",
 "all": "הכול",
 "all languages": "כל השפות",
 "sort by": "מיין לפי",
 "filter": "סינון",
 "filters": "סינונים",
 "tags": "תגיות",
 "viewers (high to low)": "צופים (מהגבוה לנמוך)",
 "viewers (low to high)": "צופים (מהנמוך לגבוה)",
 "recently started": "התחילו לאחרונה",
 "last 24 hours": "24 השעות האחרונות",
 "last 7 days": "7 הימים האחרונים",
 "last 30 days": "30 הימים האחרונים",
 "all time": "כל הזמנים",
 "today": "היום",
 "this week": "השבוע",
 "this month": "החודש",
 "viewers": "צופים",
 "viewer": "צופה",
 "views": "צפיות",
 "view": "צפייה",
 "live viewers": "צופים בשידור",
 "chat": "צ׳אט",
 "chatroom": "חדר צ׳אט",
 "live chat": "צ׳אט חי",
 "welcome to the chat room!": "ברוכים הבאים לחדר הצ׳אט!",
 "welcome to chat!": "ברוכים הבאים לצ׳אט!",
 "pinned message": "הודעה נעוצה",
 "pinned": "נעוץ",
 "moderator": "מנהל",
 "broadcaster": "משדר",
 "founder": "מייסד",
 "poll": "סקר",
 "prediction": "ניחוש",
 "predictions": "ניחושים",
 "emotes": "אמוג׳י",
 "emote": "אמוג׳י",
 "theatre mode": "מצב קולנוע",
 "fullscreen": "מסך מלא",
 "exit fullscreen": "יציאה ממסך מלא",
 "quality": "איכות",
 "auto": "אוטומטי",
 "volume": "עוצמת שמע",
 "play": "נגן",
 "pause": "השהה",
 "streaming": "משדר",
 "streamers": "סטרימרים",
 "streamer": "סטרימר",
 "channel": "ערוץ",
 "channels": "ערוצים",
 "game": "משחק",
 "games": "משחקים",
 "terms of service": "תנאי שימוש",
 "privacy policy": "מדיניות פרטיות",
 "community guidelines": "הנחיות הקהילה",
 "help": "עזרה",
 "support": "תמיכה",
 "contact us": "צור קשר",
 "careers": "קריירה",
 "download app": "הורד אפליקציה",
 "get the app": "הורד את האפליקציה",
 "loading...": "טוען...",
 "loading": "טוען",
 "no results found": "לא נמצאו תוצאות",
 "no results": "אין תוצאות",
 "something went wrong": "משהו השתבש",
 "try again": "נסה שוב",
 "retry": "נסה שוב",
 "sign in": "כניסה",
 "register": "הרשמה",
 "create account": "יצירת חשבון",
 "welcome back": "ברוך שובך",
 "already have an account?": "כבר יש לך חשבון?",
 "don't have an account?": "אין לך חשבון?",
 "verify": "אימות",
 "verification code": "קוד אימות",
 "resend code": "שלח קוד שוב",
 "birthday": "תאריך לידה",
 "date of birth": "תאריך לידה",
 "confirm password": "אימות סיסמה",
 "new password": "סיסמה חדשה",
 "current password": "סיסמה נוכחית",
 "change password": "שינוי סיסמה",
 "two-factor authentication": "אימות דו-שלבי",
 "2fa": "אימות דו-שלבי",
 "enable": "הפעל",
 "disable": "השבת",
 "enabled": "מופעל",
 "disabled": "מושבת",
 "on": "פועל",
 "off": "כבוי",
 "display name": "שם תצוגה",
 "bio": "אודות",
 "avatar": "תמונת פרופיל",
 "banner": "באנר",
 "change": "שינוי",
 "choose file": "בחר קובץ",
 "browse files": "עיון בקבצים",
 "drag and drop": "גרור ושחרר",
 "learn more": "למידע נוסף",
 "read more": "קרא עוד",
 "see more": "הצג עוד",
 "more": "עוד",
 "less": "פחות",
 "menu": "תפריט",
 "open menu": "פתח תפריט",
 "close menu": "סגור תפריט",
 "expand": "הרחב",
 "collapse": "כווץ",
 "collapse sidebar": "כווץ סרגל צד",
 "expand sidebar": "הרחב סרגל צד",
 "toggle theme": "החלף ערכת נושא",
 "dark mode": "מצב כהה",
 "light mode": "מצב בהיר",
 "theme": "ערכת נושא",
 "dark": "כהה",
 "light": "בהיר",
 "system": "מערכת",
 "browse all": "עיון בכל הקטגוריות",
 "all categories": "כל הקטגוריות",
 "top categories": "קטגוריות מובילות",
 "popular categories": "קטגוריות פופולריות",
 "recommended categories": "קטגוריות מומלצות",
 "followed categories": "קטגוריות במעקב",
 "live streams": "שידורים חיים",
 "top live streams": "שידורים חיים מובילים",
 "top streamers": "סטרימרים מובילים",
 "top clips": "קליפים מובילים",
 "trending clips": "קליפים פופולריים",
 "new clips": "קליפים חדשים",
 "new streamers": "סטרימרים חדשים",
 "your followed channels": "הערוצים שאתה עוקב אחריהם",
 "followed channels": "ערוצים במעקב",
 "recommended streams": "שידורים מומלצים",
 "continue watching": "המשך צפייה",
 "watch later": "צפה אחר כך",
 "watch history": "היסטוריית צפייה",
 "history": "היסטוריה",
 "recently watched": "נצפו לאחרונה",
 "your channels": "הערוצים שלך",
 "most popular": "הכי פופולריים",
 "newest": "החדשים ביותר",
 "oldest": "הישנים ביותר",
 "highest viewers": "הכי הרבה צופים",
 "lowest viewers": "הכי מעט צופים",
 "recommended for you": "מומלץ בשבילך",
 "because you watched": "כי צפית ב",
 "browse categories": "עיון בקטגוריות",
 "browse channels": "עיון בערוצים",
 "about me": "קצת עליי",
 "panels": "פאנלים",
 "social links": "קישורים חברתיים",
 "links": "קישורים",
 "past broadcasts": "שידורים קודמים",
 "highlights": "רגעים נבחרים",
 "uploads": "העלאות",
 "featured clip": "קליפ מומלץ",
 "created by": "נוצר על ידי",
 "clipped by": "נחתך על ידי",
 "share clip": "שתף קליפ",
 "download clip": "הורד קליפ",
 "create clip": "צור קליפ",
 "clip title": "כותרת הקליפ",
 "publish": "פרסם",
 "draft": "טיוטה",
 "stream": "שידור",
 "stream ended": "השידור הסתיים",
 "started streaming": "התחיל לשדר",
 "chat settings": "הגדרות צ׳אט",
 "chat rules": "חוקי הצ׳אט",
 "slow mode": "מצב איטי",
 "followers only": "לעוקבים בלבד",
 "subscribers only": "למנויים בלבד",
 "emotes only": "אמוג׳י בלבד",
 "clear chat": "נקה צ׳אט",
 "hide chat": "הסתר צ׳אט",
 "show chat": "הצג צ׳אט",
 "pop out chat": "פתח צ׳אט בחלון נפרד",
 "popout chat": "פתח צ׳אט בחלון נפרד",
 "chat filters": "סינוני צ׳אט",
 "mentions": "אזכורים",
 "highlight": "הדגש",
 "reply to": "תגובה ל",
 "delete message": "מחק הודעה",
 "timeout user": "הרחק משתמש",
 "ban user": "חסום משתמש",
 "unban": "בטל חסימה",
 "report message": "דווח על הודעה",
 "copy message": "העתק הודעה",
 "pin message": "נעץ הודעה",
 "unpin message": "בטל נעיצה",
 "view profile": "צפה בפרופיל",
 "mention": "אזכר",
 "block": "חסום",
 "unblock": "בטל חסימה",
 "welcome to the stream": "ברוכים הבאים לשידור",
 "say something": "כתוב משהו",
 "type a message": "הקלד הודעה",
 "chat is empty": "הצ׳אט ריק",
 "message": "הודעה",
 "messages": "הודעות",
 "new messages": "הודעות חדשות",
 "scroll to bottom": "גלול לתחתית",
 "chat paused": "הצ׳אט מושהה",
 "chat is paused": "הצ׳אט מושהה",
 "resume": "המשך",
 "you are timed out": "הורחקת זמנית",
 "you are banned": "נחסמת",
 "subscription": "מנוי",
 "subscribe now": "הירשם עכשיו",
 "resubscribe": "חדש מנוי",
 "renew": "חידוש",
 "cancel subscription": "בטל מנוי",
 "manage subscription": "נהל מנוי",
 "gift subscription": "מנוי במתנה",
 "gifted subs": "מנויים שניתנו במתנה",
 "gift a subscription": "תן מנוי במתנה",
 "tier 1": "דרגה 1",
 "tier 2": "דרגה 2",
 "tier 3": "דרגה 3",
 "payment method": "אמצעי תשלום",
 "payment methods": "אמצעי תשלום",
 "add payment method": "הוסף אמצעי תשלום",
 "billing": "חיוב",
 "billing history": "היסטוריית חיובים",
 "invoice": "חשבונית",
 "receipt": "קבלה",
 "total": "סה״כ",
 "price": "מחיר",
 "free": "חינם",
 "balance": "יתרה",
 "tip": "טיפ",
 "donate": "תרומה",
 "donations": "תרומות",
 "your subscriptions": "המנויים שלך",
 "active": "פעיל",
 "expired": "פג תוקף",
 "expires": "בתוקף עד",
 "renews on": "מתחדש ב",
 "analytics": "אנליטיקה",
 "stream info": "פרטי שידור",
 "stream title": "כותרת השידור",
 "stream key": "מפתח שידור",
 "stream url": "כתובת שידור",
 "copy key": "העתק מפתח",
 "show key": "הצג מפתח",
 "hide key": "הסתר מפתח",
 "reset key": "אפס מפתח",
 "mature content": "תוכן למבוגרים",
 "mature": "למבוגרים",
 "moderation": "ניהול",
 "moderators": "מנהלים",
 "vips": "VIPs",
 "banned users": "משתמשים חסומים",
 "timeouts": "הרחקות זמניות",
 "bans": "חסימות",
 "automod": "ניהול אוטומטי",
 "alerts": "התראות שידור",
 "overlays": "שכבות",
 "widgets": "ווידג׳טים",
 "revenue": "הכנסות",
 "payouts": "תשלומים",
 "earnings": "רווחים",
 "average viewers": "ממוצע צופים",
 "peak viewers": "שיא צופים",
 "duration": "משך",
 "date": "תאריך",
 "time": "שעה",
 "status": "סטטוס",
 "actions": "פעולות",
 "name": "שם",
 "title": "כותרת",
 "description": "תיאור",
 "type": "סוג",
 "select": "בחר",
 "select all": "בחר הכול",
 "none": "ללא",
 "optional": "אופציונלי",
 "required": "שדה חובה",
 "invalid email": "אימייל לא תקין",
 "go to dashboard": "עבור ללוח הבקרה",
 "mark all as read": "סמן הכול כנקרא",
 "no notifications": "אין התראות",
 "notification settings": "הגדרות התראות",
 "clear all": "נקה הכול",
 "mark as read": "סמן כנקרא",
 "unread": "לא נקרא",
 "read": "נקרא",
 "new notification": "התראה חדשה",
 "you have no notifications": "אין לך התראות",
 "about us": "אודות",
 "blog": "בלוג",
 "press": "עיתונות",
 "partners": "שותפים",
 "developers": "מפתחים",
 "cookie settings": "הגדרות עוגיות",
 "cookie policy": "מדיניות עוגיות",
 "accept all": "אשר הכול",
 "accept": "אשר",
 "decline": "דחה",
 "reject all": "דחה הכול",
 "manage preferences": "ניהול העדפות",
 "refund policy": "מדיניות החזרים",
 "all rights reserved": "כל הזכויות שמורות",
 "terms": "תנאים",
 "legal": "משפטי",
 "safety": "בטיחות",
 "trust and safety": "אמון ובטיחות",
 "just now": "עכשיו",
 "yesterday": "אתמול",
 "tomorrow": "מחר",
 "now": "עכשיו",
 "this year": "השנה",
 "last week": "שבוע שעבר",
 "last month": "חודש שעבר",
 "last year": "שנה שעברה",
 "captions": "כתוביות",
 "speed": "מהירות",
 "normal": "רגיל",
 "playback speed": "מהירות ניגון",
 "picture in picture": "תמונה בתוך תמונה",
 "mini player": "נגן מוקטן",
 "theater mode": "מצב קולנוע",
 "exit theater mode": "יציאה ממצב קולנוע",
 "back to live": "חזרה לשידור החי",
 "jump to live": "קפוץ לשידור החי",
 "ad": "פרסומת",
 "advertisement": "פרסומת",
 "your stream will resume shortly": "השידור יחזור בעוד רגע",
 "channel is offline": "הערוץ לא משדר כרגע",
 "playing": "מנגן",
 "paused": "מושהה",
 "muted": "מושתק",
 "enter fullscreen": "מסך מלא",
 "skip": "דלג",
 "replay": "נגן שוב",
 "live stream": "שידור חי",
 "watch live": "צפה בשידור חי",
 "watch now": "צפה עכשיו",
 "watch": "צפה",
 "watching": "צופים",
 "offline channel": "ערוץ לא משדר",
 "this channel is currently offline": "הערוץ לא משדר כרגע",
 "come back later": "חזור מאוחר יותר",
 "page not found": "הדף לא נמצא",
 "not found": "לא נמצא",
 "access denied": "הגישה נדחתה",
 "unauthorized": "אין הרשאה",
 "forbidden": "אסור",
 "network error": "שגיאת רשת",
 "connection lost": "החיבור אבד",
 "reconnecting...": "מתחבר מחדש...",
 "reconnecting": "מתחבר מחדש",
 "connected": "מחובר",
 "disconnected": "מנותק",
 "refresh": "רענן",
 "reload": "טען מחדש",
 "go back": "חזור",
 "go home": "לדף הבית",
 "back to home": "חזרה לדף הבית",
 "take me home": "קח אותי הביתה",
 "oops!": "אופס!",
 "oops": "אופס",
 "sorry": "סליחה",
 "success": "הצלחה",
 "error": "שגיאה",
 "warning": "אזהרה",
 "info": "מידע",
 "saved": "נשמר",
 "copied": "הועתק",
 "copied!": "הועתק!",
 "link copied": "הקישור הועתק",
 "link copied!": "הקישור הועתק!",
 "please wait": "אנא המתן",
 "please try again later": "נסה שוב מאוחר יותר",
 "too many requests": "יותר מדי בקשות",
 "maintenance": "תחזוקה",
 "coming soon": "בקרוב",
 "share this channel": "שתף את הערוץ",
 "share link": "שתף קישור",
 "embed": "הטמעה",
 "copy embed code": "העתק קוד הטמעה",
 "copy url": "העתק כתובת",
 "share on twitter": "שתף בטוויטר",
 "share on facebook": "שתף בפייסבוק",
 "share to": "שתף ל",
 "open in new tab": "פתח בכרטיסייה חדשה",
 "new tab": "כרטיסייה חדשה",
 "settings saved": "ההגדרות נשמרו",
 "changes saved": "השינויים נשמרו",
 "unsaved changes": "שינויים שלא נשמרו",
 "discard": "בטל שינויים",
 "are you sure?": "בטוח?",
 "this action cannot be undone": "אי אפשר לבטל את הפעולה הזאת",
 "delete account": "מחק חשבון",
 "deactivate": "השבת חשבון",
 "language preferences": "העדפות שפה",
 "content language": "שפת התוכן",
 "show mature content": "הצג תוכן למבוגרים",
 "autoplay": "ניגון אוטומטי",
 "show viewer count": "הצג מספר צופים",
 "hide viewer count": "הסתר מספר צופים",
 "sound": "שמע",
 "audio": "שמע",
 "help center": "מרכז עזרה",
 "faq": "שאלות נפוצות",
 "feedback": "משוב",
 "send feedback": "שלח משוב",
 "report a problem": "דווח על בעיה",
 "report bug": "דווח על באג",
 "contact support": "פנה לתמיכה",
 "submit": "שלח",
 "search channels": "חיפוש ערוצים",
 "search categories": "חיפוש קטגוריות",
 "search for channels": "חיפוש ערוצים",
 "search for categories": "חיפוש קטגוריות",
 "search results": "תוצאות חיפוש",
 "results": "תוצאות"
};
  var HE_UNITS = { second: ['שנייה', 'שניות'], minute: ['דקה', 'דקות'], hour: ['שעה', 'שעות'], day: ['יום', 'ימים'],
    week: ['שבוע', 'שבועות'], month: ['חודש', 'חודשים'], year: ['שנה', 'שנים'] };
  var HE_PATTERNS = [
    [/^([\d.,]+[KkMm]?) viewers?$/, function (m) { return m[1] + ' צופים'; }],
    [/^([\d.,]+[KkMm]?) followers?$/, function (m) { return m[1] + ' עוקבים'; }],
    [/^([\d.,]+[KkMm]?) subscribers?$/, function (m) { return m[1] + ' מנויים'; }],
    [/^([\d.,]+[KkMm]?) views?$/, function (m) { return m[1] + ' צפיות'; }],
    [/^([\d.,]+[KkMm]?) clips?$/, function (m) { return m[1] + ' קליפים'; }],
    [/^([\d.,]+[KkMm]?) watching$/i, function (m) { return m[1] + ' צופים'; }],
    [/^([\d.,]+[KkMm]?) following$/i, function (m) { return m[1] + ' במעקב'; }],
    [/^(\d+) (day|week|month|year)s?$/i, function (m) {
      var n = parseInt(m[1], 10), u = HE_UNITS[m[2].toLowerCase()];
      return n === 1 ? u[0] : n + ' ' + u[1];
    }],
    [/^gift (\d+) subs?$/i, function (m) { return 'תן במתנה ' + m[1] + ' מנויים'; }],
    [/^(.+) is live$/i, function (m) { return m[1] + ' משדר עכשיו'; }],
    [/^(.+) is offline$/i, function (m) { return m[1] + ' לא משדר'; }],
    [/^streaming (.+)$/i, function (m) { return 'משדר ' + m[1]; }],
    [/^replying to @?(.+)$/i, function (m) { return 'משיב ל-' + m[1]; }],
    [/^welcome to (.+?)['’]s (?:chat ?room|chat)!?$/i, function (m) { return 'ברוכים הבאים לצ׳אט של ' + m[1] + '!'; }],
    [/^page (\d+) of (\d+)$/i, function (m) { return 'עמוד ' + m[1] + ' מתוך ' + m[2]; }],
    [/^showing (\d+) of (\d+)$/i, function (m) { return 'מוצגים ' + m[1] + ' מתוך ' + m[2]; }],
    [/^(\d+) results?$/i, function (m) { return m[1] + ' תוצאות'; }],
    [/^follow (.+)$/i, function (m) { return 'עקוב אחרי ' + m[1]; }],
    [/^subscribe to (.+)$/i, function (m) { return 'הירשם כמנוי של ' + m[1]; }],
    [/^(\d+) (second|minute|hour|day|week|month|year)s? ago$/i, function (m) {
      var n = parseInt(m[1], 10), u = HE_UNITS[m[2].toLowerCase()];
      return n === 1 ? 'לפני ' + u[0] : 'לפני ' + n + ' ' + u[1];
    }]
  ];
  var HE_SKIP = { SCRIPT: 1, STYLE: 1, TEXTAREA: 1, INPUT: 1, CODE: 1, PRE: 1, NOSCRIPT: 1, SVG: 1 };
  var heCustom = {}, heSeen = {}, heSeenN = 0;
  var heOn = isKick() && SET.hebrew === true && !SAFE;

  function heParseCustom() {
    heCustom = {};
    String(SET.dict || '').split('\n').forEach(function (ln) {
      var i = ln.indexOf('=');
      if (i < 1) return;
      var k = ln.slice(0, i).trim().toLowerCase(), v = ln.slice(i + 1).trim();
      if (k && v) heCustom[k] = v;
    });
  }
  function heLookup(raw) {
    var t = String(raw).replace(/\s+/g, ' ').trim();
    if (!t || t.length > 60) return null;
    var k = t.toLowerCase();
    if (Object.prototype.hasOwnProperty.call(heCustom, k)) return heCustom[k];
    if (Object.prototype.hasOwnProperty.call(HE_DICT, k)) return HE_DICT[k];
    for (var i = 0; i < HE_PATTERNS.length; i++) {
      var m = HE_PATTERNS[i][0].exec(t);
      if (m) return HE_PATTERNS[i][1](m);
    }
    return null;
  }
  function heNode(n) {
    var raw = n.nodeValue;
    if (!raw || !/[A-Za-z]/.test(raw)) return;
    var p = n.parentNode;
    if (!p || HE_SKIP[(p.tagName || '').toUpperCase()] || p.isContentEditable) return;
    var r = heLookup(raw);
    if (r === null) {
      var t = raw.trim();
      if (t.length >= 2 && t.length <= 40 && /^[A-Za-z][A-Za-z0-9 '’&.,!?:\-\/+()]*$/.test(t) && heSeenN < 500 && !heSeen[t.toLowerCase()]) {
        heSeen[t.toLowerCase()] = t; heSeenN++;
      }
      return;
    }
    var lead = raw.match(/^\s*/)[0], trail = raw.match(/\s*$/)[0];
    var nv = lead + r + trail;
    if (nv !== raw) n.nodeValue = nv;
  }
  function heAttrs(el) {
    ['placeholder', 'title', 'aria-label', 'alt'].forEach(function (a) {
      var v = el.getAttribute && el.getAttribute(a);
      if (!v) return;
      var r = heLookup(v);
      if (r !== null && r !== v) el.setAttribute(a, r);
    });
  }
  function heScan(root) {
    if (!root) return;
    if (root.nodeType === 3) { heNode(root); return; }
    if (root.nodeType !== 1 && root.nodeType !== 9) return;
    var w = document.createTreeWalker(root, 4), n;
    while ((n = w.nextNode())) heNode(n);
    if (root.nodeType === 1) heAttrs(root);
    var els = root.querySelectorAll ? root.querySelectorAll('[placeholder],[title],[aria-label],[alt]') : [];
    for (var i = 0; i < els.length && i < 800; i++) heAttrs(els[i]);
  }
  var hePending = [], heTimer = null;
  function heFlush() {
    heTimer = null;
    var arr = hePending; hePending = [];
    for (var i = 0; i < arr.length; i++) { try { if (arr[i].isConnected !== false) heScan(arr[i]); } catch (e) {} }
  }
  function heQueue(n) { hePending.push(n); if (!heTimer) heTimer = setTimeout(heFlush, 250); }
  function heInit() {
    heParseCustom();
    if (!heOn || !document.body) return;
    heScan(document.body);
    setTimeout(function () { heScan(document.body); }, 1200);
    setTimeout(function () { heScan(document.body); }, 3500);
    try {
      new MutationObserver(function (muts) {
        for (var i = 0; i < muts.length; i++) {
          var m = muts[i];
          if (m.type === 'characterData') { heQueue(m.target); continue; }
          for (var j = 0; j < m.addedNodes.length; j++) heQueue(m.addedNodes[j]);
        }
      }).observe(document.body, { childList: true, subtree: true, characterData: true });
    } catch (e) {}
    if (SET.rtl === true) addSheet('html, body { direction: rtl !important; }');
  }

  // ----- עורך מילון אישי + רשימת מחרוזות שלא תורגמו -----
  function showDict(prefill) {
    openModal('kickbob-dict', function (box, line, close) {
      box.style.width = '620px';
      line('📖 מילון תרגומים אישי', { color: GREEN, fontSize: '22px', fontWeight: '800', marginBottom: '6px' });
      line('כל שורה: טקסט באנגלית = התרגום בעברית. התרגום האישי גובר על המילון המובנה.', { fontSize: '12px', color: '#9aa0a6', marginBottom: '10px' });
      var ta = document.createElement('textarea'); ta.setAttribute('dir', 'auto'); ta.spellcheck = false;
      ta.value = (SET.dict || '') + (prefill ? ((SET.dict ? '\n' : '') + prefill) : '');
      ta.placeholder = 'Follow = עקוב\nShow More = הצג עוד';
      Object.assign(ta.style, { width: '100%', height: '260px', boxSizing: 'border-box', background: '#1c1c20', color: '#e8eaed',
        border: '1px solid #3c4043', borderRadius: '8px', padding: '10px', fontFamily: 'Consolas, monospace', fontSize: '13px', resize: 'vertical' });
      ['keydown', 'keypress', 'keyup'].forEach(function (ev) { ta.addEventListener(ev, function (e) { e.stopPropagation(); }); });
      box.appendChild(ta);
      var msg = line('', { fontSize: '12px', color: '#9aa0a6', margin: '8px 0' });
      var row = document.createElement('div'); Object.assign(row.style, { display: 'flex', gap: '8px', justifyContent: 'center' });
      row.appendChild(mk('שמור והחל', 'שמור את המילון והחל מיד', function () {
        SET.dict = ta.value.slice(0, 30000); saveSet(); heParseCustom();
        try { if (heOn) heScan(document.body); } catch (e) {}
        msg.textContent = 'נשמר והוחל. אם הסרת שורות, רענן את הדף כדי לראות את הטקסט המקורי.';
      }, true));
      row.appendChild(mk('סגור', 'סגור', close));
      box.appendChild(row);
    });
  }
  function showUntranslated() {
    openModal('kickbob-untr', function (box, line, close) {
      box.style.width = '560px';
      line('🔎 טקסטים שעוד לא תורגמו', { color: GREEN, fontSize: '22px', fontWeight: '800', marginBottom: '6px' });
      var keys = Object.keys(heSeen);
      if (!heOn) line('התרגום כבוי או שאתה לא באתר Kick, ולכן לא נאספו טקסטים.', { fontSize: '13px', color: '#f28b82', marginBottom: '10px' });
      line(keys.length ? 'נמצאו ' + keys.length + ' טקסטים באנגלית בדפים שביקרת בהם. אפשר להעביר אותם למילון ולמלא תרגום.'
                       : 'עוד לא נאספו טקסטים. גלוש באתר Kick ואז חזור לכאן.', { fontSize: '12px', color: '#9aa0a6', marginBottom: '10px' });
      var lines = keys.map(function (k) { return heSeen[k] + ' = '; }).join('\n');
      var ta = document.createElement('textarea'); ta.readOnly = true; ta.value = lines; ta.setAttribute('dir', 'ltr');
      Object.assign(ta.style, { width: '100%', height: '240px', boxSizing: 'border-box', background: '#1c1c20', color: '#e8eaed',
        border: '1px solid #3c4043', borderRadius: '8px', padding: '10px', fontFamily: 'Consolas, monospace', fontSize: '13px' });
      box.appendChild(ta);
      var row = document.createElement('div'); Object.assign(row.style, { display: 'flex', gap: '8px', justifyContent: 'center', marginTop: '12px' });
      if (keys.length) row.appendChild(mk('העבר למילון', 'פותח את עורך המילון עם הטקסטים האלה', function () { close(); showDict(lines); }, true));
      row.appendChild(mk('סגור', 'סגור', close));
      box.appendChild(row);
    });
  }

  // ----- שאלה בהפעלה ראשונה -----
  function askHebrew() {
    if (!isKick() || SAFE || SET.hebrewAsked) return;
    openModal('kickbob-lang', function (box, line, close) {
      line('Kick בעברית', { color: GREEN, fontSize: '28px', fontWeight: '800', marginBottom: '10px' });
      line('רוצה שקיקבוב יתרגם את הממשק של Kick לעברית?', { fontSize: '17px', marginBottom: '8px' });
      line('זה תרגום אוטומטי של כפתורים, תפריטים וכותרות נפוצים. הצ׳אט ושמות הסטרימרים נשארים כמו שהם. אפשר לשנות בכל רגע בהגדרות, בסעיף "שפה".',
           { fontSize: '12px', color: '#9aa0a6', lineHeight: '1.6', marginBottom: '18px' });
      var row = document.createElement('div'); Object.assign(row.style, { display: 'flex', gap: '10px', justifyContent: 'center' });
      row.appendChild(mk('כן, תרגם לעברית', 'הפעל תרגום', function () { SET.hebrew = true; SET.hebrewAsked = true; saveSet(); location.reload(); }, true));
      row.appendChild(mk('לא, תודה', 'השאר באנגלית', function () { SET.hebrewAsked = true; saveSet(); close(); }));
      box.appendChild(row);
    });
  }

  // =====================================================================
  //  הצפייה שלי + מה חדש ומה בדרך
  // =====================================================================
  function fmtHM(sec) {
    var m = Math.floor((sec || 0) / 60);
    return m >= 60 ? Math.floor(m / 60) + ' שעות ו-' + (m % 60) + ' דקות' : m + ' דקות';
  }
  function watchedList() {
    var st = P.streamers || {}, out = [];
    Object.keys(st).forEach(function (k) { if (st[k] >= 60) out.push({ slug: k, sec: st[k], name: (P.names && P.names[k]) || k }); });
    out.sort(function (a, b) { return b.sec - a.sec; });
    return out;
  }
  function showWatched() {
    openModal('kickbob-watched', function (box, line, close) {
      box.style.width = '540px';
      var list = watchedList();
      line('📺 הצפייה שלי', { color: GREEN, fontSize: '22px', fontWeight: '800', marginBottom: '14px' });
      var tiles = document.createElement('div');
      Object.assign(tiles.style, { display: 'flex', gap: '10px', justifyContent: 'center', flexWrap: 'wrap', marginBottom: '16px' });
      function tile(big, small) {
        var t = document.createElement('div');
        Object.assign(t.style, { background: '#1c1c20', border: '1px solid #2f2f35', borderRadius: '12px', padding: '12px 14px', minWidth: '140px', flex: '1' });
        var b = document.createElement('div'); b.textContent = big; Object.assign(b.style, { fontSize: '22px', fontWeight: '800', color: GREEN, direction: 'auto' });
        var sm = document.createElement('div'); sm.textContent = small; Object.assign(sm.style, { fontSize: '12px', color: '#9aa0a6', marginTop: '2px' });
        t.appendChild(b); t.appendChild(sm); tiles.appendChild(t);
      }
      tile(String(list.length), 'סטרימרים שצפית בהם');
      tile(fmtHM(P.seconds), 'זמן צפייה כולל');
      tile(list[0] ? list[0].name : '-', 'הסטרימר המוביל');
      box.appendChild(tiles);
      if (!list.length) {
        line('עוד לא נספרו סטרימרים. כשסרטון מתנגן בדף של ערוץ, הזמן נספר.', { fontSize: '14px', color: '#b9b9c0', margin: '10px 0 14px' });
      } else {
        line('המובילים שלך', { fontWeight: '700', textAlign: 'right', marginBottom: '8px' });
        var max = list[0].sec;
        list.slice(0, 10).forEach(function (w, i) {
          var r = document.createElement('div');
          Object.assign(r.style, { display: 'flex', alignItems: 'center', gap: '10px', margin: '6px 0', textAlign: 'right' });
          var n = document.createElement('span'); n.textContent = String(i + 1); Object.assign(n.style, { width: '20px', color: '#9aa0a6', fontSize: '13px' });
          var a = document.createElement('a'); a.href = 'https://kick.com/' + encodeURIComponent(w.slug); a.textContent = w.name;
          Object.assign(a.style, { width: '130px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: '#fff', textDecoration: 'none', direction: 'ltr', textAlign: 'right' });
          a.addEventListener('click', function () { setTimeout(function () { var m = document.getElementById('kickbob-watched'); if (m) m.remove(); }, 60); });
          var bg = document.createElement('div'); Object.assign(bg.style, { flex: '1', height: '8px', background: '#2e2f33', borderRadius: '4px', overflow: 'hidden' });
          var fg = document.createElement('div'); Object.assign(fg.style, { height: '100%', width: Math.max(4, Math.round(w.sec / max * 100)) + '%', background: GREEN });
          bg.appendChild(fg);
          var tm = document.createElement('span'); tm.textContent = fmtHM(w.sec); Object.assign(tm.style, { width: '110px', fontSize: '12px', color: '#9aa0a6', textAlign: 'left' });
          r.appendChild(n); r.appendChild(a); r.appendChild(bg); r.appendChild(tm); box.appendChild(r);
        });
      }
      line('נספרים סטרימרים שצפית בהם לפחות דקה, כשהסרטון מנגן בדף הערוץ והחלון פעיל. הספירה מתחילה מגרסה 0.0.3_3.', { fontSize: '11px', color: '#777', margin: '14px 0' });
      var row = document.createElement('div'); Object.assign(row.style, { display: 'flex', gap: '8px', justifyContent: 'center' });
      row.appendChild(mk('רמות', 'פתח את חלון הרמות', function () { close(); showLevels(); }));
      row.appendChild(mk('סגור', 'סגור', close, true));
      box.appendChild(row);
    });
  }

  function showRoadmap(startTab) {
    openModal('kickbob-roadmap', function (box, line, close) {
      box.style.width = '580px';
      line('🗺️ מה חדש ומה בדרך', { color: GREEN, fontSize: '22px', fontWeight: '800', marginBottom: '12px' });
      var tabsEl = document.createElement('div');
      Object.assign(tabsEl.style, { display: 'flex', gap: '8px', justifyContent: 'center', marginBottom: '14px' });
      var bNew = mk('מה חדש', 'היסטוריית גרסאות', function () { render('new'); });
      var bNext = mk('מה בגרסה הבאה', 'תוכניות לגרסה הבאה', function () { render('next'); });
      tabsEl.appendChild(bNew); tabsEl.appendChild(bNext); box.appendChild(tabsEl);
      var body = document.createElement('div'); Object.assign(body.style, { textAlign: 'right' }); box.appendChild(body);
      function head(txt, extra) {
        var d = document.createElement('div'); d.textContent = txt;
        Object.assign(d.style, { fontWeight: '700', margin: '14px 0 6px', direction: 'ltr', textAlign: 'right' }, extra || {});
        body.appendChild(d); return d;
      }
      function bullet(txt, mark, color) {
        var d = document.createElement('div');
        Object.assign(d.style, { display: 'flex', gap: '10px', margin: '5px 0', fontSize: '14px', color: color || '#d6d6da' });
        var m = document.createElement('span'); m.textContent = mark; Object.assign(m.style, { flex: '0 0 auto', color: GREEN });
        var t = document.createElement('span'); t.textContent = txt;
        d.appendChild(m); d.appendChild(t); body.appendChild(d);
      }
      function render(which) {
        while (body.firstChild) body.removeChild(body.firstChild);
        [[bNew, 'new'], [bNext, 'next']].forEach(function (p) {
          var on = p[1] === which;
          p[0].style.background = on ? GREEN : '#3c4043'; p[0].style.color = on ? '#000' : '#e8eaed';
        });
        if (which === 'new') {
          (INFO.changelog || []).forEach(function (c, i) {
            head(c.v + (i === 0 ? '  (הגרסה שלך)' : ''), i === 0 ? { color: GREEN } : null);
            (c.items || []).forEach(function (it) { bullet(it, '•'); });
          });
        } else {
          var rm = INFO.roadmap || {};
          head(rm.next || '', { color: GREEN, fontSize: '16px' });
          line2('תוכניות לגרסה הבאה. הן עשויות להשתנות.');
          (rm.items || []).forEach(function (it) { bullet(it, '◻'); });
          if ((rm.later || []).length) {
            head('אחר כך', { direction: 'rtl' });
            rm.later.forEach(function (it) { bullet(it, '◌', '#9aa0a6'); });
          }
        }
      }
      function line2(txt) {
        var d = document.createElement('div'); d.textContent = txt;
        Object.assign(d.style, { fontSize: '12px', color: '#9aa0a6', marginBottom: '6px' }); body.appendChild(d);
      }
      render(startTab === 'next' ? 'next' : 'new');
      var sp = document.createElement('div'); sp.style.height = '16px'; box.appendChild(sp);
      box.appendChild(mk('סגור', 'סגור', close, true));
    });
  }

  // =====================================================================
  //  סימניות, מועדפים, התראות שידור, היסטוריית צפייה ועדכונים
  // =====================================================================
  function hh(tag, css, text) {
    var e = document.createElement(tag);
    if (css) Object.assign(e.style, css);
    if (text !== undefined) e.textContent = text;
    return e;
  }
  function stopKeys(el) { ['keydown', 'keypress', 'keyup'].forEach(function (ev) { el.addEventListener(ev, function (e) { e.stopPropagation(); }); }); }
  function fieldCss(el) {
    Object.assign(el.style, { background: '#1c1c20', color: '#e8eaed', border: '1px solid #3c4043', borderRadius: '8px',
      padding: '8px 10px', fontSize: '13px', fontFamily: 'inherit', outline: 'none' });
    return el;
  }
  var bannersOpen = 0;
  function banner(text, sub, onClick, color) {
    var gone = false;
    var b = hh('div', { position: 'fixed', top: (BAR_H + 10 + bannersOpen * 78) + 'px', right: '14px', width: '320px', background: '#292a2d',
      color: '#e8eaed', border: '1px solid ' + (color || GREEN), borderRadius: '12px', padding: '12px 16px', zIndex: '2147483646', cursor: 'pointer',
      boxShadow: '0 8px 28px rgba(0,0,0,0.55)', fontFamily: "'Segoe UI', Arial, sans-serif", fontSize: '14px' });
    b.setAttribute('dir', 'rtl'); b.id = 'kickbob-banner-' + Date.now();
    b.appendChild(hh('div', { fontWeight: '700' }, text));
    if (sub) b.appendChild(hh('div', { fontSize: '12px', color: '#9aa0a6', marginTop: '3px' }, sub));
    bannersOpen++;
    function done() { if (gone) return; gone = true; b.remove(); bannersOpen = Math.max(0, bannersOpen - 1); }
    b.onclick = function () { done(); if (onClick) onClick(); };
    setTimeout(done, 12000);
    document.documentElement.appendChild(b);
  }
  // התראת שידור מהחלון הנסתר (Python קורא לפונקציה הזאת בכרטיסייה הפעילה)
  window.__kbLive = function (o) {
    try {
      banner(o.title || 'ערוץ עלה לשידור', o.body || '', function () {
        if (o.url && /^https:\/\/kick\.com\//.test(o.url)) location.href = o.url;
      }, '#ff5a5a');
    } catch (e) {}
  };

  // ----- סימניות -----
  var BM = Array.isArray(CFG.bookmarks) ? CFG.bookmarks.slice(0, 500) : [];
  function saveBM() { persist('bookmarks', BM); }
  function bmIndex(u) { for (var i = 0; i < BM.length; i++) if (BM[i].url === u) return i; return -1; }
  function updateStar() {
    if (typeof omniStar === 'undefined' || !omniStar) return;
    var on = bmIndex(location.href) >= 0;
    omniStar.textContent = on ? '★' : '☆';
    omniStar.style.color = on ? '#fdd663' : '#9aa0a6';
    omniStar.title = on ? 'הסר מהסימניות (Ctrl+D)' : 'הוסף לסימניות (Ctrl+D)';
  }
  function toggleBookmark() {
    var u = location.href;
    if (!/^https?:/i.test(u)) { toast('אי אפשר להוסיף את הדף הזה לסימניות'); return; }
    var i = bmIndex(u);
    if (i >= 0) { BM.splice(i, 1); toast('הסימנייה הוסרה'); }
    else { BM.unshift({ title: (document.title || u).slice(0, 120), url: u, added: Date.now() }); if (BM.length > 500) BM.pop(); toast('★ נוספה לסימניות'); }
    saveBM(); updateStar();
  }
  function showBookmarks() {
    openModal('kickbob-bm', function (box, line, close) {
      box.style.width = '620px';
      line('🔖 סימניות', { color: GREEN, fontSize: '22px', fontWeight: '800', marginBottom: '10px' });
      var q = fieldCss(hh('input')); q.type = 'text'; q.placeholder = 'חפש בסימניות'; q.style.width = '100%'; q.style.boxSizing = 'border-box'; stopKeys(q);
      box.appendChild(q);
      var list = hh('div', { textAlign: 'right', maxHeight: '42vh', overflowY: 'auto', margin: '10px 0' });
      box.appendChild(list);
      function render() {
        while (list.firstChild) list.removeChild(list.firstChild);
        var f = q.value.trim().toLowerCase(), n = 0;
        BM.forEach(function (b, i) {
          if (f && (b.title + ' ' + b.url).toLowerCase().indexOf(f) < 0) return;
          n++;
          var r = hh('div', { display: 'flex', alignItems: 'center', gap: '10px', padding: '7px 4px', borderBottom: '1px solid #26262c' });
          var host = ''; try { host = new URL(b.url).hostname; } catch (e) {}
          r.appendChild(hh('div', { width: '26px', height: '26px', lineHeight: '26px', textAlign: 'center', borderRadius: '50%', background: '#3c4043', color: GREEN, fontWeight: '700', flex: '0 0 auto' },
            ((host.replace(/^www\./, '').charAt(0)) || '?').toUpperCase()));
          var a = hh('a', { flex: '1', minWidth: '0', color: '#e8eaed', textDecoration: 'none', overflow: 'hidden' });
          a.href = b.url;
          a.appendChild(hh('div', { overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: '14px' }, b.title || b.url));
          a.appendChild(hh('div', { fontSize: '11px', color: '#9aa0a6', direction: 'ltr', textAlign: 'right', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }, host));
          a.addEventListener('click', function () { setTimeout(function () { var m = document.getElementById('kickbob-bm'); if (m) m.remove(); }, 60); });
          var x = hh('span', { cursor: 'pointer', color: '#9aa0a6', padding: '2px 6px' }, '✕'); x.title = 'מחק';
          x.onclick = function () { BM.splice(i, 1); saveBM(); updateStar(); render(); };
          r.appendChild(a); r.appendChild(x); list.appendChild(r);
        });
        if (!n) list.appendChild(hh('div', { color: '#9aa0a6', textAlign: 'center', padding: '24px 0' }, BM.length ? 'לא נמצאו סימניות' : 'עוד אין סימניות. לחץ על הכוכב בשורת הכתובת או Ctrl+D.'));
      }
      q.oninput = render; render();
      var ex = fieldCss(hh('textarea')); ex.setAttribute('dir', 'ltr'); ex.style.cssText += ';width:100%;box-sizing:border-box;height:54px;font-family:Consolas,monospace;font-size:11px';
      ex.placeholder = 'ייצוא / ייבוא: JSON של סימניות'; stopKeys(ex);
      var msg = hh('div', { fontSize: '12px', color: '#9aa0a6', margin: '6px 0' });
      var row = hh('div', { display: 'flex', gap: '8px', justifyContent: 'center', flexWrap: 'wrap', margin: '8px 0' });
      row.appendChild(mk('הוסף את הדף הנוכחי', 'הוסף או הסר', function () { toggleBookmark(); render(); }));
      row.appendChild(mk('ייצוא', 'מציג JSON', function () { ex.value = JSON.stringify(BM); ex.select(); msg.textContent = 'העתק את הטקסט.'; }));
      row.appendChild(mk('ייבוא', 'טוען JSON', function () {
        try {
          var arr = JSON.parse(ex.value), added = 0;
          arr.forEach(function (b) { if (b && /^https?:\/\//i.test(b.url || '') && bmIndex(b.url) < 0) { BM.push({ title: String(b.title || b.url).slice(0, 120), url: String(b.url).slice(0, 600), added: b.added || Date.now() }); added++; } });
          BM = BM.slice(0, 500); saveBM(); render(); updateStar(); msg.textContent = 'נוספו ' + added + ' סימניות.';
        } catch (e) { msg.textContent = 'הטקסט לא תקין.'; }
      }));
      box.appendChild(row); box.appendChild(ex); box.appendChild(msg);
      var cl = hh('div', { display: 'flex', justifyContent: 'center', marginTop: '6px' }); cl.appendChild(mk('סגור', 'סגור', close, true)); box.appendChild(cl);
    });
  }

  // ----- ערוצים מועדפים -----
  var FAV = Array.isArray(CFG.favorites) ? CFG.favorites.slice(0, 100) : [];
  function saveFav() { persist('favorites', FAV); }
  function favIdx(slug) { slug = String(slug || '').toLowerCase(); for (var i = 0; i < FAV.length; i++) if (FAV[i].slug === slug) return i; return -1; }
  function addFav(raw, name) {
    var slug = String(raw || '').trim().toLowerCase().replace(/^https?:\/\/(www\.)?kick\.com\//, '').replace(/[\/?#].*$/, '').replace(/^@/, '');
    if (!/^[a-z0-9_-]{1,40}$/.test(slug)) return 'bad';
    if (favIdx(slug) >= 0) return 'dup';
    FAV.push({ slug: slug, name: name || slug, added: Date.now() });
    if (FAV.length > 100) FAV.shift();
    saveFav();
    return 'ok';
  }
  function liveState() {
    var a = api();
    if (!a || !a.get_live_state) return Promise.resolve({});
    return a.get_live_state().then(function (s) { try { return JSON.parse(s || '{}'); } catch (e) { return {}; } }, function () { return {}; });
  }
  function importFollows(done) {
    if (!isKick()) { done('כדי לייבא, פתח כרטיסייה באתר Kick (כשאתה מחובר לחשבון) ונסה שוב.', 0); return; }
    var added = 0;
    function page(cursor, left) {
      return fetch('/api/v2/channels/followed' + (cursor ? '?cursor=' + encodeURIComponent(cursor) : ''), { credentials: 'include', headers: { 'Accept': 'application/json' } })
        .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
        .then(function (d) {
          var list = (d && (d.channels || d.data)) || [];
          list.forEach(function (c) {
            var slug = c.channel_slug || c.slug || (c.channel && c.channel.slug);
            if (slug && addFav(slug, c.user_username || c.username) === 'ok') added++;
          });
          var next = d && (d.nextCursor || d.next_cursor);
          if (next && left > 1) return page(next, left - 1);
        });
    }
    page(null, 6).then(function () { done(added ? 'יובאו ' + added + ' ערוצים.' : 'לא נמצאו ערוצים חדשים לייבוא.', added); },
      function (e) { done('הייבוא נכשל (' + ((e && e.message) || e) + '). אפשר להוסיף ערוצים ידנית.', added); });
  }
  function showFavorites() {
    openModal('kickbob-fav', function (box, line, close) {
      box.style.width = '580px';
      line('⭐ ערוצים מועדפים', { color: GREEN, fontSize: '22px', fontWeight: '800', marginBottom: '4px' });
      line('כשערוץ מהרשימה עולה לשידור תקבל התראה. הרשימה מופיעה גם בדף הבית.', { fontSize: '12px', color: '#9aa0a6', marginBottom: '12px' });
      var addRow = hh('div', { display: 'flex', gap: '8px' });
      var inp = fieldCss(hh('input')); inp.type = 'text'; inp.placeholder = 'שם ערוץ או כתובת (למשל emuio)'; inp.style.flex = '1'; inp.setAttribute('dir', 'ltr'); stopKeys(inp);
      var msg = hh('div', { fontSize: '12px', color: '#9aa0a6', margin: '8px 0' });
      var st = {};
      var list = hh('div', { textAlign: 'right', maxHeight: '40vh', overflowY: 'auto' });
      function render() {
        while (list.firstChild) list.removeChild(list.firstChild);
        var arr = FAV.slice().sort(function (a, b) { return ((st[b.slug] && st[b.slug].live) ? 1 : 0) - ((st[a.slug] && st[a.slug].live) ? 1 : 0); });
        arr.forEach(function (f) {
          var s = st[f.slug] || {};
          var r = hh('div', { display: 'flex', alignItems: 'center', gap: '10px', padding: '8px 4px', borderBottom: '1px solid #26262c' });
          r.appendChild(hh('span', { fontSize: '12px', width: '16px' }, s.live ? '🔴' : '⚫'));
          var a = hh('a', { flex: '1', color: '#e8eaed', textDecoration: 'none', minWidth: '0' }); a.href = 'https://kick.com/' + f.slug;
          a.appendChild(hh('div', { fontWeight: '600', direction: 'ltr', textAlign: 'right' }, s.name || f.name || f.slug));
          if (s.live) a.appendChild(hh('div', { fontSize: '11px', color: '#9aa0a6', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
            (s.viewers !== undefined && s.viewers !== null ? '👁 ' + Number(s.viewers).toLocaleString('he-IL') + ' · ' : '') + (s.title || '') + (s.cat ? ' · ' + s.cat : '')));
          a.addEventListener('click', function () { setTimeout(function () { var m = document.getElementById('kickbob-fav'); if (m) m.remove(); }, 60); });
          var x = hh('span', { cursor: 'pointer', color: '#9aa0a6', padding: '2px 6px' }, '✕'); x.title = 'הסר';
          x.onclick = function () { FAV.splice(favIdx(f.slug), 1); saveFav(); render(); };
          r.appendChild(a); r.appendChild(x); list.appendChild(r);
        });
        if (!FAV.length) list.appendChild(hh('div', { color: '#9aa0a6', textAlign: 'center', padding: '22px 0' }, 'עוד אין ערוצים מועדפים.'));
      }
      function add() {
        var r = addFav(inp.value);
        msg.textContent = r === 'ok' ? 'נוסף.' : (r === 'dup' ? 'הערוץ כבר ברשימה.' : 'שם ערוץ לא תקין.');
        if (r === 'ok') { inp.value = ''; render(); }
      }
      inp.addEventListener('keydown', function (e) { if (e.key === 'Enter') add(); });
      addRow.appendChild(inp); addRow.appendChild(mk('הוסף', 'הוסף למועדפים', add, true));
      box.appendChild(addRow); box.appendChild(msg); box.appendChild(list);
      var row = hh('div', { display: 'flex', gap: '8px', justifyContent: 'center', flexWrap: 'wrap', marginTop: '14px' });
      row.appendChild(mk('ייבא את מי שאני עוקב אחריו', 'מייבא מהחשבון שלך ב-Kick (ניסיוני)', function () { msg.textContent = 'מייבא...'; importFollows(function (m) { msg.textContent = m; render(); }); }));
      row.appendChild(mk('סגור', 'סגור', close, true));
      box.appendChild(row);
      render();
      liveState().then(function (s) { st = s || {}; render(); });
    });
  }

  // ----- היסטוריית צפייה -----
  var histBuf = {};
  function pad2(n) { return (n < 10 ? '0' : '') + n; }
  function histNote(slug, sec) {
    var d = new Date(), day = d.getFullYear() + '-' + pad2(d.getMonth() + 1) + '-' + pad2(d.getDate());
    var k = day + '|' + slug.toLowerCase();
    var e = histBuf[k] || (histBuf[k] = { d: day, slug: slug.toLowerCase(), sec: 0 });
    e.sec += sec;
    if (SI && SI.slug === slug && SI.loaded) { if (SI.name) e.name = SI.name; if (SI.title) e.title = SI.title; if (SI.category) e.cat = SI.category; }
  }
  function histFlush() {
    var a = api(), arr = Object.keys(histBuf).map(function (k) { return histBuf[k]; });
    if (!arr.length || !a || !a.history_add) return;
    histBuf = {};
    try { a.history_add(JSON.stringify(arr)); } catch (e) {}
  }
  function showHistory() {
    openModal('kickbob-hist', function (box, line, close) {
      box.style.width = '700px';
      line('🕘 היסטוריית צפייה', { color: GREEN, fontSize: '22px', fontWeight: '800', marginBottom: '8px' });
      var a = api();
      if (!a || !a.history_get) { line('ההיסטוריה זמינה רק בתוך תוכנת קיקבוב.', { color: '#f28b82', margin: '12px 0' }); box.appendChild(mk('סגור', 'סגור', close, true)); return; }
      histFlush();
      var sum = hh('div', { fontSize: '13px', color: '#b9b9c0', marginBottom: '10px' }, 'טוען...');
      var q = fieldCss(hh('input')); q.type = 'text'; q.placeholder = 'חפש ערוץ, כותרת או קטגוריה'; q.style.width = '100%'; q.style.boxSizing = 'border-box'; stopKeys(q);
      var list = hh('div', { textAlign: 'right', maxHeight: '40vh', overflowY: 'auto', margin: '10px 0' });
      box.appendChild(sum); box.appendChild(q); box.appendChild(list);
      var items = [];
      function render() {
        while (list.firstChild) list.removeChild(list.firstChild);
        var f = q.value.trim().toLowerCase(), lastDay = '', n = 0;
        items.forEach(function (e) {
          if (f && ((e.slug || '') + ' ' + (e.name || '') + ' ' + (e.title || '') + ' ' + (e.cat || '')).toLowerCase().indexOf(f) < 0) return;
          n++;
          if (e.d !== lastDay) { lastDay = e.d; list.appendChild(hh('div', { fontWeight: '700', color: GREEN, margin: '12px 0 4px', direction: 'ltr', textAlign: 'right' }, e.d)); }
          var r = hh('div', { display: 'flex', gap: '10px', alignItems: 'center', padding: '5px 2px', borderBottom: '1px solid #26262c' });
          var al = hh('a', { width: '140px', color: '#e8eaed', textDecoration: 'none', direction: 'ltr', textAlign: 'right', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: '0 0 auto' }, e.name || e.slug);
          al.href = 'https://kick.com/' + encodeURIComponent(e.slug);
          al.addEventListener('click', function () { setTimeout(function () { var m = document.getElementById('kickbob-hist'); if (m) m.remove(); }, 60); });
          r.appendChild(al);
          r.appendChild(hh('div', { flex: '1', minWidth: '0', fontSize: '12px', color: '#9aa0a6', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }, (e.title || '') + (e.cat ? ' · ' + e.cat : '')));
          r.appendChild(hh('div', { width: '90px', fontSize: '12px', textAlign: 'left', flex: '0 0 auto' }, fmtHM(e.sec)));
          list.appendChild(r);
        });
        if (!n) list.appendChild(hh('div', { color: '#9aa0a6', textAlign: 'center', padding: '24px 0' }, items.length ? 'לא נמצאו תוצאות' : 'עוד אין היסטוריה. כשסרטון מתנגן בדף של ערוץ, הצפייה נרשמת.'));
      }
      q.oninput = render;
      a.history_get().then(function (s) {
        try { items = JSON.parse(s || '[]'); } catch (e) { items = []; }
        var days = {}, chans = {}, total = 0;
        items.forEach(function (e) { days[e.d] = 1; chans[e.slug] = 1; total += e.sec || 0; });
        sum.textContent = Object.keys(days).length + ' ימים · ' + Object.keys(chans).length + ' ערוצים · ' + fmtHM(total) + ' צפייה';
        render();
      });
      var msg = hh('div', { fontSize: '12px', color: '#fdd663', margin: '6px 0', minHeight: '16px' });
      var row = hh('div', { display: 'flex', gap: '8px', justifyContent: 'center', flexWrap: 'wrap' });
      var lastPath = '';
      function exp(fmt) { a.history_export(fmt).then(function (path) { lastPath = path; msg.textContent = path ? 'נשמר: ' + path : 'הייצוא נכשל.'; openBtn.style.display = path ? '' : 'none'; }); }
      row.appendChild(mk('ייצוא CSV', 'נפתח באקסל', function () { exp('csv'); }));
      row.appendChild(mk('ייצוא JSON', 'לשימוש בתוכנות אחרות', function () { exp('json'); }));
      var openBtn = mk('פתח תיקייה', 'מציג את הקובץ', function () { if (lastPath) a.open_path(lastPath); }); openBtn.style.display = 'none';
      row.appendChild(openBtn);
      var armed = false, timer = null;
      var clr = mk('נקה היסטוריה', 'מוחק את כל ההיסטוריה', function () {
        if (!armed) { armed = true; clr.textContent = 'לחץ שוב לאישור'; timer = setTimeout(function () { armed = false; clr.textContent = 'נקה היסטוריה'; }, 3500); return; }
        clearTimeout(timer); armed = false; clr.textContent = 'נקה היסטוריה';
        a.history_clear().then(function () { items = []; sum.textContent = 'ההיסטוריה נוקתה.'; render(); });
      });
      clr.style.color = '#f28b82'; row.appendChild(clr);
      row.appendChild(mk('סגור', 'סגור', close, true));
      box.appendChild(msg); box.appendChild(row);
    });
  }

  // ----- עדכונים -----
  function showUpdate(info) {
    openModal('kickbob-upd', function (box, line, close) {
      box.style.width = '520px';
      line('⬆️ עדכון זמין', { color: GREEN, fontSize: '22px', fontWeight: '800', marginBottom: '10px' });
      line('גרסה חדשה: ' + info.latest, { fontSize: '18px', fontWeight: '700', direction: 'ltr' });
      line('הגרסה שלך: ' + info.current, { fontSize: '13px', color: '#9aa0a6', direction: 'ltr', marginBottom: '12px' });
      if (info.notes) line(info.notes, { fontSize: '12px', color: '#b9b9c0', textAlign: 'right', whiteSpace: 'pre-wrap', maxHeight: '200px', overflowY: 'auto', background: '#1c1c20', borderRadius: '8px', padding: '10px', marginBottom: '12px', direction: 'auto' });
      var msg = line('', { fontSize: '12px', color: '#fdd663', margin: '6px 0' });
      var row = hh('div', { display: 'flex', gap: '8px', justifyContent: 'center' });
      var go = mk(info.kind ? 'עדכן עכשיו' : 'פתח את דף ההורדה', 'מוריד ומתקין', function () {
        var a = api(); if (!a || !a.apply_update) return;
        go.disabled = true; msg.textContent = 'מוריד...';
        a.apply_update().then(function (s) {
          var r = {}; try { r = JSON.parse(s); } catch (e) {}
          msg.textContent = r.ok ? (r.restart ? 'העדכון הורד. קיקבוב ייסגר ויופעל מחדש.' : 'נפתח דף ההורדה בדפדפן.') : 'העדכון נכשל: ' + (r.error || '');
          go.disabled = false;
        });
      }, true);
      row.appendChild(go); row.appendChild(mk('מאוחר יותר', 'סגור', close));
      box.appendChild(row);
    });
  }
  function checkUpdateNow(silent) {
    var a = api(); if (!a || !a.check_update) return;
    a.check_update().then(function (s) {
      var r = {}; try { r = JSON.parse(s); } catch (e) {}
      if (!r.ok) { if (!silent) toast(r.error === 'no_source' ? 'הגדר מקור עדכונים בהגדרות, בסעיף "עדכונים"' : 'בדיקת העדכונים נכשלה'); return; }
      if (r.newer) showUpdate(r); else if (!silent) toast('אתה על הגרסה העדכנית');
    });
  }
  function checkUpdateBanner() {
    var a = api(); if (!a || !a.get_update) return;
    a.get_update().then(function (s) {
      if (!s) return;
      var info = null; try { info = JSON.parse(s); } catch (e) { return; }
      if (!info || !info.newer) return;
      var seen = ''; try { seen = sessionStorage.getItem('kb_upd_seen') || ''; } catch (e) {}
      if (seen === info.latest) return;
      try { sessionStorage.setItem('kb_upd_seen', info.latest); } catch (e) {}
      banner('⬆️ עדכון זמין: ' + info.latest, 'לחץ לפרטים ולעדכון', function () { showUpdate(info); }, GREEN);
    });
  }
  function goHome() {
    var a = api();
    if (SET.homeButton === 'mine' && a && a.open_home) a.open_home(); else location.href = HOME;
  }
  window.__kbOpen = { fav: showFavorites, bm: showBookmarks, hist: showHistory };

  // =====================================================================
  //  תפריט קיקבוב (נפתח מהאות K)
  // =====================================================================
  function showAppMenu(anchor) {
    var old = document.getElementById('kickbob-menu-ov');
    if (old) { old.remove(); return; }
    var C = { bg: '#292a2d', line: '#3c4043', text: '#e8eaed', sub: '#9aa0a6' };
    function h(tag, css, text) { var e = document.createElement(tag); if (css) Object.assign(e.style, css); if (text !== undefined) e.textContent = text; return e; }
    var ov = h('div', { position: 'fixed', inset: '0', zIndex: '2147483647', background: 'transparent' });
    ov.id = 'kickbob-menu-ov';
    function close() { ov.remove(); document.removeEventListener('keydown', onKey, true); }
    function onKey(e) { if (e.key === 'Escape') { e.preventDefault(); close(); } }
    document.addEventListener('keydown', onKey, true);
    ov.onclick = close;
    var left = 8, top = TAB_H + 4;
    try { var r = anchor.getBoundingClientRect(); left = Math.max(8, r.left); top = r.bottom + 6; } catch (e) {}
    var box = h('div', { position: 'absolute', left: left + 'px', top: top + 'px', width: '290px', background: C.bg, border: '1px solid ' + C.line,
      borderRadius: '12px', padding: '6px 0', boxShadow: '0 10px 32px rgba(0,0,0,0.6)', color: C.text,
      fontFamily: "'Segoe UI', Arial, sans-serif", fontSize: '14px' });
    box.id = 'kickbob-menu'; box.setAttribute('dir', 'rtl');
    box.onclick = function (e) { e.stopPropagation(); };
    var head = h('div', { display: 'flex', alignItems: 'center', gap: '10px', padding: '8px 16px 10px' });
    head.appendChild(h('div', { width: '26px', height: '26px', lineHeight: '26px', textAlign: 'center', borderRadius: '50%', background: GREEN, color: '#000', fontWeight: '800' }, 'K'));
    var ht = h('div'); ht.appendChild(h('div', { fontWeight: '700' }, 'קיקבוב'));
    ht.appendChild(h('div', { fontSize: '11px', color: C.sub, direction: 'ltr', textAlign: 'right' }, '__VERSION__'));
    head.appendChild(ht); box.appendChild(head);
    function sep() { box.appendChild(h('div', { height: '1px', background: C.line, margin: '6px 0' })); }
    function item(icon, label, shortcut, fn, danger) {
      var it = h('div', { display: 'flex', alignItems: 'center', gap: '12px', padding: '8px 16px', cursor: 'pointer', color: danger ? '#f28b82' : C.text });
      it.appendChild(h('span', { width: '20px', textAlign: 'center', fontSize: '15px' }, icon));
      it.appendChild(h('span', { flex: '1' }, label));
      if (shortcut) it.appendChild(h('span', { fontSize: '12px', color: C.sub, direction: 'ltr' }, shortcut));
      it.onmouseenter = function () { it.style.background = 'rgba(255,255,255,0.08)'; };
      it.onmouseleave = function () { it.style.background = 'transparent'; };
      it.onclick = function () { close(); try { fn(); } catch (e) {} };
      box.appendChild(it);
    }
    item('➕', 'כרטיסייה חדשה', 'Ctrl+T', function () { newTab(''); });
    item('🏠', 'סטרימים בעברית', '', function () { location.href = HOME; });
    item('🧭', 'דף הבית שלי', '', function () { var a = api(); if (a && a.open_home) a.open_home(); });
    item('⭐', 'ערוצים שאני עוקב אחריהם', '', function () { location.href = FOLLOWING; });
    sep();
    item('🎬', 'חיפוש קליפים', '', function () { showClips(); });
    item('🔖', 'סימניות', 'Ctrl+Shift+O', function () { showBookmarks(); });
    item('⭐', 'ערוצים מועדפים והתראות', '', function () { showFavorites(); });
    item('🕘', 'היסטוריית צפייה', 'Ctrl+H', function () { showHistory(); });
    item('📊', 'רמות והתקדמות', '', function () { showLevels(); });
    item('📺', 'הצפייה שלי', '', function () { showWatched(); });
    item('🎨', 'עיצוב Kick', '', function () { showStyle(); });
    sep();
    item('⚙️', 'הגדרות', '', function () { showSettings(); });
    item('⬆️', 'בדוק עדכונים', '', function () { checkUpdateNow(false); });
    item('🗺️', 'מה חדש ומה בדרך', '', function () { showRoadmap('new'); });
    item('ℹ️', 'אודות קיקבוב', '', function () { showAbout(); });
    sep();
    item('⏻', 'יציאה מקיקבוב', '', function () { var a = api(); if (a && a.window_close) a.window_close(); }, true);
    ov.appendChild(box);
    document.documentElement.appendChild(ov);
  }

  // =====================================================================
  //  כרטיסיות: פתיחה, מעבר, סגירה, וקישורים שנפתחים בכרטיסייה חדשה
  // =====================================================================
  function newTab(url) { var a = api(); if (a && a.new_tab) a.new_tab(url || ''); }
  function linkToTab(e) {
    if (e.defaultPrevented) return;
    var a = e.target && e.target.closest && e.target.closest('a[href]');
    if (!a) return;
    var wantTab = a.target === '_blank' || e.ctrlKey || e.metaKey || e.button === 1;
    if (!wantTab || !/^https?:/i.test(a.href)) return;
    e.preventDefault(); e.stopPropagation();
    newTab(a.href);
  }
  document.addEventListener('click', linkToTab, true);
  document.addEventListener('auxclick', function (e) { if (e.button === 1) linkToTab(e); }, true);
  try {
    var origOpen = window.open;
    window.open = function (u, name, feats) {
      // חלונות קופצים (כמו התחברות עם גוגל) נשארים כרגיל; קישורים רגילים נפתחים בכרטיסייה
      if (u && !feats && /^https?:/i.test(String(u))) { newTab(String(u)); return null; }
      return origOpen.apply(window, arguments);
    };
  } catch (e) {}
  document.addEventListener('keydown', function (e) {
    if (!(e.ctrlKey || e.metaKey)) return;
    var a = api(); if (!a) return;
    if (e.key === 't' || e.key === 'T') { e.preventDefault(); newTab(''); }
    else if ((e.key === 'w' || e.key === 'W') && !e.shiftKey) { e.preventDefault(); a.close_tab && a.close_tab(''); }
    else if (e.key === 'Tab') { e.preventDefault(); a.next_tab && a.next_tab(); }
    else if ((e.key === 'd' || e.key === 'D') && !e.shiftKey) { e.preventDefault(); toggleBookmark(); }
    else if ((e.key === 'h' || e.key === 'H') && !e.shiftKey) { e.preventDefault(); showHistory(); }
    else if ((e.key === 'o' || e.key === 'O') && e.shiftKey) { e.preventDefault(); showBookmarks(); }
  }, true);

  // =====================================================================
  //  הסרגל העליון (כמו בדפדפן)
  // =====================================================================
  var barWrap = document.createElement('div');
  barWrap.id = 'kickbob-bar';
  barWrap.setAttribute('dir', 'ltr');
  Object.assign(barWrap.style, {
    position: 'fixed', top: '0', left: '0', right: '0', height: BAR_H + 'px', boxSizing: 'border-box',
    zIndex: '2147483646', display: 'flex', flexDirection: 'column',
    background: '#202124', borderBottom: '1px solid #3c4043',
    fontFamily: 'Segoe UI, Arial, sans-serif', fontSize: '13px', color: '#e8eaed'
  });
  var bar = document.createElement('div');
  bar.id = 'kickbob-toolbar';
  Object.assign(bar.style, { flex: '1 1 auto', display: 'flex', alignItems: 'center', gap: '4px', padding: '0 8px', minHeight: '0', background: '#35363a' });

  // ---------- שורת כרטיסיות ----------
  var tabsRow = document.createElement('div');
  tabsRow.id = 'kickbob-tabs';
  Object.assign(tabsRow.style, { height: TAB_H + 'px', flex: '0 0 auto', display: 'flex', alignItems: 'flex-end', gap: '2px',
    padding: '6px 8px 0', boxSizing: 'border-box', background: '#202124', overflow: 'hidden' });
  var tabsSig = '';
  function faviconEl(host) {
    var wrap = document.createElement('span');
    Object.assign(wrap.style, { width: '16px', height: '16px', flex: '0 0 auto', display: 'inline-flex', alignItems: 'center', justifyContent: 'center' });
    var letter = ((host || '?').replace(/^www\./, '').charAt(0) || '?').toUpperCase();
    function fallback() {
      wrap.textContent = letter;
      Object.assign(wrap.style, { borderRadius: '50%', background: '#5f6368', color: '#fff', fontSize: '10px', fontWeight: '700' });
    }
    if (!host) { fallback(); return wrap; }
    var img = new Image(); img.width = 16; img.height = 16;
    img.onerror = function () { img.remove(); fallback(); };
    img.src = 'https://www.google.com/s2/favicons?sz=32&domain=' + encodeURIComponent(host);
    wrap.appendChild(img);
    return wrap;
  }
  function renderTabs(info) {
    while (tabsRow.firstChild) tabsRow.removeChild(tabsRow.firstChild);
    var a = api();
    var logo = document.createElement('div'); logo.textContent = 'K'; logo.title = 'קיקבוב';
    Object.assign(logo.style, { width: '22px', height: '22px', lineHeight: '22px', textAlign: 'center', borderRadius: '50%', background: GREEN,
      color: '#000', fontWeight: '800', fontSize: '13px', flex: '0 0 auto', margin: '0 8px 5px 2px' });
    logo.style.cursor = 'pointer'; logo.title = 'תפריט קיקבוב';
    logo.onmouseenter = function () { logo.style.boxShadow = '0 0 10px ' + GREEN; };
    logo.onmouseleave = function () { logo.style.boxShadow = 'none'; };
    logo.onclick = function (e) { e.stopPropagation(); showAppMenu(logo); };
    tabsRow.appendChild(logo);
    (info.tabs || []).forEach(function (t) {
      var active = t.id === info.active;
      var chip = document.createElement('div');
      Object.assign(chip.style, { display: 'flex', alignItems: 'center', gap: '8px', flex: '0 1 230px', minWidth: '110px', height: (TAB_H - 6) + 'px',
        boxSizing: 'border-box', padding: '0 10px', borderRadius: '10px 10px 0 0', cursor: 'default', fontSize: '12px',
        background: active ? '#35363a' : 'transparent', color: active ? '#e8eaed' : '#9aa0a6' });
      if (!active) {
        chip.onmouseenter = function () { chip.style.background = 'rgba(255,255,255,0.08)'; };
        chip.onmouseleave = function () { chip.style.background = 'transparent'; };
      }
      var tt = document.createElement('span'); tt.textContent = t.title || 'כרטיסייה חדשה';
      Object.assign(tt.style, { flex: '1', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' });
      var x = document.createElement('span'); x.textContent = '✕'; x.title = 'סגור כרטיסייה';
      Object.assign(x.style, { width: '18px', height: '18px', lineHeight: '18px', textAlign: 'center', borderRadius: '50%', fontSize: '10px', cursor: 'pointer', flex: '0 0 auto' });
      x.onmouseenter = function () { x.style.background = 'rgba(255,255,255,0.18)'; };
      x.onmouseleave = function () { x.style.background = 'transparent'; };
      x.onclick = function (e) { e.stopPropagation(); if (a && a.close_tab) a.close_tab(t.id); };
      chip.onclick = function () { if (!active && a && a.switch_tab) a.switch_tab(t.id); };
      chip.appendChild(faviconEl(t.host)); chip.appendChild(tt); chip.appendChild(x); tabsRow.appendChild(chip);
    });
    tabsRow.className = 'pywebview-drag-region';
    var plus = document.createElement('div'); plus.textContent = '+'; plus.title = 'כרטיסייה חדשה (Ctrl+T)';
    Object.assign(plus.style, { width: '28px', height: '28px', lineHeight: '26px', textAlign: 'center', borderRadius: '50%', cursor: 'pointer',
      fontSize: '20px', color: '#e8eaed', flex: '0 0 auto', margin: '0 0 3px 6px' });
    plus.onmouseenter = function () { plus.style.background = 'rgba(255,255,255,0.1)'; };
    plus.onmouseleave = function () { plus.style.background = 'transparent'; };
    plus.onclick = function () { newTab(''); };
    tabsRow.appendChild(plus);
    if (FRAMELESS) {
      // אזור גרירה של החלון (ריק) + כפתורי מזעור / הגדלה / סגירה כמו ב-Chrome
      var spacer = document.createElement('div'); spacer.className = 'pywebview-drag-region';
      Object.assign(spacer.style, { flex: '1 1 auto', alignSelf: 'stretch', minWidth: '40px' });
      spacer.ondblclick = function () { if (a && a.toggle_maximize) a.toggle_maximize(); };
      tabsRow.appendChild(spacer);
      var caps = document.createElement('div');
      Object.assign(caps.style, { display: 'flex', alignItems: 'center', alignSelf: 'flex-start', margin: '-6px -8px 0 6px', flex: '0 0 auto',
        height: '34px', padding: '0 8px', gap: '2px', background: '#0b0b0d', borderRadius: '0 0 14px 14px',
        borderBottom: '2px solid ' + GREEN, boxShadow: '0 6px 16px rgba(0,0,0,0.45), 0 0 14px ' + GREEN + '33' });
      function cap(path, title, fn, danger) {
        var b = document.createElement('div'); b.title = title;
        Object.assign(b.style, { width: '38px', height: '26px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' });
        var NS = 'http://www.w3.org/2000/svg';
        var svg = document.createElementNS(NS, 'svg'); svg.setAttribute('viewBox', '0 0 16 16'); svg.setAttribute('width', '12'); svg.setAttribute('height', '12');
        var pth = document.createElementNS(NS, 'path'); pth.setAttribute('d', path); pth.setAttribute('fill', 'none');
        pth.setAttribute('stroke', '#e8eaed'); pth.setAttribute('stroke-width', '1.3');
        svg.appendChild(pth); b.appendChild(svg);
        b.onmouseenter = function () { b.style.background = danger ? '#e81123' : 'rgba(255,255,255,0.1)'; };
        b.onmouseleave = function () { b.style.background = 'transparent'; };
        b.onclick = function (e) { e.stopPropagation(); fn(); };
        return b;
      }
      caps.appendChild(cap('M2 8.5h12', 'מזער', function () { if (a && a.window_minimize) a.window_minimize(); }));
      caps.appendChild(info.max
        ? cap('M5 3h8v8 M3 5h8v8H3z', 'שחזר', function () { if (a && a.toggle_maximize) a.toggle_maximize(); })
        : cap('M3 3h10v10H3z', 'הגדל', function () { if (a && a.toggle_maximize) a.toggle_maximize(); }));
      caps.appendChild(cap('M3 3l10 10M13 3L3 13', 'סגור', function () { if (a && a.window_close) a.window_close(); }, true));
      tabsRow.appendChild(caps);
    }
  }
  function pollTabs() {
    var a = api();
    if (!a || !a.get_tabs) { if (!tabsSig) { tabsSig = 'x'; renderTabs({ active: 'me', tabs: [{ id: 'me', title: document.title }] }); } return; }
    try { if (a.report_title) a.report_title(document.title || '', location.href); } catch (e) {}
    a.get_tabs().then(function (info) {
      var sig = JSON.stringify(info);
      if (sig !== tabsSig) { tabsSig = sig; renderTabs(info); }
    });
  }

  var brand = document.createElement('span');
  brand.textContent = 'קיקבוב';
  Object.assign(brand.style, { color: GREEN, fontWeight: '800', padding: '0 6px 0 2px', flex: '0 0 auto' });

  var omni = document.createElement('div');
  Object.assign(omni.style, { flex: '1 1 auto', minWidth: '120px', height: '32px', boxSizing: 'border-box', display: 'flex',
    alignItems: 'center', gap: '8px', padding: '0 14px', background: '#202124', borderRadius: '16px', border: '2px solid transparent' });
  var omniIcon = document.createElement('span'); omniIcon.textContent = '🔍';
  Object.assign(omniIcon.style, { fontSize: '12px', flex: '0 0 auto', opacity: '0.85' });
  var addr = document.createElement('input');
  addr.type = 'text'; addr.setAttribute('dir', 'ltr'); addr.spellcheck = false;
  addr.placeholder = 'חפש ב' + engine().name + ', הקלד כתובת, או @ערוץ ב-Kick  (Ctrl+L)';
  Object.assign(addr.style, { flex: '1', minWidth: '0', height: '100%', background: 'transparent', color: '#e8eaed', border: 'none',
    outline: 'none', fontSize: '14px', fontFamily: 'inherit', padding: '0' });
  addr.onfocus = function () { omni.style.borderColor = GREEN; omniIcon.textContent = '🔍'; addr.select(); };
  addr.onblur = function () { omni.style.borderColor = 'transparent'; showUrl(); };
  omni.appendChild(omniIcon); omni.appendChild(addr);
  var omniStar = document.createElement('span'); omniStar.textContent = '☆';
  Object.assign(omniStar.style, { cursor: 'pointer', fontSize: '17px', lineHeight: '1', color: '#9aa0a6', flex: '0 0 auto', padding: '0 2px' });
  omniStar.onclick = function (e) { e.stopPropagation(); toggleBookmark(); };
  omni.appendChild(omniStar);
  ['keydown', 'keypress', 'keyup'].forEach(function (ev) {
    addr.addEventListener(ev, function (e) { e.stopPropagation(); });   // שלא יפעילו קיצורים של האתר
  });
  function showUrl() {
    if (document.activeElement === addr) return;
    var u = location.href.replace(/^https?:\/\//, '').replace(/\/$/, '');
    if (/^(about|data):/.test(location.href)) u = '';
    omniIcon.textContent = /^https:/.test(location.href) ? '🔒' : (/^http:/.test(location.href) ? '⚠️' : '🔍');
    if (addr.value !== u) addr.value = u;
    updateStar();
  }
  function go(v) {
    v = (v || '').trim();
    if (!v) return;
    if (/^https?:\/\//i.test(v)) location.href = v;
    else if (/^@[\w-]+$/.test(v)) location.href = 'https://kick.com/' + v.slice(1);
    else if (/^[\w-]+(\.[\w-]+)+(:\d+)?(\/\S*)?$/.test(v) || /^localhost(:\d+)?(\/\S*)?$/i.test(v)) location.href = 'https://' + v;
    else location.href = engine().url + encodeURIComponent(v);
  }
  addr.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') go(addr.value);
    if (e.key === 'Escape') { addr.blur(); }
  });
  document.addEventListener('keydown', function (e) {
    if ((e.ctrlKey || e.metaKey) && /^[lLkK]$/.test(e.key)) { e.preventDefault(); addr.focus(); addr.select(); }
  }, true);

  function findLogin() {
    var els = [].slice.call(document.querySelectorAll('button,a'));
    return els.find(function (e) { return /^(log\s?in|sign\s?in)$/i.test((e.textContent || '').trim()); });
  }
  var loginBtn = mk('👤 כניסה', 'כניסה לחשבון Kick', function () {
    var b = findLogin();
    if (b) b.click(); else location.href = 'https://kick.com/';
  });

  var badge = document.createElement('span');
  badge.textContent = '__VERSION__';
  Object.assign(badge.style, {
    fontSize: '10px', color: '#9aa0a6', borderRadius: '6px',
    padding: '2px 4px', whiteSpace: 'nowrap', flex: '0 0 auto'
  });

  var clipsBtn = flat('🎬', 'חיפוש קליפים', showClips);
  var homeBtn = flat('', 'דף הבית', function () { goHome(); });
  (function () {
    var NS = 'http://www.w3.org/2000/svg', svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('viewBox', '0 0 24 24'); svg.setAttribute('width', '22'); svg.setAttribute('height', '22');
    var roof = document.createElementNS(NS, 'path');
    roof.setAttribute('d', 'M12 2.8 L2.8 10.6 H5.4 V20.6 H18.6 V10.6 H21.2 Z');
    roof.setAttribute('fill', GREEN + '1f'); roof.setAttribute('stroke', GREEN); roof.setAttribute('stroke-width', '1.8'); roof.setAttribute('stroke-linejoin', 'round');
    var bolt = document.createElementNS(NS, 'path');
    bolt.setAttribute('d', 'M13.2 8 L9 14 H11.6 L10.8 19 L15.3 12.4 H12.6 Z');
    bolt.setAttribute('fill', GREEN);
    svg.appendChild(roof); svg.appendChild(bolt); homeBtn.appendChild(svg);
    homeBtn.onmouseenter = function () { homeBtn.style.background = GREEN + '33'; };
    homeBtn.onmouseleave = function () { homeBtn.style.background = 'transparent'; };
  })();
  [
    icoBtn('M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z', 'אחורה', function () { history.back(); }),
    icoBtn('M12 4l-1.41 1.41L16.17 11H4v2h12.17l-5.58 5.59L12 20l8-8z', 'קדימה', function () { history.forward(); }),
    icoBtn('M17.65 6.35A7.958 7.958 0 0012 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08A5.99 5.99 0 0112 18c-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z', 'רענון', function () { location.reload(); }),
    homeBtn,
    omni,
    streamBtn,
    viewerPill,
    levelBtn,
    clipsBtn,
    flat('⭐', 'ערוצים שאני עוקב אחריהם', function () { location.href = FOLLOWING; }),
    loginBtn,
    cursorBtn,
    flat('🎨', 'עיצוב קיק: צבעים, גופן ו-CSS מותאם', showStyle),
    flat('⚙️', 'הגדרות: ערכות נושא, חסימת פרסומות, פרטיות', showSettings),
    flat('ℹ️', 'אודות', showAbout),
    badge
  ].forEach(function (el) { bar.appendChild(el); });

  // דחיפת הדף למטה כדי שהסרגל לא יכסה אותו
  addSheet('html { margin-top: ' + BAR_H + 'px !important; }');
  barWrap.appendChild(tabsRow);
  barWrap.appendChild(bar);
  document.documentElement.appendChild(barWrap);


  // ---------- ידיות לשינוי גודל החלון (כשאין מסגרת של Windows) ----------
  function makeResizers() {
    var a0 = api();
    var defs = [
      ['n',  { top: '0', left: '10px', right: '10px', height: '4px' }, 'ns-resize'],
      ['s',  { bottom: '0', left: '10px', right: '10px', height: '5px' }, 'ns-resize'],
      ['e',  { right: '0', top: '10px', bottom: '10px', width: '5px' }, 'ew-resize'],
      ['w',  { left: '0', top: '10px', bottom: '10px', width: '5px' }, 'ew-resize'],
      ['nw', { top: '0', left: '0', width: '10px', height: '10px' }, 'nwse-resize'],
      ['ne', { top: '0', right: '0', width: '10px', height: '10px' }, 'nesw-resize'],
      ['sw', { bottom: '0', left: '0', width: '10px', height: '10px' }, 'nesw-resize'],
      ['se', { bottom: '0', right: '0', width: '10px', height: '10px' }, 'nwse-resize']
    ];
    var css = '';
    defs.forEach(function (d) { css += '#kickbob-rz-' + d[0] + ' { cursor: ' + d[2] + ' !important; } '; });
    addSheet(css);
    defs.forEach(function (d) {
      var h = document.createElement('div'); h.id = 'kickbob-rz-' + d[0];
      Object.assign(h.style, { position: 'fixed', zIndex: '2147483647', background: 'transparent', touchAction: 'none' });
      Object.assign(h.style, d[1]);
      var sx = 0, sy = 0, busy = false, active = false;
      h.addEventListener('pointerdown', function (e) {
        if (e.button !== 0) return;
        var a = api(); if (!a || !a.resize_start) return;
        e.preventDefault(); e.stopPropagation();
        active = true; sx = e.screenX; sy = e.screenY; busy = false;
        try { h.setPointerCapture(e.pointerId); } catch (x) {}
        a.resize_start(d[0]);
      });
      h.addEventListener('pointermove', function (e) {
        if (!active || busy) return;
        var a = api(); if (!a || !a.resize_by) return;
        busy = true;
        var done = function () { busy = false; };
        try { a.resize_by(e.screenX - sx, e.screenY - sy).then(done, done); } catch (x) { busy = false; }
      });
      function end(e) { active = false; try { h.releasePointerCapture(e.pointerId); } catch (x) {} }
      h.addEventListener('pointerup', end);
      h.addEventListener('pointercancel', end);
      document.documentElement.appendChild(h);
    });
  }

  // אלמנטים קבועים/דביקים של האתר (כמו הכותרת שלו) - מזיזים מתחת לסרגל
  function shiftFixed() {
    var list = document.querySelectorAll('header, nav, [role="banner"], body > *, body > * > *, #__next > *, #__next > * > *');
    var n = Math.min(list.length, 500);
    for (var i = 0; i < n; i++) {
      var el = list[i];
      if (el.dataset && el.dataset.kbShift === '1') continue;
      if (el.id && el.id.indexOf('kickbob') === 0) continue;
      var cs = getComputedStyle(el);
      if (cs.position !== 'fixed' && cs.position !== 'sticky') continue;
      var top = parseFloat(cs.top);
      if (isNaN(top) || top < 0 || top >= BAR_H) continue;
      el.style.setProperty('top', (top + BAR_H) + 'px', 'important');
      el.dataset.kbShift = '1';
    }
  }

  refreshLevel();
  tickStream();
  applyStyle();
  applyCursor();
  showUrl();
  pollTabs();
  setInterval(pollTabs, 1500);
  heInit();
  setTimeout(askHebrew, 1500);
  setTimeout(checkUpdateBanner, 6000);
  setInterval(checkUpdateBanner, 1800000);
  setInterval(histFlush, 60000);
  window.addEventListener('beforeunload', histFlush);
  if (FRAMELESS) makeResizers();
  try {
    var ro = sessionStorage.getItem('kb_reopen');
    if (ro !== null) { sessionStorage.removeItem('kb_reopen'); showSettings(parseInt(ro, 10) || 0); }
  } catch (e) {}

  // בונוס יומי
  if (P.daily !== today()) {
    P.daily = today();
    addXP(DAILY_BONUS, '🎁 בונוס יומי: +' + DAILY_BONUS + ' XP');
  }

  setTimeout(shiftFixed, 300); setTimeout(shiftFixed, 1200); setTimeout(shiftFixed, 3000);
  setInterval(function () {
    if (document.hidden) return;
    showUrl();
    shiftFixed();
    var needLogin = !!findLogin();
    var want = needLogin ? '👤 כניסה' : '✅ מחובר';
    if (loginBtn.textContent !== want) loginBtn.textContent = want;
  }, 3000);
})();
"""


WORKER_JS = r"""
(function () {
  if (window.__kbWorker) return;
  window.__kbWorker = true;
  var CFG = __CFG__;
  function api() { try { return window.pywebview && window.pywebview.api; } catch (e) { return null; } }
  var state = {}, busy = false;
  function sleep(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
  function getJson(u) {
    return fetch(u, { credentials: 'include', headers: { 'Accept': 'application/json' } })
      .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); });
  }
  function parseTime(t) {
    if (!t) return 0;
    var x = String(t).trim();
    if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}/.test(x)) x = x.replace(' ', 'T');
    if (/^\d{4}-\d{2}-\d{2}T[\d:.]+$/.test(x)) x += 'Z';
    var ms = Date.parse(x);
    return isNaN(ms) ? 0 : ms;
  }
  function note(slug, name, live, info) {
    var prev = state[slug];
    state[slug] = { live: live, name: name || slug, viewers: info.viewers, title: info.title || '', cat: info.cat || '', start: info.start || 0 };
    if (live && prev && prev.live === false) {   // עלה לשידור (ולא רק זוהה בפעם הראשונה)
      var a = api();
      if (a && a.notify) a.notify(JSON.stringify({ key: slug + ':' + (info.start || Math.floor(Date.now() / 3600000)), slug: slug,
        title: '🔴 ' + (name || slug) + ' עלה לשידור', body: (info.title || '') + (info.cat ? ' · ' + info.cat : ''), url: 'https://kick.com/' + slug }));
    }
  }
  function followed() {
    return getJson('/api/v2/channels/followed').then(function (d) {
      var list = (d && (d.channels || d.data)) || [];
      list.forEach(function (c) {
        var slug = c.channel_slug || c.slug || (c.channel && c.channel.slug);
        if (!slug) return;
        var ls = c.livestream;
        note(String(slug).toLowerCase(), c.user_username || c.username || slug, c.is_live === true || !!ls,
          { start: parseTime(c.start_time || (ls && (ls.start_time || ls.created_at))), title: c.session_title || (ls && ls.session_title) || '',
            viewers: c.viewer_count, cat: c.category_name || '' });
      });
    }).catch(function () {});
  }
  function cycle() {
    if (busy) return;
    var a = api();
    if (!a || !a.get_cfg) return;
    busy = true;
    a.get_cfg('settings').then(function (s) {
      var set = {}; try { set = JSON.parse(s || '{}'); } catch (e) {}
      if (set.notify === false) return null;
      return a.get_cfg('favorites').then(function (f) {
        var favs = []; try { favs = JSON.parse(f || '[]'); } catch (e) {}
        var chain = Promise.resolve();
        favs.slice(0, 40).forEach(function (fv) {
          chain = chain.then(function () {
            return getJson('/api/v2/channels/' + encodeURIComponent(fv.slug)).then(function (d) {
              var ls = d && d.livestream;
              note(fv.slug, (d && d.user && d.user.username) || fv.name, !!ls, ls ? { start: parseTime(ls.start_time || ls.created_at),
                title: ls.session_title, viewers: ls.viewer_count, cat: (ls.categories && ls.categories[0] && ls.categories[0].name) || '' } : {});
            }).catch(function () {}).then(function () { return sleep(500); });
          });
        });
        if (set.notifyFollowed !== false) chain = chain.then(followed);
        return chain;
      });
    }).catch(function () {}).then(function () {
      busy = false;
      var a2 = api();
      if (a2 && a2.report_live) a2.report_live(JSON.stringify(state));
    });
  }
  setTimeout(cycle, 6000);
  setInterval(cycle, 60000);
})();
"""


NEWTAB_HTML = """<!doctype html>
<html lang="he" dir="rtl"><head><meta charset="utf-8"><title>דף הבית שלי</title>
<style>
 body{margin:0;background:#202124;color:#e8eaed;font-family:'Segoe UI',Arial,sans-serif;
      display:flex;flex-direction:column;align-items:center;padding:7vh 16px 40px;min-height:70vh}
 h1{font-size:56px;margin:0 0 4px;color:#53fc18;font-weight:800;letter-spacing:1px}
 p.v{color:#9aa0a6;margin:0 0 26px;font-size:13px;direction:ltr}
 form{width:min(600px,90vw)}
 input[type=text]{width:100%;box-sizing:border-box;padding:14px 24px;font-size:16px;border-radius:26px;
      background:#303134;color:#e8eaed;border:1px solid #303134;outline:none}
 input[type=text]:hover{background:#3c4043}
 input[type=text]:focus{border-color:#8ab4f8;background:#303134}
 .wrap{width:min(760px,94vw);margin-top:34px}
 h2{font-size:14px;color:#9aa0a6;font-weight:600;margin:26px 0 8px}
 h2 a{color:#53fc18;font-size:12px;margin-inline-start:8px;text-decoration:none}
 .tiles{display:flex;gap:10px;flex-wrap:wrap}
 a.t{position:relative;display:flex;flex-direction:column;align-items:center;width:104px;padding:12px 6px;border-radius:12px;
      color:#e8eaed;text-decoration:none;font-size:12px;text-align:center}
 a.t:hover{background:#303134}
 a.t i{width:46px;height:46px;border-radius:50%;background:#3c4043;display:flex;align-items:center;
      justify-content:center;font-style:normal;font-size:19px;font-weight:700;margin-bottom:8px;color:#53fc18}
 a.t span{max-width:96px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
 b.live{font-size:11px;color:#ff5a5a;font-weight:700;min-height:14px}
 .hint{color:#9aa0a6;font-size:13px}
 .hint a{color:#53fc18}
 small{display:block;margin-top:34px;color:#6f7378;font-size:12px}
</style></head><body>
<h1>קיקבוב</h1><p class="v">{{VERSION}}</p>
<form action="https://www.google.com/search" method="get">
 <input type="hidden" name="hl" value="iw">
 <input type="text" name="q" autofocus autocomplete="off" placeholder="חפש בגוגל או הקלד כתובת">
</form>
<div class="wrap">
 {{FAVS}}
 {{BMS}}
 <h2>קיצורי דרך</h2>
 <div class="tiles">
  <a class="t" href="https://kick.com/browse?sort=featured&languages=he"><i>K</i><span>Kick בעברית</span></a>
  <a class="t" href="https://kick.com/clips"><i>🎬</i><span>קליפים</span></a>
  <a class="t" href="https://kick.com/following"><i>⭐</i><span>עוקב אחרי</span></a>
  <a class="t" href="https://kick.com/emuio"><i>E</i><span>EMUIO</span></a>
  <a class="t" href="https://www.google.com/?hl=iw"><i>G</i><span>Google</span></a>
  <a class="t" href="https://www.youtube.com/"><i>▶</i><span>YouTube</span></a>
 </div>
</div>
<small>Ctrl+T כרטיסייה חדשה &nbsp;|&nbsp; Ctrl+D סימנייה &nbsp;|&nbsp; Ctrl+H היסטוריה &nbsp;|&nbsp; Ctrl+W סגירה</small>
<script>
function upd(){try{var a=window.pywebview&&window.pywebview.api;if(!a||!a.get_live_state)return;
 a.get_live_state().then(function(s){var st={};try{st=JSON.parse(s||'{}')}catch(e){}
  document.querySelectorAll('a.t[data-slug]').forEach(function(el){var v=st[el.getAttribute('data-slug')];
   var b=el.querySelector('.live');if(b)b.textContent=(v&&v.live)?'🔴 משדר':'';});});}catch(e){}}
setTimeout(upd,1200);setInterval(upd,6000);
</script>
</body></html>"""

CFG_NAMES = ("settings", "style", "progress", "bookmarks", "favorites")
LIST_CFGS = ("bookmarks", "favorites")
_W = {}                       # webview module
_TABS = {}                    # tab id -> window
_ORDER = []                   # סדר הכרטיסיות
_TITLES = {}                  # tab id -> כותרת
_URLS = {}                    # tab id -> כתובת
_ACTIVE = {"id": None}
_NEXT = {"n": 0}
_STARTED = {"v": False}
_TPL = {"ui": "", "blocker": ""}
_WIN = {"max": False, "prev": None}
_RS = {"geo": None, "dir": ""}


_LOCK = threading.Lock()
_HIST = {"list": None}
_NOTIFIED = {}
_LIVE = {"state": "{}"}
_WORKER = {"w": None}
_UPDATE = {"info": None, "last": 0, "error": ""}
WORKER_URL = "https://kick.com/_kickbob-worker"
VERSION_NUM = re.sub(r"^PRE ALPHA\s*", "", VERSION)


def _clean_list(name, lst):
    out = []
    if name == "bookmarks":
        for b in lst[:500]:
            if not isinstance(b, dict):
                continue
            u = str(b.get("url", ""))[:600]
            if not re.match(r"^https?://", u, re.I):
                continue
            out.append({"title": str(b.get("title", u))[:120], "url": u, "added": int(b.get("added", 0) or 0)})
    else:
        seen = set()
        for f in lst[:100]:
            if not isinstance(f, dict):
                continue
            slug = re.sub(r"[^a-z0-9_-]", "", str(f.get("slug", "")).lower())[:40]
            if not slug or slug in seen:
                continue
            seen.add(slug)
            out.append({"slug": slug, "name": str(f.get("name", slug))[:40], "added": int(f.get("added", 0) or 0)})
    return out


# ----- היסטוריית צפייה -----
def _hist_load():
    if _HIST["list"] is None:
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            _HIST["list"] = data if isinstance(data, list) else []
        except Exception:
            _HIST["list"] = []
    return _HIST["list"]


def _hist_save():
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(_HIST["list"], f, ensure_ascii=False)
    except Exception as e:
        log("history save failed: %r" % (e,))


def _downloads_dir():
    d = os.path.join(os.path.expanduser("~"), "Downloads")
    return d if os.path.isdir(d) else os.path.expanduser("~")


# ----- התראות -----
def _toast(title, body):
    """התראת Windows (PowerShell). הטקסט עובר במשתני סביבה ולא בתוך הפקודה."""
    if os.name != "nt":
        return
    script = (
        "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null;"
        "$x = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02);"
        "$n = $x.GetElementsByTagName('text');"
        "$n.Item(0).AppendChild($x.CreateTextNode($env:KB_TITLE)) | Out-Null;"
        "$n.Item(1).AppendChild($x.CreateTextNode($env:KB_BODY)) | Out-Null;"
        "$t = [Windows.UI.Notifications.ToastNotification]::new($x);"
        "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("
        "'{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\\WindowsPowerShell\\v1.0\\powershell.exe').Show($t)")
    env = dict(os.environ, KB_TITLE=title[:120], KB_BODY=body[:200])
    subprocess.Popen(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-Command", script],
                     env=env, creationflags=0x08000000)


def _beep():
    try:
        import winsound
        winsound.MessageBeep(winsound.MB_ICONASTERISK)
    except Exception:
        pass


def _flash(w):
    """מהבהב באייקון בשורת המשימות כדי למשוך תשומת לב."""
    try:
        import ctypes
        from ctypes import wintypes

        class FLASHWINFO(ctypes.Structure):
            _fields_ = [("cbSize", wintypes.UINT), ("hwnd", wintypes.HWND), ("dwFlags", wintypes.DWORD),
                        ("uCount", wintypes.UINT), ("dwTimeout", wintypes.DWORD)]
        hwnd = int(w.native.Handle.ToInt64())
        info = FLASHWINFO(ctypes.sizeof(FLASHWINFO), hwnd, 0x0000000F, 5, 0)
        ctypes.windll.user32.FlashWindowEx(ctypes.byref(info))
    except Exception:
        pass


def _do_notify(payload, settings):
    key = str(payload.get("key", ""))[:120]
    now = time.time()
    with _LOCK:
        for k in [k for k, t in _NOTIFIED.items() if now - t > 6 * 3600]:
            _NOTIFIED.pop(k, None)
        if key and key in _NOTIFIED:
            return False
        if key:
            _NOTIFIED[key] = now
    title, body = str(payload.get("title", "קיקבוב")), str(payload.get("body", ""))
    try:
        _toast(title, body)
    except Exception as e:
        log("toast failed: %r" % (e,))
    if settings.get("notifySound", True) is not False:
        _beep()
    w = _TABS.get(_ACTIVE["id"])
    if w is not None:
        _flash(w)
        try:
            w.evaluate_js("window.__kbLive && window.__kbLive(" + json.dumps(payload, ensure_ascii=False) + ")")
        except Exception:
            pass
    return True


# ----- חלון רקע שבודק מי עלה לשידור (מוסתר) -----
def sync_worker():
    try:
        cfg = read_cfg()
        s = cfg["settings"]
        want = (_STARTED["v"] and bool(_ORDER) and s.get("notify") is not False and
                (len(cfg["favorites"]) > 0 or s.get("notifyFollowed", True) is not False))
        if want and _WORKER["w"] is None:
            wv = _W["wv"]
            import inspect
            params = inspect.signature(wv.create_window).parameters
            if "hidden" not in params:
                log("worker: hidden windows not supported by this pywebview")
                return
            w = wv.create_window("KickBob worker", WORKER_URL, width=420, height=300, hidden=True, js_api=Api("worker"))
            _WORKER["w"] = w

            def on_loaded():
                def work():
                    c = read_cfg()
                    js = WORKER_JS.replace("__CFG__", json.dumps({"settings": c["settings"], "favorites": c["favorites"]}, ensure_ascii=False))
                    try:
                        w.evaluate_js(js)
                    except Exception as e:
                        log("worker inject failed: %r" % (e,))
                threading.Thread(target=work, daemon=True).start()
            w.events.loaded += on_loaded
        elif not want and _WORKER["w"] is not None:
            w = _WORKER["w"]
            _WORKER["w"] = None
            try:
                w.destroy()
            except Exception:
                pass
    except Exception as e:
        log("sync_worker failed: %r" % (e,))


def _sync_worker_async():
    threading.Thread(target=sync_worker, daemon=True).start()


def _stop_worker():
    w = _WORKER["w"]
    _WORKER["w"] = None
    if w is not None:
        try:
            w.destroy()
        except Exception:
            pass


# ----- עדכון אוטומטי -----
def _ver_tuple(v):
    return tuple(int(n) for n in re.findall(r"\d+", v or ""))


def _is_newer(latest, current):
    a, b = _ver_tuple(latest), _ver_tuple(current)
    n = max(len(a), len(b))
    a += (0,) * (n - len(a))
    b += (0,) * (n - len(b))
    return a > b


def _feed_url(src):
    src = (src or "").strip()
    if re.fullmatch(r"[\w.-]+/[\w.-]+", src):
        return "https://api.github.com/repos/%s/releases/latest" % src
    return src


def _http_json(url, timeout=12):
    req = urllib.request.Request(url, headers={"User-Agent": "KickBob/" + VERSION_NUM.replace(" ", "_"), "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _pick_asset(assets):
    frozen = bool(getattr(sys, "frozen", False))
    for a in assets or []:
        n, u = str(a.get("name", "")).lower(), str(a.get("browser_download_url", ""))
        if frozen and n.endswith(".exe") and u.startswith("https://"):
            return "exe", u
        if not frozen and n == "kickbob.py" and u.startswith("https://"):
            return "py", u
    return None, ""


def check_update():
    try:
        src = str(read_cfg()["settings"].get("updateRepo", "")).strip()
        if not src:
            _UPDATE.update(info=None, error="no_source", last=time.time())
            return {"ok": False, "error": "no_source"}
        url = _feed_url(src)
        if not url.startswith("https://"):
            return {"ok": False, "error": "bad_source"}
        d = _http_json(url)
        if "tag_name" in d:
            latest, notes, page = str(d.get("tag_name", "")), str(d.get("body") or ""), str(d.get("html_url") or "")
            kind, dl = _pick_asset(d.get("assets"))
        else:
            latest, notes, page = str(d.get("version", "")), str(d.get("notes") or ""), str(d.get("page") or "")
            dl = str(d.get("url") or "")
            kind = d.get("kind") if d.get("kind") in ("exe", "py") and dl.startswith("https://") else None
        info = {"ok": True, "current": VERSION, "latest": latest, "newer": _is_newer(latest, VERSION),
                "notes": notes[:1500], "page": page, "kind": kind, "url": dl}
        _UPDATE.update(info=info, error="", last=time.time())
        return info
    except Exception as e:
        _UPDATE.update(error=str(e)[:200], last=time.time())
        return {"ok": False, "error": str(e)[:200]}


def _update_loop():
    time.sleep(12)
    while True:
        try:
            s = read_cfg()["settings"]
            if s.get("autoUpdate", True) is not False and str(s.get("updateRepo", "")).strip():
                check_update()
        except Exception as e:
            log("update loop: %r" % (e,))
        time.sleep(6 * 3600)


def _download(url, dst, limit=200 * 1024 * 1024):
    req = urllib.request.Request(url, headers={"User-Agent": "KickBob"})
    with urllib.request.urlopen(req, timeout=60) as r, open(dst, "wb") as f:
        size = 0
        while True:
            chunk = r.read(1 << 16)
            if not chunk:
                break
            size += len(chunk)
            if size > limit:
                raise ValueError("file too large")
            f.write(chunk)
    return dst


def _close_all():
    _stop_worker()
    for w in list(_TABS.values()):
        try:
            w.destroy()
        except Exception:
            pass


def apply_update():
    info = _UPDATE.get("info")
    if not info or not info.get("newer"):
        return {"ok": False, "error": "no_update"}
    kind, url = info.get("kind"), info.get("url") or ""
    try:
        if kind in ("exe", "py") and url.startswith("https://"):
            tmp = tempfile.mkdtemp(prefix="kickbob_upd_")
            if kind == "py":
                dst = _download(url, os.path.join(tmp, "kickbob.py"), 8 * 1024 * 1024)
                text = open(dst, "r", encoding="utf-8").read()
                ast.parse(text)
                if "VERSION =" not in text:
                    raise ValueError("not a KickBob file")
                target = os.path.abspath(__file__)
                shutil.copyfile(target, target + ".bak")
                shutil.copyfile(dst, target)
                subprocess.Popen([sys.executable, target] + sys.argv[1:])
            else:
                dst = _download(url, os.path.join(tmp, "KickBob_new.exe"))
                target = sys.executable
                bat = os.path.join(tmp, "update.bat")
                bat_text = ('@echo off\r\n'
                            'for /l %%i in (1,1,30) do (\r\n'
                            '  timeout /t 1 /nobreak >nul\r\n'
                            '  move /y "__NEW__" "__OLD__" >nul 2>&1 && goto done\r\n'
                            ')\r\n:done\r\nstart "" "__OLD__"\r\n').replace("__NEW__", dst).replace("__OLD__", target)
                with open(bat, "w", encoding="utf-8") as f:
                    f.write(bat_text)
                subprocess.Popen(["cmd", "/c", bat], creationflags=0x00000008 | 0x08000000)
            threading.Timer(1.2, _close_all).start()
            return {"ok": True, "restart": True}
        page = info.get("page") or url
        if page:
            webbrowser.open(page)
            return {"ok": True, "opened": True}
        return {"ok": False, "error": "no_asset"}
    except Exception as e:
        log("apply_update failed: %r" % (e,))
        return {"ok": False, "error": str(e)[:200]}


# ----- דף הבית / כרטיסייה חדשה (מועדפים וסימניות) -----
def build_newtab():
    cfg = read_cfg()

    def tile(href, label, slug=""):
        letter = htmllib.escape((label.strip()[:1] or "?").upper())
        extra = ' data-slug="%s"' % htmllib.escape(slug) if slug else ""
        return ('<a class="t" href="%s"%s><i>%s</i><span>%s</span><b class="live"></b></a>'
                % (htmllib.escape(href, quote=True), extra, letter, htmllib.escape(label[:28])))
    favs = "".join(tile("https://kick.com/" + f["slug"], f.get("name") or f["slug"], f["slug"]) for f in cfg["favorites"][:24])
    bms = "".join(tile(b["url"], b.get("title") or b["url"]) for b in cfg["bookmarks"][:16])
    favs_block = ('<h2>ערוצים מועדפים <a href="#" onclick="window.__kbOpen&&__kbOpen.fav();return false">ניהול</a></h2><div class="tiles">%s</div>' % favs) if favs else \
        '<h2>ערוצים מועדפים</h2><p class="hint">עוד אין מועדפים. <a href="#" onclick="window.__kbOpen&&__kbOpen.fav();return false">הוסף ערוצים</a></p>'
    bms_block = ('<h2>סימניות <a href="#" onclick="window.__kbOpen&&__kbOpen.bm();return false">ניהול</a></h2><div class="tiles">%s</div>' % bms) if bms else ""
    return NEWTAB_HTML.replace("{{FAVS}}", favs_block).replace("{{BMS}}", bms_block).replace("{{VERSION}}", VERSION)



def _cfg_path(name):
    return os.path.join(DATA_DIR, name + ".json")


def read_cfg_raw(name):
    try:
        with open(_cfg_path(name), "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def read_cfg():
    out = {}
    for n in CFG_NAMES:
        want = list if n in LIST_CFGS else dict
        try:
            o = json.loads(read_cfg_raw(n) or ("[]" if want is list else "{}"))
            out[n] = o if isinstance(o, want) else want()
        except Exception:
            out[n] = want()
    return out


def _host(url):
    try:
        from urllib.parse import urlparse
        return urlparse(url).hostname or ""
    except Exception:
        return ""


def _work_area():
    """אזור העבודה של המסך (בלי שורת המשימות), ביחידות לוגיות. None אם לא זמין."""
    try:
        import ctypes
        from ctypes import wintypes
        rect = wintypes.RECT()
        ctypes.windll.user32.SystemParametersInfoW(0x30, 0, ctypes.byref(rect), 0)
        try:
            scale = ctypes.windll.user32.GetDpiForSystem() / 96.0
        except Exception:
            scale = 1.0
        return (int(rect.left / scale), int(rect.top / scale),
                int((rect.right - rect.left) / scale), int((rect.bottom - rect.top) / scale))
    except Exception:
        return None


def activate(tid):
    w = _TABS.get(tid)
    if w is None:
        return
    prev_id = _ACTIVE["id"]
    prev = _TABS.get(prev_id) if prev_id and prev_id != tid else None
    _ACTIVE["id"] = tid
    if not _STARTED["v"]:
        return
    geo = None
    if prev is not None:
        try:
            geo = (prev.x, prev.y, prev.width, prev.height)
        except Exception:
            geo = None
    try:
        w.show()
    except Exception as e:
        log("show failed: %r" % (e,))
    if geo:
        try:
            w.move(geo[0], geo[1])
            w.resize(geo[2], geo[3])
        except Exception:
            pass
    if prev is not None:
        try:
            prev.hide()
        except Exception as e:
            log("hide failed: %r" % (e,))


def on_closed(tid):
    was_active = _ACTIVE["id"] == tid
    _TABS.pop(tid, None)
    if tid in _ORDER:
        _ORDER.remove(tid)
    _TITLES.pop(tid, None)
    _URLS.pop(tid, None)
    if not _ORDER:
        _stop_worker()
    if was_active:
        _ACTIVE["id"] = None
        if _ORDER:
            activate(_ORDER[-1])


def close_tab(tid):
    w = _TABS.get(tid)
    if w is None:
        return
    on_closed(tid)
    try:
        w.destroy()
    except Exception as e:
        log("destroy failed: %r" % (e,))


def attach(w, tid):
    def inject(js):
        try:
            w.evaluate_js(js)
        except Exception as e:
            log("inject failed: %r" % (e,))

    def on_loaded():
        # הזרקה אחרי טעינה בלבד, בתהליכון נפרד כדי לא לחסום את החלון
        def work():
            cfg = read_cfg()
            cfg["frameless"] = bool(FRAMELESS["v"])
            if not SAFE_MODE:
                inject(_TPL["blocker"].replace("__SETTINGS__", json.dumps(cfg["settings"], ensure_ascii=False)))
            inject(_TPL["ui"].replace("__CFG__", json.dumps(cfg, ensure_ascii=False)))
        import threading
        threading.Thread(target=work, daemon=True).start()

    w.events.loaded += on_loaded
    w.events.closed += lambda: on_closed(tid)


def create_tab(url=None):
    wv = _W["wv"]
    tid = "t%d" % _NEXT["n"]
    _NEXT["n"] += 1
    kw = dict(width=1280, height=800, min_size=(900, 600), js_api=Api(tid))
    if FRAMELESS["v"]:
        try:
            import inspect
            params = inspect.signature(wv.create_window).parameters
            for k, v in (("frameless", True), ("easy_drag", False), ("shadow", True)):
                if k in params:
                    kw[k] = v
        except Exception as e:
            log("frameless setup failed: %r" % (e,))
    base = _TABS.get(_ACTIVE["id"])
    if base is not None:
        try:
            kw.update(x=base.x, y=base.y, width=base.width, height=base.height)
        except Exception:
            pass
    if url:
        w = wv.create_window(TITLE, url, **kw)
    else:
        w = wv.create_window(TITLE, html=build_newtab(), **kw)
    _TABS[tid] = w
    _ORDER.append(tid)
    _TITLES[tid] = ""
    attach(w, tid)
    activate(tid)
    return tid


class Api:
    """פונקציות Python שהממשק יכול לקרוא להן. (שמות שמתחילים ב-_ לא נחשפים.)"""

    def __init__(self, tab_id):
        self._tab = tab_id

    # --- קבצי הגדרות משותפים ---
    def save_cfg(self, name, data):
        try:
            if name not in CFG_NAMES:
                return False
            new = json.loads(data)
            if name in LIST_CFGS:
                if not isinstance(new, list):
                    return False
                new = _clean_list(name, new)
                os.makedirs(DATA_DIR, exist_ok=True)
                with open(_cfg_path(name), "w", encoding="utf-8") as f:
                    f.write(json.dumps(new, ensure_ascii=False))
                if name == "favorites":
                    _sync_worker_async()
                return True
            if not isinstance(new, dict):
                return False
            if name == "progress":  # לא מאבדים התקדמות כשכמה כרטיסיות כותבות
                try:
                    old = json.loads(read_cfg_raw("progress") or "{}")
                    for k in ("xp", "seconds"):
                        new[k] = max(new.get(k, 0) or 0, old.get(k, 0) or 0)
                    ns, os_ = new.get("streamers") or {}, old.get("streamers") or {}
                    merged = dict(os_)
                    for k, v in ns.items():
                        try:
                            merged[k] = max(float(v), float(os_.get(k, 0) or 0))
                        except Exception:
                            pass
                    if len(merged) > 600:
                        keep = sorted(merged.items(), key=lambda kv: kv[1], reverse=True)[:500]
                        merged = dict(keep)
                    new["streamers"] = merged
                    names = dict(old.get("names") or {})
                    names.update(new.get("names") or {})
                    new["names"] = {k: v for k, v in names.items() if k in merged}
                except Exception:
                    pass
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(_cfg_path(name), "w", encoding="utf-8") as f:
                f.write(json.dumps(new, ensure_ascii=False))
            if name == "settings":
                _sync_worker_async()
            return True
        except Exception as e:
            log("save_cfg failed: %r" % (e,))
            return False

    def get_cfg(self, name):
        return read_cfg_raw(name) if name in CFG_NAMES else ""

    def clear_data(self):
        try:
            next(iter(_TABS.values())).clear_cookies()  # קיים בגרסאות חדשות של pywebview
        except Exception:
            pass
        try:
            open(WIPE_FLAG, "w").close()  # מחיקה סופית של תיקיית הנתונים בהפעלה הבאה
        except Exception:
            pass
        return True

    # --- כרטיסיות ---
    def get_tabs(self):
        return {"active": _ACTIVE["id"],
                "max": _WIN["max"],
                "tabs": [{"id": i, "title": _TITLES.get(i, ""), "host": _host(_URLS.get(i, ""))} for i in list(_ORDER)]}

    def report_title(self, title, url=""):
        _TITLES[self._tab] = (title or "")[:80]
        _URLS[self._tab] = (url or "")[:300]
        return True

    def new_tab(self, url=""):
        url = (url or "").strip()
        if url and not url.lower().startswith(("http://", "https://")):
            url = ""
        create_tab(url or None)
        return True

    def switch_tab(self, tab_id):
        activate(tab_id)
        return True

    def close_tab(self, tab_id=""):
        close_tab(tab_id or self._tab)
        return True

    # --- חלון: מזעור / הגדלה / סגירה / שינוי גודל (כשאין מסגרת של Windows) ---
    def window_minimize(self):
        try:
            _TABS[self._tab].minimize()
        except Exception as e:
            log("minimize failed: %r" % (e,))
        return True

    def toggle_maximize(self):
        w = _TABS.get(self._tab)
        if w is None:
            return False
        try:
            if _WIN["max"]:
                g = _WIN["prev"]
                if g:
                    w.move(g[0], g[1])
                    w.resize(g[2], g[3])
                else:
                    w.restore()
                _WIN["max"] = False
            else:
                try:
                    _WIN["prev"] = (w.x, w.y, w.width, w.height)
                except Exception:
                    _WIN["prev"] = None
                wa = _work_area()
                if wa:
                    w.move(wa[0], wa[1])
                    w.resize(wa[2], wa[3])
                else:
                    w.maximize()
                _WIN["max"] = True
        except Exception as e:
            log("maximize failed: %r" % (e,))
        return _WIN["max"]

    def window_close(self):
        _stop_worker()
        for w in list(_TABS.values()):
            try:
                w.destroy()
            except Exception:
                pass
        return True

    def resize_start(self, direction):
        w = _TABS.get(self._tab)
        _WIN["max"] = False
        try:
            _RS["geo"] = (w.x, w.y, w.width, w.height)
        except Exception:
            _RS["geo"] = None
        _RS["dir"] = str(direction)
        return True

    def resize_by(self, dx, dy):
        w = _TABS.get(self._tab)
        g, d = _RS["geo"], _RS["dir"]
        if w is None or not g:
            return False
        x, y, wd, ht = g
        if "e" in d:
            wd = g[2] + dx
        if "s" in d:
            ht = g[3] + dy
        if "w" in d:
            wd = g[2] - dx
            x = g[0] + dx
        if "n" in d:
            ht = g[3] - dy
            y = g[1] + dy
        if wd < 900:
            if "w" in d:
                x = g[0] + g[2] - 900
            wd = 900
        if ht < 600:
            if "n" in d:
                y = g[1] + g[3] - 600
            ht = 600
        try:
            w.move(int(x), int(y))
            w.resize(int(wd), int(ht))
        except Exception as e:
            log("resize failed: %r" % (e,))
        return True

    # --- היסטוריית צפייה ---
    def history_add(self, data):
        try:
            items = json.loads(data)
            with _LOCK:
                lst = _hist_load()
                idx = {(e.get("d"), e.get("slug")): e for e in lst}
                for it in items:
                    day = str(it.get("d", ""))[:10]
                    slug = re.sub(r"[^a-z0-9_-]", "", str(it.get("slug", "")).lower())[:60]
                    try:
                        sec = float(it.get("sec", 0))
                    except Exception:
                        continue
                    if not day or not slug or sec <= 0 or sec > 3600:
                        continue
                    e = idx.get((day, slug))
                    if e is None:
                        e = {"d": day, "slug": slug, "name": "", "sec": 0, "title": "", "cat": "", "t": 0}
                        lst.append(e)
                        idx[(day, slug)] = e
                    e["sec"] = round(e["sec"] + sec, 1)
                    for fld in ("name", "title", "cat"):
                        v = str(it.get(fld) or "")[:120]
                        if v:
                            e[fld] = v
                    e["t"] = int(time.time() * 1000)
                if len(lst) > 4000:
                    lst.sort(key=lambda e: e.get("t", 0), reverse=True)
                    del lst[4000:]
                _hist_save()
            return True
        except Exception as e:
            log("history_add failed: %r" % (e,))
            return False

    def history_get(self):
        with _LOCK:
            lst = sorted(_hist_load(), key=lambda e: (e.get("d", ""), e.get("t", 0)), reverse=True)[:3000]
        return json.dumps(lst, ensure_ascii=False)

    def history_export(self, fmt):
        try:
            with _LOCK:
                lst = sorted(_hist_load(), key=lambda e: (e.get("d", ""), e.get("t", 0)), reverse=True)
            stamp = time.strftime("%Y%m%d_%H%M%S")
            fmt = "json" if fmt == "json" else "csv"
            path = os.path.join(_downloads_dir(), "KickBob_history_%s.%s" % (stamp, fmt))
            if fmt == "json":
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(lst, f, ensure_ascii=False, indent=1)
            else:
                with open(path, "w", encoding="utf-8-sig", newline="") as f:
                    w = csv.writer(f)
                    w.writerow(["תאריך", "ערוץ", "שם", "דקות", "כותרת אחרונה", "קטגוריה"])
                    for e in lst:
                        w.writerow([e.get("d", ""), e.get("slug", ""), e.get("name", ""), round(e.get("sec", 0) / 60, 1), e.get("title", ""), e.get("cat", "")])
            return path
        except Exception as e:
            log("history_export failed: %r" % (e,))
            return ""

    def history_clear(self):
        with _LOCK:
            _HIST["list"] = []
            _hist_save()
        return True

    def open_path(self, path):
        try:
            path = os.path.abspath(str(path))
            if not path.startswith(os.path.expanduser("~")) or not os.path.exists(path):
                return False
            if os.name == "nt":
                subprocess.Popen(["explorer", "/select,", path])
            else:
                webbrowser.open("file://" + os.path.dirname(path))
            return True
        except Exception:
            return False

    # --- התראות ומצב שידור ---
    def notify(self, data):
        try:
            payload = json.loads(data)
            settings = read_cfg()["settings"]
            if settings.get("notify") is False:
                return False
            return _do_notify(payload, settings)
        except Exception as e:
            log("notify failed: %r" % (e,))
            return False

    def report_live(self, data):
        _LIVE["state"] = data if isinstance(data, str) and len(data) < 400000 else "{}"
        return True

    def get_live_state(self):
        return _LIVE["state"]

    # --- דף הבית ---
    def open_home(self):
        try:
            _TABS[self._tab].load_html(build_newtab())
            return True
        except Exception as e:
            log("open_home failed: %r" % (e,))
            return False

    # --- עדכונים ---
    def check_update(self):
        return json.dumps(check_update(), ensure_ascii=False)

    def get_update(self):
        info = _UPDATE.get("info")
        return json.dumps(info, ensure_ascii=False) if info else ""

    def apply_update(self):
        return json.dumps(apply_update(), ensure_ascii=False)

    def next_tab(self):
        if len(_ORDER) > 1 and _ACTIVE["id"] in _ORDER:
            activate(_ORDER[(_ORDER.index(_ACTIVE["id"]) + 1) % len(_ORDER)])
        return True


def main():
    try:
        import webview  # pip install pywebview
    except ImportError:
        print("חסרה החבילה pywebview. מתקין...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pywebview"])
        import webview
    _W["wv"] = webview

    # בקשת "נקה נתונים" מההפעלה הקודמת
    if os.path.exists(WIPE_FLAG):
        shutil.rmtree(DATA_DIR, ignore_errors=True)
        try:
            os.remove(WIPE_FLAG)
        except Exception:
            pass
    os.makedirs(DATA_DIR, exist_ok=True)

    _TPL["blocker"] = BLOCKER_JS
    _TPL["ui"] = (INJECT_JS
                  .replace("__HOME__", HOME_URL)
                  .replace("__FOLLOWING__", FOLLOWING_URL)
                  .replace("__VERSION__", VERSION)
                  .replace("__ABOUT_TEXT__", ABOUT_TEXT)
                  .replace("__ABOUT_LINK__", ABOUT_LINK)
                  .replace("__INFO__", json.dumps(INFO, ensure_ascii=False))
                  .replace("__SAFE__", "true" if SAFE_MODE else "false"))

    cfg = read_cfg()
    if cfg["settings"].get("nativeFrame") is True:
        FRAMELESS["v"] = False
    start_url = None if cfg["settings"].get("startPage") == "newtab" else HOME_URL
    create_tab(start_url)

    icon = os.path.join(getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__))), "kickbob.ico")
    def started():
        _STARTED.update(v=True)
        threading.Thread(target=_update_loop, daemon=True).start()
        threading.Timer(4.0, sync_worker).start()
    try:
        webview.start(started, private_mode=False, storage_path=DATA_DIR, icon=icon)
    except TypeError:
        webview.start(started, private_mode=False, storage_path=DATA_DIR)


if __name__ == "__main__":
    main()
