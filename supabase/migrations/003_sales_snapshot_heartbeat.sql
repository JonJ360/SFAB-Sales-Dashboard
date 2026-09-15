begin;

create or replace function public.sfab_sales_heartbeat_snapshot(p_snapshot_id bigint)
returns boolean
language plpgsql
security definer
set search_path = ''
as $$
begin
  if coalesce(auth.jwt()->>'role','') <> 'ar_current_promoter' then
    raise insufficient_privilege using message = 'Structural Fab sales promotion role required';
  end if;

  update public.sfab_sales_current
  set promoted_at = now()
  where singleton = true
    and snapshot_id = p_snapshot_id;

  return found;
end;
$$;

revoke all on function public.sfab_sales_heartbeat_snapshot(bigint) from public, anon, authenticated;
grant execute on function public.sfab_sales_heartbeat_snapshot(bigint) to ar_current_promoter;

commit;
