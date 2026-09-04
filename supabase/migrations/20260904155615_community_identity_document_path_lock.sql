alter table public.community_identity_documents
add constraint community_identity_documents_owned_paths
check (
  front_path = user_id::text || '/' || document_type || '/front'
  and back_path = user_id::text || '/' || document_type || '/back'
);
