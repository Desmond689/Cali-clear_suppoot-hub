# TODO: Implement Order Tracking System

- [x] Add `tracking_number` and `carrier` fields to the `Order` model in `models.py`
- [x] Update `update_order_status` route in `order_routes.py` to accept optional `tracking_number` and `carrier` when status is 'shipped'
- [x] Add new GET endpoint `/orders/<order_id>/tracking` in `order_routes.py` to retrieve tracking details
- [x] Modify `send_shipping_update` in `email_service.py` to include tracking information in the email if available
- [x] Create a database migration script to add the new fields to the Order table
- [x] Run the database migration to update the schema
- [x] Test the new tracking functionality (update status with tracking, retrieve tracking, check emails)
