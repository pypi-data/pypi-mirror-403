# V2

## AsyncResults

Types:

```python
from samplehc.types.v2 import AsyncResultSleepResponse
```

Methods:

- <code title="post /api/v2/async-results/sleep">client.v2.async_results.<a href="./src/samplehc/resources/v2/async_results.py">sleep</a>(\*\*<a href="src/samplehc/types/v2/async_result_sleep_params.py">params</a>) -> <a href="./src/samplehc/types/v2/async_result_sleep_response.py">AsyncResultSleepResponse</a></code>

## Documents

Types:

```python
from samplehc.types.v2 import (
    DocumentRetrieveResponse,
    DocumentClassifyResponse,
    DocumentCombineResponse,
    DocumentCreateFromSplitsResponse,
    DocumentExtractResponse,
    DocumentGenerateCsvResponse,
    DocumentPresignedUploadURLResponse,
    DocumentRetrieveCsvContentResponse,
    DocumentRetrieveMetadataResponse,
    DocumentSearchResponse,
    DocumentSplitResponse,
    DocumentTransformJsonToHTMLResponse,
)
```

Methods:

- <code title="get /api/v2/documents/{documentId}">client.v2.documents.<a href="./src/samplehc/resources/v2/documents/documents.py">retrieve</a>(document_id) -> <a href="./src/samplehc/types/v2/document_retrieve_response.py">DocumentRetrieveResponse</a></code>
- <code title="post /api/v2/documents/classify">client.v2.documents.<a href="./src/samplehc/resources/v2/documents/documents.py">classify</a>(\*\*<a href="src/samplehc/types/v2/document_classify_params.py">params</a>) -> <a href="./src/samplehc/types/v2/document_classify_response.py">DocumentClassifyResponse</a></code>
- <code title="post /api/v2/documents/combine">client.v2.documents.<a href="./src/samplehc/resources/v2/documents/documents.py">combine</a>(\*\*<a href="src/samplehc/types/v2/document_combine_params.py">params</a>) -> <a href="./src/samplehc/types/v2/document_combine_response.py">DocumentCombineResponse</a></code>
- <code title="post /api/v2/documents/create-from-splits">client.v2.documents.<a href="./src/samplehc/resources/v2/documents/documents.py">create_from_splits</a>(\*\*<a href="src/samplehc/types/v2/document_create_from_splits_params.py">params</a>) -> <a href="./src/samplehc/types/v2/document_create_from_splits_response.py">DocumentCreateFromSplitsResponse</a></code>
- <code title="post /api/v2/documents/extract">client.v2.documents.<a href="./src/samplehc/resources/v2/documents/documents.py">extract</a>(\*\*<a href="src/samplehc/types/v2/document_extract_params.py">params</a>) -> <a href="./src/samplehc/types/v2/document_extract_response.py">DocumentExtractResponse</a></code>
- <code title="post /api/v2/documents/generate-csv">client.v2.documents.<a href="./src/samplehc/resources/v2/documents/documents.py">generate_csv</a>(\*\*<a href="src/samplehc/types/v2/document_generate_csv_params.py">params</a>) -> <a href="./src/samplehc/types/v2/document_generate_csv_response.py">DocumentGenerateCsvResponse</a></code>
- <code title="post /api/v2/documents/presigned-upload-url">client.v2.documents.<a href="./src/samplehc/resources/v2/documents/documents.py">presigned_upload_url</a>(\*\*<a href="src/samplehc/types/v2/document_presigned_upload_url_params.py">params</a>) -> <a href="./src/samplehc/types/v2/document_presigned_upload_url_response.py">DocumentPresignedUploadURLResponse</a></code>
- <code title="get /api/v2/documents/{documentId}/csv-content">client.v2.documents.<a href="./src/samplehc/resources/v2/documents/documents.py">retrieve_csv_content</a>(document_id) -> <a href="./src/samplehc/types/v2/document_retrieve_csv_content_response.py">DocumentRetrieveCsvContentResponse</a></code>
- <code title="get /api/v2/documents/{documentId}/metadata">client.v2.documents.<a href="./src/samplehc/resources/v2/documents/documents.py">retrieve_metadata</a>(document_id) -> <a href="./src/samplehc/types/v2/document_retrieve_metadata_response.py">DocumentRetrieveMetadataResponse</a></code>
- <code title="post /api/v2/documents/search">client.v2.documents.<a href="./src/samplehc/resources/v2/documents/documents.py">search</a>(\*\*<a href="src/samplehc/types/v2/document_search_params.py">params</a>) -> <a href="./src/samplehc/types/v2/document_search_response.py">DocumentSearchResponse</a></code>
- <code title="post /api/v2/documents/split">client.v2.documents.<a href="./src/samplehc/resources/v2/documents/documents.py">split</a>(\*\*<a href="src/samplehc/types/v2/document_split_params.py">params</a>) -> <a href="./src/samplehc/types/v2/document_split_response.py">DocumentSplitResponse</a></code>
- <code title="post /api/v2/documents/json-to-html">client.v2.documents.<a href="./src/samplehc/resources/v2/documents/documents.py">transform_json_to_html</a>(\*\*<a href="src/samplehc/types/v2/document_transform_json_to_html_params.py">params</a>) -> <a href="./src/samplehc/types/v2/document_transform_json_to_html_response.py">DocumentTransformJsonToHTMLResponse</a></code>

