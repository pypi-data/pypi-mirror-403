#!/usr/bin/env python3
"""
Barnase-Barstar complex prediction with MSA search using GPU MSA NIM.

This demonstrates:
1. Searching for MSAs for both proteins using GPU MSA NIM
2. Using the MSAs for improved structure prediction
3. Comparing results with and without MSA
"""

import asyncio
from pathlib import Path
from boltz2_client import Boltz2Client, Polymer, PredictionRequest
from boltz2_client.msa_search import MSASearchIntegration

# GPU MSA endpoint
MSA_ENDPOINT = "http://10.34.0.226:8000"

# Barnase sequence (110 residues)
BARNASE_SEQ = "AQVINTFDGVADYLQTYHKLPDNYITKSEAQALGWVASKGNLADVAPGKSIGGDIFSNREGKLPGKSGRTWREADINYTSGFRNSDRILYSSDWLIYKTTDHYQTFTKIR"

# Barstar sequence (89 residues)  
BARSTAR_SEQ = "KKAVINGEQIRSISDLHQTLKKELALPEYYGENLDALWDCLTGWVEYPLVLEWRQFEQSKQLTENGAESVLQVFR"


async def predict_without_msa():
    """Predict Barnase-Barstar complex without MSA."""
    print("=== Prediction WITHOUT MSA ===")
    
    client = Boltz2Client()
    
    request = PredictionRequest(
        polymers=[
            Polymer(id="A", molecule_type="protein", sequence=BARNASE_SEQ),
            Polymer(id="B", molecule_type="protein", sequence=BARSTAR_SEQ)
        ],
        recycling_steps=5,
        sampling_steps=100
    )
    
    print("🔄 Predicting structure without MSA...")
    result = await client.predict(request)
    
    # Save structure
    with open("barnase_barstar_no_msa.cif", "w") as f:
        f.write(result.structures[0].structure)
    
    print("✅ Done!")
    print(f"📊 Confidence Metrics (No MSA):")
    print(f"├─ Overall: {result.confidence_scores[0]:.1%}")
    print(f"├─ pTM: {result.ptm_scores[0]:.3f}")
    print(f"├─ ipTM: {result.iptm_scores[0]:.3f}")
    print(f"└─ Complex pLDDT: {result.complex_plddt_scores[0]:.1f}")
    
    return result


async def search_and_save_msas():
    """Search for MSAs for both Barnase and Barstar."""
    print("\n=== MSA Search using GPU MSA NIM ===")
    print(f"Endpoint: {MSA_ENDPOINT}")
    
    # Initialize MSA search
    msa_client = MSASearchClient(endpoint_url=MSA_ENDPOINT)
    msa_integration = MSASearchIntegration(msa_client)
    
    # Create MSA directory
    msa_dir = Path("msas")
    msa_dir.mkdir(exist_ok=True)
    
    # Search MSA for Barnase
    print("\n🔍 Searching MSA for Barnase (Chain A)...")
    try:
        barnase_msa_path = await msa_integration.search_and_save(
            sequence=BARNASE_SEQ,
            output_path=msa_dir / "barnase_msa.a3m",
            output_format="a3m",
            databases=["Uniref30_2302", "colabfold_envdb_202108"],
            max_msa_sequences=500
        )
        print(f"✅ Barnase MSA saved to: {barnase_msa_path}")
    except Exception as e:
        print(f"❌ Barnase MSA search failed: {e}")
        barnase_msa_path = None
    
    # Search MSA for Barstar
    print("\n🔍 Searching MSA for Barstar (Chain B)...")
    try:
        barstar_msa_path = await msa_integration.search_and_save(
            sequence=BARSTAR_SEQ,
            output_path=msa_dir / "barstar_msa.a3m",
            output_format="a3m",
            databases=["Uniref30_2302", "colabfold_envdb_202108"],
            max_msa_sequences=500
        )
        print(f"✅ Barstar MSA saved to: {barstar_msa_path}")
    except Exception as e:
        print(f"❌ Barstar MSA search failed: {e}")
        barstar_msa_path = None
    
    return barnase_msa_path, barstar_msa_path


