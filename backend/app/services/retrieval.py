import re

from app.models.schemas import KnowledgeBaseScope, Source
from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorRepository


class ScopedRetrievalService:
    """The only application service allowed to perform query-time vector search."""

    def __init__(
        self,
        embeddings: EmbeddingService,
        vector_repository: VectorRepository,
        min_score: float = 0.2,
        rerank_pool_factor: int = 4,
    ) -> None:
        self.embeddings = embeddings
        self.vector_repository = vector_repository
        self.min_score = min_score
        self.rerank_pool_factor = rerank_pool_factor

    def retrieve(self, scope: KnowledgeBaseScope, question: str, limit: int) -> list[Source]:
        query_vector = self.embeddings.embed(question)
        pool_limit = max(limit * self.rerank_pool_factor, limit)
        results = self.vector_repository.search(scope=scope, query_vector=query_vector, limit=pool_limit)
        lexical_terms = _lexical_fallback_terms(question)
        lexical_search = getattr(self.vector_repository, "lexical_search", None)
        if lexical_terms and lexical_search is not None:
            results = _merge_sources(
                results,
                lexical_search(scope=scope, terms=lexical_terms, limit=pool_limit),
            )
        reranked = sorted(
            (_focus_article_text(_boost_source(source, question), question) for source in results),
            key=lambda source: source.score,
            reverse=True,
        )
        return [
            source
            for source in reranked
            if source.score >= self.min_score and _has_retrieval_evidence(question, source)
        ][:limit]


_STOP_TERMS = {
    "什么",
    "哪个",
    "哪些",
    "多少",
    "如何",
    "怎么",
    "是否",
    "需要",
    "可以",
    "一下",
    "这个",
    "那个",
    "说明",
    "介绍",
}

_SYNONYM_GROUPS = {
    "退款": {"退款", "退回", "返还", "赎回", "取消购买", "资金退回", "资金返还"},
    "退回": {"退款", "退回", "返还", "赎回", "取消购买", "资金退回", "资金返还"},
    "赎回": {"退款", "退回", "返还", "赎回", "取消购买", "资金退回", "资金返还"},
    "到账": {"到账", "到帐", "资金到账", "资金到帐"},
    "到帐": {"到账", "到帐", "资金到账", "资金到帐"},
    "购买": {"购买", "买入", "认购", "申购"},
    "买入": {"购买", "买入", "认购", "申购"},
    "认购": {"购买", "买入", "认购", "申购"},
    "申购": {"购买", "买入", "认购", "申购"},
    "端口": {"端口", "port", "ports"},
    "安装": {"安装", "部署", "配置", "install", "setup"},
}


def _merge_sources(left: list[Source], right: list[Source]) -> list[Source]:
    merged: dict[tuple[str, int], Source] = {}
    for source in [*left, *right]:
        key = (source.document_id, source.chunk_index)
        current = merged.get(key)
        if current is None or source.score > current.score:
            merged[key] = source
    return list(merged.values())


def _boost_source(source: Source, question: str) -> Source:
    lexical_score = _lexical_overlap(question, source.text)
    if lexical_score <= 0:
        return source
    return source.model_copy(update={"score": source.score + min(lexical_score, 0.35)})


def _has_retrieval_evidence(question: str, source: Source) -> bool:
    article_groups = _article_reference_groups(question)
    if article_groups:
        return bool(_matched_concepts(article_groups, source.text))
    concepts = _query_concepts(question)
    if not concepts:
        return source.score >= 0.55
    matched = _matched_concepts(concepts, source.text)
    if not matched:
        return source.score >= 0.55
    if len(concepts) == 1:
        return True
    return len(matched) >= 2


def _lexical_overlap(question: str, text: str) -> float:
    concepts = _query_concepts(question)
    if not concepts:
        return 0.0
    matched = _matched_concepts(concepts, text)
    if not matched:
        return 0.0
    coverage = len(matched) / len(concepts)
    return coverage * 0.3 + min(len(matched) * 0.06, 0.18)


def _matched_concepts(concepts: list[set[str]], text: str) -> list[set[str]]:
    normalized_text = text.lower()
    compact_text = re.sub(r"\s+", "", normalized_text)
    text_terms = _lexical_terms(normalized_text)
    return [
        concept
        for concept in concepts
        if any(term in text_terms or term in normalized_text or term in compact_text for term in concept)
    ]


