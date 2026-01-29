# Shared Types

```python
from ark.types import APIMeta
```

# Emails

Types:

```python
from ark.types import (
    EmailRetrieveResponse,
    EmailListResponse,
    EmailRetrieveDeliveriesResponse,
    EmailRetryResponse,
    EmailSendResponse,
    EmailSendBatchResponse,
    EmailSendRawResponse,
)
```

Methods:

- <code title="get /emails/{emailId}">client.emails.<a href="./src/ark/resources/emails.py">retrieve</a>(email_id, \*\*<a href="src/ark/types/email_retrieve_params.py">params</a>) -> <a href="./src/ark/types/email_retrieve_response.py">EmailRetrieveResponse</a></code>
- <code title="get /emails">client.emails.<a href="./src/ark/resources/emails.py">list</a>(\*\*<a href="src/ark/types/email_list_params.py">params</a>) -> <a href="./src/ark/types/email_list_response.py">SyncPageNumberPagination[EmailListResponse]</a></code>
- <code title="get /emails/{emailId}/deliveries">client.emails.<a href="./src/ark/resources/emails.py">retrieve_deliveries</a>(email_id) -> <a href="./src/ark/types/email_retrieve_deliveries_response.py">EmailRetrieveDeliveriesResponse</a></code>
- <code title="post /emails/{emailId}/retry">client.emails.<a href="./src/ark/resources/emails.py">retry</a>(email_id) -> <a href="./src/ark/types/email_retry_response.py">EmailRetryResponse</a></code>
- <code title="post /emails">client.emails.<a href="./src/ark/resources/emails.py">send</a>(\*\*<a href="src/ark/types/email_send_params.py">params</a>) -> <a href="./src/ark/types/email_send_response.py">EmailSendResponse</a></code>
- <code title="post /emails/batch">client.emails.<a href="./src/ark/resources/emails.py">send_batch</a>(\*\*<a href="src/ark/types/email_send_batch_params.py">params</a>) -> <a href="./src/ark/types/email_send_batch_response.py">EmailSendBatchResponse</a></code>
- <code title="post /emails/raw">client.emails.<a href="./src/ark/resources/emails.py">send_raw</a>(\*\*<a href="src/ark/types/email_send_raw_params.py">params</a>) -> <a href="./src/ark/types/email_send_raw_response.py">EmailSendRawResponse</a></code>

# Domains

Types:

```python
from ark.types import (
    DNSRecord,
    DomainCreateResponse,
    DomainRetrieveResponse,
    DomainListResponse,
    DomainDeleteResponse,
    DomainVerifyResponse,
)
```

Methods:

- <code title="post /domains">client.domains.<a href="./src/ark/resources/domains.py">create</a>(\*\*<a href="src/ark/types/domain_create_params.py">params</a>) -> <a href="./src/ark/types/domain_create_response.py">DomainCreateResponse</a></code>
- <code title="get /domains/{domainId}">client.domains.<a href="./src/ark/resources/domains.py">retrieve</a>(domain_id) -> <a href="./src/ark/types/domain_retrieve_response.py">DomainRetrieveResponse</a></code>
- <code title="get /domains">client.domains.<a href="./src/ark/resources/domains.py">list</a>() -> <a href="./src/ark/types/domain_list_response.py">DomainListResponse</a></code>
- <code title="delete /domains/{domainId}">client.domains.<a href="./src/ark/resources/domains.py">delete</a>(domain_id) -> <a href="./src/ark/types/domain_delete_response.py">DomainDeleteResponse</a></code>
- <code title="post /domains/{domainId}/verify">client.domains.<a href="./src/ark/resources/domains.py">verify</a>(domain_id) -> <a href="./src/ark/types/domain_verify_response.py">DomainVerifyResponse</a></code>

# Suppressions

Types:

```python
from ark.types import (
    SuppressionCreateResponse,
    SuppressionRetrieveResponse,
    SuppressionListResponse,
    SuppressionDeleteResponse,
    SuppressionBulkCreateResponse,
)
```

Methods:

- <code title="post /suppressions">client.suppressions.<a href="./src/ark/resources/suppressions.py">create</a>(\*\*<a href="src/ark/types/suppression_create_params.py">params</a>) -> <a href="./src/ark/types/suppression_create_response.py">SuppressionCreateResponse</a></code>
- <code title="get /suppressions/{email}">client.suppressions.<a href="./src/ark/resources/suppressions.py">retrieve</a>(email) -> <a href="./src/ark/types/suppression_retrieve_response.py">SuppressionRetrieveResponse</a></code>
- <code title="get /suppressions">client.suppressions.<a href="./src/ark/resources/suppressions.py">list</a>(\*\*<a href="src/ark/types/suppression_list_params.py">params</a>) -> <a href="./src/ark/types/suppression_list_response.py">SyncPageNumberPagination[SuppressionListResponse]</a></code>
- <code title="delete /suppressions/{email}">client.suppressions.<a href="./src/ark/resources/suppressions.py">delete</a>(email) -> <a href="./src/ark/types/suppression_delete_response.py">SuppressionDeleteResponse</a></code>
- <code title="post /suppressions/bulk">client.suppressions.<a href="./src/ark/resources/suppressions.py">bulk_create</a>(\*\*<a href="src/ark/types/suppression_bulk_create_params.py">params</a>) -> <a href="./src/ark/types/suppression_bulk_create_response.py">SuppressionBulkCreateResponse</a></code>

