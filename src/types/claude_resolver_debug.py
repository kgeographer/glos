import os
import pandas as pd
import psycopg2
import json
import time
from dotenv import load_dotenv
from anthropic import Anthropic

# Load environment variables
load_dotenv()

db_params = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

class ClaudeGeographicResolver:
    """
    Use Claude API to resolve cultural/geographic references with model knowledge.
    """
    
    def __init__(self, log_file=None):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.results = []
        self.cache_file = "out/types/claude_resolution_cache.json"
        self.log_file = log_file
        self.load_cache()
    
    def log_print(self, message):
        """Print to console and log file if specified."""
        print(message)
        if self.log_file:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(message + '\n')
    
    def load_cache(self):
        """Load previously resolved terms to avoid re-querying."""
        self.cache = {}
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    self.cache = json.load(f)
                self.log_print(f"Loaded {len(self.cache)} cached resolutions")
            except Exception as e:
                self.log_print(f"Could not load cache: {e}")
    
    def save_cache(self):
        """Save resolution cache to avoid re-querying."""
        os.makedirs("out/types", exist_ok=True)
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def test_database_connection(self):
        """Test database connection and permissions."""
        self.log_print("Testing database connection...")
        
        try:
            conn = psycopg2.connect(**db_params)
            self.log_print("✓ Database connection successful")
            
            cur = conn.cursor()
            
            # Test basic query
            cur.execute("SELECT current_database(), current_user;")
            db_name, user = cur.fetchone()
            self.log_print(f"✓ Connected to database: {db_name} as user: {user}")
            
            # Test schema access
            cur.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'folklore';")
            schema_exists = cur.fetchone()
            if schema_exists:
                self.log_print("✓ 'folklore' schema exists")
            else:
                self.log_print("✗ 'folklore' schema does not exist")
                # Try to create it
                try:
                    cur.execute("CREATE SCHEMA IF NOT EXISTS folklore;")
                    conn.commit()
                    self.log_print("✓ Created 'folklore' schema")
                except Exception as e:
                    self.log_print(f"✗ Could not create 'folklore' schema: {e}")
            
            # Test table creation permissions
            test_table_sql = """
            CREATE TABLE IF NOT EXISTS folklore.test_table_permissions (
                id SERIAL PRIMARY KEY,
                test_field VARCHAR(50)
            );
            """
            
            try:
                cur.execute(test_table_sql)
                conn.commit()
                self.log_print("✓ Can create tables in folklore schema")
                
                # Clean up test table
                cur.execute("DROP TABLE IF EXISTS folklore.test_table_permissions;")
                conn.commit()
                
            except Exception as e:
                self.log_print(f"✗ Cannot create tables in folklore schema: {e}")
            
            cur.close()
            conn.close()
            return True
            
        except Exception as e:
            self.log_print(f"✗ Database connection failed: {e}")
            self.log_print(f"Connection parameters: {db_params}")
            return False
    
    def get_unique_terms(self):
        """Extract all unique cultural reference terms from database."""
        
        try:
            conn = psycopg2.connect(**db_params)
            
            query = """
            SELECT DISTINCT ref_term, COUNT(*) as usage_count
            FROM (
                SELECT ref_term FROM folklore.motif_ref
                UNION ALL
                SELECT ref_term FROM folklore.type_ref
            ) combined
            GROUP BY ref_term
            ORDER BY usage_count DESC
            """
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            self.log_print(f"Found {len(df)} unique cultural reference terms")
            self.log_print(f"Usage range: {df['usage_count'].min()} to {df['usage_count'].max()}")
            
            return df
            
        except Exception as e:
            self.log_print(f"Error getting unique terms: {e}")
            # Return empty DataFrame for testing
            return pd.DataFrame(columns=['ref_term', 'usage_count'])
    
    def resolve_term_with_claude(self, term):
        """
        Use Claude API to categorize and geolocate a cultural reference term.
        """
        
        # Check cache first
        if term in self.cache:
            return self.cache[term]
        
        prompt = f"""Analyze this cultural/geographic reference term from folklore indexes: "{term}"

Please provide a JSON response with these fields:

1. "category": Choose from: geographic, linguistic, ethnic_tribal, religious, temporal, unknown
2. "subcategory": More specific classification (e.g., country, language, indigenous_group, etc.)
3. "confidence": Float 0.0-1.0 indicating confidence in categorization
4. "toponym": A geographic place name that best represents where this term is associated (even if approximate)
5. "explanation": Brief explanation of what this term refers to
6. "coordinates": [latitude, longitude] if you can provide approximate coordinates, or null

Examples:
- "Irish" → category: "geographic", toponym: "Ireland", coordinates: [53.4, -8.2]
- "Cheremis" → category: "linguistic", toponym: "Mari El Republic", coordinates: [56.6, 47.9]
- "Buddhist" → category: "religious", toponym: "Tibet", coordinates: [29.6, 91.1]

Be as specific as possible with toponyms - prefer specific regions/countries over continents when applicable.

Term to analyze: "{term}"

Respond only with valid JSON:"""

        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text.strip()
            
            # Try to parse JSON response
            try:
                result = json.loads(response_text)
                
                # Validate required fields
                required_fields = ['category', 'subcategory', 'confidence', 'toponym', 'explanation']
                if all(field in result for field in required_fields):
                    # Cache the result
                    self.cache[term] = result
                    return result
                else:
                    self.log_print(f"Missing required fields in response for '{term}'")
                    return self._create_fallback_result(term, "incomplete_response")
                    
            except json.JSONDecodeError:
                self.log_print(f"Could not parse JSON response for '{term}': {response_text[:100]}...")
                return self._create_fallback_result(term, "json_parse_error")
                
        except Exception as e:
            self.log_print(f"API error for '{term}': {e}")
            return self._create_fallback_result(term, "api_error")
    
    def _create_fallback_result(self, term, error_type):
        """Create a fallback result for failed resolutions."""
        return {
            "category": "unknown",
            "subcategory": "api_failed",
            "confidence": 0.0,
            "toponym": None,
            "explanation": f"Resolution failed: {error_type}",
            "coordinates": None
        }
    
    def resolve_all_terms(self, terms_df, batch_size=50, delay=1.0):
        """
        Resolve all terms using Claude API with rate limiting.
        """
        
        self.log_print(f"Resolving {len(terms_df)} terms with Claude API...")
        self.log_print(f"Using batch size: {batch_size}, delay: {delay}s between requests")
        
        results = []
        
        for idx, row in terms_df.iterrows():
            term = row['ref_term']
            usage_count = row['usage_count']
            
            # Skip if already cached
            if term in self.cache:
                result = self.cache[term]
                self.log_print(f"  [{idx+1:4}/{len(terms_df)}] CACHED '{term}'")
            else:
                self.log_print(f"  [{idx+1:4}/{len(terms_df)}] RESOLVING '{term}'...")
                result = self.resolve_term_with_claude(term)
                
                # Add delay to respect rate limits
                time.sleep(delay)
            
            # Combine with usage data
            full_result = {
                'ref_term': term,
                'usage_count': usage_count,
                **result
            }
            
            results.append(full_result)
            
            # Save cache periodically
            if (idx + 1) % batch_size == 0:
                self.save_cache()
                self.log_print(f"    Saved cache at {idx+1} terms")
                
                # Show progress statistics
                resolved_so_far = [r for r in results if r['category'] != 'unknown']
                resolution_rate = len(resolved_so_far) / len(results) * 100
                self.log_print(f"    Resolution rate so far: {resolution_rate:.1f}%")
        
        # Final cache save
        self.save_cache()
        
        return pd.DataFrame(results)
    
    def analyze_results(self, results_df):
        """Analyze the resolution results."""
        
        self.log_print(f"\n" + "="*60)
        self.log_print("CLAUDE API RESOLUTION RESULTS")
        self.log_print("="*60)
        
        total_terms = len(results_df)
        if total_terms == 0:
            self.log_print("No results to analyze!")
            return results_df
            
        resolved_terms = len(results_df[results_df['category'] != 'unknown'])
        geocoded_terms = len(results_df[results_df['coordinates'].notna()])
        
        self.log_print(f"Total unique terms: {total_terms:,}")
        self.log_print(f"Successfully resolved: {resolved_terms:,} ({resolved_terms/total_terms*100:.1f}%)")
        self.log_print(f"With coordinates: {geocoded_terms:,} ({geocoded_terms/total_terms*100:.1f}%)")
        
        # Category breakdown
        self.log_print(f"\nCategory distribution:")
        category_counts = results_df['category'].value_counts()
        for category, count in category_counts.items():
            pct = (count / total_terms) * 100
            self.log_print(f"  {category:15}: {count:4,} ({pct:5.1f}%)")
        
        return results_df
    
    def save_to_database(self, results_df):
        """Save results to the cultural_geography table with detailed debugging."""
        
        self.log_print(f"\n{'='*60}")
        self.log_print("ATTEMPTING TO SAVE TO DATABASE")
        self.log_print("="*60)
        
        if len(results_df) == 0:
            self.log_print("No data to save to database!")
            return False
        
        try:
            self.log_print("Opening database connection...")
            conn = psycopg2.connect(**db_params)
            cur = conn.cursor()
            self.log_print("✓ Database connection opened")
            
            # Create/update table
            self.log_print("Creating table if it doesn't exist...")
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS folklore.cultural_geography_claude (
                ref_term VARCHAR(255) PRIMARY KEY,
                category VARCHAR(50),
                subcategory VARCHAR(50),
                confidence DECIMAL(3,2),
                toponym VARCHAR(255),
                explanation TEXT,
                latitude DECIMAL(8,5),
                longitude DECIMAL(8,5),
                usage_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_cultural_geography_claude_category 
            ON folklore.cultural_geography_claude(category);
            
            CREATE INDEX IF NOT EXISTS idx_cultural_geography_claude_coords 
            ON folklore.cultural_geography_claude(latitude, longitude) 
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL;
            """
            
            cur.execute(create_table_sql)
            conn.commit()
            self.log_print("✓ Table created/verified")
            
            # Prepare data for insertion
            self.log_print("Preparing data for insertion...")
            data_to_insert = []
            skipped_rows = 0
            
            for idx, row in results_df.iterrows():
                try:
                    # Parse coordinates if available
                    lat, lon = None, None
                    if pd.notna(row['coordinates']) and row['coordinates']:
                        try:
                            coords = row['coordinates']
                            if isinstance(coords, str):
                                coords = json.loads(coords)
                            if isinstance(coords, list) and len(coords) == 2:
                                lat, lon = float(coords[0]), float(coords[1])
                        except Exception as coord_e:
                            self.log_print(f"  Warning: Could not parse coordinates for '{row['ref_term']}': {coord_e}")
                    
                    # Prepare row data
                    row_data = (
                        str(row['ref_term']),
                        str(row['category']),
                        str(row['subcategory']),
                        float(row['confidence']) if pd.notna(row['confidence']) else 0.0,
                        str(row['toponym']) if pd.notna(row['toponym']) and row['toponym'] else None,
                        str(row['explanation']) if pd.notna(row['explanation']) else None,
                        lat,
                        lon,
                        int(row['usage_count'])
                    )
                    
                    data_to_insert.append(row_data)
                    
                except Exception as row_e:
                    self.log_print(f"  Error preparing row {idx} ('{row.get('ref_term', 'UNKNOWN')}'): {row_e}")
                    skipped_rows += 1
            
            self.log_print(f"✓ Prepared {len(data_to_insert)} rows for insertion")
            if skipped_rows > 0:
                self.log_print(f"  Skipped {skipped_rows} problematic rows")
            
            if len(data_to_insert) == 0:
                self.log_print("No valid data to insert!")
                return False
            
            # Insert data
            self.log_print("Inserting data...")
            insert_sql = """
            INSERT INTO folklore.cultural_geography_claude 
            (ref_term, category, subcategory, confidence, toponym, explanation, 
             latitude, longitude, usage_count)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ref_term) DO UPDATE SET
                category = EXCLUDED.category,
                subcategory = EXCLUDED.subcategory,
                confidence = EXCLUDED.confidence,
                toponym = EXCLUDED.toponym,
                explanation = EXCLUDED.explanation,
                latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude,
                usage_count = EXCLUDED.usage_count
            """
            
            # Insert in batches to catch individual row errors
            batch_size = 10
            successful_inserts = 0
            
            for i in range(0, len(data_to_insert), batch_size):
                batch = data_to_insert[i:i+batch_size]
                try:
                    cur.executemany(insert_sql, batch)
                    conn.commit()
                    successful_inserts += len(batch)
                    self.log_print(f"  ✓ Inserted batch {i//batch_size + 1}: {len(batch)} rows")
                except Exception as batch_e:
                    self.log_print(f"  ✗ Error inserting batch {i//batch_size + 1}: {batch_e}")
                    # Try inserting rows individually to identify problem rows
                    for j, single_row in enumerate(batch):
                        try:
                            cur.execute(insert_sql, single_row)
                            conn.commit()
                            successful_inserts += 1
                        except Exception as single_e:
                            self.log_print(f"    ✗ Failed to insert row {i+j} ('{single_row[0]}'): {single_e}")
            
            # Verify insertion
            cur.execute("SELECT COUNT(*) FROM folklore.cultural_geography_claude;")
            total_count = cur.fetchone()[0]
            
            cur.close()
            conn.close()
            
            self.log_print(f"✓ Database operations completed")
            self.log_print(f"  Successfully inserted: {successful_inserts} records")
            self.log_print(f"  Total records in table: {total_count}")
            
            return True
            
        except Exception as e:
            self.log_print(f"✗ Database error: {e}")
            self.log_print(f"  Error type: {type(e).__name__}")
            import traceback
            self.log_print(f"  Traceback: {traceback.format_exc()}")
            return False
    
    def save_results(self, results_df):
        """Save results to CSV and database."""
        
        # Save to CSV first (this should always work)
        os.makedirs("out/types", exist_ok=True)
        csv_file = "out/types/claude_geographic_resolution.csv"
        try:
            results_df.to_csv(csv_file, index=False)
            self.log_print(f"✓ Results saved to CSV: {csv_file}")
        except Exception as e:
            self.log_print(f"✗ Could not save CSV: {e}")
        
        # Save to database with debugging
        db_success = self.save_to_database(results_df)
        if db_success:
            self.log_print("✓ Database save completed successfully")
        else:
            self.log_print("✗ Database save failed - check log for details")

def create_test_data():
    """Create minimal test data for debugging database issues."""
    return pd.DataFrame([
        {
            'ref_term': 'Irish',
            'usage_count': 100,
            'category': 'geographic',
            'subcategory': 'country',
            'confidence': 0.9,
            'toponym': 'Ireland',
            'explanation': 'Related to Ireland',
            'coordinates': [53.4, -8.2]
        },
        {
            'ref_term': 'Buddhist',
            'usage_count': 50,
            'category': 'religious',
            'subcategory': 'religion',
            'confidence': 0.95,
            'toponym': 'Tibet',
            'explanation': 'Related to Buddhism',
            'coordinates': [29.6, 91.1]
        },
        {
            'ref_term': 'Unknown_Term',
            'usage_count': 5,
            'category': 'unknown',
            'subcategory': 'unclassified',
            'confidence': 0.0,
            'toponym': None,
            'explanation': 'Could not classify',
            'coordinates': None
        }
    ])

def debug_database_only():
    """Just test the database functionality without API calls."""
    
    log_file = "out/types/debug_database_log.txt"
    os.makedirs("out/types", exist_ok=True)
    
    # Clear the log file at start
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write("=== Database Debug Log ===\n")
        f.write(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    resolver = ClaudeGeographicResolver(log_file=log_file)
    
    # Test database connection
    if not resolver.test_database_connection():
        resolver.log_print("Database connection failed - stopping here")
        return None
    
    # Create test data
    resolver.log_print("\nCreating test data...")
    test_df = create_test_data()
    resolver.log_print(f"Created {len(test_df)} test records")
    
    # Test database save
    resolver.log_print("\nTesting database save...")
    success = resolver.save_to_database(test_df)
    
    if success:
        resolver.log_print("\n✓ Database debugging completed successfully!")
    else:
        resolver.log_print("\n✗ Database debugging failed - check log for details")
    
    return test_df

def main():
    """Main execution function with enhanced debugging."""
    
    # Set up logging to file
    log_file = "out/types/claude_resolution_debug_log.txt"
    os.makedirs("out/types", exist_ok=True)
    
    # Clear the log file at start
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write("=== Claude API Geographic Resolution Debug Log ===\n")
        f.write(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    # Create resolver with logging
    resolver = ClaudeGeographicResolver(log_file=log_file)
    
    # Test database connection first
    if not resolver.test_database_connection():
        resolver.log_print("Database connection test failed - stopping execution")
        return None
    
    # Get unique terms
    resolver.log_print("\nStep 1: Getting unique cultural reference terms...")
    terms_df = resolver.get_unique_terms()
    
    if len(terms_df) == 0:
        resolver.log_print("No terms found - using test data instead")
        results_df = create_test_data()
    else:
        # TESTING: Limit to first 10 terms for debugging
        original_count = len(terms_df)
        terms_df = terms_df.head(10)
        resolver.log_print(f"DEBUG MODE: Limited to first {len(terms_df)} terms (out of {original_count} total)")
        
        # Resolve with Claude API
        resolver.log_print(f"\nStep 2: Resolving {len(terms_df)} terms with Claude API...")
        results_df = resolver.resolve_all_terms(terms_df, batch_size=5, delay=1.0)
    
    # Analyze results
    resolver.log_print("\nStep 3: Analyzing results...")
    results_df = resolver.analyze_results(results_df)
    
    # Save results
    resolver.log_print("\nStep 4: Saving results...")
    resolver.save_results(results_df)
    
    resolver.log_print("\nDebugging complete!")
    resolver.log_print(f"Full log saved to: {log_file}")
    
    return results_df

if __name__ == "__main__":
    # Uncomment one of these options:
    
    # Option 1: Just test database functionality
    print("Testing database functionality only...")
    debug_database_only()
    
    # Option 2: Full debugging (uncomment to use)
    # print("Running full debugging...")
    # results = main()
