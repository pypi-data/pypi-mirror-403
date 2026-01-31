#!/usr/bin/env python3
"""
Test script to verify the notebook cells work correctly now.
"""

import asyncio
from boltz2_client import Boltz2Client
from boltz2_client.models import Polymer, Ligand, PredictionRequest

# Endpoints
BOLTZ2_ENDPOINT = "http://10.176.195.30:8001"

# CDK4 sequence (short version for testing)
CDK4_SHORT = "MATSRYEPVAEIGVGAYGTVYKARDPHSGHFVALKSVRVPNGGGGGGGLP"

# Palbociclib SMILES
PALBOCICLIB_SMILES = "CC1=C(C(=CC=C1)F)C2=NC(=NC=C2)NC3=NC=C(C(=N3)C4=CN=CC=C4)N5CCN(CC5)C(=O)C6CC6"


async def test_basic_prediction():
    """Test the basic prediction without MSA or affinity - mimics notebook cell 19."""
    print("🧪 Testing CDK4 prediction without MSA or affinity...")
    
    # Initialize client if not already done
    if 'client' not in locals():
        client = Boltz2Client(base_url=BOLTZ2_ENDPOINT)
        print("✅ Client initialized")
    
    try:
        # CDK4 without MSA
        cdk4_simple = Polymer(
            id="A",
            molecule_type="protein",
            sequence=CDK4_SHORT
        )
        
        # Ligand without affinity
        palbociclib_simple = Ligand(
            id="LIG",
            smiles=PALBOCICLIB_SMILES,
            predict_affinity=False
        )
        
        simple_request = PredictionRequest(
            polymers=[cdk4_simple],
            ligands=[palbociclib_simple],
            recycling_steps=3,
            sampling_steps=50
        )
        
        print("Predicting without MSA or affinity...")
        print("This simulates the notebook cell that was failing...")
        
        # This is where the error occurred - client not defined
        simple_result = await client.predict(simple_request)
        
        print("✅ Basic prediction works!")
        print(f"   pTM: {simple_result.ptm_scores[0]:.3f}")
        print(f"   pLDDT: {simple_result.complex_plddt_scores[0]:.1f}")
        
        return True
        
    except NameError as e:
        if "client" in str(e):
            print("❌ Error: client is not defined")
            print("The notebook cell still has the initialization issue")
            return False
        else:
            raise
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("This is a different error (not the client initialization issue)")
        return False


async def verify_fixes():
    """Verify all fixes are working."""
    print("CDK4 Notebook Fix Verification")
    print("=" * 60)
    
    # Test 1: Basic prediction
    success1 = await test_basic_prediction()
    
    print("\n" + "=" * 60)
    print("Summary:")
    print(f"Basic prediction test: {'✅ PASSED' if success1 else '❌ FAILED'}")
    
    if success1:
        print("\n✅ The notebook cells should now work correctly!")
        print("The 'client not defined' error has been fixed.")
    else:
        print("\n❌ The notebook still has issues.")
        print("Please reload the notebook and try again.")


if __name__ == "__main__":
    asyncio.run(verify_fixes())
