#!/usr/bin/env python3
"""
Quick GCN4 homodimer prediction example - ready to run!

This script demonstrates homodimer prediction with boltz2-python-client.
GCN4 leucine zipper is a classic example of a coiled-coil dimer.

Usage:
    python quick_gcn4_homodimer.py
"""

import asyncio
from boltz2_client import Boltz2Client, Polymer, PredictionRequest

async def predict_gcn4_homodimer():
    client = Boltz2Client()
    
    # GCN4 leucine zipper - forms parallel coiled-coil homodimer (33 residues)
    gcn4_sequence = "RMKQLEDKVEELLSKNYHLENEVARLKKLVGER"
    
    print("🧬 GCN4 Leucine Zipper Homodimer")
    print(f"   Sequence length: {len(gcn4_sequence)} residues")
    print(f"   Known structure: Parallel α-helical coiled-coil")
    print(f"   Reference PDB: 2ZTA\n")
    
    request = PredictionRequest(
        polymers=[
            Polymer(id="A", molecule_type="protein", sequence=gcn4_sequence),
            Polymer(id="B", molecule_type="protein", sequence=gcn4_sequence)
        ],
        recycling_steps=5,
        sampling_steps=100
    )
    
    print("🔄 Predicting structure...")
    result = await client.predict(request)
    
    # Save CIF file
    with open("gcn4_homodimer.cif", "w") as f:
        f.write(result.structures[0].structure)
    
    # Print results
    print("\n✅ Homodimer prediction complete!")
    print(f"📁 Saved to: gcn4_homodimer.cif")
    print(f"\n📊 Confidence Metrics:")
    print(f"├─ Overall: {result.confidence_scores[0]:.1%}")
    print(f"├─ pTM: {result.ptm_scores[0]:.3f}")
    print(f"└─ ipTM: {result.iptm_scores[0]:.3f}")
    
    # Evaluate interface quality
    if result.iptm_scores[0] > 0.8:
        print("\n✅ Excellent interface quality - strong dimer predicted!")
    elif result.iptm_scores[0] > 0.7:
        print("\n✅ Good interface quality - dimer formation likely!")
    else:
        print("\n⚠️  Lower interface confidence")
    
    return result

# Run it
if __name__ == "__main__":
    asyncio.run(predict_gcn4_homodimer())
