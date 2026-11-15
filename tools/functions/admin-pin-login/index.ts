// Admin sign-in with only the PIN. Deploy with verify_jwt = false (the PIN is the credential).
// POST {pin}            -> {r:'ok'|'wrong'|'locked'}              (checks the PIN only)
// POST {pin, username}  -> {r:'ok', token_hash} | wrong | locked  (client then calls auth.verifyOtp({token_hash,type:'magiclink'}), then rpc admin_unlock)
// Shares the 5-wrong-tries-per-15-minutes lockout (admin_attempts) with admin_verify_pin.
import { createClient } from "jsr:@supabase/supabase-js@2";

const NAMES = ["ZH_VARSITY_ADMIN", "AB_VARSITY_ADMIN"];
const NIL = "00000000-0000-0000-0000-000000000000";
const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, apikey, content-type, x-client-info",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const out = (b: unknown, s = 200) =>
  new Response(JSON.stringify(b), { status: s, headers: { ...CORS, "Content-Type": "application/json" } });

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
  if (req.method !== "POST") return out({ r: "error" }, 405);
  let body: { pin?: string; username?: string } = {};
  try { body = await req.json(); } catch (_) { return out({ r: "error" }, 400); }
  const pin = String(body.pin ?? "");
  const name = body.username ? String(body.username).trim().toUpperCase() : "";
  if (name && !NAMES.includes(name)) return out({ r: "error" }, 400);

  const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, {
    auth: { persistSession: false, autoRefreshToken: false },
  });

  const since = new Date(Date.now() - 15 * 60 * 1000).toISOString();
  const { count } = await sb.from("admin_attempts").select("id", { count: "exact", head: true }).gt("at", since);
  if ((count ?? 0) >= 5) return out({ r: "locked" });

  const { data: ok, error: e1 } = await sb.rpc("admin_pin_ok", { p_pin: pin });
  if (e1) return out({ r: "error" }, 500);
  if (!ok) {
    await sb.from("admin_attempts").insert({ uid: NIL });
    return out({ r: "wrong" });
  }
  if (!name) return out({ r: "ok" });

  const email = name.toLowerCase().replace(/_/g, "-") + "@admin.varsity.invalid";
  const pw = crypto.randomUUID() + crypto.randomUUID();
  await sb.auth.admin.createUser({ email, password: pw, email_confirm: true, user_metadata: { shared_admin: name } }); // already-exists error is fine
  const { data, error } = await sb.auth.admin.generateLink({ type: "magiclink", email });
  const th = data?.properties?.hashed_token;
  if (error || !th) return out({ r: "error" }, 500);
  await sb.from("admin_attempts").delete().eq("uid", NIL);
  return out({ r: "ok", token_hash: th });
});
