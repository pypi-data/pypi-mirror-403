from prestashop_webservice.base_model import BaseModel
from prestashop_webservice.models import OrderDetailData
from prestashop_webservice.params import Params


class OrderDetail(BaseModel):
    """Complex queries for order_details endpoint."""

    _data_class = OrderDetailData

    def get_by_id(self, order_detail_id: str) -> OrderDetailData:
        """Get order detail by ID."""
        return self._query(f"order_details/{order_detail_id}", None, "order_detail")

    def get_by_order(self, order_id: str) -> list[OrderDetailData]:
        """Get details (products) for a specific order."""
        params = Params(filter={"id_order": order_id}, display=["full"])
        return self._query("order_details", params, "order_details")

    def get_by_orders(self, order_ids: list[str]) -> list[OrderDetailData]:
        """Get details for multiple orders."""
        if not order_ids:
            return []

        orders_filter_value = "|".join(order_ids)

        params = Params(filter={"id_order": f"[{orders_filter_value}]"}, display=["full"])
        return self._query("order_details", params, "order_details")
