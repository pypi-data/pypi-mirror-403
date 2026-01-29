# API Reference (Публічне API)

> **Цільова аудиторія:** Всі розробники, від Junior до Senior

## Огляд

```
graph_crawler module
├── crawl()           - Синхронний краулінг (рекомендовано)
├── async_crawl()     - Асинхронний краулінг
├── crawl_sitemap()   - Краулінг через sitemap.xml
├── Crawler           - Reusable синхронний краулер
└── AsyncCrawler      - Reusable асинхронний краулер
```

---

## crawl()

```python
def crawl(
    url: Optional[str] = None,
    *,
    seed_urls: Optional[list[str]] = None,
    base_graph: Optional[Graph] = None,

    # Основні параметри
    max_depth: int = 3,
    max_pages: Optional[int] = 100,
    same_domain: bool = True,
    timeout: Optional[int] = None,
    request_delay: float = 0.5,

    # Компоненти
    driver: Optional[str | IDriver] = None,
    driver_config: Optional[dict] = None,
    storage: Optional[str | IStorage] = None,
    storage_config: Optional[dict] = None,
    plugins: Optional[list[BaseNodePlugin]] = None,

    # Кастомізація
    node_class: Optional[type[Node]] = None,
    edge_class: Optional[type[Edge]] = None,
    url_rules: Optional[list[URLRule]] = None,
    edge_strategy: str = "all",

    # Callbacks
    on_progress: Optional[Callable] = None,
    on_node_scanned: Optional[Callable] = None,
    on_error: Optional[Callable] = None,
    on_completed: Optional[Callable] = None,

    # Distributed mode
    wrapper: Optional[dict] = None,
) -> Graph
```

Синхронний краулінг веб-сайту - **простий як requests**.

🆕 **NEW in v3.2.0:** Підтримка множинних точок входу (`seed_urls`) та продовження існуючого краулінгу (`base_graph`)!

**Параметри:**

| Параметр          | Тип          | Default  | Опис                                                    |
| ----------------- | ------------ | -------- | ------------------------------------------------------- |
| `url`             | str          | None     | URL для початку краулінгу (якщо seed_urls не передано)  |
| `seed_urls` 🆕    | list[str]    | None     | Список URL для початку краулінгу (множинні точки входу) |
| `base_graph` 🆕   | Graph        | None     | Існуючий граф для продовження краулінгу (incremental)   |
| `max_depth`       | int          | 3        | Максимальна глибина обходу                              |
| `max_pages`       | int          | 100      | Максимальна кількість сторінок                          |
| `same_domain`     | bool         | True     | Сканувати тільки поточний домен                         |
| `timeout`         | int          | None     | Максимальний час в секундах                             |
| `request_delay`   | float        | 0.5      | Затримка між запитами                                   |
| `driver`          | str/IDriver  | "http"   | "http", "async", "playwright", "stealth"                |
| `driver_config`   | dict         | None     | Конфігурація драйвера                                   |
| `storage`         | str/IStorage | "memory" | "memory", "json", "sqlite", "postgresql"                |
| `storage_config`  | dict         | None     | Конфігурація storage                                    |
| `plugins`         | list         | default  | Список плагінів                                         |
| `node_class`      | type         | Node     | Кастомний клас Node                                     |
| `edge_class`      | type         | Edge     | Кастомний клас Edge                                     |
| `url_rules`       | list         | None     | Список URLRule                                          |
| `edge_strategy`   | str          | "all"    | "all", "new_only", "max_in_degree", "deeper_only"       |
| `on_progress`     | Callable     | None     | Callback для прогресу                                   |
| `on_node_scanned` | Callable     | None     | Callback після сканування ноди                          |
| `on_error`        | Callable     | None     | Callback для помилок                                    |
| `on_completed`    | Callable     | None     | Callback після завершення                               |
| `wrapper`         | dict         | None     | Конфіг distributed crawling                             |

**Повертає:** `Graph`

**Приклади:**

