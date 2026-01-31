#!/usr/bin/env python3
"""
Fix and test CDK4 MSA search to ensure we get actual homologs.
"""

import asyncio
from pathlib import Path
from boltz2_client import Boltz2Client
from boltz2_client.msa_search import MSASearchClient, MSASearchIntegration

# Endpoints
MSA_ENDPOINT = "http://10.34.0.226:8000"

# Use a well-known protein sequence that should have many homologs
# Let's try with a kinase domain region that's more conserved
KINASE_DOMAIN = "VAEIGVGAYGTVYKARDPHSGHFVALKSVRVPNGGGGGGGLPISTVREVALLRRLEAFEHPNVVRLMDVCATSRTDREIKVTLVFEHVDQDLRTYLDKAP"

# Or use ubiquitin - almost guaranteed to find homologs
UBIQUITIN = "MQIFVKTLTGKTITLEVEPSDTIENVKAKIQDKEGIPPDQQRLIFAGKQLEDGRTLSDYNIQKESTLHLVLRLRGG"

# Full CDK4
CDK4_FULL = "MATSRYEPVAEIGVGAYGTVYKARDPHSGHFVALKSVRVPNGGGGGGGLPISTVREVALLRRLEAFEHPNVVRLMDVCATSRTDREIKVTLVFEHVDQDLRTYLDKAPPPGLPAETIKDLMRQFLRGLDFLHANCIVHRDLKPENILVTSGGTVKLADFGLARIYSYQMALTPVVVTLWYRAPEVLLQSTYATPVDMWSVGCIFAEMFRRKPLFCGNSEADQLGKIFDLIGLPPEDDWPRDVSLPRGAFPPRGPRPVQSVVPEMEESGAQLLLEMLTFNPHKRISAFRALQHSYLHKDEGNPE"


async def test_sequence_with_client(sequence_name, sequence, output_dir):
    """Test MSA search using Boltz2Client."""
    print(f"\n{'='*60}")
    print(f"Testing: {sequence_name}")
    print(f"Length: {len(sequence)} residues")
    print(f"{'='*60}")
    
    # Initialize client
    client = Boltz2Client()
    client.configure_msa_search(msa_endpoint_url=MSA_ENDPOINT)
    
    try:
        # Search with very permissive parameters
        print("\n🔍 Searching for MSA...")
        msa_path = await client.search_msa(
            sequence=sequence,
            databases=["Uniref30_2302", "colabfold_envdb_202108", "PDB70_220313"],
            max_msa_sequences=1000,  # Request many
            e_value=100.0,           # Very permissive E-value
            output_format="a3m",
            save_path=output_dir / f"{sequence_name}.a3m"
        )
        
        print(f"✅ MSA saved to: {msa_path}")
        
        # Check the content
        with open(msa_path, 'r') as f:
            content = f.read()
            sequences = content.count('>')
            lines = content.strip().split('\n')
            
        print(f"\n📊 Results:")
        print(f"   Total sequences: {sequences}")
        print(f"   Total lines: {len(lines)}")
        
        if sequences > 1:
            print(f"   ✅ Found {sequences - 1} homologs!")
            print("\n   First 5 headers:")
            headers = [line for line in lines if line.startswith('>')]
            for header in headers[:5]:
                print(f"   {header}")
        else:
            print("   ⚠️  No homologs found")
            
        return sequences > 1
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_with_raw_client(sequence_name, sequence, output_dir):
    """Test with raw MSASearchClient for more control."""
    print(f"\n🔬 Raw client test for {sequence_name}")
    
    client = MSASearchClient(endpoint_url=MSA_ENDPOINT)
    
    try:
        # Try with all available databases
        print("Getting available databases...")
        databases_response = await client.get_databases()
        available_dbs = list(databases_response.keys())
        print(f"Available databases: {available_dbs}")
        
        # Search with all databases
        response = await client.search(
            sequence=sequence,
            databases=available_dbs,  # Use all available
            max_msa_sequences=1000,
            e_value=1000.0,  # Extremely permissive
            output_alignment_formats=["a3m"]
        )
        
        # Debug the response
        total = 0
        for db, alignments in response.alignments.items():
            if isinstance(alignments, list):
                count = len(alignments)
                if count > 0:
                    print(f"   {db}: {count} hits")
                    total += count
            elif isinstance(alignments, dict) and "a3m" in alignments:
                if hasattr(alignments["a3m"], 'alignment'):
                    seqs = alignments["a3m"].alignment.count('>')
                    print(f"   {db}: {seqs} sequences in A3M")
                    total += seqs
        
        print(f"   Total hits across all databases: {total}")
        
        # Save using integration
        integration = MSASearchIntegration(client)
        a3m_path = await integration.search_and_save(
            sequence=sequence,
            output_path=output_dir / f"{sequence_name}_raw.a3m",
            output_format="a3m",
            databases=available_dbs,
            max_msa_sequences=1000,
            e_value=1000.0
        )
        
        print(f"   Saved to: {a3m_path}")
        
        return total > 0
        
    except Exception as e:
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Test different sequences to find which work."""
    print("🧪 CDK4 MSA Search Troubleshooting")
    print("Testing different sequences to identify the issue\n")
    
    output_dir = Path("msa_troubleshooting")
    output_dir.mkdir(exist_ok=True)
    
    # Test sequences
    sequences = [
        ("ubiquitin", UBIQUITIN),
        ("cdk4_kinase_domain", KINASE_DOMAIN),
        ("cdk4_full", CDK4_FULL)
    ]
    
    results = {}
    
    # Test each sequence
    for name, seq in sequences:
        # Test with Boltz2Client
        success1 = await test_sequence_with_client(name, seq, output_dir)
        
        # Test with raw client
        success2 = await test_with_raw_client(name, seq, output_dir)
        
        results[name] = success1 or success2
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for name, success in results.items():
        status = "✅ Found homologs" if success else "❌ No homologs"
        print(f"{name}: {status}")
    
    print("\n💡 Recommendations:")
    
    if not any(results.values()):
        print("❌ No sequences found homologs. Possible issues:")
        print("   1. MSA endpoint may not be properly configured")
        print("   2. Databases might be empty or inaccessible")
        print("   3. Network/firewall issues")
        print("   4. Try using the MSA Search NIM directly with curl")
        
        print("\n   Test the endpoint directly:")
        print(f'   curl -X POST {MSA_ENDPOINT}/search \\')
        print('     -H "Content-Type: application/json" \\')
        print('     -d \'{"sequence": "' + UBIQUITIN[:50] + '...", "databases": ["Uniref30_2302"]}\'')
    
    elif results["ubiquitin"] and not results["cdk4_full"]:
        print("⚠️  Common sequences work but CDK4 doesn't:")
        print("   1. CDK4 might be too unique/synthetic")
        print("   2. Try using just the conserved kinase domain")
        print("   3. Consider using a different CDK family member")
        print("   4. Manual MSA construction might be needed")
    
    else:
        print("✅ MSA search is working!")
        print("   Check the output files in: msa_troubleshooting/")
    
    print(f"\n📁 All output saved to: {output_dir}/")


if __name__ == "__main__":
    asyncio.run(main())
