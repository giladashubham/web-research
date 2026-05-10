# Implementation Plan: BrightData SERP Search Provider

This plan outlines the steps to add BrightData's SERP API as a search provider and refactor the provider selection logic to be explicit rather than environment-variable-presence-based.

## 1. Core Changes

### 1.1 New Provider: `BrightDataSearchProvider`
Location: `webresearch/providers/search.py`

Implement a new class `BrightDataSearchProvider` that satisfies the `SearchProvider` protocol.

**Configuration Requirements:**
- `BRIGHTDATA_API_KEY`: API Key for BrightData.
- `BRIGHTDATA_ZONE`: The SERP API zone name (e.g., `serp_api_1`).

**Implementation Details:**
- **Endpoint**: `https://api.brightdata.com/request`
- **Method**: `POST`
- **Payload**:
  ```json
  {
    "zone": "ZONE_NAME",
    "url": "https://www.google.com/search?q={query}&hl=en&gl=us",
    "format": "raw",
    "data_format": "parsed_light"
  }
  ```
- **Response Mapping**:
  - `response["organic"]` -> List of results.
  - `link` -> `SearchResult.url`
  - `title` -> `SearchResult.title`
  - `description` -> `SearchResult.snippet`

### 1.2 Refactor Provider Selection
We will move away from implicit selection based on API keys and use an explicit configuration setting.

**New Environment Variable**: `WEBRESEARCH_SEARCH_PROVIDER`
- Values: `tavily` (default), `brightdata`, `mock`.

**Update `default_search_provider()`**:
- It should read `WEBRESEARCH_SEARCH_PROVIDER`.
- It should raise a clear error if the selected provider is missing its required credentials (instead of silently falling back to mock).

## 2. Configuration & Env Changes

### 2.1 Update `.env.example`
Add the following keys:
```bash
# Provider selection (tavily | brightdata | mock)
WEBRESEARCH_SEARCH_PROVIDER=tavily

# BrightData Credentials
BRIGHTDATA_API_KEY=
BRIGHTDATA_ZONE=
```

### 2.2 Add Settings to `webresearch/types.py` (Optional)
Consider adding a `SearchProviderType` enum to centralize the allowed values.

## 3. Implementation Steps

### Step 1: Define `BrightDataSearchProvider`
Add the class to `webresearch/providers/search.py`.
- Handle async requests using `httpx`.
- Implement robust error handling (BrightData can return 403 for zone issues or 401 for auth).
- URL encode the query before injecting it into the search URL.

### Step 2: Update Provider Factory
Modify `default_search_provider()` in `webresearch/providers/search.py`:
```python
def default_search_provider() -> SearchProvider:
    provider_id = os.getenv("WEBRESEARCH_SEARCH_PROVIDER", "tavily").lower()
    
    if provider_id == "tavily":
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY is required for Tavily provider")
        return TavilySearchProvider(api_key=api_key)
        
    if provider_id == "brightdata":
        api_key = os.getenv("BRIGHTDATA_API_KEY")
        zone = os.getenv("BRIGHTDATA_ZONE")
        if not api_key or not zone:
            raise ValueError("BRIGHTDATA_API_KEY and BRIGHTDATA_ZONE are required")
        return BrightDataSearchProvider(api_key=api_key, zone=zone)
        
    if provider_id == "mock":
        return MockSearchProvider()
        
    raise ValueError(f"Unknown search provider: {provider_id}")
```

### Step 3: Validation & Testing
1. **Unit Test**: Create `tests/providers/test_brightdata.py`.
   - Mock the BrightData API response using `respx`.
   - Verify mapping of fields (`link`, `title`, `description`).
   - Verify error handling for invalid keys/zones.
2. **Factory Test**: Verify that setting `WEBRESEARCH_SEARCH_PROVIDER` correctly switches instances.

## 4. Why This Approach?
- **Explicit Choice**: The user knows exactly which provider they are paying for.
- **Fail Fast**: If a provider is configured but credentials are missing, the system errors immediately instead of wasting tokens with a mock/empty search.
- **Extensibility**: Adding a 4th or 5th provider (e.g., Bing, Serper) follows the same pattern.
