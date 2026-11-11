/* Validador gratuito IBAN, NIF, NIE, CIF y Acreedor SEPA: todo se calcula en el navegador, nada se envía. */
(function () {
  "use strict";
  var NIF_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE";
  var CIF_LETTERS = "JABCDEFGHI";
  var IBAN_LENS = {
    ES: 24, PT: 25, FR: 27, DE: 22, IT: 27, BE: 16, NL: 18, GB: 22, IE: 22, LU: 20,
    AT: 20, CH: 21, DK: 18, SE: 24, NO: 15, FI: 18, PL: 28, CZ: 24, SK: 24, HU: 28,
    RO: 24, BG: 22, HR: 21, SI: 19, GR: 27, CY: 28, MT: 31, EE: 20, LV: 21, LT: 20,
  };
  var CCC_W = [1, 2, 4, 8, 5, 10, 9, 7, 3, 6];

  function clean(s) { return String(s || "").toUpperCase().replace(/[\s\-._]+/g, "").trim(); }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }

  function mod97(str) {
    var rem = 0;
    for (var i = 0; i < str.length; i++) {
      var code = str.charCodeAt(i);
      if (code >= 48 && code <= 57) {
        rem = (rem * 10 + (code - 48)) % 97;
      } else if (code >= 65 && code <= 90) {
        var val = code - 55;
        rem = (rem * 10 + Math.floor(val / 10)) % 97;
        rem = (rem * 10 + (val % 10)) % 97;
      } else {
        return -1;
      }
    }
    return rem;
  }

  function cccDigit(ten) {
    var sum = 0;
    for (var i = 0; i < 10; i++) sum += (ten.charCodeAt(i) - 48) * CCC_W[i];
    var r = 11 - (sum % 11);
    return r === 10 ? 1 : r === 11 ? 0 : r;
  }

  function formatIban(s) { return s.replace(/(.{4})/g, "$1 ").trim(); }

  function checkIban(raw) {
    var s = clean(raw);
    if (!/^[A-Z]{2}\d{2}[A-Z0-9]{10,30}$/.test(s)) return null;
    var cc = s.slice(0, 2);
    if (IBAN_LENS[cc] && s.length !== IBAN_LENS[cc]) {
      return { value: s, kind: "IBAN (" + cc + ")", valid: false, detail: "Longitud incorrecta para " + cc + ": " + s.length + " caracteres (esperados " + IBAN_LENS[cc] + ")." };
    }
    if (mod97(s.slice(4) + s.slice(0, 4)) !== 1) {
      return { value: formatIban(s), kind: "IBAN (" + cc + ")", valid: false, detail: "Dígitos de control ISO 13616 (mod 97) incorrectos." };
    }
    if (cc === "ES") {
      var bank = s.slice(4, 8), branch = s.slice(8, 12), dc = s.slice(12, 14), acct = s.slice(14, 24);
      var expect = String(cccDigit("00" + bank + branch)) + String(cccDigit(acct));
      if (dc !== expect) {
        return { value: formatIban(s), kind: "IBAN (ES)", valid: false, detail: "Pasa mod 97 pero falla el DC bancario español (CCC: esperado " + expect + ", recibido " + dc + ")." };
      }
      return { value: formatIban(s), kind: "IBAN (ES)", valid: true, detail: "Entidad " + bank + " · Oficina " + branch + " · DC " + dc + " · Cuenta " + acct };
    }
    return { value: formatIban(s), kind: "IBAN (" + cc + ")", valid: true, detail: "Válido según ISO 13616 (mod 97)." };
  }

  function checkNifNie(raw) {
    var s = clean(raw);
    var mNif = s.match(/^(\d{8})([A-Z])$/);
    if (mNif) {
      var want = NIF_LETTERS[parseInt(mNif[1], 10) % 23];
      var ok = mNif[2] === want;
      return { value: s, kind: "NIF / DNI", valid: ok, detail: ok ? "Letra correcta." : "Letra incorrecta (esperada " + want + ")." };
    }
    var mNie = s.match(/^([XYZ])(\d{7})([A-Z])$/);
    if (mNie) {
      var pre = { X: "0", Y: "1", Z: "2" }[mNie[1]];
      var wantNie = NIF_LETTERS[parseInt(pre + mNie[2], 10) % 23];
      var okNie = mNie[3] === wantNie;
      return { value: s, kind: "NIE", valid: okNie, detail: okNie ? "Letra correcta." : "Letra incorrecta (esperada " + wantNie + ")." };
    }
    return null;
  }

  function checkCif(raw) {
    var s = clean(raw);
    var m = s.match(/^([ABCDEFGHJNPQRSUVW])(\d{7})([0-9A-J])$/);
    if (!m) return null;
    var type = m[1], digits = m[2], ctrl = m[3];
    var evenSum = parseInt(digits[1], 10) + parseInt(digits[3], 10) + parseInt(digits[5], 10);
    var oddSum = 0;
    for (var i = 0; i < 7; i += 2) {
      var p = parseInt(digits[i], 10) * 2;
      oddSum += Math.floor(p / 10) + (p % 10);
    }
    var unit = (evenSum + oddSum) % 10;
    var d = unit === 0 ? 0 : 10 - unit;
    var l = CIF_LETTERS[d];
    var mustLetter = "PQRSNW".indexOf(type) >= 0;
    var mustDigit = "ABEH".indexOf(type) >= 0;
    var ok = mustLetter ? ctrl === l : mustDigit ? ctrl === String(d) : (ctrl === l || ctrl === String(d));
    var expected = mustLetter ? l : mustDigit ? String(d) : (d + " o " + l);
    return { value: s, kind: "CIF", valid: ok, detail: ok ? "Dígito/letra de control válido (tipo " + type + ")." : "Control incorrecto (esperado " + expected + ")." };
  }

  function checkSepaId(raw) {
    var s = clean(raw);
    var m = s.match(/^([A-Z]{2})(\d{2})([A-Z0-9]{3})([A-Z0-9]{1,28})$/);
    if (!m || IBAN_LENS[m[1]] === s.length) return null;
    if (mod97(m[4] + m[1] + m[2]) !== 1) {
      return { value: s, kind: "Acreedor SEPA (" + m[1] + ")", valid: false, detail: "Dígitos de control ISO 13616 incorrectos tras quitar sufijo " + m[3] + "." };
    }
    if (m[1] === "ES" && m[4].length === 9) {
      var sub = checkNifNie(m[4]) || checkCif(m[4]);
      if (sub && !sub.valid) {
        return { value: s, kind: "Acreedor SEPA (ES)", valid: false, detail: "Pasa mod 97 pero falla el NIF/CIF interno (" + m[4] + "): " + sub.detail };
      }
    }
    return { value: s, kind: "Acreedor SEPA (" + m[1] + ")", valid: true, detail: "Válido · Sufijo " + m[3] + " · ID " + m[4] };
  }

  function validateOne(raw) {
    var s = clean(raw);
    if (!s) return null;
    var iban = checkIban(s);
    if (iban && iban.valid) return iban;
    var sepa = checkSepaId(s);
    if (sepa && sepa.valid) return sepa;
    var nif = checkNifNie(s) || checkCif(s);
    if (nif) return nif;
    if (sepa && !/^\d+$/.test(s.slice(4))) return sepa;
    return iban || sepa ||
      { value: s, kind: "No reconocido", valid: false, detail: "No encaja con IBAN, NIF, NIE, CIF ni identificador de acreedor SEPA." };
  }

  function validateMany(text) {
    return String(text || "")
      .split(/[\r\n,;]+/)
      .map(function (x) { return x.trim(); })
      .filter(Boolean)
      .slice(0, 500)
      .map(validateOne)
      .filter(Boolean);
  }

  window.__validador = {
    checkIban: checkIban, checkNifNie: checkNifNie, checkCif: checkCif, checkSepaId: checkSepaId,
    validateOne: validateOne, validateMany: validateMany,
  };

  var form = document.querySelector("[data-val-form]"), input = document.querySelector("[data-val-input]");
  var out = document.querySelector("[data-val-out]"), sample = document.querySelector("[data-val-sample]");
  if (!form || !input || !out) return;

  function render(items) {
    if (!items.length) { out.hidden = true; out.innerHTML = ""; return; }
    var okCount = items.filter(function (x) { return x.valid; }).length;
    var h = '<p class="status ' + (okCount === items.length ? "ok" : "warn") + '">' +
      okCount + " de " + items.length + " válidos</p>" +
      '<div class="tw"><table class="uso-t"><thead><tr><th>Dato</th><th>Tipo</th><th>Estado</th><th>Detalle</th></tr></thead><tbody>';
    items.forEach(function (it) {
      h += "<tr><td class=\"tabnum\">" + esc(it.value) + "</td><td>" + esc(it.kind) + "</td><td class=\"" +
        (it.valid ? "ok" : "bad") + "\">" + (it.valid ? "✔ Válido" : "✘ Error") + '</td><td style="white-space:normal">' + esc(it.detail) + "</td></tr>";
    });
    h += "</tbody></table></div>";
    out.innerHTML = h;
    out.hidden = false;
  }

  form.addEventListener("submit", function (ev) { ev.preventDefault(); render(validateMany(input.value)); });
  input.addEventListener("input", function () { if (input.value.trim()) render(validateMany(input.value)); else out.hidden = true; });
  if (sample) {
    sample.addEventListener("click", function () {
      input.value = "ES9121000418450200051332\nB84372291\n12345678Z\nX0000001R\nES14000B84372291";
      render(validateMany(input.value));
    });
  }
})();
