#!/usr/bin/env python3
"""
Example showing all output files you can generate from multimer prediction.
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from boltz2_client import Boltz2Client, Polymer, PredictionRequest

async def predict_and_save_all_outputs():
    """Demonstrate saving all possible outputs from multimer prediction."""
    
    client = Boltz2Client()
    
    # Create output directory
    output_dir = Path("multimer_results")
    output_dir.mkdir(exist_ok=True)
    
    # Define proteins
    request = PredictionRequest(
        polymers=[
            Polymer(id="A", molecule_type="protein", 
                   sequence="MKTVRQERLKSIVRILERSKEPVSGAQLAEELSVSRQVIVQDIAYLRSLGYNIVATPRGYVLAGG"),
            Polymer(id="B", molecule_type="protein",
                   sequence="MVTPEGNVSLVDESLLVGVTDEDRAVRSAHQFYERLIGLWAPAVMEAAHELGVFAALAEAPAD")
        ],
        recycling_steps=5,
        sampling_steps=100
    )
    
    print("🔄 Running prediction...")
    result = await client.predict(request)
    print("✅ Prediction complete!")
    
    # Generate timestamp for unique filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"heterodimer_{timestamp}"
    
    # 1. Save CIF structure file (ALWAYS save this!)
    cif_path = output_dir / f"{base_name}.cif"
    with open(cif_path, "w") as f:
        f.write(result.structures[0].structure)
    print(f"📁 Structure saved: {cif_path}")
    
    # 2. Save all confidence scores as JSON
    scores_path = output_dir / f"{base_name}_scores.json"
    scores = {
        "prediction_timestamp": timestamp,
        "overall_confidence": result.confidence_scores[0],
        "ptm": result.ptm_scores[0],
        "iptm": result.iptm_scores[0],
        "complex_plddt": result.complex_plddt_scores[0],
        "per_chain_ptm": {
            f"chain_{chr(65+i)}": score 
            for i, score in enumerate(result.chains_ptm_scores)
        },
        "pairwise_interactions": result.pair_chains_iptm_scores
    }
    with open(scores_path, "w") as f:
        json.dump(scores, f, indent=2)
    print(f"📊 Scores saved: {scores_path}")
    
    # 3. Save human-readable summary
    summary_path = output_dir / f"{base_name}_summary.txt"
    with open(summary_path, "w") as f:
        f.write(f"Multimer Prediction Summary\n")
        f.write(f"Generated: {timestamp}\n")
        f.write("=" * 50 + "\n\n")
        
        f.write("SEQUENCES:\n")
        f.write(f"Chain A ({len(request.polymers[0].sequence)} residues):\n")
        f.write(f"{request.polymers[0].sequence}\n\n")
        f.write(f"Chain B ({len(request.polymers[1].sequence)} residues):\n")
        f.write(f"{request.polymers[1].sequence}\n\n")
        
        f.write("CONFIDENCE METRICS:\n")
        f.write(f"Overall Confidence: {result.confidence_scores[0]:.1%}\n")
        f.write(f"pTM Score: {result.ptm_scores[0]:.3f}\n")
        f.write(f"Interface pTM (ipTM): {result.iptm_scores[0]:.3f}\n")
        f.write(f"Complex pLDDT: {result.complex_plddt_scores[0]:.1f}\n\n")
        
        f.write("PER-CHAIN SCORES:\n")
        for i, score in enumerate(result.chains_ptm_scores):
            f.write(f"Chain {chr(65+i)} pTM: {score:.3f}\n")
        
        f.write("\nINTERFACE ANALYSIS:\n")
        if result.iptm_scores[0] > 0.8:
            f.write("✅ Excellent interface quality - strong interaction predicted\n")
        elif result.iptm_scores[0] > 0.7:
            f.write("✅ Good interface quality - likely interaction\n")
        else:
            f.write("⚠️  Low interface confidence - interaction uncertain\n")
    
    print(f"📝 Summary saved: {summary_path}")
    
    # 4. Save input configuration for reproducibility
    config_path = output_dir / f"{base_name}_config.json"
    config = {
        "timestamp": timestamp,
        "request": {
            "polymers": [
                {"id": p.id, "sequence": p.sequence, "type": p.molecule_type}
                for p in request.polymers
            ],
            "recycling_steps": request.recycling_steps,
            "sampling_steps": request.sampling_steps
        }
    }
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    print(f"⚙️  Config saved: {config_path}")
    
    print(f"\n✅ All outputs saved to: {output_dir}/")
    return result

if __name__ == "__main__":
    asyncio.run(predict_and_save_all_outputs())
