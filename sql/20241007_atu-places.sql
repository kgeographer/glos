-- ATU place work

set search_path = folklore, ne;

select subregion from ne.admin0_10m am where subregion like '%Africa';

select name from ne.admin0_10m 
	where subregion like 'Middle Africa' order by name;

select name, coalesce(iso_a2,''), geom from ne.admin0_10m where name in
('Syria','Iraq','Democratic Republic of the Congo','Republic of the Congo',
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

-- 
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
SELECT cl.name
FROM country_list cl
LEFT JOIN ne.admin0_10m ne ON cl.name = ne.name
WHERE ne.name IS NULL;



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