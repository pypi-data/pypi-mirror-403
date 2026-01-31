#!/usr/bin/env python3
"""
Simple test to check MSA search and A3M conversion issue.
"""

import asyncio
from boltz2_client.msa_search import MSASearchClient, MSAFormatConverter

# GPU MSA endpoint
MSA_ENDPOINT = "http://10.34.0.226:8000"

# CDK4 fragment for testing
TEST_SEQUENCE = "MATSRYEPVAEIGVGAYGTVYKARDPHSGHFVALKSVRVPNGGGGGGGLP"


async def test_msa_and_a3m():
    """Test MSA search and check why only 1 sequence is found."""
    
    print("🧪 Testing MSA Search and A3M Conversion")
    print(f"Endpoint: {MSA_ENDPOINT}")
    print(f"Sequence: {TEST_SEQUENCE[:30]}... ({len(TEST_SEQUENCE)} residues)\n")
    
    # Initialize client
    client = MSASearchClient(endpoint_url=MSA_ENDPOINT)
    
    # Test 1: Basic search
    print("Test 1: Basic MSA search")
    print("-" * 40)
    
    try:
        response = await client.search(
            sequence=TEST_SEQUENCE,
            databases=["Uniref30_2302", "colabfold_envdb_202108"],
            max_msa_sequences=100,
            e_value=10.0  # Very permissive
        )
        
        print(f"✅ Search completed")
        print(f"Databases in response: {list(response.alignments.keys())}")
        
        # Count actual sequences found
        total_sequences = 0
        for db_name, alignments in response.alignments.items():
            if isinstance(alignments, list):
                count = len(alignments)
                total_sequences += count
                print(f"  {db_name}: {count} sequences")
                
                # Show first alignment details
                if count > 0 and hasattr(alignments[0], '__dict__'):
                    print(f"    First alignment attributes: {list(alignments[0].__dict__.keys())}")
        
        print(f"\nTotal sequences found: {total_sequences}")
        
        if total_sequences == 0:
            print("⚠️  No homologs found! Possible reasons:")
            print("   1. Sequence is too unique/synthetic")
            print("   2. E-value threshold too strict")
            print("   3. Database doesn't contain similar sequences")
            print("   4. MSA endpoint configuration issue")
        
    except Exception as e:
        print(f"❌ Search failed: {e}")
        return
    
    # Test 2: Check A3M conversion
    print("\n\nTest 2: A3M Format Conversion")
    print("-" * 40)
    
    try:
        # Method 1: Using MSAFormatConverter
        a3m_content = MSAFormatConverter.extract_alignment(response, "a3m")
        
        if a3m_content:
            print("✅ MSAFormatConverter.extract_alignment worked!")
            lines = a3m_content.strip().split('\n')
            sequences = [line for line in lines if line.startswith('>')]
            print(f"   Headers found: {len(sequences)}")
            print(f"   Total lines: {len(lines)}")
            print("\n   First few lines:")
            for line in lines[:6]:
                print(f"   {line[:70]}...")
        else:
            print("❌ MSAFormatConverter.extract_alignment returned empty")
            
            # Try manual extraction
            print("\n   Attempting manual extraction...")
            a3m_lines = [">query", TEST_SEQUENCE]
            found_any = False
            
            for db_name, alignments in response.alignments.items():
                if isinstance(alignments, dict):
                    # Format-based response
                    for fmt, record in alignments.items():
                        if fmt == "a3m" and hasattr(record, 'alignment'):
                            print(f"   ✅ Found A3M in {db_name}")
                            a3m_lines = [record.alignment]
                            found_any = True
                            break
                elif isinstance(alignments, list):
                    # List of alignment objects
                    for i, align in enumerate(alignments[:5]):  # First 5
                        seq = None
                        for attr in ['sequence', 'aligned_sequence']:
                            if hasattr(align, attr):
                                seq = getattr(align, attr)
                                break
                        if seq:
                            a3m_lines.append(f">{db_name}_{i}")
                            a3m_lines.append(seq)
                            found_any = True
            
            if found_any:
                manual_a3m = "\n".join(a3m_lines)
                print(f"\n   ✅ Manual extraction found sequences")
                print(f"   Total: {(len(a3m_lines) - 2) // 2 + 1} sequences")
            else:
                print("   ❌ No sequences found for manual extraction")
    
    except Exception as e:
        print(f"❌ A3M conversion error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Try with different parameters
    print("\n\nTest 3: Search with Different Parameters")
    print("-" * 40)
    
    try:
        # Request A3M format explicitly
        response2 = await client.search(
            sequence=TEST_SEQUENCE,
            databases=["Uniref30_2302"],  # Just one database
            max_msa_sequences=500,         # More sequences
            e_value=100.0,                 # Very permissive
            output_alignment_formats=["a3m"]  # Request A3M specifically
        )
        
        # Check if format is returned differently
        for db_name, content in response2.alignments.items():
            print(f"Database: {db_name}")
            print(f"Content type: {type(content)}")
            
            if isinstance(content, dict):
                print(f"  Formats: {list(content.keys())}")
                if "a3m" in content:
                    a3m_rec = content["a3m"]
                    if hasattr(a3m_rec, 'alignment'):
                        seqs = a3m_rec.alignment.count('>')
                        print(f"  ✅ A3M format found with {seqs} sequences")
            elif isinstance(content, list):
                print(f"  List with {len(content)} items")
    
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("- If only 1 sequence is found, the MSA search isn't finding homologs")
    print("- This could be due to the sequence being unique or database limitations")
    print("- The A3M conversion itself seems to work, but with no homologs, you only get the query")


if __name__ == "__main__":
    asyncio.run(test_msa_and_a3m())
