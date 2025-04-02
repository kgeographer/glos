-- ATU place work
set search_path = folklore, ne;

-- places with counts of types and geometry
WITH toponym_counts AS (
  SELECT 
    rp.toponym, 
    rp.geo_class, 
    COUNT(tr.type_id) AS type_count
  FROM 
    ref_place_atu_norm rp
  LEFT JOIN 
    type_ref tr 
    ON rp.ref_term = tr.ref_term
  GROUP BY 
    rp.toponym, 
    rp.geo_class
)
SELECT 
  tc.toponym,
  tc.geo_class,
  tc.type_count,
  CASE 
    WHEN tc.geo_class IN ('admin_0', 'multi0') THEN a0.geom
    WHEN tc.geo_class = 'admin_1' THEN a1.geom
  END AS geometry
  into folklore.map_atu_01
FROM 
  toponym_counts tc
LEFT JOIN ne.admin0_10m a0 
  ON tc.toponym = a0.name 
  AND tc.geo_class IN ('admin_0', 'multi0')
LEFT JOIN ne.admin1_10m a1 
  ON tc.toponym = a1.name 
  AND tc.geo_class = 'admin_1'
WHERE 
  (a0.geom IS NOT NULL OR a1.geom IS NOT NULL)
ORDER BY 
  tc.type_count DESC;

-- types for a toponym
SELECT 
    tr.type_id,
    rp.ref_term,
    rp.geo_class,
    rp.toponym
FROM 
    type_ref tr
JOIN 
    ref_place_atu_norm rp ON tr.ref_term = rp.ref_term
WHERE 
    rp.toponym = 'Latvia';  -- Replace 'Latvia' with any toponym you want to query

-- tale type counts per toponym
SELECT 
    rp.toponym, 
    COUNT(DISTINCT tr.type_id) AS tale_count
FROM 
    type_ref tr
JOIN 
    ref_place_atu_norm rp ON tr.ref_term = rp.ref_term
GROUP BY 
    rp.toponym
ORDER BY 
    tale_count DESC;    


-- normalized atu term > toponym
CREATE TABLE ref_place_atu_norm (
    id SERIAL PRIMARY KEY,
    ref_term_id INTEGER,
    ref_term VARCHAR,
    geo_class VARCHAR,
    toponym VARCHAR
);
INSERT INTO ref_place_atu_norm (ref_term_id, ref_term, geo_class, toponym)
SELECT 
    id,
    ref_term,
    geo_class,
    unnest(string_to_array(toponyms, ', ')) AS toponym
FROM 
    ref_place_atu;

---- **** ---- **** ---- **** ---- **** ---- **** ---- **** 
select subregion from ne.admin0_10m am where subregion like '%Africa';

select name from ne.admin0_10m 
	where subregion like 'Middle Africa' order by name;

SELECT name FROM ne.admin0_10m WHERE geom IS NULL;

WITH country_list AS (
    SELECT UNNEST(ARRAY[  
'Syria','Democratic Republic of the Congo','Republic of the Congo',
'Burundi','Comoros','Djibouti','Eritrea','Ethiopia','Madagascar','Malawi','Mauritius',
'Mozambique','Rwanda','S. Sudan','Seychelles','Somalia','Zambia','Zimbabwe',
'Finland','Sweden','Suriname','Republic of Korea','Dem. Rep. Korea',
'Papua New Guinea','Fiji','Vanuatu','Micronesia','Marshall Is.','Palau','Egypt','Libya',
'Tunisia','Algeria','Morocco','United States','Canada','Indonesia','Iran',
'Iraq','Kuwait','Saudi Arabia','Bahrain','Qatar','United Arab Emirates','Oman','Samoa','Tonga',
'Tuvalu','Argentina','Bolivia','Brazil','Brazilian Island','Chile','Colombia','Ecuador',
'Falkland Is.','Guyana','Paraguay','Peru','Uruguay','Venezuela','Kenya','Tanzania',
'Uganda','Benin','Burkina Faso','Cabo Verde','Côte d''Ivoire','Gambia','Ghana',
'Guinea','Guinea-Bissau','Liberia','Mali','Mauritania','Niger','Nigeria','Saint Helena',
'Senegal','Sierra Leone','Togo','Anguilla','Antigua and Barb.','Aruba','Bahamas','Barbados',
'British Virgin Is.','Cayman Is.','Cuba','Curaçao','Dominica','Dominican Republic','Grenada',
'Haiti','Jamaica','Montserrat','Puerto Rico','Saint Kitts and Nevis','Saint Lucia','Saint-Martin',
'Sint Maarten','St-Barthélemy','St. Vin. and Gren.','Trinidad and Tobago','Turks and Caicos Is.',
'U.S. Virgin Is.']) AS name
)
SELECT cl.name, ne.name, ne.geom 
FROM country_list cl
LEFT JOIN ne.admin0_10m ne ON cl.name = ne.name
WHERE ne.name IS NOT NULL;