```python
import graph_crawler as gc

# Базове використання
graph = gc.crawl("https://example.com")

# 🆕 NEW: Множинні точки входу
graph = gc.crawl(
    seed_urls=[
        "https://www.work.ua/jobs/by-category/it/",
        "https://www.work.ua/jobs/by-category/marketing/",
        "https://www.work.ua/jobs/by-category/sales/",
    ],
    max_depth=3
)

# 🆕 NEW: Продовження існуючого краулінгу
graph1 = gc.crawl("https://example.com", max_pages=50)
# ... зберегти граф ...
# Пізніше продовжити
graph2 = gc.crawl(base_graph=graph1, max_pages=100)

# 🆕 NEW: Комбінація обох
sitemap_graph = gc.crawl_sitemap("https://example.com")
# Відфільтрувати ноди...
result = gc.crawl(
    base_graph=filtered_graph,
    seed_urls=["https://example.com/new-section"],
    max_pages=100
)

# З параметрами
graph = gc.crawl(
    "https://example.com",
    max_depth=5,
    max_pages=200,
    driver="playwright"
)

# Distributed режим
config = {
    "broker": {"type": "redis", "host": "server.com", "port": 6379},
    "database": {"type": "mongodb", "host": "server.com", "port": 27017}
}
graph = gc.crawl("https://example.com", wrapper=config)
```

---

## async_crawl()

```python
async def async_crawl(
    url: str,
    *,
    # ... ті самі параметри що і crawl() (без wrapper)
) -> Graph
```

Async версія crawl() для максимальної продуктивності.

**Приклади:**

```python
import asyncio
import graph_crawler as gc

# Базове
graph = await gc.async_crawl("https://example.com")

# Паралельний краулінг
graphs = await asyncio.gather(
    gc.async_crawl("https://site1.com"),
    gc.async_crawl("https://site2.com"),
)
```

---

## crawl_sitemap()

```python
def crawl_sitemap(
    url: str,
    *,
    max_urls: Optional[int] = None,
    include_urls: bool = True,
    timeout: Optional[int] = None,
    driver: Optional[str | IDriver] = None,
    driver_config: Optional[dict] = None,
    storage: Optional[str | IStorage] = None,
    storage_config: Optional[dict] = None,
    wrapper: Optional[dict] = None,
    on_progress: Optional[Callable] = None,
    on_error: Optional[Callable] = None,
    on_completed: Optional[Callable] = None,
) -> Graph
```

Краулінг через sitemap.xml - парсить robots.txt → знаходить sitemap → обробляє всі URL.

**Приклади:**

```python
# Базове
graph = gc.crawl_sitemap("https://example.com")

# Тільки структура (без кінцевих URL)
graph = gc.crawl_sitemap("https://example.com", include_urls=False)

# З лімітом
graph = gc.crawl_sitemap("https://example.com", max_urls=1000)
```

---

## Crawler

```python
class Crawler:
    def __init__(
        self,
        *,
        max_depth: int = 3,
        max_pages: Optional[int] = 100,
        same_domain: bool = True,
        request_delay: float = 0.5,
        driver: Optional[str | IDriver] = None,
        driver_config: Optional[dict] = None,
        storage: Optional[str | IStorage] = None,
        storage_config: Optional[dict] = None,
        plugins: Optional[list[BaseNodePlugin]] = None,
        node_class: Optional[type[Node]] = None,
        edge_strategy: str = "all",
    ): ...

    def crawl(self, url: str, **kwargs) -> Graph: ...
    def close(self) -> None: ...
    def __enter__(self) -> Crawler: ...
    def __exit__(self, ...): ...
```

Reusable синхронний краулер.

**Приклад:**

```python
with gc.Crawler(max_depth=5) as crawler:
    graph1 = crawler.crawl("https://site1.com")
    graph2 = crawler.crawl("https://site2.com")
```

---

## AsyncCrawler

```python
class AsyncCrawler:
    async def crawl(self, url: str, **kwargs) -> Graph: ...
    async def close(self) -> None: ...
    async def __aenter__(self) -> AsyncCrawler: ...
    async def __aexit__(self, ...): ...
```

Async версія Crawler.

**Приклад:**

```python
async with gc.AsyncCrawler() as crawler:
    graphs = await asyncio.gather(
        crawler.crawl("https://site1.com"),
        crawler.crawl("https://site2.com"),
    )
```

---

## Graph