def _query_concepts(value: str) -> list[set[str]]:
    concepts: list[set[str]] = []
    seen: set[str] = set()
    for group in _article_reference_groups(value):
        key = "|".join(sorted(group))
        concepts.append(group)
        seen.add(key)
    for term in _domain_terms(value) or _meaningful_terms(value):
        group = _SYNONYM_GROUPS.get(term, {term})
        key = "|".join(sorted(group))
        if key not in seen:
            concepts.append(group)
            seen.add(key)
    return concepts


def _domain_terms(value: str) -> set[str]:
    normalized = value.lower()
    terms = set(re.findall(r"[a-z0-9]+(?:\+[0-9]+)?日?", normalized))
    for term in _SYNONYM_GROUPS:
        if term in normalized:
            terms.add(term)
    return {term for term in terms if term not in _STOP_TERMS}


def _lexical_fallback_terms(value: str) -> list[str]:
    article_terms = sorted(
        {term for group in _article_reference_groups(value) for term in group},
        key=len,
        reverse=True,
    )
    terms = [*article_terms, *sorted(_meaningful_terms(value), key=len, reverse=True)]
    compact_terms: list[str] = []
    for term in terms:
        if len(term) < 3:
            continue
        if any(term in existing or existing in term for existing in compact_terms):
            continue
        compact_terms.append(term)
    return compact_terms[:4]


def _lexical_terms(value: str) -> set[str]:
    normalized = value.lower()
    terms = set(re.findall(r"[a-z0-9]+", normalized))
    terms.update(re.findall(r"[a-z0-9]+(?:\+[0-9]+)?[\u4e00-\u9fff]+", normalized))
    cjk_chars = re.findall(r"[\u4e00-\u9fff]", normalized)
    terms.update(cjk_chars)
    terms.update("".join(cjk_chars[index : index + 2]) for index in range(max(len(cjk_chars) - 1, 0)))
    terms.update("".join(cjk_chars[index : index + 3]) for index in range(max(len(cjk_chars) - 2, 0)))
    return {term for term in terms if term.strip()}


def _meaningful_terms(value: str) -> set[str]:
    terms = set(re.findall(r"[a-z0-9]+(?:\+[0-9]+)?[\u4e00-\u9fff]*", value.lower()))
    cjk_chars = re.findall(r"[\u4e00-\u9fff]", value.lower())
    terms.update("".join(cjk_chars[index : index + 2]) for index in range(max(len(cjk_chars) - 1, 0)))
    terms.update("".join(cjk_chars[index : index + 3]) for index in range(max(len(cjk_chars) - 2, 0)))
    return {
        term
        for term in terms
        if len(term) >= 2 and term.strip() and term not in _STOP_TERMS
    }


_CHINESE_DIGITS = {
    "零": 0,
    "〇": 0,
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}

_ARABIC_TO_CHINESE_DIGITS = {
    0: "零",
    1: "一",
    2: "二",
    3: "三",
    4: "四",
    5: "五",
    6: "六",
    7: "七",
    8: "八",
    9: "九",
}


def _article_reference_groups(value: str) -> list[set[str]]:
    return [_article_terms(number) for number in _article_reference_numbers(value)]


def _article_reference_numbers(value: str) -> list[int]:
    normalized = re.sub(r"\s+", "", value)
    numbers: list[int] = []
    seen_numbers: set[int] = set()
    for number in re.findall(r"第([0-9]{1,4})条", normalized):
        parsed = int(number)
        if parsed not in seen_numbers:
            numbers.append(parsed)
            seen_numbers.add(parsed)
    for number in re.findall(r"第([零〇一二两三四五六七八九十百千]{1,12})条", normalized):
        parsed = _chinese_number_to_int(number)
        if parsed is not None and parsed not in seen_numbers:
            numbers.append(parsed)
            seen_numbers.add(parsed)
    return numbers


def _article_terms(number: int) -> set[str]:
    chinese = _int_to_chinese_number(number)
    return {
        f"第{number}条",
        f"第{chinese}条",
    }


