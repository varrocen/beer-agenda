# Extraction Strategies Reference

## Table of Contents
1. [JsonCssExtractionStrategy](#jsoncssextractionstrategy)
2. [JsonXPathExtractionStrategy](#jsonxpathextractionstrategy)
3. [RegexExtractionStrategy](#regexextractionstrategy)
4. [LLMExtractionStrategy](#llmextractionstrategy)
5. [Schema Field Types](#schema-field-types)
6. [Nested Structures](#nested-structures)

---

## JsonCssExtractionStrategy

Fast, LLM-free extraction using CSS selectors.

### Schema Structure

```python
schema = {
    "name": "SchemaName",           # Required: identifier
    "baseSelector": "css-selector", # Required: container for each item
    "fields": [                     # Required: list of fields to extract
        {
            "name": "fieldName",    # Required: output key name
            "selector": "css",      # Required: CSS selector relative to baseSelector
            "type": "text",         # Required: text|attribute|html|regex|nested|list
            "attribute": "href",    # Required if type="attribute"
            "pattern": r"\d+",      # Required if type="regex"
            "transform": "strip",   # Optional: strip|lowercase|uppercase
            "default": None         # Optional: default value if not found
        }
    ]
}
```

### Complete Example

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, JsonCssExtractionStrategy
import json

schema = {
    "name": "NewsArticles",
    "baseSelector": "article.news-item",
    "fields": [
        {"name": "title", "selector": "h2.headline", "type": "text", "transform": "strip"},
        {"name": "author", "selector": ".author-name", "type": "text", "default": "Unknown"},
        {"name": "date", "selector": "time", "type": "attribute", "attribute": "datetime"},
        {"name": "link", "selector": "a.read-more", "type": "attribute", "attribute": "href"},
        {"name": "summary", "selector": ".excerpt", "type": "html"},
        {"name": "category", "selector": ".tag", "type": "text", "transform": "lowercase"}
    ]
}

async def extract_news(url):
    strategy = JsonCssExtractionStrategy(schema, verbose=True)
    config = CrawlerRunConfig(extraction_strategy=strategy)

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url, config=config)
        articles = json.loads(result.extracted_content)
        return articles
```

---

## JsonXPathExtractionStrategy

Similar to CSS but uses XPath selectors for complex DOM traversal.

```python
schema = {
    "name": "TableData",
    "baseSelector": "//table[@class='data']//tr[position()>1]",
    "fields": [
        {"name": "col1", "selector": "./td[1]", "type": "text"},
        {"name": "col2", "selector": "./td[2]", "type": "text"},
        {"name": "link", "selector": "./td[3]/a/@href", "type": "text"}
    ]
}

strategy = JsonXPathExtractionStrategy(schema)
```

---

## RegexExtractionStrategy

Fast pattern-based extraction for common data types.

### Built-in Patterns

```python
from crawl4ai import RegexExtractionStrategy

# Use built-in patterns (can combine with |)
strategy = RegexExtractionStrategy(
    pattern=RegexExtractionStrategy.Email | RegexExtractionStrategy.PhoneUS | RegexExtractionStrategy.Url
)

# Available patterns:
# - Email, PhoneUS, PhoneIntl
# - Url, IPv4, IPv6
# - Date, Time, DateTime
# - CreditCard, SSN
# - Price, Percentage
# - Hashtag, Mention
```

### Custom Patterns

```python
strategy = RegexExtractionStrategy(
    custom={
        "product_id": r"SKU-\d{6}",
        "price_usd": r"\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?",
        "dimension": r"\d+x\d+x\d+ (?:cm|in)"
    }
)
```

### Generate Pattern with LLM (One-Time)

```python
from crawl4ai import LLMConfig

# Generate pattern from sample HTML
pattern = RegexExtractionStrategy.generate_pattern(
    label="product_price",
    html=sample_html,
    query="Extract product prices in various formats",
    llm_config=LLMConfig(provider="openai/gpt-4o", api_token="token")
)

# Save and reuse
import json
with open("patterns.json", "w") as f:
    json.dump(pattern, f)

# Use without LLM
strategy = RegexExtractionStrategy(custom=pattern)
```

---

## LLMExtractionStrategy

AI-powered extraction for unstructured or semantically complex content.

### Basic Usage

```python
from crawl4ai import LLMExtractionStrategy, LLMConfig

strategy = LLMExtractionStrategy(
    llm_config=LLMConfig(
        provider="openai/gpt-4o",      # or "ollama/llama3.3", "anthropic/claude-3"
        api_token="your-token",         # None for Ollama
        temperature=0.0
    ),
    instruction="Extract all product information including name, price, and features",
    input_format="fit_markdown"         # markdown|html|fit_markdown
)
```

### With Pydantic Schema

```python
from pydantic import BaseModel
from typing import List, Optional

class Product(BaseModel):
    name: str
    price: float
    currency: str = "USD"
    features: List[str]
    in_stock: Optional[bool] = None

strategy = LLMExtractionStrategy(
    llm_config=LLMConfig(provider="openai/gpt-4o", api_token="token"),
    schema=Product.model_json_schema(),
    extraction_type="schema"
)
```

### Chunking for Large Documents

```python
strategy = LLMExtractionStrategy(
    llm_config=LLMConfig(provider="openai/gpt-4o", api_token="token"),
    instruction="Extract key information",
    chunk_token_threshold=2000,  # Split into smaller chunks
    overlap_rate=0.1,            # 10% overlap between chunks
    apply_chunking=True
)
```

### Supported Providers (via LiteLLM)

- OpenAI: `openai/gpt-4o`, `openai/gpt-4o-mini`
- Anthropic: `anthropic/claude-3-opus`, `anthropic/claude-3-sonnet`
- Ollama (local): `ollama/llama3.3`, `ollama/mistral`
- Google: `gemini/gemini-1.5-pro`
- And many more via LiteLLM

---

## Schema Field Types

| Type | Description | Required Attributes |
|------|-------------|---------------------|
| `text` | Inner text content | - |
| `attribute` | HTML attribute value | `attribute` |
| `html` | Raw HTML content | - |
| `regex` | Regex match on text | `pattern` |
| `nested` | Nested object | `fields` |
| `list` | List of nested items | `fields` |

---

## Nested Structures

### Nested Object

```python
{
    "name": "product",
    "selector": ".product-details",
    "type": "nested",
    "fields": [
        {"name": "brand", "selector": ".brand", "type": "text"},
        {"name": "model", "selector": ".model", "type": "text"}
    ]
}
```

### List of Items

```python
{
    "name": "reviews",
    "selector": ".review-item",
    "type": "list",
    "fields": [
        {"name": "author", "selector": ".reviewer", "type": "text"},
        {"name": "rating", "selector": ".stars", "type": "attribute", "attribute": "data-rating"},
        {"name": "comment", "selector": ".review-text", "type": "text"}
    ]
}
```

### Complete Nested Example

```python
schema = {
    "name": "EcommerceProducts",
    "baseSelector": ".product-card",
    "fields": [
        {"name": "title", "selector": "h2", "type": "text"},
        {"name": "price", "selector": ".price", "type": "text"},
        {
            "name": "details",
            "selector": ".specs",
            "type": "nested",
            "fields": [
                {"name": "sku", "selector": ".sku", "type": "text"},
                {"name": "weight", "selector": ".weight", "type": "text"}
            ]
        },
        {
            "name": "images",
            "selector": ".gallery img",
            "type": "list",
            "fields": [
                {"name": "src", "type": "attribute", "attribute": "src"},
                {"name": "alt", "type": "attribute", "attribute": "alt"}
            ]
        }
    ]
}
```

---

## Combining Strategies

```python
# First pass: CSS extraction for structure
css_strategy = JsonCssExtractionStrategy(product_schema)
result1 = await crawler.arun(url, config=CrawlerRunConfig(extraction_strategy=css_strategy))
products = json.loads(result1.extracted_content)

# Second pass: Regex for specific patterns in descriptions
descriptions = [p["description"] for p in products]
regex_strategy = RegexExtractionStrategy(
    custom={"emails": r"[\w.-]+@[\w.-]+\.\w+"}
)

# Third pass: LLM for semantic analysis (if needed)
llm_strategy = LLMExtractionStrategy(
    llm_config=LLMConfig(provider="openai/gpt-4o", api_token="token"),
    instruction="Classify product sentiment and extract key selling points"
)
```