async def predict_with_msa(barnase_msa_path, barstar_msa_path):
    """Predict Barnase-Barstar complex with MSA."""
    print("\n=== Prediction WITH MSA ===")
    
    client = Boltz2Client()
    
    # Create polymers
    barnase = Polymer(id="A", molecule_type="protein", sequence=BARNASE_SEQ)
    barstar = Polymer(id="B", molecule_type="protein", sequence=BARSTAR_SEQ)
    
    # Load MSAs if available
    from boltz2_client.models import AlignmentFileRecord
    
    if barnase_msa_path and barnase_msa_path.exists():
        with open(barnase_msa_path, "r") as f:
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
    else:
        print("⚠️  No MSA for Barnase")
    
    if barstar_msa_path and barstar_msa_path.exists():
        with open(barstar_msa_path, "r") as f:
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
    else:
        print("⚠️  No MSA for Barstar")
    
    # Create request
    request = PredictionRequest(
        polymers=[barnase, barstar],
        recycling_steps=5,
        sampling_steps=100
    )
    
    print("\n🔄 Predicting structure with MSA...")
    result = await client.predict(request)
    
    # Save structure
    with open("barnase_barstar_with_msa.cif", "w") as f:
        f.write(result.structures[0].structure)
    
    print("✅ Done!")
    print(f"📊 Confidence Metrics (With MSA):")
    print(f"├─ Overall: {result.confidence_scores[0]:.1%}")
    print(f"├─ pTM: {result.ptm_scores[0]:.3f}")
    print(f"├─ ipTM: {result.iptm_scores[0]:.3f}")
    print(f"└─ Complex pLDDT: {result.complex_plddt_scores[0]:.1f}")
    
    return result


async def main():
    """Main workflow."""
    print("🧬 Barnase-Barstar Complex Prediction with MSA Search")
    print("=" * 60)
    print(f"Barnase: {len(BARNASE_SEQ)} residues")
    print(f"Barstar: {len(BARSTAR_SEQ)} residues")
    print(f"MSA Endpoint: {MSA_ENDPOINT}")
    print("=" * 60)
    
    # 1. Predict without MSA (baseline)
    result_no_msa = await predict_without_msa()
    
    # 2. Search for MSAs
    barnase_msa, barstar_msa = await search_and_save_msas()
    
    # 3. Predict with MSA
    result_with_msa = await predict_with_msa(barnase_msa, barstar_msa)
    
    # 4. Compare results
    print("\n=== COMPARISON ===")
    print("Metric         | No MSA  | With MSA | Improvement")
    print("---------------|---------|----------|------------")
    print(f"pTM            | {result_no_msa.ptm_scores[0]:.3f}   | {result_with_msa.ptm_scores[0]:.3f}    | {'+' if result_with_msa.ptm_scores[0] > result_no_msa.ptm_scores[0] else '-'}")
    print(f"ipTM           | {result_no_msa.iptm_scores[0]:.3f}   | {result_with_msa.iptm_scores[0]:.3f}    | {'+' if result_with_msa.iptm_scores[0] > result_no_msa.iptm_scores[0] else '-'}")
    print(f"Complex pLDDT  | {result_no_msa.complex_plddt_scores[0]:.1f}    | {result_with_msa.complex_plddt_scores[0]:.1f}     | {'+' if result_with_msa.complex_plddt_scores[0] > result_no_msa.complex_plddt_scores[0] else '-'}")
    
    if result_with_msa.iptm_scores[0] > result_no_msa.iptm_scores[0]:
        improvement = (result_with_msa.iptm_scores[0] - result_no_msa.iptm_scores[0]) / result_no_msa.iptm_scores[0] * 100
        print(f"\n✅ MSA improved interface confidence by {improvement:.1f}%!")
    
    print("\n📁 Output Files:")
    print("├─ barnase_barstar_no_msa.cif    (baseline)")
    print("├─ barnase_barstar_with_msa.cif  (MSA-enhanced)")
    print("├─ msas/barnase_*.a3m            (Barnase MSA)")
    print("└─ msas/barstar_*.a3m            (Barstar MSA)")
    
    print("\n💡 Visualize in PyMOL:")
    print("pymol barnase_barstar_no_msa.cif barnase_barstar_with_msa.cif")


if __name__ == "__main__":
    asyncio.run(main())