WITH country_list AS (
    SELECT UNNEST(ARRAY[
        'Syria','Iraq','Democratic Republic of the Congo','Republic of the Congo',
        'Burundi','Comoros','Djibouti','Eritrea','Ethiopia','Kenya','Madagascar','Malawi','Mauritius',
        'Mozambique','Rwanda','S. Sudan','Seychelles','Somalia','Tanzania','Uganda','Zambia','Zimbabwe',
        'Finland','Sweden','Guyana','Suriname','Republic of Korea','Dem. Rep. Korea',
        'Papua New Guinea','Fiji','Vanuatu','Micronesia','Marshall Is.','Palau','Egypt','Libya',
        'Tunisia','Algeria','Morocco','United States','Canada','Papua New Guinea','Indonesia','Iran',
        'Iraq','Kuwait','Saudi Arabia','Bahrain','Qatar','United Arab Emirates','Oman','Samoa','Tonga',
        'Tuvalu','Argentina','Bolivia','Brazil','Brazilian Island','Chile','Colombia','Ecuador',
        'Falkland Is.','Guyana','Paraguay','Peru','Suriname','Uruguay','Venezuela','Kenya','Tanzania',
        'Uganda','Mozambique','Benin','Burkina Faso','Cabo Verde','Côte d''Ivoire','Gambia','Ghana',
        'Guinea','Guinea-Bissau','Liberia','Mali','Mauritania','Niger','Nigeria','Saint Helena',
        'Senegal','Sierra Leone','Togo','Anguilla','Antigua and Barb.','Aruba','Bahamas','Barbados',
        'British Virgin Is.','Cayman Is.','Cuba','Curaçao','Dominica','Dominican Republic','Grenada',
        'Haiti','Jamaica','Montserrat','Puerto Rico','Saint Kitts and Nevis','Saint Lucia','Saint-Martin',
        'Sint Maarten','St-Barthélemy','St. Vin. and Gren.','Trinidad and Tobago','Turks and Caicos Is.',
        'U.S. Virgin Is.'
    ]) AS name
)
SELECT cl.name AS list_name, ne.name AS table_name
FROM country_list cl
FULL OUTER JOIN ne.admin0_10m ne ON cl.name = ne.name
WHERE cl.name IS NULL OR ne.name IS NULL;

SELECT name
FROM ne.admin0_10m 
WHERE name IN (
'Syria','Democratic Republic of the Congo','Republic of the Congo',
'Burundi','Comoros','Djibouti','Eritrea','Ethiopia','Madagascar','Malawi','Mauritius',
'Mozambique','Rwanda','S. Sudan','Seychelles','Somalia','Zambia','Zimbabwe',
'Finland','Sweden','Suriname','Republic of Korea','Dem. Rep. Korea',
'Papua New Guinea','Fiji','Vanuatu','Micronesia','Marshall Is.','Palau','Egypt','Libya',
'Tunisia','Algeria','Morocco','United States','Canada','Indonesia','Iran',
'Iraq','Kuwait','Saudi Arabia','Bahrain','Qatar','United Arab Emirates','Oman','Samoa','Tonga',
'Tuvalu','Argentina','Bolivia','Brazil','Brazilian Island','Chile','Colombia','Ecuador',
'Falkland Is.','Guyana','Paraguay','Peru','Uruguay','Venezuela','Kenya','Tanzania',
'Uganda','Benin','Burkina Faso','Cabo Verde','Côte d''Ivoire','Gambia','Ghana',
'Guinea','Guinea-Bissau','Liberia','Mali','Mauritania','Niger','Nigeria','Saint Helena',
'Senegal','Sierra Leone','Togo','Anguilla','Antigua and Barb.','Aruba','Bahamas','Barbados',
'British Virgin Is.','Cayman Is.','Cuba','Curaçao','Dominica','Dominican Republic','Grenada',
'Haiti','Jamaica','Montserrat','Puerto Rico','Saint Kitts and Nevis','Saint Lucia','Saint-Martin',
'Sint Maarten','St-Barthélemy','St. Vin. and Gren.','Trinidad and Tobago','Turks and Caicos Is.',
'U.S. Virgin Is.'
)
AND TRIM(name) = name -- Ensures no extra whitespace
AND LENGTH(name) = CHAR_LENGTH(name) order by name; -- Ensures no hidden characters

