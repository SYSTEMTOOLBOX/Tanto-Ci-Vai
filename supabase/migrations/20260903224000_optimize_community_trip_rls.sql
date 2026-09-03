drop policy if exists community_trips_select on public.community_trips;
create policy community_trips_select on public.community_trips
for select to authenticated
using (active = true or user_id = (select auth.uid()));

drop policy if exists community_trips_insert on public.community_trips;
create policy community_trips_insert on public.community_trips
for insert to authenticated
with check (user_id = (select auth.uid()));

drop policy if exists community_trips_update on public.community_trips;
create policy community_trips_update on public.community_trips
for update to authenticated
using (user_id = (select auth.uid()))
with check (user_id = (select auth.uid()));

drop policy if exists community_trips_delete on public.community_trips;
create policy community_trips_delete on public.community_trips
for delete to authenticated
using (user_id = (select auth.uid()));
