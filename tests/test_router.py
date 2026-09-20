from app.router import route_query

def test_weather_route():
    i = route_query("What is the weather in Singapore tomorrow?")
    assert i.weather and not i.currency

def test_currency_route():
    i = route_query("Convert INR 50,000 to SGD")
    assert i.currency
    assert i.amount == 50000
    assert i.from_currency == "INR"
    assert i.to_currency == "SGD"

def test_combined_route():
    i = route_query("Plan a three-day Singapore itinerary and adjust it for the weather forecast.")
    assert i.rag and i.weather

def test_rag_only():
    i = route_query("Which neighbourhoods are best for cultural experiences?")
    assert i.rag and not i.weather and not i.currency