### Legacy

Types:

```python
from samplehc.types.v2.documents import (
    LegacyExtractResponse,
    LegacyReasonResponse,
    LegacySplitResponse,
)
```

Methods:

- <code title="post /api/v2/documents/legacy/extract">client.v2.documents.legacy.<a href="./src/samplehc/resources/v2/documents/legacy.py">extract</a>(\*\*<a href="src/samplehc/types/v2/documents/legacy_extract_params.py">params</a>) -> <a href="./src/samplehc/types/v2/documents/legacy_extract_response.py">LegacyExtractResponse</a></code>
- <code title="post /api/v2/documents/legacy/reason">client.v2.documents.legacy.<a href="./src/samplehc/resources/v2/documents/legacy.py">reason</a>(\*\*<a href="src/samplehc/types/v2/documents/legacy_reason_params.py">params</a>) -> <a href="./src/samplehc/types/v2/documents/legacy_reason_response.py">LegacyReasonResponse</a></code>
- <code title="post /api/v2/documents/legacy/split">client.v2.documents.legacy.<a href="./src/samplehc/resources/v2/documents/legacy.py">split</a>(\*\*<a href="src/samplehc/types/v2/documents/legacy_split_params.py">params</a>) -> <a href="./src/samplehc/types/v2/documents/legacy_split_response.py">LegacySplitResponse</a></code>

### Templates

Types:

```python
from samplehc.types.v2.documents import (
    TemplateGenerateDocumentAsyncResponse,
    TemplateRenderDocumentResponse,
)
```

Methods:

- <code title="post /api/v2/documents/templates/generate-document">client.v2.documents.templates.<a href="./src/samplehc/resources/v2/documents/templates.py">generate_document_async</a>(\*\*<a href="src/samplehc/types/v2/documents/template_generate_document_async_params.py">params</a>) -> <a href="./src/samplehc/types/v2/documents/template_generate_document_async_response.py">TemplateGenerateDocumentAsyncResponse</a></code>
- <code title="post /api/v2/documents/templates/render">client.v2.documents.templates.<a href="./src/samplehc/resources/v2/documents/templates.py">render_document</a>(\*\*<a href="src/samplehc/types/v2/documents/template_render_document_params.py">params</a>) -> <a href="./src/samplehc/types/v2/documents/template_render_document_response.py">TemplateRenderDocumentResponse</a></code>

### Formats

Types:

```python
from samplehc.types.v2.documents import FormatCreatePdfResponse
```

Methods:

- <code title="post /api/v2/documents/{documentId}/formats/pdf">client.v2.documents.formats.<a href="./src/samplehc/resources/v2/documents/formats.py">create_pdf</a>(document_id, \*\*<a href="src/samplehc/types/v2/documents/format_create_pdf_params.py">params</a>) -> <a href="./src/samplehc/types/v2/documents/format_create_pdf_response.py">FormatCreatePdfResponse</a></code>

## Communication

Types:

```python
from samplehc.types.v2 import (
    CommunicationSendEmailResponse,
    CommunicationSendFaxResponse,
    CommunicationSendLetterResponse,
)
```

Methods:

- <code title="post /api/v2/communication/send-email">client.v2.communication.<a href="./src/samplehc/resources/v2/communication.py">send_email</a>(\*\*<a href="src/samplehc/types/v2/communication_send_email_params.py">params</a>) -> <a href="./src/samplehc/types/v2/communication_send_email_response.py">CommunicationSendEmailResponse</a></code>
- <code title="post /api/v2/communication/send-fax">client.v2.communication.<a href="./src/samplehc/resources/v2/communication.py">send_fax</a>(\*\*<a href="src/samplehc/types/v2/communication_send_fax_params.py">params</a>) -> <a href="./src/samplehc/types/v2/communication_send_fax_response.py">CommunicationSendFaxResponse</a></code>
- <code title="post /api/v2/communication/letters">client.v2.communication.<a href="./src/samplehc/resources/v2/communication.py">send_letter</a>(\*\*<a href="src/samplehc/types/v2/communication_send_letter_params.py">params</a>) -> <a href="./src/samplehc/types/v2/communication_send_letter_response.py">CommunicationSendLetterResponse</a></code>

## Events

Types:

```python
from samplehc.types.v2 import EventEmitResponse
```

Methods:

- <code title="post /api/v2/events/">client.v2.events.<a href="./src/samplehc/resources/v2/events.py">emit</a>(\*\*<a href="src/samplehc/types/v2/event_emit_params.py">params</a>) -> <a href="./src/samplehc/types/v2/event_emit_response.py">EventEmitResponse</a></code>

## Database

Types:

```python
from samplehc.types.v2 import DatabaseExecuteSqlResponse
```

Methods:

- <code title="post /api/v2/database/sql">client.v2.database.<a href="./src/samplehc/resources/v2/database.py">execute_sql</a>(\*\*<a href="src/samplehc/types/v2/database_execute_sql_params.py">params</a>) -> <a href="./src/samplehc/types/v2/database_execute_sql_response.py">DatabaseExecuteSqlResponse</a></code>
