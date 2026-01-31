#!/usr/bin/env python3
"""
Simple examples of small protein dimers for testing.
"""

import asyncio
from boltz2_client import Boltz2Client, Polymer, PredictionRequest

async def predict_gcn4_homodimer():
    """
    Predict GCN4 leucine zipper homodimer.
    
    GCN4 is a classic coiled-coil forming sequence (33 residues).
    It forms a parallel alpha-helical dimer.
    """
    client = Boltz2Client()
    
    # GCN4 leucine zipper sequence (33 amino acids)
    gcn4_sequence = "RMKQLEDKVEELLSKNYHLENEVARLKKLVGER"
    
    print("=== GCN4 Leucine Zipper Homodimer ===")
    print(f"Sequence length: {len(gcn4_sequence)} residues")
    print(f"Known structure: Parallel coiled-coil dimer")
    print(f"Reference PDB: 2ZTA\n")
    
    # Create homodimer request
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
    
    # Save structure
    with open("gcn4_homodimer.cif", "w") as f:
        f.write(result.structures[0].structure)
    
    print("\n✅ Prediction complete!")
    print(f"📊 Confidence Metrics:")
    print(f"├─ Overall: {result.confidence_scores[0]:.1%}")
    print(f"├─ pTM: {result.ptm_scores[0]:.3f}")
    print(f"└─ ipTM: {result.iptm_scores[0]:.3f}")
    print(f"\n📁 Structure saved to: gcn4_homodimer.cif")
    
    return result


async def predict_max_myc_heterodimer():
    """
    Predict Max-Myc heterodimer (bHLHZ domain).
    
    Max and Myc are transcription factors that form heterodimers.
    Using just the dimerization domains for simplicity.
    """
    client = Boltz2Client()
    
    # Simplified Max bHLHZ domain (60 residues)
    max_sequence = "SDNDDDDEVDVVTNEENNQKAAHDQLERLRQEQQRLEQLISGQGLLSNMQTQPTAILG"
    
    # Simplified Myc bHLHZ domain (58 residues)
    myc_sequence = "SGGGDNDEKRRAHNALERKRRDHIKDSFHSLRDSVPSLQGEKARRAQILDKATEYIQ"
    
    print("\n=== Max-Myc Heterodimer ===")
    print(f"Max length: {len(max_sequence)} residues")
    print(f"Myc length: {len(myc_sequence)} residues")
    print(f"Known structure: Basic helix-loop-helix leucine zipper")
    print(f"Reference PDB: 1NKP\n")
    
    # Create heterodimer request
    request = PredictionRequest(
        polymers=[
            Polymer(id="A", molecule_type="protein", sequence=max_sequence),
            Polymer(id="B", molecule_type="protein", sequence=myc_sequence)
        ],
        recycling_steps=5,
        sampling_steps=100
    )
    
    print("🔄 Predicting structure...")
    result = await client.predict(request)
    
    # Save structure
    with open("max_myc_heterodimer.cif", "w") as f:
        f.write(result.structures[0].structure)
    
    print("\n✅ Prediction complete!")
    print(f"📊 Confidence Metrics:")
    print(f"├─ Overall: {result.confidence_scores[0]:.1%}")
    print(f"├─ pTM: {result.ptm_scores[0]:.3f}")
    print(f"└─ ipTM: {result.iptm_scores[0]:.3f}")
    print(f"\n📁 Structure saved to: max_myc_heterodimer.cif")
    
    return result


async def main():
    """Run both dimer predictions."""
    print("Small Protein Dimer Examples\n")
    print("These are well-characterized protein dimers suitable for testing:")
    print("1. GCN4 - Forms homodimer (2x33 residues)")
    print("2. Max-Myc - Forms heterodimer (60+58 residues)\n")
    
    # Predict both
    gcn4_result = await predict_gcn4_homodimer()
    max_myc_result = await predict_max_myc_heterodimer()
    
    # Compare results
    print("\n=== Summary ===")
    print(f"GCN4 homodimer ipTM: {gcn4_result.iptm_scores[0]:.3f}")
    print(f"Max-Myc heterodimer ipTM: {max_myc_result.iptm_scores[0]:.3f}")
    
    if gcn4_result.iptm_scores[0] > 0.7 and max_myc_result.iptm_scores[0] > 0.7:
        print("\n✅ Both dimers predicted with high interface confidence!")
    
    print("\nVisualize structures with PyMOL:")
    print("  pymol gcn4_homodimer.cif max_myc_heterodimer.cif")


if __name__ == "__main__":
    asyncio.run(main())
