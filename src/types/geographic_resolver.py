import os
import pandas as pd
import re
from collections import defaultdict
import json

class GeographicResolver:
    def __init__(self):
        """Initialize with expanded geographic and ethnographic dictionaries."""
        
        # Obvious geographic patterns - demonyms and regional adjectives
        self.demonym_patterns = {
            # Clear country demonyms
            'Argentine': 'Argentina',
            'Catalan': 'Spain/Catalonia', 
            'Irish': 'Ireland',
            'Mexican': 'Mexico',
            'Flemish': 'Belgium/Flanders',
            'Frisian': 'Netherlands/Frisia',
            'Costa Rican': 'Costa Rica',
            'Liberian': 'Liberia',
            'Namibian': 'Namibia',
            'Austrian': 'Austria',
            'Brazilian': 'Brazil',
            'Bulgarian': 'Bulgaria',
            'Canadian': 'Canada',
            'Chilean': 'Chile',
            'Colombian': 'Colombia',
            'Croatian': 'Croatia',
            'Danish': 'Denmark',
            'Egyptian': 'Egypt',
            'Estonian': 'Estonia',
            'Ethiopian': 'Ethiopia',
            'Finnish': 'Finland',
            'German': 'Germany',
            'Icelandic': 'Iceland',
            'Indonesian': 'Indonesia',
            'Latvian': 'Latvia',
            'Lithuanian': 'Lithuania',
            'Norwegian': 'Norway',
            'Polish': 'Poland',
            'Portuguese': 'Portugal',
            'Romanian': 'Romania',
            'Serbian': 'Serbia',
            'Slovenian': 'Slovenia',
            'Swedish': 'Sweden',
            'Swiss': 'Switzerland',
            'Ukrainian': 'Ukraine'
        }
        
        # Indigenous and ethnic groups with known geographic regions
        self.indigenous_groups = {
            # Major language families and regions
            'Cheremis': 'Russia/Mari El',
            'Mari': 'Russia/Mari El', 
            'Chuvash': 'Russia/Chuvashia',
            'Karelian': 'Finland/Karelia',
            'Kazakh': 'Kazakhstan',
            'Lappish': 'Scandinavia/Sápmi',
            'Livonian': 'Latvia/Estonia',
            'Mordvinian': 'Russia/Mordovia',
            'Nenets': 'Russia/Arctic',
            'Ossetian': 'Caucasus/Ossetia',
            'Sami': 'Scandinavia/Sápmi',
            'Yakut': 'Russia/Sakha',
            'Tungus': 'Siberia',
            'Buryat': 'Russia/Buryatia',
            'Evenk': 'Siberia',
            'Komi': 'Russia/Komi',
            'Udmurt': 'Russia/Udmurtia',
            
            # Historical regions
            'Lydian': 'Turkey/Ancient Anatolia',
            'Phoenician': 'Lebanon/Ancient Levant',
            'Sumerian': 'Iraq/Ancient Mesopotamia',
            'Babylonian': 'Iraq/Ancient Mesopotamia',
            'Assyrian': 'Iraq/Ancient Mesopotamia',
            'Hittite': 'Turkey/Ancient Anatolia',
            'Celtic': 'Western Europe',
            'Germanic': 'Northern/Central Europe',
            'Slavic': 'Eastern/Central Europe',
            'Nordic': 'Scandinavia',
            
            # Regional cultural groups
            'Basque': 'Spain/France Basque Country',
            'Kurdish': 'Kurdistan (Turkey/Iraq/Iran/Syria)',
            'Berber': 'North Africa',
            'Bedouin': 'Arabian Peninsula/North Africa',
            'Romani': 'Europe (dispersed)',
            'Gypsy': 'Europe (dispersed)',
            
            # American indigenous
            'Apache': 'Southwestern United States',
            'Cherokee': 'Southeastern United States', 
            'Sioux': 'Great Plains United States',
            'Iroquois': 'Northeastern United States',
            'Navajo': 'Southwestern United States',
            'Pueblo': 'Southwestern United States',
            'Algonquin': 'Northeastern North America',
            'Ojibwe': 'Great Lakes North America',
            'Mayan': 'Mesoamerica',
            'Aztec': 'Mexico',
            'Inca': 'Peru/Andes',
            'Quechua': 'Andes',
            'Guarani': 'Paraguay/Brazil',
            
            # African groups
            'Zulu': 'South Africa',
            'Masai': 'Kenya/Tanzania',
            'Yoruba': 'Nigeria',
            'Hausa': 'Nigeria/Niger',
            'Swahili': 'East Africa',
            'Bantu': 'Sub-Saharan Africa',
            'Fulani': 'West Africa',
            'Dogon': 'Mali',
            
            # Pacific
            'Maori': 'New Zealand',
            'Hawaiian': 'Hawaii',
            'Polynesian': 'Pacific Ocean',
            'Melanesian': 'Southwest Pacific',
            'Micronesian': 'Western Pacific',
            'Aboriginal': 'Australia',
            'Papuan': 'Papua New Guinea'
        }
        
        # Language-based geographic associations
        self.language_regions = {
            'Aramaic': 'Middle East/Ancient',
            'Coptic': 'Egypt',
            'Gaelic': 'Ireland/Scotland',
            'Welsh': 'Wales',
            'Cornish': 'Cornwall/England',
            'Breton': 'Brittany/France',
            'Yiddish': 'Eastern Europe/Jewish',
            'Ladino': 'Sephardic Jewish/Mediterranean',
            'Pashto': 'Afghanistan/Pakistan',
            'Urdu': 'Pakistan/India',
            'Bengali': 'Bangladesh/India',
            'Tamil': 'Tamil Nadu/Sri Lanka',
            'Telugu': 'Andhra Pradesh/India',
            'Gujarati': 'Gujarat/India',
            'Punjabi': 'Punjab/India/Pakistan',
            'Marathi': 'Maharashtra/India',
            'Oriya': 'Odisha/India',
            'Assamese': 'Assam/India',
            'Tibetan': 'Tibet/Himalayas',
            'Mongolian': 'Mongolia',
            'Manchu': 'Manchuria/China',
            'Uighur': 'Xinjiang/China'
        }

    def resolve_unknown_references(self, df):
        """
        Attempt to resolve geographic locations for unknown references.
        Returns updated dataframe with new geographic assignments.
        """
        
        print("Resolving unknown geographic references...")
        
        # Get all unknown references
        unknown_refs = df[df['category'] == 'unknown'].copy()
        
        resolved_count = 0
        resolution_methods = defaultdict(int)
        
        for idx, row in unknown_refs.iterrows():
            ref_term = row['ref_term'].strip()
            original_category = row['category']
            
            # Method 1: Direct demonym lookup
            if ref_term in self.demonym_patterns:
                df.at[idx, 'category'] = 'geographic'
                df.at[idx, 'subcategory'] = 'country'
                df.at[idx, 'confidence'] = 0.95
                df.at[idx, 'resolution_method'] = 'demonym_lookup'
                df.at[idx, 'geographic_region'] = self.demonym_patterns[ref_term]
                resolved_count += 1
                resolution_methods['demonym_lookup'] += 1
                continue
            
            # Method 2: Indigenous/ethnic group lookup
            if ref_term in self.indigenous_groups:
                df.at[idx, 'category'] = 'ethnic_tribal'
                df.at[idx, 'subcategory'] = 'indigenous_group'
                df.at[idx, 'confidence'] = 0.85
                df.at[idx, 'resolution_method'] = 'indigenous_lookup'
                df.at[idx, 'geographic_region'] = self.indigenous_groups[ref_term]
                resolved_count += 1
                resolution_methods['indigenous_lookup'] += 1
                continue
            
            # Method 3: Language-based geographic inference
            if ref_term in self.language_regions:
                df.at[idx, 'category'] = 'linguistic'
                df.at[idx, 'subcategory'] = 'language'
                df.at[idx, 'confidence'] = 0.80
                df.at[idx, 'resolution_method'] = 'language_geographic'
                df.at[idx, 'geographic_region'] = self.language_regions[ref_term]
                resolved_count += 1
                resolution_methods['language_geographic'] += 1
                continue
            
            # Method 4: Pattern-based inference
            resolved = self._pattern_based_resolution(ref_term)
            if resolved:
                df.at[idx, 'category'] = resolved['category']
                df.at[idx, 'subcategory'] = resolved['subcategory']
                df.at[idx, 'confidence'] = resolved['confidence']
                df.at[idx, 'resolution_method'] = resolved['method']
                df.at[idx, 'geographic_region'] = resolved['region']
                resolved_count += 1
                resolution_methods[resolved['method']] += 1
                continue
            
            # Method 5: Mark for manual review with hints
            df.at[idx, 'resolution_method'] = 'needs_manual_review'
            df.at[idx, 'manual_hints'] = self._generate_manual_hints(ref_term)
        
        print(f"Resolved {resolved_count} unknown references using automated methods:")
        for method, count in resolution_methods.items():
            print(f"  {method}: {count}")
        
        return df

    def _pattern_based_resolution(self, ref_term):
        """Apply pattern-based resolution for complex cases."""
        
        ref_lower = ref_term.lower()
        
        # Pattern: ends with -ian, -an (likely demonyms)
        if re.search(r'(ian|an)$', ref_lower):
            if any(geo in ref_lower for geo in ['america', 'africa', 'asia', 'europe']):
                return {
                    'category': 'geographic',
                    'subcategory': 'regional',
                    'confidence': 0.70,
                    'method': 'pattern_continental',
                    'region': f"Inferred from pattern: {ref_term}"
                }
        
        # Pattern: contains "Indian" or "Native"
        if any(term in ref_lower for term in ['indian', 'native', 'tribe']):
            return {
                'category': 'ethnic_tribal',
                'subcategory': 'indigenous_group',
                'confidence': 0.75,
                'method': 'pattern_indigenous',
                'region': 'Indigenous group (region needs specification)'
            }
        
        # Pattern: Ancient/Historical indicators
        if any(term in ref_lower for term in ['ancient', 'old', 'classical']):
            return {
                'category': 'geographic',
                'subcategory': 'historical_region',
                'confidence': 0.65,
                'method': 'pattern_historical',
                'region': f"Historical region: {ref_term}"
            }
        
        return None

    def _generate_manual_hints(self, ref_term):
        """Generate hints for manual resolution."""
        
        hints = []
        ref_lower = ref_term.lower()
        
        # Check for partial matches in our dictionaries
        for group, region in self.indigenous_groups.items():
            if group.lower() in ref_lower or ref_lower in group.lower():
                hints.append(f"Similar to {group} ({region})")
        
        # Check for common suffixes
        if ref_term.endswith(('ish', 'ese', 'ic')):
            hints.append("Likely language/ethnic group")
        
        if ref_term.endswith(('an', 'ian')):
            hints.append("Likely demonym/nationality")
        
        # Check for geographic keywords
        if any(kw in ref_lower for kw in ['island', 'mountain', 'river', 'desert']):
            hints.append("Contains geographic feature")
        
        return "; ".join(hints) if hints else "No obvious patterns"

    def generate_resolution_report(self, df_original, df_resolved):
        """Generate a report showing resolution results."""
        
        print("\n" + "="*60)
        print("GEOGRAPHIC RESOLUTION REPORT")
        print("="*60)
        
        # Count changes
        original_unknown = len(df_original[df_original['category'] == 'unknown'])
        resolved_unknown = len(df_resolved[df_resolved['category'] == 'unknown'])
        total_resolved = original_unknown - resolved_unknown
        
        print(f"\nOriginal unknown references: {original_unknown}")
        print(f"Remaining unknown references: {resolved_unknown}")
        print(f"Successfully resolved: {total_resolved} ({(total_resolved/original_unknown)*100:.1f}%)")
        
        # Show resolution methods
        if 'resolution_method' in df_resolved.columns:
            method_counts = df_resolved['resolution_method'].value_counts()
            print(f"\nResolution methods used:")
            for method, count in method_counts.items():
                if method != 'needs_manual_review':
                    print(f"  {method}: {count}")
        
        # Show some examples of resolved references
        resolved_refs = df_resolved[
            (df_resolved['category'] != 'unknown') & 
            (df_resolved['resolution_method'].notna())
        ]
        
        if len(resolved_refs) > 0:
            print(f"\nExample resolved references:")
            for idx, row in resolved_refs.head(10).iterrows():
                print(f"  '{row['ref_term']}' -> {row['category']}/{row['subcategory']} ({row['geographic_region']})")
        
        # Show remaining problematic cases
        still_unknown = df_resolved[df_resolved['category'] == 'unknown']
        if len(still_unknown) > 0:
            print(f"\nRemaining unknown references (first 20):")
            for ref in still_unknown['ref_term'].unique()[:20]:
                hints_row = still_unknown[still_unknown['ref_term'] == ref].iloc[0]
                hints = hints_row.get('manual_hints', 'No hints')
                print(f"  '{ref}' - {hints}")

    def export_for_manual_review(self, df, output_dir="out/types"):
        """Export remaining unknowns for manual review."""
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Export remaining unknowns with hints
        unknown_refs = df[df['category'] == 'unknown'].copy()
        if len(unknown_refs) > 0:
            manual_review_file = os.path.join(output_dir, "manual_review_needed.csv")
            unknown_refs[['ref_term', 'manual_hints']].drop_duplicates().to_csv(
                manual_review_file, index=False
            )
            print(f"\nExported {len(unknown_refs)} unknown references for manual review: {manual_review_file}")
        
        # Export resolved references with geographic regions
        resolved_refs = df[df['geographic_region'].notna()].copy()
        if len(resolved_refs) > 0:
            resolved_file = os.path.join(output_dir, "resolved_geographic_references.csv")
            resolved_refs.to_csv(resolved_file, index=False)
            print(f"Exported {len(resolved_refs)} resolved references: {resolved_file}")

def main():
    """Main execution function."""
    
    # Load the previous analysis results
    input_file = "out/types/cultural_reference_analysis.csv"
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found. Please run the cultural reference categorizer first.")
        return
    
    df_original = pd.read_csv(input_file)
    print(f"Loaded {len(df_original)} cultural references from {input_file}")
    
    # Initialize resolver
    resolver = GeographicResolver()
    
    # Add new columns for resolution tracking
    df_resolved = df_original.copy()
    df_resolved['resolution_method'] = None
    df_resolved['geographic_region'] = None
    df_resolved['manual_hints'] = None
    
    # Resolve unknown references
    df_resolved = resolver.resolve_unknown_references(df_resolved)
    
    # Generate report
    resolver.generate_resolution_report(df_original, df_resolved)
    
    # Export results
    os.makedirs("out/types", exist_ok=True)
    output_file = "out/types/cultural_reference_analysis_resolved.csv"
    df_resolved.to_csv(output_file, index=False)
    print(f"\nUpdated analysis saved to: {output_file}")
    
    # Export files for manual review
    resolver.export_for_manual_review(df_resolved)
    
    return df_resolved

if __name__ == "__main__":
    resolved_df = main()