```python
class Graph:
    nodes: Dict[str, Node]       # {node_id: Node}
    edges: List[Edge]            # Список ребер

    def add_node(self, node: Node, overwrite: bool = False) -> Node: ...
    def add_edge(self, edge: Edge) -> Edge: ...
    def get_node_by_url(self, url: str) -> Optional[Node]: ...
    def get_node_by_id(self, node_id: str) -> Optional[Node]: ...
    def has_edge(self, source_id: str, target_id: str) -> bool: ...
    def remove_node(self, node_id: str) -> bool: ...
    def get_stats(self) -> Dict[str, int]: ...
    def copy(self) -> Graph: ...
    def clear(self) -> None: ...

    # Edge Analysis
    def get_popular_nodes(self, top_n: int = 10, by: str = 'in_degree') -> List[Node]: ...
    def get_edge_statistics(self) -> Dict[str, Any]: ...
    def find_cycles(self, max_cycles: Optional[int] = None) -> List[List[str]]: ...
    def export_edges(self, filepath: str, format: str = 'json') -> Any: ...

    # Операції
    def __add__(self, other: Graph) -> Graph: ...  # union
    def __sub__(self, other: Graph) -> Graph: ...  # difference
    def __and__(self, other: Graph) -> Graph: ...  # intersection
    def __or__(self, other: Graph) -> Graph: ...   # union
    def __xor__(self, other: Graph) -> Graph: ...  # symmetric_difference

    # Порівняння
    def __eq__(self, other: Graph) -> bool: ...
    def __lt__(self, other: Graph) -> bool: ...    # is_subgraph (strict)
    def __le__(self, other: Graph) -> bool: ...    # is_subgraph
    def __gt__(self, other: Graph) -> bool: ...    # is_supergraph (strict)
    def __ge__(self, other: Graph) -> bool: ...    # is_supergraph

    # Колекційні
    def __len__(self) -> int: ...
    def __iter__(self) -> Iterator[Node]: ...
    def __contains__(self, item: str | Node) -> bool: ...
    def __getitem__(self, key: str | int) -> Node: ...
```

---

## Node

```python
class Node(BaseModel):
    url: str
    node_id: str = Field(default_factory=uuid4)  # UUID (auto-generated)
    depth: int = 0
    scanned: bool = False
    should_scan: bool = True
    can_create_edges: bool = True
    priority: Optional[int] = None    # 1-10, None = default
    metadata: Dict[str, Any] = {}
    user_data: Dict[str, Any] = {}
    content_hash: Optional[str] = None
    response_status: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.now)
    lifecycle_stage: NodeLifecycle = NodeLifecycle.URL_STAGE

    async def process_html(self, html: str) -> List[str]: ...
    def mark_as_scanned(self) -> None: ...
    def get_content_hash(self) -> str: ...

    # Metadata helpers (Law of Demeter)
    def get_title(self) -> Optional[str]: ...
    def get_description(self) -> Optional[str]: ...
    def get_h1(self) -> Optional[str]: ...
    def get_keywords(self) -> Optional[str]: ...
    def get_meta_value(self, key: str, default: Any = None) -> Any: ...
```

---

## Edge

```python
class Edge(BaseModel):
    source_node_id: str
    target_node_id: str
    edge_id: str              # UUID (auto-generated)
    metadata: Dict[str, Any] = {}

    def add_metadata(self, key: str, value: Any) -> None: ...
    def get_meta_value(self, key: str, default: Any = None) -> Any: ...
```

---

## URLRule

```python
class URLRule(BaseModel):
    pattern: str                              # Regex патерн
    priority: int = 5                         # 1-10 (default: 5)
    should_scan: Optional[bool] = None        # Перебиває фільтри
    should_follow_links: Optional[bool] = None
    create_edge: Optional[bool] = None
```

---

## BaseNodePlugin

```python
class BaseNodePlugin(ABC):
    @property
    @abstractmethod
    def plugin_type(self) -> NodePluginType: ...

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def execute(self, context: NodePluginContext) -> NodePluginContext: ...

    def setup(self) -> None: ...
    def teardown(self) -> None: ...
```

**NodePluginType:**

- `ON_NODE_CREATED` - після створення Node (ЕТАП 1: URL)
- `ON_BEFORE_SCAN` - перед скануванням (ЕТАП 2: HTML)
- `ON_HTML_PARSED` - після парсингу HTML (ЕТАП 2: HTML)
- `ON_AFTER_SCAN` - після сканування (ЕТАП 2: HTML)
- `BEFORE_CRAWL` - перед початком краулінгу (ЕТАП 3: CRAWL)
- `AFTER_CRAWL` - після завершення краулінгу (ЕТАП 3: CRAWL)

**NodePluginContext:**

```python
@dataclass
class NodePluginContext:
    node: Any                           # Node об'єкт
    url: str
    depth: int
    should_scan: bool
    can_create_edges: bool
    html: Optional[str] = None          # Тільки ЕТАП 2
    html_tree: Optional[Any] = None     # Тільки ЕТАП 2
    parser: Optional[Any] = None        # Тільки ЕТАП 2
    metadata: Dict[str, Any] = {}
    extracted_links: List[str] = []
    user_data: Dict[str, Any] = {}
    skip_link_extraction: bool = False
    skip_metadata_extraction: bool = False
```
