#!/usr/bin/env python3
"""
Fixed CDK4 MSA search test with correct E-value range.
"""

import asyncio
from pathlib import Path
from boltz2_client import Boltz2Client
from boltz2_client.msa_search import MSASearchClient

# GPU MSA endpoint
MSA_ENDPOINT = "http://10.34.0.226:8000"

# CDK4 sequence
CDK4_SEQUENCE = "MATSRYEPVAEIGVGAYGTVYKARDPHSGHFVALKSVRVPNGGGGGGGLPISTVREVALLRRLEAFEHPNVVRLMDVCATSRTDREIKVTLVFEHVDQDLRTYLDKAPPPGLPAETIKDLMRQFLRGLDFLHANCIVHRDLKPENILVTSGGTVKLADFGLARIYSYQMALTPVVVTLWYRAPEVLLQSTYATPVDMWSVGCIFAEMFRRKPLFCGNSEADQLGKIFDLIGLPPEDDWPRDVSLPRGAFPPRGPRPVQSVVPEMEESGAQLLLEMLTFNPHKRISAFRALQHSYLHKDEGNPE"


async def test_msa_with_correct_params():
    """Test MSA search with correct E-value."""
    
    print("🧪 CDK4 MSA Search with Correct Parameters")
    print("=" * 60)
    print(f"Sequence length: {len(CDK4_SEQUENCE)} residues")
    print("E-value must be ≤ 1.0 (not > 1.0 as attempted before)\n")
    
    # Method 1: Using Boltz2Client
    print("Method 1: Using Boltz2Client")
    print("-" * 40)
    
    client = Boltz2Client()
    client.configure_msa_search(msa_endpoint_url=MSA_ENDPOINT)
    
    output_dir = Path("cdk4_msa_fixed")
    output_dir.mkdir(exist_ok=True)
    
    try:
        # Use maximum allowed E-value
        print("Searching with E-value = 1.0 (most permissive allowed)...")
        
        msa_path = await client.search_msa(
            sequence=CDK4_SEQUENCE,
            databases=["Uniref30_2302", "colabfold_envdb_202108"],
            max_msa_sequences=500,
            e_value=1.0,  # Maximum allowed value
            output_format="a3m",
            save_path=output_dir / "cdk4_eval_1.0.a3m"
        )
        
        print(f"✅ MSA saved to: {msa_path}")
        
        # Check results
        with open(msa_path, 'r') as f:
            content = f.read()
            sequences = content.count('>')
            
        print(f"Found {sequences} sequences (including query)")
        
        if sequences > 1:
            print("✅ Found homologs!")
            headers = [line for line in content.split('\n') if line.startswith('>')]
            print("\nFirst 5 headers:")
            for header in headers[:5]:
                print(f"  {header}")
        else:
            print("⚠️  No homologs found even with E-value = 1.0")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Method 2: Try with different E-values
    print("\n\nMethod 2: Testing Different E-values")
    print("-" * 40)
    
    e_values = [0.001, 0.01, 0.1, 0.5, 1.0]
    
    for e_val in e_values:
        try:
            print(f"\nTesting E-value = {e_val}...")
            
            msa_path = await client.search_msa(
                sequence=CDK4_SEQUENCE,
                databases=["Uniref30_2302"],  # Just one database for speed
                max_msa_sequences=100,
                e_value=e_val,
                output_format="a3m",
                save_path=output_dir / f"cdk4_eval_{e_val}.a3m"
            )
            
            with open(msa_path, 'r') as f:
                sequences = f.read().count('>')
                
            print(f"  → Found {sequences} sequences")
            
            if sequences > 1:
                print(f"  ✅ E-value {e_val} found homologs!")
                break
                
        except Exception as e:
            print(f"  ❌ Error with E-value {e_val}: {e}")
    
    # Method 3: Try with just the kinase domain
    print("\n\nMethod 3: Testing Conserved Kinase Domain Only")
    print("-" * 40)
    
    # Extract just the conserved kinase domain region
    kinase_domain = CDK4_SEQUENCE[12:250]  # Approximate kinase domain
    
    print(f"Kinase domain length: {len(kinase_domain)} residues")
    
    try:
        msa_path = await client.search_msa(
            sequence=kinase_domain,
            databases=["Uniref30_2302", "colabfold_envdb_202108"],
            max_msa_sequences=500,
            e_value=1.0,
            output_format="a3m",
            save_path=output_dir / "cdk4_kinase_domain.a3m"
        )
        
        with open(msa_path, 'r') as f:
            sequences = f.read().count('>')
            
        print(f"Found {sequences} sequences for kinase domain")
        
        if sequences > 1:
            print("✅ Kinase domain found more homologs!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Method 4: Check available databases
    print("\n\nMethod 4: Checking Available Databases")
    print("-" * 40)
    
    try:
        msa_client = MSASearchClient(endpoint_url=MSA_ENDPOINT)
        databases = await msa_client.get_databases()
        
        print("Available databases:")
        for db_name, db_info in databases.items():
            print(f"  - {db_name}: {db_info}")
            
        # Try with each database individually
        for db_name in databases.keys():
            print(f"\nTrying {db_name} alone...")
            
            try:
                response = await msa_client.search(
                    sequence=CDK4_SEQUENCE[:100],  # Use shorter sequence for speed
                    databases=[db_name],
                    max_msa_sequences=50,
                    e_value=1.0
                )
                
                total = 0
                for db, alignments in response.alignments.items():
                    if isinstance(alignments, list):
                        total += len(alignments)
                        
                print(f"  → Found {total} hits in {db_name}")
                
            except Exception as e:
                print(f"  ❌ Error with {db_name}: {e}")
                
    except Exception as e:
        print(f"❌ Error checking databases: {e}")
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("- E-value must be ≤ 1.0 (validation constraint)")
    print("- If no homologs found, CDK4 might be too divergent")
    print("- Try using conserved domains instead of full sequence")
    print("- Check which databases actually contain CDK sequences")
    print(f"\nAll results saved to: {output_dir}/")


if __name__ == "__main__":
    asyncio.run(test_msa_with_correct_params())
