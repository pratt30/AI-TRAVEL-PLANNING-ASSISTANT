# 5-Minute Demonstration Guide

## 0:00–0:45 — Architecture
Show the README diagram. Explain the separation between stable destination knowledge and current data.

## 0:45–1:30 — RAG
Ask:
> Which neighbourhoods are suitable for cultural experiences in Singapore?

Point out retrieved source metadata and that no MCP call is needed.

## 1:30–2:15 — Weather MCP
Ask:
> What is the weather forecast for Singapore for the next three days?

Point out the `get_weather_forecast` tool and live returned values.

## 2:15–3:30 — Combined scenario
Ask:
> Plan a three-day Singapore trip for next week and adjust outdoor activities according to the weather forecast.

Point out RAG evidence, MCP forecast and `[AI recommendation]` substitutions.

## 3:30–4:15 — Currency MCP
Ask:
> Convert INR 50,000 to SGD.

Point out `convert_currency`, returned rate/date and absence of hard-coded values.

## 4:15–5:00 — Context + no hallucination
First:
> I am travelling with children. Keep the plan family-friendly.

Then:
> Make it three days and adapt it to rain.

Finally:
> What is the exact ticket price for every attraction in Singapore?

Show that the assistant preserves context and states when the KB is insufficient.
