# V2

Types:

```python
from nimbleway_webit.types import V2ExtractResponse, V2ExtractTemplateResponse, V2MapResponse
```

Methods:

- <code title="post /api/v2/extract">client.v2.<a href="./src/nimbleway_webit/resources/v2/v2.py">extract</a>(\*\*<a href="src/nimbleway_webit/types/v2_extract_params.py">params</a>) -> <a href="./src/nimbleway_webit/types/v2_extract_response.py">V2ExtractResponse</a></code>
- <code title="post /api/v2/extract-template">client.v2.<a href="./src/nimbleway_webit/resources/v2/v2.py">extract_template</a>(\*\*<a href="src/nimbleway_webit/types/v2_extract_template_params.py">params</a>) -> <a href="./src/nimbleway_webit/types/v2_extract_template_response.py">V2ExtractTemplateResponse</a></code>
- <code title="post /api/v2/map">client.v2.<a href="./src/nimbleway_webit/resources/v2/v2.py">map</a>(\*\*<a href="src/nimbleway_webit/types/v2_map_params.py">params</a>) -> <a href="./src/nimbleway_webit/types/v2_map_response.py">V2MapResponse</a></code>

## Crawl

Types:

```python
from nimbleway_webit.types.v2 import (
    CrawlListResponse,
    CrawlCancelResponse,
    CrawlCrawlResponse,
    CrawlGetResponse,
)
```

Methods:

- <code title="get /api/v2/crawl?status={status}">client.v2.crawl.<a href="./src/nimbleway_webit/resources/v2/crawl.py">list</a>(path_status, \*\*<a href="src/nimbleway_webit/types/v2/crawl_list_params.py">params</a>) -> <a href="./src/nimbleway_webit/types/v2/crawl_list_response.py">CrawlListResponse</a></code>
- <code title="delete /api/v2/crawl/{id}">client.v2.crawl.<a href="./src/nimbleway_webit/resources/v2/crawl.py">cancel</a>(id) -> <a href="./src/nimbleway_webit/types/v2/crawl_cancel_response.py">CrawlCancelResponse</a></code>
- <code title="post /api/v2/crawl">client.v2.crawl.<a href="./src/nimbleway_webit/resources/v2/crawl.py">crawl</a>(\*\*<a href="src/nimbleway_webit/types/v2/crawl_crawl_params.py">params</a>) -> <a href="./src/nimbleway_webit/types/v2/crawl_crawl_response.py">CrawlCrawlResponse</a></code>
- <code title="get /api/v2/crawl/{id}">client.v2.crawl.<a href="./src/nimbleway_webit/resources/v2/crawl.py">get</a>(id) -> <a href="./src/nimbleway_webit/types/v2/crawl_get_response.py">CrawlGetResponse</a></code>
