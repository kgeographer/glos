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
            except:
                self.log_print("Could not load cache, starting fresh")
    
    def save_cache(self):
        """Save resolution cache to avoid re-querying."""
        os.makedirs("out/types", exist_ok=True)
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def get_unique_terms(self):
        """Extract all unique cultural reference terms from database."""
        
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
        
        # Show some sample resolved terms with their full details
        self.log_print(f"\nSample resolved terms with details:")
        for _, row in results_df.head(5).iterrows():
            self.log_print(f"  '{row['ref_term']}' -> {row['category']}/{row['subcategory']}")
            self.log_print(f"    Toponym: {row['toponym']}")
            self.log_print(f"    Coordinates: {row['coordinates']} (type: {type(row['coordinates'])})")
            self.log_print(f"    Explanation: {row['explanation'][:100]}...")
            self.log_print("")
        high_usage_resolved = results_df[
            (results_df['category'] != 'unknown') & 
            (results_df['usage_count'] >= 100)
        ].sort_values('usage_count', ascending=False)
        
        self.log_print(f"\nHigh-usage resolved terms (sample):")
        for _, row in high_usage_resolved.head(15).iterrows():
            # Handle coordinates properly - they come as lists from JSON
            coords_display = "No coords"
            try:
                coords = row['coordinates']
                if coords is not None and isinstance(coords, (list, tuple)) and len(coords) == 2:
                    coords_display = f"[{coords[0]:.2f}, {coords[1]:.2f}]"
                elif coords is not None:
                    coords_display = str(coords)
            except:
                coords_display = "Invalid coords"
            
            self.log_print(f"  '{row['ref_term']}' ({row['usage_count']} uses) -> {row['toponym']} | {coords_display}")
        
        # Calculate total instances coverage
        total_instances = results_df['usage_count'].sum()
        resolved_instances = results_df[
            results_df['category'] != 'unknown'
        ]['usage_count'].sum()
        geocoded_instances = 0
        for _, row in results_df.iterrows():
            try:
                coords = row['coordinates']
                if coords is not None and isinstance(coords, (list, tuple)) and len(coords) == 2:
                    geocoded_instances += row['usage_count']
            except:
                pass
        
        self.log_print(f"\nInstance coverage:")
        self.log_print(f"Total reference instances: {total_instances:,}")
        self.log_print(f"Resolved instances: {resolved_instances:,} ({resolved_instances/total_instances*100:.1f}%)")
        self.log_print(f"Geocoded instances: {geocoded_instances:,} ({geocoded_instances/total_instances*100:.1f}%)")
        
        return results_df
    
    def save_to_database(self, results_df):
        """Save results to the cultural_geography table."""
        
        print("\n" + "="*50)
        print("DEBUGGING: save_to_database() called")
        print(f"Results DataFrame shape: {results_df.shape}")
        print(f"DataFrame columns: {list(results_df.columns)}")
        print("="*50)
        
        if len(results_df) == 0:
            print("ERROR: No data to save!")
            return
        
        try:
            print("Step 1: Connecting to database...")
            print(f"DB params: {db_params}")
            conn = psycopg2.connect(**db_params)
            print("✓ Database connection successful")
            
            cur = conn.cursor()
            
            print("Step 2: Creating table...")
            # Create/update table
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
            print("✓ Table created/verified")
            
            print("Step 3: Preparing data...")
            # Insert data
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
            
            data_to_insert = []
            for idx, row in results_df.iterrows():
                # Parse coordinates if available
                lat, lon = None, None
                if pd.notna(row['coordinates']) and row['coordinates']:
                    try:
                        coords = row['coordinates']
                        if isinstance(coords, str):
                            coords = json.loads(coords)
                        if isinstance(coords, list) and len(coords) == 2:
                            lat, lon = float(coords[0]), float(coords[1])
                    except Exception as e:
                        print(f"  Warning: coordinate parsing error for {row['ref_term']}: {e}")
                
                row_data = (
                    row['ref_term'], row['category'], row['subcategory'],
                    row['confidence'], row['toponym'], row['explanation'],
                    lat, lon, row['usage_count']
                )
                data_to_insert.append(row_data)
                
                if idx < 3:  # Show first few rows for debugging
                    print(f"  Sample row {idx}: {row_data}")
            
            print(f"Step 4: Inserting {len(data_to_insert)} rows...")
            cur.executemany(insert_sql, data_to_insert)
            conn.commit()
            print("✓ Data inserted successfully")
            
            # Verify insertion
            cur.execute("SELECT COUNT(*) FROM folklore.cultural_geography_claude;")
            count = cur.fetchone()[0]
            print(f"✓ Table now contains {count} total rows")
            
            cur.close()
            conn.close()
            print("✓ Database connection closed")
            
        except Exception as e:
            print(f"ERROR in save_to_database(): {e}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            print("Full traceback:")
            traceback.print_exc()
        
        self.log_print(f"\nSaved {len(data_to_insert)} records to folklore.cultural_geography_claude")
    
    def save_results(self, results_df):
        """Save results to CSV and database."""
        
        # Save to CSV
        os.makedirs("out/types", exist_ok=True)
        csv_file = "out/types/claude_geographic_resolution.csv"
        results_df.to_csv(csv_file, index=False)
        self.log_print(f"Results saved to: {csv_file}")
        
        # Save to database
        print("\nCalling save_to_database()...")
        self.save_to_database(results_df)

def main():
    """Main execution function."""
    
    # Set up logging to file
    log_file = "out/types/claude_resolution_log.txt"
    os.makedirs("out/types", exist_ok=True)
    
    # Clear the log file at start
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write("=== Claude API Geographic Resolution Log ===\n")
        f.write(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    # Create resolver with logging
    resolver = ClaudeGeographicResolver(log_file=log_file)
    
    # Get unique terms
    resolver.log_print("Step 1: Getting unique cultural reference terms...")
    terms_df = resolver.get_unique_terms()
    
    # TESTING: Limit to first 5 terms for debugging
    original_count = len(terms_df)
    terms_df = terms_df.head(5)
    resolver.log_print(f"DEBUG MODE: Limited to first {len(terms_df)} terms (out of {original_count} total)")
    
    # Show the terms we'll be testing
    resolver.log_print(f"\nTerms to resolve:")
    for i, row in terms_df.iterrows():
        resolver.log_print(f"  {i+1}. '{row['ref_term']}' ({row['usage_count']} uses)")
    
    # Resolve with Claude API
    resolver.log_print(f"\nStep 2: Resolving {len(terms_df)} terms with Claude API...")
    results_df = resolver.resolve_all_terms(terms_df, batch_size=5, delay=1.0)
    
    # Analyze results
    resolver.log_print("\nStep 3: Analyzing results...")
    results_df = resolver.analyze_results(results_df)
    
    # Save results
    resolver.log_print("\nStep 4: Saving results...")
    resolver.save_results(results_df)
    
    resolver.log_print("\nResolution complete!")
    resolver.log_print(f"Full log saved to: {log_file}")
    
    return results_df

if __name__ == "__main__":
    results = main()
