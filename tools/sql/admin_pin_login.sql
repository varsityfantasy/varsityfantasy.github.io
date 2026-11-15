-- Admin sign-in with only the PIN (v508). Used by the admin-pin-login edge function (service role only).
-- Checks the PIN against admin_secret without needing a signed-in user. Not callable from the app.
CREATE OR REPLACE FUNCTION public.admin_pin_ok(p_pin text)
 RETURNS boolean
 LANGUAGE sql
 SECURITY DEFINER
 SET search_path TO 'public', 'extensions'
AS $function$
  select exists(select 1 from public.admin_secret
    where pin_hash = extensions.crypt(regexp_replace(coalesce(p_pin,''),'\D','','g'), pin_hash));
$function$;
REVOKE ALL ON FUNCTION public.admin_pin_ok(text) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.admin_pin_ok(text) TO service_role;
