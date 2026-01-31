#!/usr/bin/env python3
"""
Quick Barnase-Barstar prediction with MSA search.
Uses GPU MSA NIM to enhance prediction accuracy.
"""

import asyncio
from pathlib import Path
from boltz2_client import Boltz2Client, Polymer, PredictionRequest
from boltz2_client.models import AlignmentFileRecord

# GPU MSA endpoint
MSA_ENDPOINT = "http://10.34.0.226:8000"

# Protein sequences
BARNASE_SEQ = "AQVINTFDGVADYLQTYHKLPDNYITKSEAQALGWVASKGNLADVAPGKSIGGDIFSNREGKLPGKSGRTWREADINYTSGFRNSDRILYSSDWLIYKTTDHYQTFTKIR"
BARSTAR_SEQ = "KKAVINGEQIRSISDLHQTLKKELALPEYYGENLDALWDCLTGWVEYPLVLEWRQFEQSKQLTENGAESVLQVFR"


async def main():
    """Predict Barnase-Barstar with MSA-guided approach."""
    
    print("🧬 Barnase-Barstar Complex with MSA Search")
    print(f"MSA Endpoint: {MSA_ENDPOINT}\n")
    
    # Initialize client
    client = Boltz2Client()
    
    # Configure MSA search
    client.configure_msa_search(
        msa_endpoint_url=MSA_ENDPOINT
    )
    
    # Create output directory
    output_dir = Path("barnase_barstar_msa_results")
    output_dir.mkdir(exist_ok=True)
    
    # Batch MSA search for both sequences
    print("🔍 Searching MSAs for both proteins...")
    
    try:
        sequences = {
            "barnase": BARNASE_SEQ,
            "barstar": BARSTAR_SEQ
        }
        
        # Perform batch MSA search
        msa_files = await client.batch_msa_search(
            sequences=sequences,
            output_dir=output_dir,
            databases=["Uniref30_2302", "colabfold_envdb_202108"],
            max_msa_sequences=500
        )
        
        print(f"✅ MSA search complete!")
        for seq_id, msa_path in msa_files.items():
            print(f"   {seq_id}: {msa_path}")
        
        # Create polymers with MSAs
        polymers = []
        
        # Barnase (Chain A)
        barnase = Polymer(id="A", molecule_type="protein", sequence=BARNASE_SEQ)
        if "barnase" in msa_files and msa_files["barnase"].exists():
            with open(msa_files["barnase"], "r") as f:
                msa_content = f.read()
            barnase.msa = {
                "default": {
                    "a3m": AlignmentFileRecord(
                        alignment=msa_content,
                        format="a3m",
                        rank=0
                    )
                }
            }
            print("✅ Using MSA for Barnase")
        polymers.append(barnase)
        
        # Barstar (Chain B)
        barstar = Polymer(id="B", molecule_type="protein", sequence=BARSTAR_SEQ)
        if "barstar" in msa_files and msa_files["barstar"].exists():
            with open(msa_files["barstar"], "r") as f:
                msa_content = f.read()
            barstar.msa = {
                "default": {
                    "a3m": AlignmentFileRecord(
                        alignment=msa_content,
                        format="a3m",
                        rank=0
                    )
                }
            }
            print("✅ Using MSA for Barstar")
        polymers.append(barstar)
        
        # Predict with MSAs
        print("\n🧬 Predicting structure with MSA enhancement...")
        request = PredictionRequest(
            polymers=polymers,
            recycling_steps=5,
            sampling_steps=100
        )
        
        result = await client.predict(request, save_structures=True, output_dir=output_dir)
        
        print("\n✅ Prediction complete!")
        print(f"📊 Confidence Metrics:")
        print(f"├─ Overall: {result.confidence_scores[0]:.1%}")
        print(f"├─ pTM: {result.ptm_scores[0]:.3f}")
        print(f"├─ ipTM: {result.iptm_scores[0]:.3f} {'⭐' if result.iptm_scores[0] > 0.8 else ''}")
        print(f"└─ Complex pLDDT: {result.complex_plddt_scores[0]:.1f}")
        
        # Check interface quality
        if result.iptm_scores[0] > 0.8:
            print("\n🎯 Excellent interface prediction - high-confidence complex!")
        elif result.iptm_scores[0] > 0.7:
            print("\n✅ Good interface prediction - proteins likely interact")
        
        # Show per-chain scores
        if len(result.chains_ptm_scores) >= 2:
            print(f"\n📊 Per-chain pTM:")
            print(f"├─ Barnase (A): {result.chains_ptm_scores[0]:.3f}")
            print(f"└─ Barstar (B): {result.chains_ptm_scores[1]:.3f}")
        
        print(f"\n📁 Results saved in: {output_dir}/")
        print("├─ structure_0.cif      (Complex structure)")
        print("├─ barnase_*.a3m       (Barnase MSA)")
        print("└─ barstar_*.a3m       (Barstar MSA)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nFalling back to prediction without MSA...")
        
        # Fallback: Direct prediction without MSA search
        request = PredictionRequest(
            polymers=[
                Polymer(id="A", molecule_type="protein", sequence=BARNASE_SEQ),
                Polymer(id="B", molecule_type="protein", sequence=BARSTAR_SEQ)
            ],
            recycling_steps=5,
            sampling_steps=100
        )
        
        result = await client.predict(request)
        
        # Save structure
        output_file = output_dir / "barnase_barstar_complex.cif"
        with open(output_file, "w") as f:
            f.write(result.structures[0].structure)
        
        print(f"✅ Prediction complete (without MSA)")
        print(f"📁 Structure saved to: {output_file}")
        print(f"📊 ipTM: {result.iptm_scores[0]:.3f}")


if __name__ == "__main__":
    asyncio.run(main())