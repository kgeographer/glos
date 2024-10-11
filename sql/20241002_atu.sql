-- misc. (latest first, mostly)
set search_path = folklore, ne, public;

-- Check the norm of the embeddings in the table
SELECT motif_id, sqrt(GREATEST(embedding <#> embedding, 0)) AS norm
FROM motif_embeddings
ORDER BY norm DESC
LIMIT 10;
SELECT motif_id, embedding
FROM motif_embeddings
LIMIT 5;

WITH zero_vector AS (
    SELECT array_fill(0, ARRAY[1536])::vector(1536) AS zero_vec
)
SELECT motif_id, sqrt(GREATEST(embedding <#> zero_vec, 0)) AS norm
FROM motif_embeddings, zero_vector
ORDER BY norm DESC
LIMIT 10;

-- get ranges and expand them
-- 
select * from edges_atu_tmi eat where type_id like '%–%';
-- 750A–750C	K1811

select * from edges_atu_tmi eat where motif_id like '%–%';

update edges_atu_tmi set motif_id = replace(motif_id,'–', '-')
	where motif_id like '%–%';

update edges_atu_tmi set motif_id = replace(motif_id, 'ff', '')
	where motif_id like '%ff';



-- ****** ---- ****** ---- ****** ---- ****** ---- ****** --
select distinct(type_id) from edges_atu_tmi eat; -- 1722
drop table bak.edges_atu_tmi;
select * into bak.edges_atu_tmi from edges_atu_tmi;

select * from edges_atu_tmi eat 
	where motif_id like '%.';

UPDATE edges_atu_tmi
SET motif_id = rtrim(motif_id, '.')
WHERE motif_id LIKE '%.';

UPDATE bak.edges_atu_tmi
SET motif_id = rtrim(motif_id, ' ')
WHERE motif_id LIKE '% ';

UPDATE edges_atu_tmi
SET motif_id = rtrim(motif_id, ' ')
WHERE motif_id LIKE '% ';


select * from bak.edges_atu_tmi where motif_id not like '%.';

-- ******* ---- ******* ---- ******* ---- ******* ---- ******* --
delete from motif_embeddings_3sm;
select array_length(embedding) from type_embeddings te limit 1; 


CREATE TABLE motif_embeddings_3sm (
	id serial4 NOT NULL,
	motif_id varchar(255) NULL,
	motif_text text NULL,
	embedding public.vector NULL,
	CONSTRAINT motif_embeddings_3sm_pkey1 PRIMARY KEY (id)
)

CREATE TABLE type_embeddings_3sm (
    type_id VARCHAR PRIMARY KEY,
    label TEXT,
    text TEXT,
    embedding VECTOR
);

CREATE TABLE type_embeddings_plus (
    type_id VARCHAR PRIMARY KEY,
    label TEXT,
    text TEXT,
    embedding VECTOR
);