def _focus_article_text(source: Source, question: str) -> Source:
    article_text = extract_requested_article(question, source.text)
    if article_text is not None:
        return source.model_copy(update={"text": article_text})
    return _focus_article_excerpt(source, question)


def extract_requested_article(question: str, text: str) -> str | None:
    numbers = _article_reference_numbers(question)
    if not numbers:
        return None
    for number in numbers:
        match = _find_compact_match(text, list(_article_terms(number)))
        if match is None:
            continue
        start, _end = match
        next_match = _find_next_article_match(text, number, start)
        end = next_match[0] if next_match is not None else len(text)
        article_text = text[start:end].strip()
        return _clean_article_text(article_text)
    return None


def _focus_article_excerpt(source: Source, question: str) -> Source:
    article_groups = _article_reference_groups(question)
    if not article_groups:
        return source
    match = _find_compact_match(source.text, [term for group in article_groups for term in group])
    if match is None:
        return source
    start, end = match
    excerpt_start = max(0, start - 140)
    excerpt_end = min(len(source.text), max(end + 650, start + 650))
    excerpt = source.text[excerpt_start:excerpt_end].strip()
    if excerpt_start > 0:
        excerpt = f"...{excerpt}"
    if excerpt_end < len(source.text):
        excerpt = f"{excerpt}..."
    return source.model_copy(update={"text": excerpt})


def _find_next_article_match(text: str, number: int, start: int) -> tuple[int, int] | None:
    next_number = number + 1
    return _offset_match(_find_compact_match(text[start + 1 :], list(_article_terms(next_number))), start + 1)


def _offset_match(match: tuple[int, int] | None, offset: int) -> tuple[int, int] | None:
    if match is None:
        return None
    return match[0] + offset, match[1] + offset


def _clean_article_text(value: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", value).strip()


def _find_compact_match(text: str, terms: list[str]) -> tuple[int, int] | None:
    compact_chars: list[str] = []
    positions: list[int] = []
    for index, char in enumerate(text):
        if char.isspace():
            continue
        compact_chars.append(char)
        positions.append(index)
    compact_text = "".join(compact_chars)
    for term in sorted(terms, key=len, reverse=True):
        compact_term = re.sub(r"\s+", "", term)
        match_index = compact_text.find(compact_term)
        if match_index >= 0:
            start = positions[match_index]
            end = positions[match_index + len(compact_term) - 1] + 1
            return start, end
    return None


def _chinese_number_to_int(value: str) -> int | None:
    if not value:
        return None
    if value == "十":
        return 10
    total = 0
    current = 0
    unit_seen = False
    units = {"十": 10, "百": 100, "千": 1000}
    for char in value:
        if char in _CHINESE_DIGITS:
            current = _CHINESE_DIGITS[char]
            continue
        if char in units:
            unit_seen = True
            total += (current or 1) * units[char]
            current = 0
            continue
        return None
    total += current
    if total == 0 and not unit_seen:
        return None
    return total


def _int_to_chinese_number(number: int) -> str:
    if number < 0 or number > 9999:
        return str(number)
    if number < 10:
        return _ARABIC_TO_CHINESE_DIGITS[number]
    if number < 100:
        tens, ones = divmod(number, 10)
        prefix = "十" if tens == 1 else f"{_ARABIC_TO_CHINESE_DIGITS[tens]}十"
        return prefix if ones == 0 else f"{prefix}{_ARABIC_TO_CHINESE_DIGITS[ones]}"
    if number < 1000:
        hundreds, remainder = divmod(number, 100)
        prefix = f"{_ARABIC_TO_CHINESE_DIGITS[hundreds]}百"
        if remainder == 0:
            return prefix
        if remainder < 10:
            return f"{prefix}零{_ARABIC_TO_CHINESE_DIGITS[remainder]}"
        return f"{prefix}{_int_to_chinese_number(remainder)}"
    thousands, remainder = divmod(number, 1000)
    prefix = f"{_ARABIC_TO_CHINESE_DIGITS[thousands]}千"
    if remainder == 0:
        return prefix
    if remainder < 100:
        return f"{prefix}零{_int_to_chinese_number(remainder)}"
    return f"{prefix}{_int_to_chinese_number(remainder)}"
