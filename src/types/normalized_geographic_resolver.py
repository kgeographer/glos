import os
import pandas as pd
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

db_params = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

class NormalizedGeographicResolver:
    """
    Create a normalized approach: resolve unique terms once, 
    then join back to the main reference table.
    """
    
    def __init__(self):
        self.geographic_lookup = {}
    
    def extract_unique_terms(self):
        """Extract all unique cultural reference terms from the database."""
        
        conn = psycopg2.connect(**db_params)
        
        # Get unique terms from both motif_ref and type_ref
        query = """
        SELECT DISTINCT ref_term, 'motif' as source_table
        FROM folklore.motif_ref
        UNION
        SELECT DISTINCT ref_term, 'type' as source_table  
        FROM folklore.type_ref
        ORDER BY ref_term
        """
        
        unique_terms_df = pd.read_sql_query(query, conn)
        conn.close()
        
        print(f"Found {len(unique_terms_df)} unique cultural reference terms")
        
        # Count usage frequency for each term
        conn = psycopg2.connect(**db_params)
        
        usage_query = """
        SELECT ref_term, COUNT(*) as usage_count
        FROM (
            SELECT ref_term FROM folklore.motif_ref
            UNION ALL
            SELECT ref_term FROM folklore.type_ref
        ) combined
        GROUP BY ref_term
        ORDER BY usage_count DESC
        """
        
        usage_df = pd.read_sql_query(usage_query, conn)
        conn.close()
        
        # Merge to get usage counts
        unique_terms_df = unique_terms_df.merge(usage_df, on='ref_term', how='left')
        
        print(f"Usage frequency range: {usage_df['usage_count'].min()} to {usage_df['usage_count'].max()}")
        print(f"Most common terms:")
        for _, row in usage_df.head(10).iterrows():
            print(f"  '{row['ref_term']}': {row['usage_count']} instances")
        
        return unique_terms_df
    
    def resolve_unique_terms(self, unique_terms_df):
        """
        Resolve geographic information for each unique term.
        This is where we apply Claude's knowledge efficiently.
        """
        
        print(f"\nResolving geographic information for {len(unique_terms_df)} unique terms...")
        
        # Initialize the geography lookup table
        geography_records = []
        
        for idx, row in unique_terms_df.iterrows():
            term = row['ref_term'].strip()
            usage_count = row['usage_count']
            
            # Apply Claude's knowledge to resolve this term
            geo_info = self._resolve_single_term(term)
            
            # Add usage information
            geo_info['ref_term'] = term
            geo_info['usage_count'] = usage_count
            geo_info['source_tables'] = row['source_table']
            
            geography_records.append(geo_info)
            
            if idx % 100 == 0:
                print(f"  Processed {idx} terms...")
        
        geography_df = pd.DataFrame(geography_records)
        
        return geography_df
    
    def _resolve_single_term(self, term):
        """
        Resolve a single cultural reference term using Claude's knowledge.
        Returns a standardized geography record.
        """
        
        # Comprehensive geographic mappings using Claude's knowledge
        geographic_mappings = self._get_comprehensive_mappings()
        
        # Check direct mappings first
        if term in geographic_mappings:
            info = geographic_mappings[term]
            return {
                'category': info[0],
                'subcategory': info[1], 
                'geographic_region': info[2],
                'latitude': info[3][0] if info[3] else None,
                'longitude': info[3][1] if info[3] else None,
                'confidence': info[4],
                'resolution_method': 'claude_knowledge_direct'
            }
        
        # Pattern-based resolution for remaining terms
        pattern_result = self._pattern_based_resolution(term)
        if pattern_result:
            return pattern_result
        
        # Unresolved
        return {
            'category': 'unknown',
            'subcategory': 'unresolved',
            'geographic_region': None,
            'latitude': None,
            'longitude': None,
            'confidence': 0.0,
            'resolution_method': 'unresolved'
        }
    
    def _get_comprehensive_mappings(self):
        """
        Comprehensive cultural reference mappings using Claude's embedded knowledge.
        Format: term -> (category, subcategory, region, (lat, lon), confidence)
        """
        
        return {
            # Countries and territories - obvious demonyms
            'Afghan': ('geographic', 'country', 'Afghanistan', (33.9, 67.7), 0.98),
            'Albanian': ('geographic', 'country', 'Albania', (41.2, 19.6), 0.98),
            'Algerian': ('geographic', 'country', 'Algeria', (28.0, 1.7), 0.98),
            'Argentine': ('geographic', 'country', 'Argentina', (-38.4, -63.6), 0.98),
            'Armenian': ('geographic', 'country', 'Armenia', (40.1, 45.0), 0.98),
            'Australian': ('geographic', 'country', 'Australia', (-25.3, 131.0), 0.98),
            'Austrian': ('geographic', 'country', 'Austria', (47.5, 14.6), 0.98),
            'Azerbaijani': ('geographic', 'country', 'Azerbaijan', (40.1, 47.6), 0.98),
            'Bahraini': ('geographic', 'country', 'Bahrain', (26.0, 50.5), 0.98),
            'Bangladeshi': ('geographic', 'country', 'Bangladesh', (23.7, 90.4), 0.98),
            'Belgian': ('geographic', 'country', 'Belgium', (50.5, 4.5), 0.98),
            'Bhutanese': ('geographic', 'country', 'Bhutan', (27.5, 90.4), 0.98),
            'Bolivian': ('geographic', 'country', 'Bolivia', (-16.3, -63.6), 0.98),
            'Brazilian': ('geographic', 'country', 'Brazil', (-14.2, -51.9), 0.98),
            'Bruneian': ('geographic', 'country', 'Brunei', (4.5, 114.7), 0.98),
            'Bulgarian': ('geographic', 'country', 'Bulgaria', (42.7, 25.5), 0.98),
            'Burmese': ('geographic', 'country', 'Myanmar', (21.9, 95.9), 0.98),
            'Cambodian': ('geographic', 'country', 'Cambodia', (12.6, 104.9), 0.98),
            'Canadian': ('geographic', 'country', 'Canada', (56.1, -106.3), 0.98),
            'Cape Verdian': ('geographic', 'country', 'Cape Verde', (16.0, -24.0), 0.98),
            'Chilean': ('geographic', 'country', 'Chile', (-35.7, -71.5), 0.98),
            'Chinese': ('geographic', 'country', 'China', (35.9, 104.2), 0.98),
            'Colombian': ('geographic', 'country', 'Colombia', (4.6, -74.1), 0.98),
            'Costa Rican': ('geographic', 'country', 'Costa Rica', (9.7, -83.8), 0.98),
            'Croatian': ('geographic', 'country', 'Croatia', (45.1, 15.2), 0.98),
            'Cuban': ('geographic', 'country', 'Cuba', (21.5, -77.8), 0.98),
            'Cypriot': ('geographic', 'country', 'Cyprus', (35.1, 33.4), 0.98),
            'Czech': ('geographic', 'country', 'Czech Republic', (49.8, 15.5), 0.98),
            'Danish': ('geographic', 'country', 'Denmark', (56.3, 9.5), 0.98),
            'Dominican': ('geographic', 'country', 'Dominican Republic', (18.7, -70.2), 0.98),
            'Ecuadorian': ('geographic', 'country', 'Ecuador', (-1.8, -78.2), 0.98),
            'Egyptian': ('geographic', 'country', 'Egypt', (26.8, 30.8), 0.98),
            'Emirati': ('geographic', 'country', 'UAE', (23.4, 53.8), 0.98),
            'Estonian': ('geographic', 'country', 'Estonia', (58.6, 25.0), 0.98),
            'Ethiopian': ('geographic', 'country', 'Ethiopia', (9.1, 40.5), 0.98),
            'Faeroese': ('geographic', 'territory', 'Faroe Islands', (62.0, -6.8), 0.98),
            'Fijian': ('geographic', 'country', 'Fiji', (-16.6, 179.1), 0.98),
            'Finnish': ('geographic', 'country', 'Finland', (61.9, 25.7), 0.98),
            'French': ('geographic', 'country', 'France', (46.6, 2.2), 0.98),
            'German': ('geographic', 'country', 'Germany', (51.2, 10.5), 0.98),
            'Ghanaian': ('geographic', 'country', 'Ghana', (7.9, -1.0), 0.98),
            'Greek': ('geographic', 'country', 'Greece', (39.1, 21.8), 0.98),
            'Guatemalan': ('geographic', 'country', 'Guatemala', (15.8, -90.2), 0.98),
            'Haitian': ('geographic', 'country', 'Haiti', (18.7, -72.3), 0.98),
            'Hungarian': ('geographic', 'country', 'Hungary', (47.2, 19.5), 0.98),
            'Icelandic': ('geographic', 'country', 'Iceland', (64.9, -19.0), 0.98),
            'Indian': ('geographic', 'country', 'India', (20.6, 78.9), 0.98),
            'Indonesian': ('geographic', 'country', 'Indonesia', (-0.8, 113.9), 0.98),
            'Iranian': ('geographic', 'country', 'Iran', (32.4, 53.7), 0.98),
            'Iraqi': ('geographic', 'country', 'Iraq', (33.2, 43.7), 0.98),
            'Irish': ('geographic', 'country', 'Ireland', (53.4, -8.2), 0.98),
            'Israeli': ('geographic', 'country', 'Israel', (31.0, 34.9), 0.98),
            'Italian': ('geographic', 'country', 'Italy', (41.9, 12.6), 0.98),
            'Japanese': ('geographic', 'country', 'Japan', (36.2, 138.3), 0.98),
            'Jordanian': ('geographic', 'country', 'Jordan', (30.6, 36.2), 0.98),
            'Kazakh': ('geographic', 'country', 'Kazakhstan', (48.0, 66.9), 0.98),
            'Kenyan': ('geographic', 'country', 'Kenya', (-0.0, 37.9), 0.98),
            'Korean': ('geographic', 'country', 'South Korea', (35.9, 127.8), 0.98),
            'Kuwaiti': ('geographic', 'country', 'Kuwait', (29.3, 47.5), 0.98),
            'Kyrgyz': ('geographic', 'country', 'Kyrgyzstan', (41.2, 74.8), 0.98),
            'Laotian': ('geographic', 'country', 'Laos', (19.9, 102.5), 0.98),
            'Latvian': ('geographic', 'country', 'Latvia', (56.9, 24.6), 0.98),
            'Lebanese': ('geographic', 'country', 'Lebanon', (33.9, 35.5), 0.98),
            'Liberian': ('geographic', 'country', 'Liberia', (6.4, -9.4), 0.98),
            'Libyan': ('geographic', 'country', 'Libya', (26.3, 17.2), 0.98),
            'Lithuanian': ('geographic', 'country', 'Lithuania', (55.2, 23.9), 0.98),
            'Luxembourgish': ('geographic', 'country', 'Luxembourg', (49.8, 6.1), 0.98),
            'Madagascan': ('geographic', 'country', 'Madagascar', (-18.8, 47.0), 0.98),
            'Malaysian': ('geographic', 'country', 'Malaysia', (4.2, 101.9), 0.98),
            'Maldivian': ('geographic', 'country', 'Maldives', (3.2, 73.2), 0.98),
            'Maltese': ('geographic', 'country', 'Malta', (35.9, 14.4), 0.98),
            'Mexican': ('geographic', 'country', 'Mexico', (23.6, -102.6), 0.98),
            'Mongolian': ('geographic', 'country', 'Mongolia', (46.9, 103.8), 0.98),
            'Moroccan': ('geographic', 'country', 'Morocco', (31.8, -7.1), 0.98),
            'Namibian': ('geographic', 'country', 'Namibia', (-22.3, 18.1), 0.98),
            'Nepalese': ('geographic', 'country', 'Nepal', (28.4, 84.1), 0.98),
            'Dutch': ('geographic', 'country', 'Netherlands', (52.1, 5.3), 0.98),
            'New Zealand': ('geographic', 'country', 'New Zealand', (-40.9, 174.9), 0.98),
            'Nigerian': ('geographic', 'country', 'Nigeria', (9.1, 8.7), 0.98),
            'Norwegian': ('geographic', 'country', 'Norway', (60.5, 8.5), 0.98),
            'Omani': ('geographic', 'country', 'Oman', (21.5, 55.9), 0.98),
            'Pakistani': ('geographic', 'country', 'Pakistan', (30.4, 69.3), 0.98),
            'Palestinian': ('geographic', 'territory', 'Palestine', (31.9, 35.2), 0.98),
            'Panamanian': ('geographic', 'country', 'Panama', (8.5, -80.8), 0.98),
            'Paraguayan': ('geographic', 'country', 'Paraguay', (-23.4, -58.4), 0.98),
            'Peruvian': ('geographic', 'country', 'Peru', (-9.2, -75.0), 0.98),
            'Filipino': ('geographic', 'country', 'Philippines', (12.9, 121.8), 0.98),
            'Polish': ('geographic', 'country', 'Poland', (51.9, 19.1), 0.98),
            'Portuguese': ('geographic', 'country', 'Portugal', (39.4, -8.2), 0.98),
            'Puerto Rican': ('geographic', 'territory', 'Puerto Rico', (18.2, -66.6), 0.98),
            'Qatari': ('geographic', 'country', 'Qatar', (25.3, 51.2), 0.98),
            'Romanian': ('geographic', 'country', 'Romania', (45.9, 24.9), 0.98),
            'Rumanian': ('geographic', 'country', 'Romania', (45.9, 24.9), 0.98),
            'Russian': ('geographic', 'country', 'Russia', (61.5, 105.3), 0.98),
            'Saudi Arabian': ('geographic', 'country', 'Saudi Arabia', (23.9, 45.1), 0.98),
            'Scottish': ('geographic', 'region', 'Scotland', (56.5, -4.2), 0.98),
            'Senegalese': ('geographic', 'country', 'Senegal', (14.5, -14.5), 0.98),
            'Serbian': ('geographic', 'country', 'Serbia', (44.0, 21.0), 0.98),
            'Singaporean': ('geographic', 'country', 'Singapore', (1.4, 103.8), 0.98),
            'Slovak': ('geographic', 'country', 'Slovakia', (48.7, 19.7), 0.98),
            'Slovene': ('geographic', 'country', 'Slovenia', (46.1, 14.9), 0.98),
            'Slovenian': ('geographic', 'country', 'Slovenia', (46.1, 14.9), 0.98),
            'Somali': ('geographic', 'country', 'Somalia', (5.2, 46.2), 0.98),
            'Spanish': ('geographic', 'country', 'Spain', (40.5, -3.7), 0.98),
            'Sri Lankan': ('geographic', 'country', 'Sri Lanka', (7.9, 80.8), 0.98),
            'Sudanese': ('geographic', 'country', 'Sudan', (12.9, 30.4), 0.98),
            'Swedish': ('geographic', 'country', 'Sweden', (60.1, 18.6), 0.98),
            'Swiss': ('geographic', 'country', 'Switzerland', (46.8, 8.2), 0.98),
            'Syrian': ('geographic', 'country', 'Syria', (34.8, 38.9), 0.98),
            'Taiwanese': ('geographic', 'territory', 'Taiwan', (23.8, 120.9), 0.98),
            'Tadzhik': ('geographic', 'country', 'Tajikistan', (38.9, 71.3), 0.98),
            'Tanzanian': ('geographic', 'country', 'Tanzania', (-6.4, 34.9), 0.98),
            'Thai': ('geographic', 'country', 'Thailand', (15.9, 100.9), 0.98),
            'Tibetan': ('geographic', 'region', 'Tibet', (29.6, 91.1), 0.98),
            'Tunisian': ('geographic', 'country', 'Tunisia', (33.9, 9.6), 0.98),
            'Turkish': ('geographic', 'country', 'Turkey', (38.9, 35.2), 0.98),
            'Turkmen': ('geographic', 'country', 'Turkmenistan', (38.9, 59.6), 0.98),
            'Ukrainian': ('geographic', 'country', 'Ukraine', (48.4, 31.2), 0.98),
            'Uruguayan': ('geographic', 'country', 'Uruguay', (-32.5, -55.8), 0.98),
            'Uzbek': ('geographic', 'country', 'Uzbekistan', (41.4, 64.6), 0.98),
            'Venezuelan': ('geographic', 'country', 'Venezuela', (6.4, -66.6), 0.98),
            'Vietnamese': ('geographic', 'country', 'Vietnam', (14.1, 108.3), 0.98),
            'Welsh': ('geographic', 'region', 'Wales', (52.1, -3.8), 0.98),
            'Yemeni': ('geographic', 'country', 'Yemen', (15.6, 48.0), 0.98),
            
            # Linguistic/ethnic groups with geographic associations
            'Basque': ('ethnic_tribal', 'linguistic_group', 'Basque Country', (43.2, -2.9), 0.95),
            'Catalan': ('linguistic', 'regional_language', 'Catalonia/Spain', (41.8, 1.6), 0.95),
            'Flemish': ('linguistic', 'regional_language', 'Flanders/Belgium', (51.0, 4.5), 0.95),
            'Frisian': ('linguistic', 'regional_language', 'Frisia/Netherlands', (53.2, 5.8), 0.95),
            'Walloon': ('linguistic', 'regional_language', 'Wallonia/Belgium', (50.4, 4.4), 0.95),
            'Kurdish': ('ethnic_tribal', 'stateless_people', 'Kurdistan', (36.5, 43.0), 0.90),
            
            # Russian Federation ethnic groups
            'Cheremis': ('linguistic', 'uralic_language', 'Mari El/Russia', (56.6, 47.9), 0.90),
            'Mari': ('linguistic', 'uralic_language', 'Mari El/Russia', (56.6, 47.9), 0.90),
            'Chuvash': ('linguistic', 'turkic_language', 'Chuvashia/Russia', (55.5, 47.2), 0.90),
            'Tatar': ('ethnic_tribal', 'turkic_people', 'Tatarstan/Russia', (55.8, 49.1), 0.90),
            'Karelian': ('linguistic', 'uralic_language', 'Karelia/Russia', (63.2, 32.4), 0.90),
            'Kalmyk': ('ethnic_tribal', 'mongolic_people', 'Kalmykia/Russia', (46.3, 44.3), 0.90),
            'Yakut': ('ethnic_tribal', 'turkic_people', 'Sakha/Russia', (62.0, 129.7), 0.90),
            'Buryat': ('ethnic_tribal', 'mongolic_people', 'Buryatia/Russia', (51.8, 107.6), 0.90),
            'Tuva': ('ethnic_tribal', 'turkic_people', 'Tuva/Russia', (51.7, 94.4), 0.90),
            'Sorbian': ('linguistic', 'slavic_minority', 'Lusatia/Germany', (51.5, 14.3), 0.90),
            'Syrjanian': ('linguistic', 'uralic_language', 'Komi/Russia', (64.0, 54.0), 0.90),
            'Votyak': ('linguistic', 'uralic_language', 'Udmurtia/Russia', (57.0, 53.0), 0.90),
            'Wepsian': ('linguistic', 'uralic_language', 'Karelia/Russia', (61.8, 34.3), 0.90),
            'Wotian': ('linguistic', 'uralic_language', 'Estonia/Ingria', (59.4, 24.8), 0.90),
            
            # Regional/historical
            'West Indies': ('geographic', 'region', 'Caribbean', (18.0, -77.0), 0.85),
            'Scandinavian': ('geographic', 'region', 'Scandinavia', (62.0, 15.0), 0.85),
            'Baltic': ('geographic', 'region', 'Baltic States', (56.9, 24.1), 0.85),
            'Balkan': ('geographic', 'region', 'Balkans', (44.0, 20.0), 0.85),
            
            # Indigenous groups
            'Inuit': ('ethnic_tribal', 'indigenous_group', 'Arctic', (70.0, -100.0), 0.95),
            'Eskimo': ('ethnic_tribal', 'indigenous_group', 'Arctic', (70.0, -100.0), 0.95),
            'Maori': ('ethnic_tribal', 'indigenous_group', 'New Zealand', (-40.9, 174.9), 0.95),
            'Aboriginal': ('ethnic_tribal', 'indigenous_group', 'Australia', (-25.3, 131.0), 0.95),
            
            # Complex cases
            'Cheremis/Mari': ('linguistic', 'uralic_language', 'Mari El/Russia', (56.6, 47.9), 0.85),
        }
    
    def _pattern_based_resolution(self, term):
        """Pattern-based resolution for terms not in direct mapping."""
        
        term_lower = term.lower()
        
        # American Indian pattern
        if 'american indian' in term_lower or 'american' in term_lower:
            return {
                'category': 'ethnic_tribal',
                'subcategory': 'indigenous_american',
                'geographic_region': 'North America',
                'latitude': 45.0,
                'longitude': -100.0,
                'confidence': 0.75,
                'resolution_method': 'pattern_american_indian'
            }
        
        # African pattern
        if 'african' in term_lower:
            return {
                'category': 'ethnic_tribal',
                'subcategory': 'african_group',
                'geographic_region': 'Africa',
                'latitude': 0.0,
                'longitude': 20.0,
                'confidence': 0.70,
                'resolution_method': 'pattern_african'
            }
        
        return None
    
    def create_geography_table(self, geography_df, create_db_table=True):
        """
        Create a normalized geography lookup table.
        Optionally create it in the database.
        """
        
        print(f"\nCreating geography lookup table with {len(geography_df)} entries...")
        
        # Save to CSV first
        os.makedirs("out/types", exist_ok=True)
        geography_file = "out/types/cultural_geography_lookup.csv"
        geography_df.to_csv(geography_file, index=False)
        print(f"Geography lookup saved to: {geography_file}")
        
        # Optionally create database table
        if create_db_table:
            self._create_database_geography_table(geography_df)
        
        # Generate summary statistics
        self._generate_geography_summary(geography_df)
        
        return geography_df
    
    def _create_database_geography_table(self, geography_df):
        """Create a proper normalized geography table in the database."""
        
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        
        # Create the geography lookup table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS folklore.cultural_geography (
            ref_term VARCHAR(255) PRIMARY KEY,
            category VARCHAR(50),
            subcategory VARCHAR(50),
            geographic_region VARCHAR(255),
            latitude DECIMAL(8,5),
            longitude DECIMAL(8,5),
            confidence DECIMAL(3,2),
            resolution_method VARCHAR(50),
            usage_count INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_cultural_geography_category 
        ON folklore.cultural_geography(category);
        
        CREATE INDEX IF NOT EXISTS idx_cultural_geography_coordinates 
        ON folklore.cultural_geography(latitude, longitude) 
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL;
        """
        
        cur.execute(create_table_sql)
        
        # Insert the data
        insert_sql = """
        INSERT INTO folklore.cultural_geography 
        (ref_term, category, subcategory, geographic_region, latitude, longitude, 
         confidence, resolution_method, usage_count)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (ref_term) DO UPDATE SET
            category = EXCLUDED.category,
            subcategory = EXCLUDED.subcategory,
            geographic_region = EXCLUDED.geographic_region,
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude,
            confidence = EXCLUDED.confidence,
            resolution_method = EXCLUDED.resolution_method,
            usage_count = EXCLUDED.usage_count
        """
        
        # Prepare data for insertion
        data_to_insert = []
        for _, row in geography_df.iterrows():
            data_to_insert.append((
                row['ref_term'],
                row['category'],
                row['subcategory'],
                row['geographic_region'],
                row['latitude'],
                row['longitude'], 
                row['confidence'],
                row['resolution_method'],
                row['usage_count']
            ))
        
        cur.executemany(insert_sql, data_to_insert)
        conn.commit()
        cur.close()
        conn.close()
        
        print("Geography lookup table created in database: folklore.cultural_geography")
    
    def _generate_geography_summary(self, geography_df):
        """Generate summary statistics for the geography resolution."""
        
        total_terms = len(geography_df)
        resolved_terms = len(geography_df[geography_df['category'] != 'unknown'])
        geocoded_terms = len(geography_df[geography_df['latitude'].notna()])
        
        print(f"\n" + "="*60)
        print("GEOGRAPHY RESOLUTION SUMMARY")
        print("="*60)
        
        print(f"Total unique terms: {total_terms:,}")
        print(f"Successfully resolved: {resolved_terms:,} ({resolved_terms/total_terms*100:.1f}%)")
        print(f"With coordinates: {geocoded_terms:,} ({geocoded_terms/total_terms*100:.1f}%)")
        
        # Category breakdown
        print(f"\nCategory distribution:")
        category_counts = geography_df['category'].value_counts()
        for category, count in category_counts.items():
            pct = (count / total_terms) * 100
            print(f"  {category:15}: {count:4,} ({pct:5.1f}%)")
        
        # High-usage terms that are geocoded
        high_usage_geocoded = geography_df[
            (geography_df['latitude'].notna()) & 
            (geography_df['usage_count'] >= 10)
        ].sort_values('usage_count', ascending=False)
        
        print(f"\nHigh-usage geocoded terms (top 15):")
        for _, row in high_usage_geocoded.head(15).iterrows():
            print(f"  '{row['ref_term']}': {row['usage_count']} uses -> {row['geographic_region']}")
        
        # Resolution method breakdown
        print(f"\nResolution methods:")
        method_counts = geography_df['resolution_method'].value_counts()
        for method, count in method_counts.items():
            print(f"  {method}: {count}")
        
        # Calculate total reference instances that can now be geocoded
        total_instances = geography_df['usage_count'].sum()
        geocoded_instances = geography_df[
            geography_df['latitude'].notna()
        ]['usage_count'].sum()
        
        print(f"\nTotal reference instances: {total_instances:,}")
        print(f"Geocodable instances: {geocoded_instances:,} ({geocoded_instances/total_instances*100:.1f}%)")
    
    def generate_joined_analysis(self, geography_df):
        """
        Generate analysis by joining geography back to the original reference tables.
        This simulates what the visualization pipeline would use.
        """
        
        print(f"\n" + "="*60)
        print("JOINED ANALYSIS (Geography + Tale Types)")
        print("="*60)
        
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        
        # Create a temporary table with our geography data for joining using psycopg2
        cur.execute("DROP TABLE IF EXISTS temp_geography")
        
        create_temp_sql = """
        CREATE TEMP TABLE temp_geography (
            ref_term VARCHAR(255),
            category VARCHAR(50),
            subcategory VARCHAR(50),
            geographic_region VARCHAR(255),
            latitude DECIMAL(8,5),
            longitude DECIMAL(8,5),
            confidence DECIMAL(3,2),
            resolution_method VARCHAR(50),
            usage_count INTEGER
        )
        """
        cur.execute(create_temp_sql)
        
        # Insert data using executemany
        insert_temp_sql = """
        INSERT INTO temp_geography 
        (ref_term, category, subcategory, geographic_region, latitude, longitude, confidence, resolution_method, usage_count)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        temp_data = []
        for _, row in geography_df.iterrows():
            temp_data.append((
                row['ref_term'], row['category'], row['subcategory'], 
                row['geographic_region'], row['latitude'], row['longitude'],
                row['confidence'], row['resolution_method'], row['usage_count']
            ))
        
        cur.executemany(insert_temp_sql, temp_data)
        conn.commit()
        
        # Analyze tale types with geographic distribution
        tale_type_geo_query = """
        SELECT 
            tr.type_id,
            COUNT(*) as total_refs,
            COUNT(CASE WHEN tg.latitude IS NOT NULL THEN 1 END) as geocoded_refs,
            COUNT(DISTINCT tg.ref_term) as unique_terms,
            COUNT(DISTINCT CASE WHEN tg.latitude IS NOT NULL THEN tg.ref_term END) as geocoded_terms,
            STRING_AGG(DISTINCT tg.category, ', ') as categories
        FROM folklore.type_ref tr
        LEFT JOIN temp_geography tg ON tr.ref_term = tg.ref_term
        GROUP BY tr.type_id
        HAVING COUNT(*) >= 20  -- Only tale types with significant references
        ORDER BY geocoded_refs DESC
        LIMIT 20
        """
        
        tale_geo_df = pd.read_sql_query(tale_type_geo_query, conn)
        
        print(f"Tale types with best geographic coverage:")
        for _, row in tale_geo_df.iterrows():
            geo_pct = (row['geocoded_refs'] / row['total_refs']) * 100
            print(f"  {row['type_id']}: {row['geocoded_refs']}/{row['total_refs']} refs geocoded ({geo_pct:.0f}%) | {row['geocoded_terms']} unique locations")
        
        # Geographic distribution of tale types
        continent_query = """
        SELECT 
            CASE 
                WHEN tg.latitude > 35 AND tg.latitude < 70 AND tg.longitude > -10 AND tg.longitude < 50 THEN 'Europe'
                WHEN tg.latitude > 10 AND tg.latitude < 70 AND tg.longitude > 50 AND tg.longitude < 180 THEN 'Asia'
                WHEN tg.latitude > -35 AND tg.latitude < 35 AND tg.longitude > -20 AND tg.longitude < 50 THEN 'Africa'
                WHEN tg.longitude > -180 AND tg.longitude < -30 THEN 'Americas'
                WHEN tg.latitude > -50 AND tg.longitude > 110 THEN 'Oceania'
                ELSE 'Other'
            END as continent,
            COUNT(DISTINCT tr.type_id) as tale_types,
            COUNT(*) as total_references
        FROM folklore.type_ref tr
        JOIN temp_geography tg ON tr.ref_term = tg.ref_term
        WHERE tg.latitude IS NOT NULL AND tg.longitude IS NOT NULL
        GROUP BY 1
        ORDER BY tale_types DESC
        """
        
        continent_df = pd.read_sql_query(continent_query, conn)
        
        print(f"\nTale type distribution by continent:")
        for _, row in continent_df.iterrows():
            print(f"  {row['continent']}: {row['tale_types']} tale types, {row['total_references']} references")
        
        # Clean up
        cur.execute("DROP TABLE IF EXISTS temp_geography")
        conn.commit()
        cur.close()
        conn.close()
        
        return tale_geo_df, continent_df