# Webhooks

Types:

```python
from ark.types import (
    WebhookCreateResponse,
    WebhookRetrieveResponse,
    WebhookUpdateResponse,
    WebhookListResponse,
    WebhookDeleteResponse,
    WebhookListDeliveriesResponse,
    WebhookReplayDeliveryResponse,
    WebhookRetrieveDeliveryResponse,
    WebhookTestResponse,
)
```

Methods:

- <code title="post /webhooks">client.webhooks.<a href="./src/ark/resources/webhooks.py">create</a>(\*\*<a href="src/ark/types/webhook_create_params.py">params</a>) -> <a href="./src/ark/types/webhook_create_response.py">WebhookCreateResponse</a></code>
- <code title="get /webhooks/{webhookId}">client.webhooks.<a href="./src/ark/resources/webhooks.py">retrieve</a>(webhook_id) -> <a href="./src/ark/types/webhook_retrieve_response.py">WebhookRetrieveResponse</a></code>
- <code title="patch /webhooks/{webhookId}">client.webhooks.<a href="./src/ark/resources/webhooks.py">update</a>(webhook_id, \*\*<a href="src/ark/types/webhook_update_params.py">params</a>) -> <a href="./src/ark/types/webhook_update_response.py">WebhookUpdateResponse</a></code>
- <code title="get /webhooks">client.webhooks.<a href="./src/ark/resources/webhooks.py">list</a>() -> <a href="./src/ark/types/webhook_list_response.py">WebhookListResponse</a></code>
- <code title="delete /webhooks/{webhookId}">client.webhooks.<a href="./src/ark/resources/webhooks.py">delete</a>(webhook_id) -> <a href="./src/ark/types/webhook_delete_response.py">WebhookDeleteResponse</a></code>
- <code title="get /webhooks/{webhookId}/deliveries">client.webhooks.<a href="./src/ark/resources/webhooks.py">list_deliveries</a>(webhook_id, \*\*<a href="src/ark/types/webhook_list_deliveries_params.py">params</a>) -> <a href="./src/ark/types/webhook_list_deliveries_response.py">WebhookListDeliveriesResponse</a></code>
- <code title="post /webhooks/{webhookId}/deliveries/{deliveryId}/replay">client.webhooks.<a href="./src/ark/resources/webhooks.py">replay_delivery</a>(delivery_id, \*, webhook_id) -> <a href="./src/ark/types/webhook_replay_delivery_response.py">WebhookReplayDeliveryResponse</a></code>
- <code title="get /webhooks/{webhookId}/deliveries/{deliveryId}">client.webhooks.<a href="./src/ark/resources/webhooks.py">retrieve_delivery</a>(delivery_id, \*, webhook_id) -> <a href="./src/ark/types/webhook_retrieve_delivery_response.py">WebhookRetrieveDeliveryResponse</a></code>
- <code title="post /webhooks/{webhookId}/test">client.webhooks.<a href="./src/ark/resources/webhooks.py">test</a>(webhook_id, \*\*<a href="src/ark/types/webhook_test_params.py">params</a>) -> <a href="./src/ark/types/webhook_test_response.py">WebhookTestResponse</a></code>

# Tracking

Types:

```python
from ark.types import (
    TrackDomain,
    TrackingCreateResponse,
    TrackingRetrieveResponse,
    TrackingUpdateResponse,
    TrackingListResponse,
    TrackingDeleteResponse,
    TrackingVerifyResponse,
)
```

Methods:

- <code title="post /tracking">client.tracking.<a href="./src/ark/resources/tracking.py">create</a>(\*\*<a href="src/ark/types/tracking_create_params.py">params</a>) -> <a href="./src/ark/types/tracking_create_response.py">TrackingCreateResponse</a></code>
- <code title="get /tracking/{trackingId}">client.tracking.<a href="./src/ark/resources/tracking.py">retrieve</a>(tracking_id) -> <a href="./src/ark/types/tracking_retrieve_response.py">TrackingRetrieveResponse</a></code>
- <code title="patch /tracking/{trackingId}">client.tracking.<a href="./src/ark/resources/tracking.py">update</a>(tracking_id, \*\*<a href="src/ark/types/tracking_update_params.py">params</a>) -> <a href="./src/ark/types/tracking_update_response.py">TrackingUpdateResponse</a></code>
- <code title="get /tracking">client.tracking.<a href="./src/ark/resources/tracking.py">list</a>() -> <a href="./src/ark/types/tracking_list_response.py">TrackingListResponse</a></code>
- <code title="delete /tracking/{trackingId}">client.tracking.<a href="./src/ark/resources/tracking.py">delete</a>(tracking_id) -> <a href="./src/ark/types/tracking_delete_response.py">TrackingDeleteResponse</a></code>
- <code title="post /tracking/{trackingId}/verify">client.tracking.<a href="./src/ark/resources/tracking.py">verify</a>(tracking_id) -> <a href="./src/ark/types/tracking_verify_response.py">TrackingVerifyResponse</a></code>
