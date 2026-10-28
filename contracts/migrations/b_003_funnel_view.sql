-- B5: public report. Returns counts and top quotes only, never emails.
alter table waitlists add column if not exists report_public boolean not null default false;

create or replace function public_report(p_slug text)
returns json
language sql stable security definer set search_path = public
as $$
  select case when not w.report_public
    then json_build_object('public', false, 'product_name', w.product_name)
    else json_build_object(
      'public', true,
      'product_name', w.product_name,
      'product_description', w.product_description,
      'signups', s.signups,
      'humans', s.humans,
      'pain', s.pain,
      'paid', s.paid,
      'updated_at', coalesce(s.updated_at, w.created_at),
      'quotes', (
        select coalesce(json_agg(q.pain_quote), '[]'::json) from (
          select pain_quote from signups
          where waitlist_id = w.id and human_verdict = 'verified' and pain_score >= 70
            and pain_quote is not null and pain_quote <> ''
          order by pain_score desc limit 3
        ) q
      )
    ) end
  from waitlists w
  cross join lateral (
    select count(*) as signups,
           count(*) filter (where human_verdict = 'verified') as humans,
           count(*) filter (where human_verdict = 'verified' and pain_score >= 70) as pain,
           count(*) filter (where deposit_status = 'paid') as paid,
           max(created_at) as updated_at
    from signups where waitlist_id = w.id
  ) s
  where w.slug = p_slug
$$;

grant execute on function public_report(text) to anon, authenticated;
