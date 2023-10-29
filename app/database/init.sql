CREATE TABLE IF NOT EXISTS public.document (id serial PRIMARY KEY, user_id integer, filename character varying(512) NOT NULL, "timestamp" character varying(512) NOT NULL, status character varying(512) NOT NULL, format_in character varying(512) NOT NULL, format_out character varying(512) NOT NULL, location_in character varying(512), location_out character varying(512));

CREATE TABLE IF NOT EXISTS public.userlogin (id serial PRIMARY KEY, username character varying(512) NOT NULL, useremail character varying(512) NOT NULL, userpassword character varying(512) NOT NULL);
ALTER TABLE public.document ADD CONSTRAINT document_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.userlogin (id);
ALTER TABLE public.userlogin OWNER to postgres;
