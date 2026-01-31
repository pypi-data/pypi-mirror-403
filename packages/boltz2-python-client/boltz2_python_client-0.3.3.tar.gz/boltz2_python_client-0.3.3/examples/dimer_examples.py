#!/usr/bin/env python3
"""
Example protein sequences that form dimers - suitable for testing multimer predictions.
"""

# Example 1: GCN4 Leucine Zipper (Homodimer)
# A classic coiled-coil dimerization domain from yeast
# PDB examples: 1ZIK, 2ZTA
GCN4_LEUCINE_ZIPPER = {
    "name": "GCN4 Leucine Zipper",
    "type": "homodimer",
    "length": 33,
    "sequence": "RMKQLEDKVEELLSKNYHLENEVARLKKLVGER",
    "description": "Classic leucine zipper that forms a parallel coiled-coil homodimer",
    "pdb": "2ZTA"
}

# Example 2: Max and Myc Basic Helix-Loop-Helix Leucine Zipper (Heterodimer)
# Well-studied transcription factor heterodimer
# PDB example: 1NKP
MAX_MYCD = {
    "name": "Max/Myc heterodimer",
    "type": "heterodimer",
    "chain_A": {
        "name": "Max bHLHZ",
        "length": 92,
        "sequence": "SDNDDDDEVDVVTNEENNQKAAHDQLERLRQEQQRLEQLISGQGLLSNMQTQPTAILG"
    },
    "chain_B": {
        "name": "Myc bHLHZ", 
        "length": 88,
        "sequence": "SGGGDNDEKRRAHNALERKRRDHIKDSFHSLRDSVPSLQGEKARRAQILDKATEYIQ"
    },
    "description": "Basic helix-loop-helix leucine zipper transcription factor heterodimer",
    "pdb": "1NKP"
}

# Example 3: CREB/ATF-1 bZIP domain (Homodimer)
# Another transcription factor dimerization domain
# PDB example: 1DH3
CREB_BZIP = {
    "name": "CREB bZIP domain",
    "type": "homodimer", 
    "length": 57,
    "sequence": "SQKRREILSRRPSYRKILNDLSSDAPGVPRIEEEKSEEETSAPAITTVTVPTPIY",
    "description": "Basic leucine zipper (bZIP) domain that forms homodimer",
    "pdb": "1DH3"
}

# Example 4: p53 DNA-binding domain (forms dimers and tetramers)
# Tumor suppressor protein domain
# PDB example: 2AC0 (dimer), 3SAK (tetramer)
P53_DBD = {
    "name": "p53 DNA-binding domain",
    "type": "homodimer/tetramer",
    "length": 94,
    "sequence": ("SSSVPSQKTYQGSYGFRLGFLHSGTAKSVTCTYSPALNKMFCQLAKTCPVQLWVDSTPPPGTRVRAMAIYKQSQH"
                 "MTEVVRRCPHHERCSD"),
    "description": "p53 tumor suppressor DNA-binding domain - can form dimers",
    "pdb": "2AC0"
}

# Example 5: Barnase-Barstar complex (Heterodimer)
# Classic protein-protein interaction pair
# PDB example: 1BRS
BARNASE_BARSTAR = {
    "name": "Barnase-Barstar complex",
    "type": "heterodimer",
    "barnase": {
        "name": "Barnase",
        "length": 110,
        "sequence": ("AQVINTFDGVADYLQTYHKLPDNYITKSEAQALGWVASKGNLADVAPGKSIGGDIFSNREGKLPGKSGRTWREADINYTSGFRNSDRILYSSDWLIYKTTDHYQTFTKIR"),
        "description": "Bacterial ribonuclease"
    },
    "barstar": {
        "name": "Barstar",
        "length": 89,
        "sequence": "KKAVINGEQIRSISDLHQTLKKELALPEYYGENLDALWDCLTGWVEYPLVLEWRQFEQSKQLTENGAESVLQVFR",
        "description": "Barnase inhibitor"
    },
    "description": "Well-studied protein-protein interaction complex",
    "pdb": "1BRS"
}

# Recommended examples for testing
print("=== Recommended Protein Dimer Examples ===\n")

print("1. SIMPLE HOMODIMER (33 residues each):")
print(f"   {GCN4_LEUCINE_ZIPPER['name']}")
print(f"   Sequence: {GCN4_LEUCINE_ZIPPER['sequence']}")
print(f"   Description: {GCN4_LEUCINE_ZIPPER['description']}")
print(f"   PDB: {GCN4_LEUCINE_ZIPPER['pdb']}\n")

print("2. HETERODIMER (92 + 88 residues):")
print(f"   {MAX_MYCD['name']}")
print(f"   Chain A (Max): {MAX_MYCD['chain_A']['sequence']}")
print(f"   Chain B (Myc): {MAX_MYCD['chain_B']['sequence']}")
print(f"   Description: {MAX_MYCD['description']}")
print(f"   PDB: {MAX_MYCD['pdb']}\n")

print("3. PROTEIN-PROTEIN INTERACTION (110 + 89 residues):")
print(f"   {BARNASE_BARSTAR['name']}")
print(f"   Barnase: {BARNASE_BARSTAR['barnase']['sequence']}")
print(f"   Barstar: {BARNASE_BARSTAR['barstar']['sequence']}")
print(f"   Description: {BARNASE_BARSTAR['description']}")
print(f"   PDB: {BARNASE_BARSTAR['pdb']}")

# Example usage with boltz2_client
example_code = '''
# Example: Predict GCN4 homodimer
import asyncio
from boltz2_client import Boltz2Client, Polymer, PredictionRequest

async def predict_gcn4_homodimer():
    client = Boltz2Client()
    
    # GCN4 leucine zipper sequence
    gcn4_seq = "RMKQLEDKVEELLSKNYHLENEVARLKKLVGER"
    
    # Create two copies for homodimer
    request = PredictionRequest(
        polymers=[
            Polymer(id="A", molecule_type="protein", sequence=gcn4_seq),
            Polymer(id="B", molecule_type="protein", sequence=gcn4_seq)
        ],
        recycling_steps=5,
        sampling_steps=100
    )
    
    result = await client.predict(request)
    
    with open("gcn4_homodimer.cif", "w") as f:
        f.write(result.structures[0].structure)
    
    print(f"ipTM score: {result.iptm_scores[0]:.3f}")
    return result

# Run prediction
asyncio.run(predict_gcn4_homodimer())
'''

print(f"\n{'='*50}")
print("EXAMPLE CODE:")
print('='*50)
print(example_code)
