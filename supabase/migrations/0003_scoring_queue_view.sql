-- 0003_scoring_queue_view.sql
-- Daily scorer queue: resolved handles with no score row yet, suppression
-- enforced at scoring time (F-108).

create or replace view v_prospects_to_score as
select p.id, p.ig_handle, p.segment, p.business_name
from prospects p
left join prospect_scores s on s.ig_handle = p.ig_handle
where p.ig_handle is not null
  and s.id is null
  and not exists (
    select 1 from suppression_list x where x.ig_handle = p.ig_handle
  );
