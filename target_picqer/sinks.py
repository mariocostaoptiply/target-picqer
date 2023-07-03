"""Picqer target sink class, which handles writing streams."""


from singer_sdk.sinks import RecordSink
from target_picqer.client import PicqerSink


class PurchaseOrders(PicqerSink):
    """Picqer target sink class."""

    endpoint = "purchaseorders"
    names_available = ["purchase_orders", "purchaseorders"]
    name = "PurchaseOrders"

    def get_purchase_order(self, order_id):
        po = self.request_api("GET", f"purchaseorders/{order_id}")
        if po.status_code != 200:
            return []
        return po.json()

    def search_product(self, products, search):
        if products:
            for product in products:
                if str(product.get("idproduct")) == search:
                    return product
        return {}

    def update_po_product(self, order_id, idpurchaseorder_product, payload):
        res = self.request_api(
            "PUT",
            f"purchaseorders/{order_id}/products/{idpurchaseorder_product}",
            request_data=payload,
        )
        return res

    def add_po_product(self, order_id, payload):
        res = self.request_api(
            "POST", f"purchaseorders/{order_id}/products", request_data=payload
        )
        return res

    def preprocess_record(self, record: dict, context: dict) -> None:
        line_items = self.parse_json(record.get("line_items", []))
        delivery_date = self.convert_datetime(record.get("created_at"))

        # Process updates for line items
        if record.get("id"):
            purchase_order_detail = self.get_purchase_order(record.get("id"))
            if purchase_order_detail:
                purchase_products = purchase_order_detail.get("products", [])

                # Search and upsert line items.
                for line in line_items:
                    product = self.search_product(
                        purchase_products, line.get("product_id")
                    )
                    # update product if found
                    if product:
                        payload = {
                            "amount": line.get("quantity"),
                            "price": line.get("unit_price"),
                        }
                        if line.get("delivery_date"):
                            payload.update({"delivery_date": line.get("delivery_date")})

                        # How do we add these results to state.json?
                        self.update_po_product(
                            record.get("id"),
                            product.get("idpurchaseorder_product"),
                            payload,
                        )
                    else:
                        # Looks like it is a new line item. Lets add it.
                        payload = {
                            "idproduct": line.get("product_id"),
                            "name": line.get("product_name"),
                            "amount": line.get("quantity"),
                            "price": line.get("unit_price"),
                        }
                        self.add_po_product(record.get("id"), payload)

        # When performing updates these lines are ignored so let them proceed as usual
        lines = [
            {
                "idproduct": i.get("product_id"),
                # Although allowed as input but ignored. Name is picked up using idproduct
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
            mapping.update({"idsupplier": record.get("supplier_code")})

        if record.get("warehouse_id"):
            mapping.update({"idwarehouse": record.get("warehouse_id")})

        if record.get("id"):
            mapping.update({"id": record.get("id")})
        return mapping

    def upsert_record(self, record: dict, context: dict):
        endpoint = self.endpoint
        method_type = "POST"
        action_text = "created"
        state_updates = dict()
        if record.get("id"):
            endpoint = f"{endpoint}/{record.get('id')}"
            method_type = "PUT"
            state_updates["is_updated"] = True
            action_text = "updated"
        if record:
            try:
                buy_order_response = self.request_api(
                    method_type, endpoint=endpoint, request_data=record
                )
                po_id = buy_order_response.json()["idpurchaseorder"]
                self.logger.info(
                    f"Purchase Order Successfully {action_text} with ID {po_id}"
                )
            except:
                raise KeyError
            return po_id, True, state_updates
