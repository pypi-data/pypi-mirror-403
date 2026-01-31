#!/usr/bin/env python3
"""
Test script to diagnose Boltz2 NIM server issues.
Run this to check what features your server supports.
"""

import asyncio
from boltz2_client import Boltz2Client, Polymer, Ligand, PredictionRequest

# Update this with your Boltz2 endpoint
BOLTZ2_ENDPOINT = "http://localhost:8000"

# Test sequences
SHORT_PROTEIN = "MKTVRQERLKSIVRILERSKEPVSGAQ"  # 28 residues
MEDIUM_PROTEIN = "MKTVRQERLKSIVRILERSKEPVSGAQLAEELSVSRQVIVQDIAYLRSLGYNIVATPRGYVLAGG"  # 66 residues
TEST_LIGAND = "CC(=O)OC1=CC=CC=C1C(=O)O"  # Aspirin


async def test_basic_prediction():
    """Test 1: Basic protein structure prediction."""
    print("=" * 60)
    print("TEST 1: Basic Protein Structure Prediction")
    print("=" * 60)
    
    try:
        client = Boltz2Client(base_url=BOLTZ2_ENDPOINT)
        polymer = Polymer(id="A", molecule_type="protein", sequence=SHORT_PROTEIN)
        request = PredictionRequest(
            polymers=[polymer],
            recycling_steps=1,
            sampling_steps=10
        )
        
        print(f"Predicting structure for {len(SHORT_PROTEIN)} residue protein...")
        result = await client.predict(request)
        print(f"✅ SUCCESS - pTM: {result.ptm_scores[0]:.3f}")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


async def test_protein_ligand():
    """Test 2: Protein-ligand complex prediction."""
    print("\n" + "=" * 60)
    print("TEST 2: Protein-Ligand Complex")
    print("=" * 60)
    
    try:
        client = Boltz2Client(base_url=BOLTZ2_ENDPOINT)
        polymer = Polymer(id="A", molecule_type="protein", sequence=MEDIUM_PROTEIN)
        ligand = Ligand(id="LIG", smiles=TEST_LIGAND, predict_affinity=False)
        request = PredictionRequest(
            polymers=[polymer],
            ligands=[ligand],
            recycling_steps=2,
            sampling_steps=25
        )
        
        print(f"Predicting complex: {len(MEDIUM_PROTEIN)} residue protein + ligand...")
        result = await client.predict(request)
        print(f"✅ SUCCESS - pTM: {result.ptm_scores[0]:.3f}")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


async def test_affinity_prediction():
    """Test 3: Affinity prediction."""
    print("\n" + "=" * 60)
    print("TEST 3: Affinity Prediction")
    print("=" * 60)
    
    try:
        client = Boltz2Client(base_url=BOLTZ2_ENDPOINT)
        polymer = Polymer(id="A", molecule_type="protein", sequence=MEDIUM_PROTEIN)
        ligand = Ligand(id="LIG", smiles=TEST_LIGAND, predict_affinity=True)
        request = PredictionRequest(
            polymers=[polymer],
            ligands=[ligand],
            recycling_steps=2,
            sampling_steps=25,
            sampling_steps_affinity=50,
            diffusion_samples_affinity=2,
            affinity_mw_correction=True
        )
        
        print("Predicting with affinity (reduced parameters)...")
        result = await client.predict(request)
        
        if result.affinities and "LIG" in result.affinities:
            aff = result.affinities["LIG"]
            print(f"✅ SUCCESS - pIC50: {aff.affinity_pic50[0]:.2f}")
        else:
            print("✅ Structure predicted but no affinity scores returned")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


async def test_large_complex():
    """Test 4: Larger protein-ligand with standard parameters."""
    print("\n" + "=" * 60)
    print("TEST 4: Standard Parameters (Larger Complex)")
    print("=" * 60)
    
    try:
        client = Boltz2Client(base_url=BOLTZ2_ENDPOINT)
        
        # 150 residue protein
        large_protein = MEDIUM_PROTEIN * 2 + SHORT_PROTEIN
        
        polymer = Polymer(id="A", molecule_type="protein", sequence=large_protein)
        ligand = Ligand(id="LIG", smiles=TEST_LIGAND, predict_affinity=False)
        request = PredictionRequest(
            polymers=[polymer],
            ligands=[ligand],
            recycling_steps=3,
            sampling_steps=50
        )
        
        print(f"Predicting complex: {len(large_protein)} residue protein + ligand...")
        result = await client.predict(request)
        print(f"✅ SUCCESS - pTM: {result.ptm_scores[0]:.3f}")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        if "DataLoader worker" in str(e):
            print("\n⚠️  Server resource issue detected!")
            print("   Possible causes:")
            print("   - Insufficient GPU memory")
            print("   - Server needs restart")
            print("   - Too many concurrent requests")
        return False


async def main():
    """Run all tests."""
    print(f"🔍 Testing Boltz2 NIM Server: {BOLTZ2_ENDPOINT}")
    print("This will help identify what your server can handle.\n")
    
    results = {
        "Basic prediction": await test_basic_prediction(),
        "Protein-ligand": await test_protein_ligand(),
        "Affinity prediction": await test_affinity_prediction(),
        "Large complex": await test_large_complex()
    }
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test:.<30} {status}")
    
    # Recommendations
    print("\n📋 RECOMMENDATIONS:")
    
    if not results["Basic prediction"]:
        print("❌ Server is not responding. Check:")
        print("   - Is Boltz2 NIM running?")
        print("   - Is the endpoint URL correct?")
        print("   - Check server logs")
    
    elif not results["Large complex"]:
        print("⚠️  Server has resource limitations. Try:")
        print("   - Reducing protein size (<150 residues)")
        print("   - Lowering sampling_steps")
        print("   - Restarting the server")
        print("   - Checking GPU memory (nvidia-smi)")
    
    elif not results["Affinity prediction"]:
        print("⚠️  Affinity prediction issues. Try:")
        print("   - Reducing sampling_steps_affinity (<100)")
        print("   - Reducing diffusion_samples_affinity (<3)")
        print("   - Disabling affinity prediction")
    
    else:
        print("✅ Server is working well!")
        print("   You can run complex predictions with confidence.")
    
    print(f"\n💡 For CDK4-Palbociclib (295 residues):")
    if results["Large complex"] and results["Affinity prediction"]:
        print("   Full prediction with MSA and affinity should work.")
    elif results["Large complex"]:
        print("   Try without affinity prediction first.")
    else:
        print("   Consider using a shorter CDK4 fragment or disabling MSA.")


if __name__ == "__main__":
    asyncio.run(main())
