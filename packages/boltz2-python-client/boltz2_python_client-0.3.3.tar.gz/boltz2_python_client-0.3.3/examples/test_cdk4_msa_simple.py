#!/usr/bin/env python3
"""
Simple test for CDK4 MSA search and conversion.
Tests just the MSA search and A3M conversion without full prediction.
"""

import asyncio
from boltz2_client.msa_search import MSASearchClient

# GPU MSA endpoint
MSA_ENDPOINT = "http://10.34.0.226:8000"

# Short CDK4 fragment for quick testing (50 residues)
CDK4_FRAGMENT = "MATSRYEPVAEIGVGAYGTVYKARDPHSGHFVALKSVRVPNGGGGGGGLP"


async def test_msa_conversion():
    """Test MSA search and A3M conversion."""
    
    print("🧪 Testing CDK4 MSA Search and A3M Conversion")
    print(f"MSA Endpoint: {MSA_ENDPOINT}")
    print(f"Test sequence: {len(CDK4_FRAGMENT)} residues\n")
    
    try:
        # Initialize MSA client
        msa_client = MSASearchClient(endpoint_url=MSA_ENDPOINT)
        
        # Quick MSA search
        print("🔍 Searching MSA...")
        msa_response = await msa_client.search(
            sequence=CDK4_FRAGMENT,
            databases=["Uniref30_2302"],
            max_results=10  # Small number for quick test
        )
        
        print(f"✅ MSA search complete!")
        
        # Simple A3M conversion
        a3m_lines = [f">query", CDK4_FRAGMENT]
        
        for db_name, alignments in msa_response.alignments.items():
            print(f"   {db_name}: {len(alignments)} sequences")
            for i, alignment in enumerate(alignments[:5]):  # Just first 5
                seq = getattr(alignment, 'sequence', '')
                if seq and seq != CDK4_FRAGMENT:
                    a3m_lines.append(f">{db_name}_{i}")
                    a3m_lines.append(seq)
        
        a3m_content = "\n".join(a3m_lines)
        
        print(f"\n✅ A3M conversion complete!")
        print(f"   Total sequences: {(len(a3m_lines) - 2) // 2 + 1}")
        print(f"   A3M size: {len(a3m_content)} bytes")
        
        print("\n📄 A3M preview:")
        for line in a3m_lines[:6]:
            print(f"   {line[:70]}...")
        
        print("\n✅ Test successful! CDK4 MSA search and A3M conversion working.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_msa_conversion())
    
    if success:
        print("\n💡 You can now run the full CDK4 examples:")
        print("   python examples/cdk4_msa_affinity_example.py")
        print("   jupyter notebook examples/14_cdk4_msa_affinity_prediction.ipynb")
