#!/usr/bin/env python3
"""
Debug script to test MSA search and A3M conversion.
"""

import asyncio
import json
from pathlib import Path
from boltz2_client.msa_search import MSASearchClient

# GPU MSA endpoint
MSA_ENDPOINT = "http://10.34.0.226:8000"

# Test with a shorter CDK4 fragment
CDK4_FRAGMENT = "MATSRYEPVAEIGVGAYGTVYKARDPHSGHFVALKSVRVPNGGGGGGGLP"  # 51 residues


async def debug_msa_search():
    """Debug MSA search response structure."""
    print("🔍 Debugging MSA Search and A3M Conversion")
    print("=" * 60)
    print(f"Endpoint: {MSA_ENDPOINT}")
    print(f"Test sequence: {len(CDK4_FRAGMENT)} residues")
    print(f"Sequence: {CDK4_FRAGMENT}\n")
    
    try:
        # Initialize MSA client
        msa_client = MSASearchClient(endpoint_url=MSA_ENDPOINT)
        
        # Search with different parameters
        print("📡 Performing MSA search...")
        msa_response = await msa_client.search(
            sequence=CDK4_FRAGMENT,
            databases=["Uniref30_2302", "colabfold_envdb_202108"],
            max_msa_sequences=100,
            e_value=10.0,  # More permissive E-value
            output_alignment_formats=["a3m", "fasta"]  # Request multiple formats
        )
        
        # Debug response structure
        print("\n📊 MSA Response Structure:")
        print(f"Response type: {type(msa_response)}")
        print(f"Has alignments: {'alignments' in msa_response.__dict__}")
        
        if hasattr(msa_response, 'alignments'):
            print(f"Number of databases: {len(msa_response.alignments)}")
            for db_name, alignments in msa_response.alignments.items():
                print(f"\n  Database: {db_name}")
                print(f"  Type of alignments: {type(alignments)}")
                
                # Check if alignments is a list
                if isinstance(alignments, list):
                    print(f"  Number of sequences: {len(alignments)}")
                    
                    # Examine first few alignments
                    for i, alignment in enumerate(alignments[:3]):
                        print(f"\n  Alignment {i}:")
                        print(f"    Type: {type(alignment)}")
                        print(f"    Attributes: {dir(alignment)}")
                        
                        # Try different attribute names
                        for attr in ['sequence', 'aligned_sequence', 'alignment', 'seq']:
                            if hasattr(alignment, attr):
                                seq = getattr(alignment, attr)
                                print(f"    {attr}: {seq[:50]}..." if len(seq) > 50 else f"    {attr}: {seq}")
                        
                        # Check for metadata
                        for attr in ['description', 'e_value', 'score', 'identity']:
                            if hasattr(alignment, attr):
                                print(f"    {attr}: {getattr(alignment, attr)}")
                
                # Check if alignments is a dict (format -> content)
                elif isinstance(alignments, dict):
                    print(f"  Formats available: {list(alignments.keys())}")
                    for fmt, content in alignments.items():
                        print(f"    Format: {fmt}")
                        print(f"    Type: {type(content)}")
                        if hasattr(content, 'alignment'):
                            print(f"    Content preview: {content.alignment[:200]}...")
        
        # Try the MSAFormatConverter approach
        print("\n🔧 Testing MSAFormatConverter:")
        from boltz2_client.msa_search import MSAFormatConverter
        
        try:
            a3m_content = MSAFormatConverter.extract_alignment(msa_response, "a3m")
            if a3m_content:
                print(f"✅ A3M extraction successful!")
                print(f"   Length: {len(a3m_content)} characters")
                print(f"   Sequences: {a3m_content.count('>')}")
                print("\n   First 500 characters:")
                print(a3m_content[:500])
            else:
                print("❌ No A3M content extracted")
        except Exception as e:
            print(f"❌ MSAFormatConverter error: {e}")
        
        # Manual A3M construction
        print("\n🛠️ Manual A3M Construction:")
        a3m_lines = [f">query", CDK4_FRAGMENT]
        seq_count = 0
        
        for db_name, alignments in msa_response.alignments.items():
            if isinstance(alignments, list):
                for i, alignment in enumerate(alignments):
                    # Try to get sequence
                    seq = None
                    for attr in ['sequence', 'aligned_sequence', 'alignment']:
                        if hasattr(alignment, attr):
                            seq = getattr(alignment, attr)
                            break
                    
                    if seq and seq != CDK4_FRAGMENT:
                        a3m_lines.append(f">{db_name}_{i}")
                        a3m_lines.append(seq)
                        seq_count += 1
                        
                        if seq_count < 5:  # Show first few
                            print(f"   Added: {db_name}_{i} ({len(seq)} residues)")
        
        manual_a3m = "\n".join(a3m_lines)
        print(f"\n✅ Manual A3M created:")
        print(f"   Total sequences: {(len(a3m_lines) - 2) // 2 + 1}")
        print(f"   File size: {len(manual_a3m)} bytes")
        
        # Save debug outputs
        output_dir = Path("debug_msa_output")
        output_dir.mkdir(exist_ok=True)
        
        # Save response as JSON for inspection
        response_dict = {
            "databases": list(msa_response.alignments.keys()),
            "alignment_counts": {db: len(aligns) if isinstance(aligns, list) else "dict" 
                               for db, aligns in msa_response.alignments.items()}
        }
        
        with open(output_dir / "msa_response_debug.json", "w") as f:
            json.dump(response_dict, f, indent=2)
        
        # Save manual A3M
        with open(output_dir / "manual.a3m", "w") as f:
            f.write(manual_a3m)
        
        print(f"\n📁 Debug files saved to: {output_dir}/")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_direct_format_request():
    """Test requesting specific output formats directly."""
    print("\n\n🔬 Testing Direct Format Request")
    print("=" * 60)
    
    try:
        msa_client = MSASearchClient(endpoint_url=MSA_ENDPOINT)
        
        # Search requesting only A3M format
        print("Requesting A3M format directly...")
        response = await msa_client.search(
            sequence=CDK4_FRAGMENT,
            databases=["Uniref30_2302"],
            max_msa_sequences=50,
            e_value=10.0,
            output_alignment_formats=["a3m"]
        )
        
        # Check if we get the format directly
        print("\nChecking response for A3M content...")
        
        # Method 1: Check alignments structure
        for db_name, content in response.alignments.items():
            print(f"\nDatabase: {db_name}")
            if isinstance(content, dict) and "a3m" in content:
                print("✅ Found A3M in response!")
                a3m_record = content["a3m"]
                if hasattr(a3m_record, 'alignment'):
                    print(f"   A3M content length: {len(a3m_record.alignment)}")
                    print(f"   Preview: {a3m_record.alignment[:200]}...")
                    
                    # Save it
                    with open("debug_msa_output/direct_a3m.a3m", "w") as f:
                        f.write(a3m_record.alignment)
                    print("   Saved to: debug_msa_output/direct_a3m.a3m")
        
    except Exception as e:
        print(f"❌ Error in direct format test: {e}")


if __name__ == "__main__":
    print("CDK4 MSA Debug Script")
    print("=" * 60)
    
    # Run both tests
    asyncio.run(debug_msa_search())
    asyncio.run(test_direct_format_request())
