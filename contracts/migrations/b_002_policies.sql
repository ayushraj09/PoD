-- B2: row-level security. The backend and web server routes use the service key, which bypasses this.
alter table waitlists enable row level security;
alter table signups enable row level security;

create policy "founder reads own waitlists" on waitlists
  for select to authenticated using (owner_id = auth.uid());
create policy "founder creates own waitlists" on waitlists
  for insert to authenticated with check (owner_id = auth.uid());
create policy "founder updates own waitlists" on waitlists
  for update to authenticated using (owner_id = auth.uid()) with check (owner_id = auth.uid());
create policy "founder deletes own waitlists" on waitlists
  for delete to authenticated using (owner_id = auth.uid());

create policy "founder reads own signups" on signups
  for select to authenticated
  using (exists (select 1 from waitlists w where w.id = signups.waitlist_id and w.owner_id = auth.uid()));
create policy "founder deletes own signups" on signups
  for delete to authenticated
  using (exists (select 1 from waitlists w where w.id = signups.waitlist_id and w.owner_id = auth.uid()));

-- No policies for anon on either table: the public (anon) key can read nothing.
-- Storage bucket "audio" stays private with no storage.objects policies: only the service key can read it.
