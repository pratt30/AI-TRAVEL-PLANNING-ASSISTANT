from app.router import route_query

cases = [
    "What are the must-visit attractions in Singapore?",
    "What is the weather in Singapore?",
    "Convert INR 50000 to SGD.",
    "Plan a three-day Singapore itinerary and adjust it for rain.",
]
for q in cases:
    print(q)
    print(route_query(q))
    print("-" * 60)