select name, geom from ne.admin0_10m where name in (
        'Syria','Iraq','Democratic Republic of the Congo','Republic of the Congo',
        'Burundi','Comoros','Djibouti','Eritrea','Ethiopia','Kenya','Madagascar','Malawi','Mauritius',
        'Mozambique','Rwanda','S. Sudan','Seychelles','Somalia','Tanzania','Uganda','Zambia','Zimbabwe',
        'Finland','Sweden','Guyana','Suriname','Republic of Korea','Dem. Rep. Korea',
        'Papua New Guinea','Fiji','Vanuatu','Micronesia','Marshall Is.','Palau','Egypt','Libya',
        'Tunisia','Algeria','Morocco','United States','Canada','Papua New Guinea','Indonesia','Iran',
        'Iraq','Kuwait','Saudi Arabia','Bahrain','Qatar','United Arab Emirates','Oman','Samoa','Tonga',
        'Tuvalu','Argentina','Bolivia','Brazil','Brazilian Island','Chile','Colombia','Ecuador',
        'Falkland Is.','Guyana','Paraguay','Peru','Suriname','Uruguay','Venezuela','Kenya','Tanzania',
        'Uganda','Mozambique','Benin','Burkina Faso','Cabo Verde','Côte d''Ivoire','Gambia','Ghana',
        'Guinea','Guinea-Bissau','Liberia','Mali','Mauritania','Niger','Nigeria','Saint Helena',
        'Senegal','Sierra Leone','Togo','Anguilla','Antigua and Barb.','Aruba','Bahamas','Barbados',
        'British Virgin Is.','Cayman Is.','Cuba','Curaçao','Dominica','Dominican Republic','Grenada',
        'Haiti','Jamaica','Montserrat','Puerto Rico','Saint Kitts and Nevis','Saint Lucia','Saint-Martin',
        'Sint Maarten','St-Barthélemy','St. Vin. and Gren.','Trinidad and Tobago','Turks and Caicos Is.',
        'U.S. Virgin Is.');



-- ***** -- ***** -- ***** -- ***** -- ***** -- ***** -- ***** -- ***** 
-- 143/143
select name, iso_a2, geom into folklore.atu_a0 from ne.admin0_10m where name in (
'Afghanistan','Albania','Algeria','Angola','Argentina','Armenia','Australia','Austria',
'Azerbaijan','Belarus','Belize','Benin','Bolivia','Bosnia and Herzegovina','Botswana',
'Brazil','Bulgaria','Burkina Faso','Burundi','Cambodia','Cameroon','Cabo Verde',
'Central African Republic','Chad','Chile','China','Colombia','Costa Rica',
'Côte d''Ivoire','Croatia','Cuba','Czechia','Denmark','Dominican Republic',
'Ecuador','Egypt','El Salvador','Eritrea','Estonia','Eswatini','Ethiopia',
'Finland','France','Gabon','Gambia','Georgia','Germany','Ghana','Greece','Guatemala',
'Guinea','Guinea-Bissau','Honduras','Hungary','Iceland','India','Indonesia','Iran',
'Iraq','Ireland','Israel','Italy','Japan','Jordan','Kazakhstan','Kenya','Kuwait',
'Kyrgyzstan','Laos','Latvia','Lebanon','Lesotho','Liberia','Libya','Lithuania',
'Luxembourg','Madagascar','Malawi','Malaysia','Mali','Malta','Mauritania','Mauritius',
'Mexico','Mongolia','Montenegro','Morocco','Mozambique','Myanmar','Namibia','Nepal',
'Netherlands','New Zealand','Nicaragua','Niger','Nigeria','North Macedonia','Norway','Oman',
'Pakistan','Panama','Paraguay','Peru','Philippines','Poland','Portugal','Puerto Rico','Qatar',
'Romania','Russia','Rwanda','Saudi Arabia','Senegal','Serbia','Sierra Leone',
'Slovakia','Slovenia','Somalia','South Africa','Spain','Sri Lanka','Sudan',
'Sweden','Switzerland','Syria','Tajikistan','Tanzania','Thailand','Togo','Tunisia','Turkey',
'Turkmenistan','Uganda','Ukraine','United Kingdom','United States','Uruguay','Uzbekistan',
'Venezuela','Vietnam','Yemen','Zambia','Zimbabwe') order by name;