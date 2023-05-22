"""Picqer target sink class, which handles writing streams."""


from singer_sdk.sinks import RecordSink
from target_picqer.client import PicqerSink

class PurchaseOrders(PicqerSink):
    """Picqer target sink class."""
    endpoint = "purchaseorders"
    name = "PurchaseOrders"
    
    def preprocess_record(self, record: dict, context: dict) -> None:
        line_items = self.parse_json(record.get("line_items", []))
        delivery_date = self.convert_datetime(record.get("created_at"))

        lines = [
            {
                "idproduct": i.get("product_id"),
                #Although allowed as input but ignored. Name is picked up using idproduct
                "name": i.get("product_name"),
                "amount": i.get("quantity"),
                "price": i.get("unit_price"),
            }
            for i in line_items
        ]

        mapping = {
            "delivery_date": delivery_date,
            "supplier_name": record.get("supplier_name"),
            "supplier_orderid": record.get("order_number"),
            "products": lines,
            
        }
        if record.get("supplier_code"):
            mapping.update({"idsupplier":record.get("supplier_code")})
        if record.get("id"):
             mapping.update({"id":record.get("id")})
        return mapping

    def upsert_record(self, record: dict, context: dict):
            endpoint = self.endpoint
            method_type = "POST"
            action_text = "created"
            state_updates = dict()
            if record.get("id"):
                 endpoint = f"{endpoint}/{record.get('id')}"
                 method_type = "PUT"
                 state_updates['is_updated'] = True
                 action_text = "updated"
            if record:
                try:
                    buy_order_response = self.request_api(
                        method_type, endpoint=endpoint, request_data=record
                    )
                    po_id = buy_order_response.json()["idpurchaseorder"]
                    self.logger.info(f"Purchase Order Successfully {action_text} with ID {po_id}")
                except:
                    raise KeyError
                return po_id, True, state_updates
