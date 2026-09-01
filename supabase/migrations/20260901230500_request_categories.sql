-- Categorie richieste per la beta reale
alter table public.consegne
  add column if not exists categoria text not null default 'altro';

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'consegne_categoria_check'
      and conrelid = 'public.consegne'::regclass
  ) then
    alter table public.consegne
      add constraint consegne_categoria_check
      check (categoria in ('spesa','farmacia','ritiro','altro'));
  end if;
end;
$$;
