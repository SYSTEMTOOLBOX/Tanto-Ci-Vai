# Tanto-Ci-Vai

MVP per consegne locali/community nei piccoli comuni e nelle zone dove i servizi di delivery tradizionali sono poco presenti.

## Backend

Il backend usa Supabase.

Lo schema del database e le regole RLS sono versionati nel repository tramite migration:

`supabase/migrations/20260901162400_initial_schema.sql`

La migration contiene:
- profili utenti collegati a Supabase Auth
- consegne con cliente e rider
- coordinate GPS di ritiro e consegna
- compenso rider e commissione app
- stati della consegna
- Row Level Security
- funzione atomica `accetta_consegna`
- creazione automatica del profilo alla registrazione

Da questo momento le modifiche al database devono essere aggiunte come nuove migration dentro `supabase/migrations/`, evitando modifiche manuali non tracciate nel dashboard quando possibile.
