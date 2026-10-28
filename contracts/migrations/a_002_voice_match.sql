-- A5: same-voice lookup. pgvector's <=> is cosine DISTANCE, so similarity = 1 - distance.
-- Called by the backend with supabase.rpc("match_voices", {...}) using the service key.
create or replace function match_voices(
  p_waitlist_id uuid,
  p_embedding vector(192),
  p_exclude uuid,
  p_threshold float
)
returns table (id uuid, similarity float)
language sql stable
set search_path = public
as $$
  select s.id, 1 - (s.voice_embedding <=> p_embedding) as similarity
  from signups s
  where s.waitlist_id = p_waitlist_id
    and s.id <> p_exclude
    and s.voice_embedding is not null
    and 1 - (s.voice_embedding <=> p_embedding) >= p_threshold
  order by s.voice_embedding <=> p_embedding
  limit 5;
$$;

-- Only the backend (service role) may call it; the public key must not probe voices.
revoke execute on function match_voices(uuid, vector, uuid, float) from public, anon, authenticated;
grant execute on function match_voices(uuid, vector, uuid, float) to service_role;
