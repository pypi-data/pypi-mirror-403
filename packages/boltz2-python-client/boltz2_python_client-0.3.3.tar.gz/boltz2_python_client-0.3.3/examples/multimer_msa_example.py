#!/usr/bin/env python3
"""
Example demonstrating MSA handling for multimer predictions in Boltz2.

IMPORTANT: Each protein chain gets its own MSA file.
"""

import asyncio
from pathlib import Path
from boltz2_client import Boltz2Client, Polymer, PredictionRequest

async def multimer_with_individual_msas():
    """
    Show how each chain in a multimer can have its own MSA file.
    
    KEY POINT: Boltz2 NIM accepts ONE MSA per polymer/chain.
    """
    client = Boltz2Client()
    
    # Define Chain A with its MSA
    chain_A = Polymer(
        id="A",
        molecule_type="protein",
        sequence="MKTVRQERLKSIVRILERSKEPVSGAQLAEELSVSRQVIVQDIAYLRSLGYNIVATPRGYVLAGG",
        # MSA for Chain A - loaded from file
        msa=None  # Will be added below
    )
    
    # Define Chain B with its MSA
    chain_B = Polymer(
        id="B",
        molecule_type="protein",
        sequence="MVTPEGNVSLVDESLLVGVTDEDRAVRSAHQFYERLIGLWAPAVMEAAHELGVFAALAEAPAD",
        # MSA for Chain B - loaded from file
        msa=None  # Will be added below
    )
    
    # Load MSA for Chain A if available
    msa_a_path = Path("msas/chain_A.a3m")
    if msa_a_path.exists():
        with open(msa_a_path, "r") as f:
            msa_content_a = f.read()
        
        from boltz2_client.models import AlignmentFileRecord
        chain_A.msa = {
            "default": {
                "a3m": AlignmentFileRecord(
                    alignment=msa_content_a,
                    format="a3m",
                    rank=0
                )
            }
        }
        print("✅ Loaded MSA for Chain A")
    else:
        print("⚠️  No MSA file found for Chain A - proceeding without MSA")
    
    # Load MSA for Chain B if available
    msa_b_path = Path("msas/chain_B.a3m")
    if msa_b_path.exists():
        with open(msa_b_path, "r") as f:
            msa_content_b = f.read()
        
        chain_B.msa = {
            "default": {
                "a3m": AlignmentFileRecord(
                    alignment=msa_content_b,
                    format="a3m",
                    rank=0
                )
            }
        }
        print("✅ Loaded MSA for Chain B")
    else:
        print("⚠️  No MSA file found for Chain B - proceeding without MSA")
    
    # Create prediction request
    request = PredictionRequest(
        polymers=[chain_A, chain_B],
        recycling_steps=5,
        sampling_steps=100,
        concatenate_msas=False  # Each chain uses its own MSA
    )
    
    print("\n🔄 Predicting heterodimer structure with individual MSAs...")
    result = await client.predict(request)
    
    # Save results
    with open("heterodimer_with_msa.cif", "w") as f:
        f.write(result.structures[0].structure)
    
    print("\n✅ Prediction complete!")
    print(f"📊 Confidence Metrics:")
    print(f"├─ pTM: {result.ptm_scores[0]:.3f}")
    print(f"├─ ipTM: {result.iptm_scores[0]:.3f}")
    print(f"└─ Complex pLDDT: {result.complex_plddt_scores[0]:.1f}")
    
    return result


async def yaml_multimer_with_msas():
    """
    Demonstrate YAML configuration for multimer with MSAs.
    """
    yaml_content = """
version: 1
sequences:
  - protein:
      id: A
      sequence: "MKTVRQERLKSIVRILERSKEPVSGAQLAEELSVSRQVIVQDIAYLRSLGYNIVATPRGYVLAGG"
      msa: "chain_A.a3m"  # MSA file for chain A
  - protein:
      id: B
      sequence: "MVTPEGNVSLVDESLLVGVTDEDRAVRSAHQFYERLIGLWAPAVMEAAHELGVFAALAEAPAD"
      msa: "chain_B.a3m"  # MSA file for chain B
"""
    
    # Save YAML config
    with open("multimer_config.yaml", "w") as f:
        f.write(yaml_content)
    
    print("\n📄 Using YAML configuration for multimer with MSAs...")
    
    client = Boltz2Client()
    
    # Predict from YAML (assumes MSA files are in msas/ directory)
    result = await client.predict_from_yaml_file(
        "multimer_config.yaml",
        msa_dir=Path("msas/")  # Directory containing chain_A.a3m and chain_B.a3m
    )
    
    print("✅ YAML-based prediction complete!")
    print(f"📊 ipTM score: {result.iptm_scores[0]:.3f}")
    
    return result


async def concatenated_msa_example():
    """
    Show the concatenate_msas option for related sequences.
    
    IMPORTANT: This is different from individual MSAs per chain!
    When concatenate_msas=True, MSAs from multiple chains are merged.
    """
    client = Boltz2Client()
    
    # Two related proteins (e.g., from same family)
    proteins = [
        Polymer(
            id="A",
            molecule_type="protein", 
            sequence="MKTVRQERLKSIVRILERSKEPVSGAQLAEELSVSRQVIVQDIAYLRSLGYNIVATPRGYVLAGG"
            # MSA would be loaded here
        ),
        Polymer(
            id="B",
            molecule_type="protein",
            sequence="MKTVRQERLKSIVRILERSKEPVSGAQLAEELSVSRQVIVQDIAYLRSLGYNIVATPRGYVLAGG"
            # Same or very similar sequence
        )
    ]
    
    request = PredictionRequest(
        polymers=proteins,
        recycling_steps=5,
        sampling_steps=100,
        concatenate_msas=True  # Merge MSAs from both chains
    )
    
    print("\n🔄 Predicting with concatenated MSAs...")
    result = await client.predict(request)
    
    print("✅ Prediction with concatenated MSAs complete!")
    print(f"📊 ipTM: {result.iptm_scores[0]:.3f}")
    
    return result


# Summary of MSA handling in Boltz2 NIM
print("""
=== MSA Handling in Boltz2 NIM for Multimers ===

1. **Individual MSAs per Chain** (Most Common)
   - Each polymer/chain can have its own MSA file
   - Chain A gets chain_A.a3m, Chain B gets chain_B.a3m
   - Set concatenate_msas=False (default)

2. **MSA File Structure**
   - One MSA per polymer object
   - MSA is attached to the Polymer's 'msa' field
   - Format: {"database_name": {"format": AlignmentFileRecord}}

3. **Concatenated MSAs** (Special Case)
   - For related/homologous sequences
   - Set concatenate_msas=True
   - Merges MSAs from multiple chains

4. **File Formats Supported**
   - A3M (most common)
   - Stockholm (.sto)
   - FASTA alignment
   - CSV

5. **YAML Configuration**
   - Each protein entry can specify its MSA file
   - MSA files are loaded relative to msa_dir

ANSWER: Yes, Boltz2 NIM accepts multiple MSA files for multimeric 
protein complex predictions - one MSA file per chain!
""")

if __name__ == "__main__":
    # Run the example
    asyncio.run(multimer_with_individual_msas())
