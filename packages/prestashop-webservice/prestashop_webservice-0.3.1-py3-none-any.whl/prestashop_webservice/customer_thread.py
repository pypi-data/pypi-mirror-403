from prestashop_webservice.base_model import BaseModel
from prestashop_webservice.models import CustomerThreadData
from prestashop_webservice.params import Params


class CustomerThread(BaseModel):
    """Complex queries for customer_threads endpoint."""

    _data_class = CustomerThreadData

    def get_by_id(self, thread_id: str) -> CustomerThreadData:
        """Get customer thread by ID."""
        return self._query(f"customer_threads/{thread_id}", None, "customer_thread")

    def get_by_customer(self, customer_id: str) -> list[CustomerThreadData]:
        """Get customer threads by customer ID."""
        params = Params(filter={"id_customer": customer_id}, display=["full"])
        return self._query("customer_threads", params, "customer_threads")

    def get_by_order(self, order_id: str) -> list[CustomerThreadData]:
        """Get customer threads by order ID."""
        params = Params(filter={"id_order": order_id}, display=["full"])
        return self._query("customer_threads", params, "customer_threads")
