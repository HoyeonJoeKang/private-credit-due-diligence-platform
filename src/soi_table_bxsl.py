import pandas as pd

from src.fetch_soi_full import to_float


def _is_affiliation_banner(text: str) -> bool:
    t = str(text).lower()
    return "affiliated" in t or "controlled" in t


GRAND_TOTAL_PREFIX = "total portfolio investments"


def classify_and_assign_bxsl(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    current_asset_class = None
    current_affiliation = None
    current_sector = None
    prev_row_type = None

    asset_classes, affiliations, sectors, row_types = [], [], [], []

    for _, row in df.iterrows():
        investments_val = row["Investments"]
        cost_val = row["Cost"]

        has_investments = pd.notna(investments_val)
        has_cost = pd.notna(cost_val)
        investments_text = str(investments_val).strip().lower() if has_investments else ""

        is_grand_total = investments_text.startswith(GRAND_TOTAL_PREFIX)
        is_asset_class_subtotal = (not is_grand_total) and investments_text.startswith("total ")
        is_banner = (not is_grand_total and not is_asset_class_subtotal
                     and has_investments and to_float(cost_val) is None)

        if is_grand_total:
            row_type = "grand_total"
        elif is_asset_class_subtotal:
            row_type = "asset_class_subtotal"
        elif is_banner:
            if _is_affiliation_banner(investments_val):
                current_affiliation = investments_val
            else:
                if prev_row_type != "banner":
                    current_asset_class = investments_val
                current_sector = investments_val
            row_type = "banner"
        elif not has_investments and has_cost:
            row_type = "sector_subtotal"
        elif has_investments:
            row_type = "company_row"
        else:
            row_type = "blank"

        asset_classes.append(current_asset_class)
        affiliations.append(current_affiliation)
        sectors.append(current_sector)
        row_types.append(row_type)
        prev_row_type = row_type

    df["AssetClass"] = asset_classes
    df["Affiliation"] = affiliations
    df["Sector"] = sectors
    df["RowType"] = row_types
    return df
