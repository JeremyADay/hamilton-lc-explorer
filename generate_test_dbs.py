import sqlite3
import shutil

def create_test_scenario():
    original = "ML_STARLiquids.db"
    site_a = "Site_A_Master.db"
    site_b = "Site_B_STARlet.db"

    # 1. Create two identical copies
    shutil.copy2(original, site_a)
    shutil.copy2(original, site_b)
    print(f"Created {site_a} and {site_b}")

    # 2. Inject differences into Site B (The 'Problem' Instrument)
    conn = sqlite3.connect(site_b)
    cursor = conn.cursor()

    # Change 1: Modify Aspiration Flow Rate for Water
    # We use a wildcard to catch variations like 'Water_Standard'
    cursor.execute("""
        UPDATE LiquidClass 
        SET AsFlowRate = 250.0 
        WHERE LiquidClassName LIKE '%Water%'
    """)
    
    # Change 2: Modify Dispense Settling Time for a Viscous class
    cursor.execute("""
        UPDATE LiquidClass 
        SET DsSettlingTime = 5.0 
        WHERE LiquidClassName LIKE '%Glycerol%' OR LiquidClassName LIKE '%Visc%'
    """)

    # Change 3: Modify LLD Sensitivity 
    cursor.execute("""
        UPDATE LiquidClass 
        SET PressureLLDSensitivity = 1
        WHERE LiquidClassName LIKE '%Ethanol%'
    """)

    conn.commit()
    print("SUCCESS: Injected 3 specific mismatches into Site B.")
    conn.close()

if __name__ == "__main__":
    create_test_scenario()