def main():
    """Main execution function for normalized geographic resolution."""
    
    resolver = NormalizedGeographicResolver()
    
    # Step 1: Extract unique terms
    print("Step 1: Extracting unique cultural reference terms...")
    unique_terms_df = resolver.extract_unique_terms()
    
    # Step 2: Resolve each unique term once
    print("\nStep 2: Resolving geographic information for unique terms...")
    geography_df = resolver.resolve_unique_terms(unique_terms_df)
    
    # Step 3: Create normalized geography table
    print("\nStep 3: Creating normalized geography lookup table...")
    geography_df = resolver.create_geography_table(geography_df, create_db_table=True)
    
    # Step 4: Analyze joined results
    print("\nStep 4: Analyzing geographic coverage for tale types...")
    tale_geo_df, continent_df = resolver.generate_joined_analysis(geography_df)
    
    # Step 5: Final recommendations
    print(f"\n" + "="*60)
    print("VISUALIZATION READINESS ASSESSMENT")
    print("="*60)
    
    geocoded_terms = len(geography_df[geography_df['latitude'].notna()])
    total_instances = geography_df['usage_count'].sum()
    geocoded_instances = geography_df[geography_df['latitude'].notna()]['usage_count'].sum()
    
    print(f"Unique geocoded terms: {geocoded_terms:,}")
    print(f"Geocodable reference instances: {geocoded_instances:,}/{total_instances:,} ({geocoded_instances/total_instances*100:.1f}%)")
    
    if geocoded_terms >= 1000 and geocoded_instances/total_instances >= 0.80:
        print("\n✓ EXCELLENT: Ready for comprehensive geographic visualization")
        print("  → Choropleth maps, cultural distance analysis, diffusion modeling")
    elif geocoded_terms >= 500 and geocoded_instances/total_instances >= 0.70:
        print("\n✓ GOOD: Ready for meaningful geographic visualization")
        print("  → Regional maps, major cultural area analysis")
    elif geocoded_terms >= 200:
        print("\n△ MODERATE: Limited but workable for basic visualization")
        print("  → Focus on major countries/regions only")
    else:
        print("\n✗ INSUFFICIENT: Need more resolution work")
    
    return geography_df

if __name__ == "__main__":
    geography_lookup = main()