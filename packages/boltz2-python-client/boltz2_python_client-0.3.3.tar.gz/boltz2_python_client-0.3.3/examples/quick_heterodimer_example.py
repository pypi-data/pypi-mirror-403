#!/usr/bin/env python3
"""
Quick heterodimer prediction example - ready to run!

This script demonstrates multimer prediction with boltz2-python-client.
It predicts the structure of two different proteins interacting.

Usage:
    python quick_heterodimer_example.py
"""

import asyncio
from boltz2_client import Boltz2Client, Polymer, PredictionRequest

async def predict_heterodimer():
    client = Boltz2Client()
    
    # Using GCN4 leucine zipper - a well-studied coiled-coil homodimer (33 residues each)
    gcn4_sequence = "RMKQLEDKVEELLSKNYHLENEVARLKKLVGER"
    
    request = PredictionRequest(
        polymers=[
            Polymer(id="A", molecule_type="protein", 
                   sequence=gcn4_sequence),
            Polymer(id="B", molecule_type="protein",
                   sequence=gcn4_sequence)  # Same sequence for homodimer
        ],
        recycling_steps=5,
        sampling_steps=100
    )
    
    # Predict
    result = await client.predict(request)
    
    # Save CIF file
    with open("heterodimer.cif", "w") as f:
        f.write(result.structures[0].structure)
    
    # Print all scores
    print("✅ Heterodimer prediction complete!")
    print(f"📁 Saved to: heterodimer.cif")
    print(f"\n📊 Confidence Metrics:")
    print(f"Overall: {result.confidence_scores[0]:.1%}")
    print(f"pTM: {result.ptm_scores[0]:.3f}")
    print(f"Interface pTM: {result.iptm_scores[0]:.3f}")
    
    # Check if good quality
    if result.iptm_scores[0] > 0.7:
        print("✅ Good interface quality - proteins likely interact!")
    else:
        print("⚠️  Low interface confidence - interaction uncertain")
    
    return result

# Run it
if __name__ == "__main__":
    asyncio.run(predict_heterodimer())
