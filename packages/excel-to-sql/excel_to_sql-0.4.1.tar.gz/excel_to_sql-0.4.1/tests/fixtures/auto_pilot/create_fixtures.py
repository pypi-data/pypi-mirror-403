"""
Create sample Excel test fixtures for auto-pilot pattern detection.

This script generates three Excel files:
1. produits.xlsx - Products with PK and French status codes
2. mouvements.xlsx - Movements with FK and French movement codes
3. commandes.xlsx - Orders with split status fields
"""

import pandas as pd
from pathlib import Path

# Create fixtures directory
fixtures_dir = Path(__file__).parent
fixtures_dir.mkdir(parents=True, exist_ok=True)

# 1. produits.xlsx - Products with PK and status codes
produits_data = pd.DataFrame({
    "no_produit": [1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 1010],
    "nom_produit": [
        "Widget A",
        "Widget B",
        "Widget C",
        "Widget D",
        "Widget E",
        "Widget F",
        "Widget G",
        "Widget H",
        "Widget I",
        "Widget J",
    ],
    "etat": ["ACTIF", "ACTIF", "INACTIF", "EN_ATTENTE", "ACTIF", "INACTIF", "ACTIF", "EN_ATTENTE", "ACTIF", "INACTIF"],
    "categorie_1": ["Électronique", "Mécanique", None, "Électronique", None, "Mécanique", "Électronique", None, "Mécanique", None],
    "description": ["Lorem ipsum", "Sans description", None, "Test product", None, "Another product", "Quality item", None, "Good product", None],
    "prix": [10.50, 20.00, 15.75, 30.25, 12.99, 25.50, 18.00, 22.75, 14.50, 28.00],
    "date_creation": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05",
                                      "2024-01-06", "2024-01-07", "2024-01-08", "2024-01-09", "2024-01-10"]),
})
produits_file = fixtures_dir / "produits.xlsx"
produits_data.to_excel(produits_file, index=False)
print(f"Created: {produits_file}")

# 2. mouvements.xlsx - Movements with FK and movement codes
mouvements_data = pd.DataFrame({
    "oid": list(range(1, 51)),
    "no_produit": [1001, 1002, 1003, 1004, 1005] * 10,
    "type": ["ENTRÉE", "SORTIE", "TRANSFERT", "AJUSTEMENT", "INVENTAIRE"] * 10,
    "quantite": [10, -5, 3, 2, 1] * 10,
    "date_heure": pd.date_range("2024-01-01", periods=50, freq="h"),
    "date_heure_2": [pd.Timestamp("2024-01-01 12:00:00") if i % 2 == 0 else None for i in range(50)],
})
mouvements_file = fixtures_dir / "mouvements.xlsx"
mouvements_data.to_excel(mouvements_file, index=False)
print(f"Created: {mouvements_file}")

# 3. commandes.xlsx - Orders with split status fields
commandes_data = pd.DataFrame({
    "commande": [f"C{i:04d}" for i in range(1, 21)],
    "client": [f"Client_{i}" for i in range(1, 21)],
    "montant": [100.0, 250.5, 175.0, 300.0, 125.0, 200.0, 150.0, 275.0, 225.0, 180.0,
                190.0, 210.0, 165.0, 245.0, 130.0, 195.0, 170.0, 220.0, 140.0, 205.0],
    # Split status fields - mutually exclusive
    "etat_superieur": ["EN_COURS"] * 5 + [None] * 15,
    "etat_inferieur": [None] * 5 + ["EN_ATTENTE"] * 5 + [None] * 10,
    "etat": [None] * 10 + ["COMPLETE"] * 5 + ["ANNULEE"] * 5,
    "date_commande": pd.date_range("2024-01-01", periods=20, freq="D"),
})
commandes_file = fixtures_dir / "commandes.xlsx"
commandes_data.to_excel(commandes_file, index=False)
print(f"Created: {commandes_file}")

print("\n✅ All test fixtures created successfully!")
print(f"\nFixture directory: {fixtures_dir.absolute()}")
print("\nFiles created:")
print(f"  - {produits_file.name} (10 rows, 7 columns)")
print(f"  - {mouvements_file.name} (50 rows, 6 columns)")
print(f"  - {commandes_file.name} (20 rows, 7 columns)")
