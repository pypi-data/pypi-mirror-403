from prestashop_webservice.base_model import BaseModel
from prestashop_webservice.models import CustomerMessageData
from prestashop_webservice.params import Params


class CustomerMessage(BaseModel):
    """Complex queries for customer_messages endpoint."""

    _data_class = CustomerMessageData

    def get_by_id(self, message_id: str) -> CustomerMessageData:
        """Get customer message by ID."""
        return self._query(f"customer_messages/{message_id}", None, "customer_message")

    def get_by_order(self, order_id: str) -> list[CustomerMessageData]:
        """Get messages associated with an order (via customer thread potentially, but often queried by order)."""
        params = Params(
            filter={"id_order": order_id},
            display=["id", "message", "id_employee", "private", "date_add"],
        )
        return self._query("customer_messages", params, "customer_messages")

    def get_by_thread(self, thread_id: str) -> list[CustomerMessageData]:
        """Get messages associated with a specific customer thread."""
        params = Params(
            filter={"id_customer_thread": thread_id},
            display=["full"],
        )
        return self._query("customer_messages", params, "customer_messages")
