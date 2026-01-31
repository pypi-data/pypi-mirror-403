#!/usr/bin/env python3
"""
Quick test to verify MSA search issue and solution.
"""

import asyncio
from boltz2_client.msa_search import MSASearchClient

MSA_ENDPOINT = "http://10.34.0.226:8000"
CDK4_FRAGMENT = "MATSRYEPVAEIGVGAYGTVYKARDPHSGHFVALKSVRVPNGGGGGGGLP"


async def test():
    client = MSASearchClient(endpoint_url=MSA_ENDPOINT)
    
    print("Testing MSA search with CDK4 fragment...")
    print(f"Sequence: {CDK4_FRAGMENT}")
    
    # Test with correct parameters
    try:
        response = await client.search(
            sequence=CDK4_FRAGMENT,
            databases=["Uniref30_2302"],
            max_msa_sequences=100,  # Correct parameter
            e_value=1.0  # Maximum allowed
        )
        
        # Count results
        total = 0
        for db, alignments in response.alignments.items():
            if isinstance(alignments, list):
                total += len(alignments)
                print(f"{db}: {len(alignments)} sequences")
        
        print(f"\nTotal sequences found: {total}")
        
        if total == 0:
            print("\n⚠️ No homologs found even with E-value=1.0")
            print("Possible reasons:")
            print("1. CDK4 is too unique in the database")
            print("2. Database might not contain CDK sequences")
            print("3. Try using a more common protein like ubiquitin")
        else:
            print(f"\n✅ Found {total} homologs!")
            
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(test())
