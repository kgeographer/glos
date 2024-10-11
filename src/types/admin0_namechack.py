import psycopg2

# Connection to the PostgreSQL database
conn = psycopg2.connect(
    dbname="staging",
    user="postgres",
    host="localhost",
    port="5435"
)

# The list of country names you want to check
country_list = [
    'Syria','Iraq','Democratic Republic of the Congo','Republic of the Congo',
    'Burundi','Comoros','Djibouti','Eritrea','Ethiopia','Kenya','Madagascar','Malawi','Mauritius',
    'Mozambique','Rwanda','S. Sudan','Seychelles','Somalia','Tanzania','Uganda','Zambia','Zimbabwe',
    'Finland','Sweden','Guyana','Suriname','Republic of Korea','Dem. Rep. Korea',
    'Papua New Guinea','Fiji','Vanuatu','Micronesia','Marshall Is.','Palau','Egypt','Libya',
    'Tunisia','Algeria','Morocco','United States','Canada','Papua New Guinea','Indonesia','Iran',
    'Iraq','Kuwait','Saudi Arabia','Bahrain','Qatar','United Arab Emirates','Oman','Samoa','Tonga',
    'Tuvalu','Argentina','Bolivia','Brazil','Brazilian Island','Chile','Colombia','Ecuador',
    'Falkland Is.','Guyana','Paraguay','Peru','Suriname','Uruguay','Venezuela','Kenya','Tanzania',
    'Uganda','Mozambique','Benin','Burkina Faso','Cabo Verde','Côte d\'Ivoire','Gambia','Ghana',
    'Guinea','Guinea-Bissau','Liberia','Mali','Mauritania','Niger','Nigeria','Saint Helena',
    'Senegal','Sierra Leone','Togo','Anguilla','Antigua and Barb.','Aruba','Bahamas','Barbados',
    'British Virgin Is.','Cayman Is.','Cuba','Curaçao','Dominica','Dominican Republic','Grenada',
    'Haiti','Jamaica','Montserrat','Puerto Rico','Saint Kitts and Nevis','Saint Lucia','Saint-Martin',
    'Sint Maarten','St-Barthélemy','St. Vin. and Gren.','Trinidad and Tobago','Turks and Caicos Is.',
    'U.S. Virgin Is.'
]

# Dictionary to store results
country_results = {}

try:
    # Create a cursor to execute SQL queries
    with conn.cursor() as cursor:
        for country in country_list:
            # Execute a parameterized query for each country name
            cursor.execute("SELECT name, iso_a2, geom FROM ne.admin0_10m WHERE name = %s", (country,))
            result = cursor.fetchone()  # Fetch one result for the current country
            country_results[country] = result  # Store the result in the dictionary

    # Output the results for countries that were not found
    missing_countries = [country for country, result in country_results.items() if result is None]
    print(f"Total countries in list: {len(country_list)}")
    print(f"Total countries found: {len(country_list) - len(missing_countries)}")
    print(f"Missing countries (no record found): {missing_countries}")

finally:
    # Close the connection
    conn.close()
