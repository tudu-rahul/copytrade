import codecs
from typing import Dict, Optional


class Index:
    """
    Manages functions related to indices

    ...

    Methods
    -------
    get_details(index: str = None) -> Dict:
        Get details of any index
    """
    @staticmethod
    def get_details(index: str = None) -> Dict:
        """
        Get details of any index

        Details of each index is stored in index_details.txt

        Returns
        -------
        Dict:
            { "index": str, "freeze_quantity": int, "quantity_per_lot": int, :"spreadwidth": int }
        """
        if index is None:
            return {}
        details: Dict = {}
        index_details_file = codecs.open("index_details.txt", "r")
        freeze_quantity: int = 0
        quantity_per_lot: int = 0
        ind: Optional[str] = None
        for lin in index_details_file:
            if len(lin.strip()) == 0:
                continue
            key: str = lin.split(':')[0].strip()
            value: str = lin.split(':')[1].strip()
            if key == "index":
                ind = value
            elif key == "freeze_quantity":
                freeze_quantity = int(value)
            elif key == "quantity_per_lot":
                quantity_per_lot = int(value)
            elif key == "spreadwidth":
                spreadwidth: int = int(value)
                if ind == index:
                    details["index"] = ind
                    details["freeze_quantity"] = freeze_quantity
                    details["quantity_per_lot"] = quantity_per_lot
                    details["spreadwidth"] = spreadwidth
            else:
                break
        index_details_file.close()
        
        return details
