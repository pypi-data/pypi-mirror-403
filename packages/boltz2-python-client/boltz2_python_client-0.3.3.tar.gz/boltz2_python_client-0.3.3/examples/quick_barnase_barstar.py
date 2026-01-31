#!/usr/bin/env python3
"""
Quick Barnase-Barstar heterodimer prediction example.

This demonstrates heterodimer prediction with a well-studied protein complex:
- Barnase: Bacterial ribonuclease (110 residues)
- Barstar: Barnase inhibitor (89 residues)
- Known to form a tight 1:1 complex (PDB: 1BRS)

Usage:
    python quick_barnase_barstar.py
"""

import asyncio
from boltz2_client import Boltz2Client, Polymer, PredictionRequest

async def predict_barnase_barstar():
    client = Boltz2Client()
    
    # Barnase sequence (Chain A) - 110 residues
    barnase_seq = "AQVINTFDGVADYLQTYHKLPDNYITKSEAQALGWVASKGNLADVAPGKSIGGDIFSNREGKLPGKSGRTWREADINYTSGFRNSDRILYSSDWLIYKTTDHYQTFTKIR"
    
    # Barstar sequence (Chain B) - 89 residues
    barstar_seq = "KKAVINGEQIRSISDLHQTLKKELALPEYYGENLDALWDCLTGWVEYPLVLEWRQFEQSKQLTENGAESVLQVFR"
    
    print("🧬 Barnase-Barstar Complex")
    print(f"   Barnase: {len(barnase_seq)} residues (ribonuclease)")
    print(f"   Barstar: {len(barstar_seq)} residues (inhibitor)")
    print(f"   Known interaction: High-affinity complex")
    print(f"   Reference PDB: 1BRS\n")
    
    request = PredictionRequest(
        polymers=[
            Polymer(id="A", molecule_type="protein", sequence=barnase_seq),
            Polymer(id="B", molecule_type="protein", sequence=barstar_seq)
        ],
        recycling_steps=5,
        sampling_steps=100
    )
    
    print("🔄 Predicting complex structure...")
    result = await client.predict(request)
    
    # Save CIF file
    with open("barnase_barstar_complex.cif", "w") as f:
        f.write(result.structures[0].structure)
    
    # Print results
    print("\n✅ Complex prediction complete!")
    print(f"📁 Saved to: barnase_barstar_complex.cif")
    print(f"\n📊 Confidence Metrics:")
    print(f"├─ Overall: {result.confidence_scores[0]:.1%}")
    print(f"├─ pTM: {result.ptm_scores[0]:.3f}")
    print(f"├─ ipTM: {result.iptm_scores[0]:.3f}")
    print(f"└─ Complex pLDDT: {result.complex_plddt_scores[0]:.1f}")
    
    # Check interaction quality
    if result.iptm_scores[0] > 0.8:
        print("\n✅ Excellent interface quality - strong interaction predicted!")
        print("   This matches the known high-affinity complex.")
    elif result.iptm_scores[0] > 0.7:
        print("\n✅ Good interface quality - interaction likely!")
    else:
        print("\n⚠️  Lower interface confidence than expected")
    
    # Show per-chain scores
    if len(result.chains_ptm_scores) >= 2:
        print(f"\n📊 Per-chain pTM scores:")
        print(f"├─ Barnase (A): {result.chains_ptm_scores[0]:.3f}")
        print(f"└─ Barstar (B): {result.chains_ptm_scores[1]:.3f}")
    
    return result

# Run it
if __name__ == "__main__":
    asyncio.run(predict_barnase_barstar())
