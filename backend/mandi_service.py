import httpx
import os
from typing import Optional

AGMARKNET_KEY = os.getenv("AGMARKNET_API_KEY", "579b464db66ec23bdd000001fd708c378207461f583e8eb166ea8ffe")
BASE_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"

async def get_mandi_price(commodity: str, state: str = "Maharashtra") -> str:
    """
    Fetches wholesale prices from Agmarknet API (data.gov.in).
    """
    params = {
        "api-key": AGMARKNET_KEY,
        "format": "json",
        "filters[State]": state,
        "filters[Commodity]": commodity,
        "limit": 5
    }
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(BASE_URL, params=params, timeout=10)
            if resp.status_code != 200:
                return f"Mandi Error: API returned status {resp.status_code}"
            
            data = resp.json()
    
        records = data.get("records", [])
        if not records:
            return f"No live mandi price found for {commodity} in {state} at the moment."
        
        # Format the top 3 records for context
        output = f"LIVE MANDI PRICES for {commodity} in {state}:\n"
        for r in records[:3]:
            output += (
                f"- Market: {r['Market']}\n"
                f"  Price (per Quintal): Min ₹{r['Min Price']} | Max ₹{r['Max Price']} | Modal ₹{r['Modal Price']}\n"
                f"  Update Date: {r['Arrival_Date']}\n"
            )
        
        output += "Source: Agmarknet (data.gov.in)"
        return output

    except Exception as e:
        return f"Mandi Error: {str(e)}"

if __name__ == "__main__":
    # Test script (synchronous wrapper for testing)
    import asyncio
    async def test():
        print(await get_mandi_price("Tomato"))
        print(await get_mandi_price("Wheat"))
    asyncio.run(test())
