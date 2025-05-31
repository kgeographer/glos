import os
import psycopg2
import pandas as pd
import re
from collections import defaultdict, Counter
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters
db_params = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

class CulturalReferenceCategorizr:
    def __init__(self):
        """Initialize the categorizer with reference dictionaries."""
        
        # Modern countries and major historical regions
        self.geographic_entities = {
            'countries': [
                'Afghanistan', 'Albania', 'Algeria', 'Argentina', 'Armenia', 'Australia', 
                'Austria', 'Azerbaijan', 'Bangladesh', 'Belgium', 'Bolivia', 'Brazil', 
                'Bulgaria', 'Cambodia', 'Canada', 'Chile', 'China', 'Colombia', 'Croatia',
                'Czech', 'Czechoslovakia', 'Denmark', 'Ecuador', 'Egypt', 'England', 
                'Estonia', 'Ethiopia', 'Finland', 'France', 'Georgia', 'Germany', 'Ghana',
                'Greece', 'Guatemala', 'Hungary', 'Iceland', 'India', 'Indonesia', 'Iran',
                'Iraq', 'Ireland', 'Israel', 'Italy', 'Japan', 'Jordan', 'Kazakhstan',
                'Kenya', 'Korea', 'Latvia', 'Lebanon', 'Lithuania', 'Madagascar', 'Malaysia',
                'Mexico', 'Mongolia', 'Morocco', 'Nepal', 'Netherlands', 'Nigeria', 'Norway',
                'Pakistan', 'Peru', 'Philippines', 'Poland', 'Portugal', 'Romania', 'Russia',
                'Scotland', 'Serbia', 'Slovakia', 'Slovenia', 'Somalia', 'Spain', 'Sudan',
                'Sweden', 'Switzerland', 'Syria', 'Thailand', 'Tibet', 'Turkey', 'Ukraine',
                'Uruguay', 'Venezuela', 'Vietnam', 'Wales', 'Yugoslavia'
            ],
            'regions': [
                'Africa', 'Asia', 'Europe', 'America', 'Americas', 'Oceania', 'Polynesia',
                'Melanesia', 'Micronesia', 'Caribbean', 'Scandinavia', 'Balkans', 'Caucasus',
                'Middle East', 'Far East', 'Near East', 'Central Asia', 'Southeast Asia',
                'South Asia', 'East Africa', 'West Africa', 'North Africa', 'Southern Africa',
                'Central America', 'South America', 'North America', 'Mediterranean',
                'Baltic', 'Siberia', 'Circumpolar', 'Arctic', 'Antarctic'
            ]
        }
        
        # Language families and major languages
        self.linguistic_entities = {
            'language_families': [
                'Indo-European', 'Sino-Tibetan', 'Afro-Asiatic', 'Niger-Congo', 
                'Austronesian', 'Trans-New Guinea', 'Altaic', 'Dravidian', 'Uralic',
                'Amerind', 'Khoisan', 'Nilo-Saharan', 'Eskimo-Aleut', 'Na-Dene',
                'Papuan', 'Australian', 'Caucasian', 'Kartvelian'
            ],
            'languages': [
                'Arabic', 'Bengali', 'Chinese', 'English', 'French', 'German', 'Hindi',
                'Italian', 'Japanese', 'Korean', 'Persian', 'Portuguese', 'Russian',
                'Spanish', 'Turkish', 'Urdu', 'Vietnamese', 'Swahili', 'Hebrew',
                'Greek', 'Latin', 'Sanskrit', 'Tibetan', 'Thai', 'Burmese', 'Malay',
                'Tagalog', 'Javanese', 'Hausa', 'Yoruba', 'Amharic', 'Finnish',
                'Hungarian', 'Estonian', 'Latvian', 'Lithuanian', 'Polish', 'Czech',
                'Slovak', 'Serbo-Croatian', 'Bulgarian', 'Romanian', 'Albanian',
                'Dutch', 'Swedish', 'Norwegian', 'Danish', 'Icelandic'
            ]
        }
        
        # Religious and cultural systems
        self.religious_entities = [
            'Christianity', 'Christian', 'Catholic', 'Protestant', 'Orthodox',
            'Islam', 'Islamic', 'Muslim', 'Judaism', 'Jewish', 'Hinduism', 'Hindu',
            'Buddhism', 'Buddhist', 'Jainism', 'Jain', 'Sikhism', 'Sikh',
            'Zoroastrianism', 'Zoroastrian', 'Confucianism', 'Confucian', 'Taoism',
            'Taoist', 'Shintoism', 'Shinto', 'Animism', 'Shamanism', 'Paganism',
            'Pagan', 'Druidism', 'Manichaeism', 'Gnosticism', 'Mithraic'
        ]
        
        # Ethnic and tribal groups (will expand as we see the data)
        self.ethnic_tribal_patterns = [
            'Aboriginal', 'Native', 'Indigenous', 'Tribal', 'Bedouin', 'Nomadic',
            'Gypsy', 'Roma', 'Sami', 'Inuit', 'Eskimo', 'Maori', 'Cherokee',
            'Apache', 'Sioux', 'Zulu', 'Masai', 'Berber', 'Kurdish', 'Basque'
        ]

    def categorize_reference(self, ref_term):
        """
        Categorize a cultural reference term.
        Returns a dict with category and confidence score.
        """
        ref_clean = ref_term.strip()
        categories = []
        
        # Check geographic entities
        for country in self.geographic_entities['countries']:
            if country.lower() in ref_clean.lower():
                categories.append(('geographic', 'country', 0.9))
                break
                
        for region in self.geographic_entities['regions']:
            if region.lower() in ref_clean.lower():
                categories.append(('geographic', 'region', 0.8))
                break
        
        # Check linguistic entities
        for lang_fam in self.linguistic_entities['language_families']:
            if lang_fam.lower() in ref_clean.lower():
                categories.append(('linguistic', 'language_family', 0.9))
                break
                
        for lang in self.linguistic_entities['languages']:
            if lang.lower() in ref_clean.lower():
                categories.append(('linguistic', 'language', 0.9))
                break
        
        # Check religious entities
        for religion in self.religious_entities:
            if religion.lower() in ref_clean.lower():
                categories.append(('religious', 'religion', 0.9))
                break
        
        # Check ethnic/tribal patterns
        for pattern in self.ethnic_tribal_patterns:
            if pattern.lower() in ref_clean.lower():
                categories.append(('ethnic_tribal', 'group', 0.7))
                break
        
        # Additional pattern matching
        if any(indicator in ref_clean.lower() for indicator in ['american indian', 'indian', 'tribe', 'clan']):
            categories.append(('ethnic_tribal', 'indigenous', 0.7))
        
        if any(indicator in ref_clean.lower() for indicator in ['ancient', 'medieval', 'classical']):
            categories.append(('temporal', 'historical_period', 0.6))
            
        # If no clear category found
        if not categories:
            categories.append(('unknown', 'unclassified', 0.1))
        
        # Return the highest confidence category
        return max(categories, key=lambda x: x[2])

    def analyze_cultural_references(self):
        """Analyze all cultural references in the database."""
        
        conn = psycopg2.connect(**db_params)
        
        # Get all cultural references for tale types
        query = """
        SELECT type_id, ref_term 
        FROM folklore.type_ref 
        ORDER BY type_id, ref_term
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        print(f"Analyzing {len(df)} cultural reference entries...")
        
        # Categorize each reference
        results = []
        category_counts = Counter()
        
        for idx, row in df.iterrows():
            category, subcategory, confidence = self.categorize_reference(row['ref_term'])
            
            results.append({
                'type_id': row['type_id'],
                'ref_term': row['ref_term'],
                'category': category,
                'subcategory': subcategory,
                'confidence': confidence
            })
            
            category_counts[category] += 1
            
            if idx % 1000 == 0:
                print(f"Processed {idx} references...")
        
        results_df = pd.DataFrame(results)
        
        return results_df, category_counts

    def generate_summary_report(self, results_df, category_counts):
        """Generate a summary report of the categorization."""
        
        print("\n" + "="*60)
        print("CULTURAL REFERENCE CATEGORIZATION SUMMARY")
        print("="*60)
        
        print(f"\nTotal references analyzed: {len(results_df)}")
        print(f"Unique tale types: {results_df['type_id'].nunique()}")
        
        print("\nCategory Distribution:")
        for category, count in category_counts.most_common():
            percentage = (count / len(results_df)) * 100
            print(f"  {category:15}: {count:4} ({percentage:5.1f}%)")
        
        print("\nSubcategory Breakdown:")
        subcategory_counts = results_df.groupby(['category', 'subcategory']).size()
        for (cat, subcat), count in subcategory_counts.items():
            print(f"  {cat:15} > {subcat:15}: {count:4}")
        
        print("\nConfidence Score Distribution:")
        confidence_bins = pd.cut(results_df['confidence'], 
                               bins=[0, 0.3, 0.6, 0.8, 1.0], 
                               labels=['Low', 'Medium', 'High', 'Very High'])
        confidence_dist = confidence_bins.value_counts()
        for conf_level, count in confidence_dist.items():
            percentage = (count / len(results_df)) * 100
            print(f"  {conf_level:10}: {count:4} ({percentage:5.1f}%)")
        
        print("\nSample unclassified references (for manual review):")
        unclassified = results_df[results_df['category'] == 'unknown']['ref_term'].unique()
        for ref in unclassified[:20]:  # Show first 20
            print(f"  '{ref}'")
        if len(unclassified) > 20:
            print(f"  ... and {len(unclassified) - 20} more")
        
        return results_df

    def analyze_tale_type_signatures(self, results_df, top_n=10):
        """Analyze cultural signatures of specific tale types."""
        
        print(f"\n" + "="*60)
        print("TALE TYPE CULTURAL SIGNATURES")
        print("="*60)
        
        # Find tale types with most references
        type_ref_counts = results_df.groupby('type_id').size().sort_values(ascending=False)
        
        print(f"\nTale types with most cultural references:")
        for type_id, count in type_ref_counts.head(top_n).items():
            print(f"\n{type_id}: {count} references")
            
            type_data = results_df[results_df['type_id'] == type_id]
            
            # Show category distribution for this tale type
            type_cats = type_data['category'].value_counts()
            for cat, cnt in type_cats.items():
                print(f"  {cat:15}: {cnt:2}")
            
            # Show some example references
            print("  Examples:")
            for ref in type_data['ref_term'].unique()[:5]:
                print(f"    '{ref}'")
            if len(type_data) > 5:
                print(f"    ... and {len(type_data) - 5} more")

def main():
    """Main execution function."""
    
    categorizer = CulturalReferenceCategorizr()
    
    print("Starting cultural reference analysis...")
    results_df, category_counts = categorizer.analyze_cultural_references()
    
    # Generate summary report
    categorizer.generate_summary_report(results_df, category_counts)
    
    # Analyze specific tale type signatures
    categorizer.analyze_tale_type_signatures(results_df)
    
    # Save results for further analysis
    output_file = "out/types/cultural_reference_analysis.csv"
    results_df.to_csv(output_file, index=False)
    print(f"\nDetailed results saved to: {output_file}")
    
    return results_df

if __name__ == "__main__":
    results = main()
