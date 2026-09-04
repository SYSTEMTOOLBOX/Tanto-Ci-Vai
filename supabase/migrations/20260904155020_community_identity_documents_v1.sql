create table public.community_identity_documents (
  user_id uuid primary key references auth.users(id) on delete cascade,
  document_type text not null check (document_type in ('identity_card','driving_license')),
  first_name text not null check (length(btrim(first_name)) between 1 and 80),
  last_name text not null check (length(btrim(last_name)) between 1 and 80),
  front_path text not null,
  back_path text not null,
  license_category text,
  license_b_since date,
  license_expires_on date,
  license_expiry_reminder boolean not null default false,
  submitted_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint community_identity_documents_driver_fields check (
    document_type <> 'driving_license'
    or (
      license_category is not null
      and license_b_since is not null
      and license_expires_on is not null
      and license_expires_on >= license_b_since
    )
  )
);

alter table public.community_identity_documents enable row level security;
revoke all on table public.community_identity_documents from anon;
grant select, insert, update, delete on table public.community_identity_documents to authenticated;

create policy "community_documents_select_own"
on public.community_identity_documents
for select
to authenticated
using ((select auth.uid()) = user_id);

create policy "community_documents_insert_own"
on public.community_identity_documents
for insert
to authenticated
with check ((select auth.uid()) = user_id);

create policy "community_documents_update_own"
on public.community_identity_documents
for update
to authenticated
using ((select auth.uid()) = user_id)
with check ((select auth.uid()) = user_id);

create policy "community_documents_delete_own"
on public.community_identity_documents
for delete
to authenticated
using ((select auth.uid()) = user_id);

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'community-documents',
  'community-documents',
  false,
  8388608,
  array['image/jpeg','image/png','image/webp']::text[]
)
on conflict (id) do update
set public = excluded.public,
    file_size_limit = excluded.file_size_limit,
    allowed_mime_types = excluded.allowed_mime_types;

create policy "community_documents_storage_select_own"
on storage.objects
for select
to authenticated
using (
  bucket_id = 'community-documents'
  and (storage.foldername(name))[1] = (select auth.uid()::text)
);

create policy "community_documents_storage_insert_own"
on storage.objects
for insert
to authenticated
with check (
  bucket_id = 'community-documents'
  and (storage.foldername(name))[1] = (select auth.uid()::text)
);

create policy "community_documents_storage_update_own"
on storage.objects
for update
to authenticated
using (
  bucket_id = 'community-documents'
  and (storage.foldername(name))[1] = (select auth.uid()::text)
)
with check (
  bucket_id = 'community-documents'
  and (storage.foldername(name))[1] = (select auth.uid()::text)
);

create policy "community_documents_storage_delete_own"
on storage.objects
for delete
to authenticated
using (
  bucket_id = 'community-documents'
  and (storage.foldername(name))[1] = (select auth.uid()::text)
);
