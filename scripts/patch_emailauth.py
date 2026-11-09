with open(r'C:\Users\Usuario\mcp-hub\src\emailauth.js', 'r', encoding='utf-8') as f:
    c = f.read()

old = """async function sendCode(env, email, code) {
  const r = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: { authorization: `Bearer ${env.RESEND_API_KEY}`, "content-type": "application/json", "user-agent": "mcp-hub-oauth" },
    body: JSON.stringify({
      from: env.EMAIL_FROM || "Flint by KeyFlint <licenses@keyflint.dev>",
      to: [email],
      subject: `Tu código de acceso a Flint: ${code}`,
      text: `Tu código para conectar Flint by KeyFlint es ${code}\\n\\nCaduca en 10 minutos. Si no lo has pedido tú, ignora este correo: nadie puede usar tu licencia sin este código.\\n\\nKeyFlint · support@keyflint.dev`,
    }),
    signal: AbortSignal.timeout(8000),
  });
  return r.ok;
}"""

new = """async function sendCode(env, email, code) {
  const key = String(env.RESEND_API_KEY || "").trim();
  const from = String(env.EMAIL_FROM || "Flint by KeyFlint <licenses@keyflint.dev>").trim();
  try {
    const r = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: { authorization: `Bearer ${key}`, "content-type": "application/json", "user-agent": "mcp-hub-oauth" },
      body: JSON.stringify({
        from,
        to: [email],
        subject: `Tu código de acceso a Flint: ${code}`,
        text: `Tu código para conectar Flint by KeyFlint es ${code}\\n\\nCaduca en 10 minutos. Si no lo has pedido tú, ignora este correo: nadie puede usar tu licencia sin este código.\\n\\nKeyFlint · support@keyflint.dev`,
      }),
      signal: AbortSignal.timeout(8000),
    });
    if (!r.ok) {
      const err = await r.text().catch(() => "");
      console.error("resend email error", r.status, err);
    }
    return r.ok;
  } catch (e) {
    console.error("resend fetch exception", e?.message);
    return false;
  }
}"""

le = '\r\n' if '\r\n' in c else '\n'
old_fmt = old.replace('\n', le)
new_fmt = new.replace('\n', le)

assert old_fmt in c, 'old block not found'
c = c.replace(old_fmt, new_fmt, 1)

with open(r'C:\Users\Usuario\mcp-hub\src\emailauth.js', 'w', encoding='utf-8', newline='') as f:
    f.write(c)

print('Updated src/emailauth.js successfully.')
