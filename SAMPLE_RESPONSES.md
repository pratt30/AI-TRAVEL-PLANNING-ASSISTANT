# Sample Questions and Application Responses

These are illustrative acceptance-test examples. Weather and exchange-rate values are deliberately not hard-coded; the live MCP tools supply them at runtime.

## 1. RAG — attractions

**Question:** What are the must-visit attractions in Singapore?

**Expected response shape:**
- `[KB]` mention attractions supported by retrieved sources such as Marina Bay, Gardens by the Bay, ArtScience Museum, National Gallery, Chinatown, Little India or Sentosa.
- `[AI recommendation]` group compatible attractions into practical day blocks.
- Show source titles/URLs.
- Do not add unsupported ticket prices/opening hours.

## 2. RAG — transportation

**Question:** How can a tourist travel around Singapore?

**Expected response shape:**
- `[KB]` MRT/LRT and buses are the main public transport options described by the KB.
- `[KB]` taxis/rideshares are also described as alternatives.
- `[AI recommendation]` suggest public transport as a planning approach without inventing exact journey times.
- Show sources.

## 3. MCP — weather

**Question:** What is the weather forecast for Singapore for the next three days?

**Expected response shape:**
- `[MCP]` current conditions and forecast returned by `get_weather_forecast`.
- List returned dates, temperatures and precipitation probabilities.
- Identify Open-Meteo and the MCP tool.
- If the tool fails, say so instead of estimating.

## 4. MCP — currency

**Question:** Convert INR 50,000 to SGD.

**Expected response shape:**
- `[MCP]` amount and converted value returned by `convert_currency`.
- Include returned rate/date where available.
- Never use a hard-coded exchange rate.

## 5. Combined RAG + MCP

**Question:** Plan a three-day Singapore trip for next week and adjust outdoor activities according to the weather forecast.

**Expected response shape:**
- `[KB]` attractions and itinerary ideas from retrieved content.
- `[MCP]` forecast from `get_weather_forecast`.
- `[AI recommendation]` day-wise itinerary with weather-aware choices.
- Indoor substitutions must come from retrieved KB content.
- Sources and MCP tool name shown.

## 6. Multi-turn

Turn 1:
> I am travelling with children. Suggest things to do in Singapore.

Turn 2:
> Make it a three-day plan and adjust it if rain is expected.

Expected: the second answer retains the family preference and uses weather information when planning.

## 7. Missing knowledge

**Question:** What is the exact ticket price for every attraction in Singapore?

Expected: explicitly say the KB does not contain enough current ticket-pricing information. Do not invent a table.

## 8. Unsupported live data

**Question:** Is Gardens by the Bay sold out tomorrow?

Expected: explain that reservation/inventory data is not available in the current toolset. Do not guess.
