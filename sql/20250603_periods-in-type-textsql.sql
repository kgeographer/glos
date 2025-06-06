-- fix the '.' stripping on tale type 'text' field

set search_path = folklore, public, bak;

-- confirm bak has the periods (also the repeat of label field values we don't want)
SELECT f.type_id, f.text AS current_text, b.text AS backup_text
FROM folklore.type_embeddings_3sm f
JOIN bak.type_embeddings_bak b ON f.type_id = b.type_id
LIMIT 10;

UPDATE folklore.type_embeddings_3sm AS f
SET text = b.text
FROM bak.type_embeddings_bak AS b
WHERE f.type_id = b.type_id;
-- 2232

-- UPDATE to clean the text field where it starts with label

-- 1. Handle "Label. Rest" pattern --> 2119 rows
UPDATE folklore.type_embeddings_3sm 
SET text = TRIM(SUBSTRING(text FROM LENGTH(label) + 3))
WHERE text LIKE label || '. %'
  AND LENGTH(text) > LENGTH(label) + 2;

-- 2. Handle "Label.Rest" pattern (no space after period) --> 8 rows
UPDATE folklore.type_embeddings_3sm 
SET text = TRIM(SUBSTRING(text FROM LENGTH(label) + 2))
WHERE text LIKE label || '.%'
  AND text NOT LIKE label || '. %'  -- Don't re-process step 1
  AND LENGTH(text) > LENGTH(label) + 1;

-- 3. Handle "Label Rest" pattern (space but no period) --> 68 rows
UPDATE folklore.type_embeddings_3sm 
SET text = TRIM(SUBSTRING(text FROM LENGTH(label) + 2))
WHERE text LIKE label || ' %'
  AND text NOT LIKE label || '.%'  -- Don't re-process steps 1&2
  AND LENGTH(text) > LENGTH(label) + 1;

-- 4. Handle exact matches (text = label) --> 2 rows
UPDATE folklore.type_embeddings_3sm 
SET text = ''
WHERE text = label;

-- Now let's check random samples to see if any still start with label
SELECT 
    type_id,
    label,
    LEFT(text, 80) as text_preview,
    CASE WHEN text LIKE label || '%' THEN 'STILL HAS PREFIX' ELSE 'CLEAN' END as status
FROM folklore.type_embeddings_3sm 
ORDER BY RANDOM()
LIMIT 15;

-- some appearances of the label at start of 'text' were sort of warranted; how many?
SELECT 
    type_id,
    label,
    LEFT(text, 80) AS text_preview
FROM folklore.type_embeddings_3sm
WHERE text ~ '^[a-z]';

-- preview a fix
SELECT 
    type_id,
    label,
    LEFT(text, 80) AS old_text,
    LEFT(label || ' ' || text, 80) AS new_text
FROM folklore.type_embeddings_3sm
WHERE text ~ '^[a-z]';

-- looks good, do it
UPDATE folklore.type_embeddings_3sm
SET text = label || ' ' || text
WHERE text ~ '^[a-z]';