#!/usr/bin/env python3
"""
Test GPU MSA NIM endpoint connectivity and functionality.
"""

import asyncio
from boltz2_client import Boltz2Client

# GPU MSA endpoint
MSA_ENDPOINT = "http://10.34.0.226:8000"

# Short test sequence (50 residues)
TEST_SEQUENCE = "MKTVRQERLKSIVRILERSKEPVSGAQLAEELSVSRQVIVQDIAYLRSL"


async def test_msa_endpoint():
    """Test basic MSA search functionality."""
    
    print(f"🔍 Testing MSA Endpoint: {MSA_ENDPOINT}")
    print(f"   Test sequence: {len(TEST_SEQUENCE)} residues")
    print("-" * 60)
    
    # Initialize client
    client = Boltz2Client()
    
    # Configure MSA search
    client.configure_msa_search(msa_endpoint_url=MSA_ENDPOINT)
    print("✅ MSA search configured")
    
    try:
        # Test 1: Get available databases
        print("\n📊 Available MSA Databases:")
        databases = await client.get_msa_databases()
        for db_name, db_info in databases.items():
            print(f"   - {db_name}: {db_info}")
        
        # Test 2: Simple MSA search
        print(f"\n🔍 Searching MSA for test sequence...")
        result = await client.search_msa(
            sequence=TEST_SEQUENCE,
            databases=["Uniref30_2302"],
            max_msa_sequences=10  # Small number for quick test
        )
        
        if result:
            print(f"✅ MSA search successful!")
            print(f"   Found alignments in {len(result.alignments)} databases")
            for db_name, alignments in result.alignments.items():
                print(f"   - {db_name}: {len(alignments)} sequences")
        else:
            print("⚠️  No MSA results found")
        
        print("\n✅ MSA endpoint is working correctly!")
        return True
        
    except Exception as e:
        print(f"\n❌ MSA endpoint test failed: {e}")
        print("\nPossible issues:")
        print("1. Check if the endpoint URL is correct")
        print("2. Verify the MSA NIM service is running")
        print("3. Check network connectivity")
        return False


async def main():
    """Run the test."""
    success = await test_msa_endpoint()
    
    if success:
        print("\n💡 You can now run the full Barnase-Barstar MSA examples:")
        print("   python examples/quick_barnase_barstar_msa.py")
        print("   python examples/barnase_barstar_with_msa.py")


if __name__ == "__main__":
    asyncio.run(main())
