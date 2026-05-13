from app.models.schemas import KnowledgeBase, KnowledgeBaseCreate, KnowledgeBaseScope


class KnowledgeBaseService:
    def __init__(self) -> None:
        self._items: dict[str, KnowledgeBase] = {}

    def create(self, request: KnowledgeBaseCreate) -> KnowledgeBase:
        item = KnowledgeBase(product_line=request.product_line, product_version=request.product_version)
        self._items[item.key] = item
        return item

    def ensure(self, scope: KnowledgeBaseScope) -> KnowledgeBase:
        key = scope.key
        if key not in self._items:
            self._items[key] = KnowledgeBase(
                product_line=scope.product_line,
                product_version=scope.product_version,
            )
        return self._items[key]

    def list(self) -> list[KnowledgeBase]:
        return sorted(self._items.values(), key=lambda item: (item.product_line, item.product_version))

