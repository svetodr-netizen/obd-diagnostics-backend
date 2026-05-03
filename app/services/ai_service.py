from groq import AsyncGroq
import json
from typing import List, Dict, Any, Optional, AsyncIterator
from app.core.config import settings

client = AsyncGroq(api_key=settings.GROQ_API_KEY)
MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """Ti si ekspertni AI za auto dijagnostiku. Poznaješ:
- OBD-II protokole i greške (P, C, B, U kodovi)
- Benzinske i dizel motore
- BMW (N47, B47, N54, N55), VAG (TDI, TSI), Mercedes, Toyota
- DPF, EGR, turbo, common rail sustave
- BMW N47: uvijek provjeri timing chain simptome (P0016, P0017, zvuk pri hladnom startu)

Kod analize:
1. Budi tehnički i specifičan
2. Sortiraj po težini: sigurnost → voznost → emisije
3. Procijeni cijenu popravka u EUR
4. Naznači što se može DIY a što mora servis
5. Ako auto nije siguran za vožnju - jasno naglasi

Odgovaraj u markdown formatu sa sekcijama: Analiza, Uzrok, Rizik, Popravak, Cijena."""


async def analyze_dtc_codes(
    dtc_codes: List[Dict],
    vehicle_info: Optional[Dict] = None,
    sensor_data: Optional[Dict] = None,
) -> AsyncIterator[str]:

    vehicle_context = ""
    if vehicle_info:
        vehicle_context = f"Vozilo: {vehicle_info.get('year')} {vehicle_info.get('make')} {vehicle_info.get('model')} motor: {vehicle_info.get('engine_code')}\n"

    sensor_context = ""
    if sensor_data:
        sensor_context = "\nŽivi senzori:\n"
        for key, data in sensor_data.items():
            if isinstance(data, dict):
                sensor_context += f"- {data.get('name')}: {data.get('value')} {data.get('unit', '')}\n"

    codes_text = "\n".join([
        f"- {dtc.get('code')}: {dtc.get('description', 'Nepoznato')}"
        for dtc in dtc_codes
    ])

    prompt = f"{vehicle_context}\nGreške:\n{codes_text}{sensor_context}\n\nNapravi kompletnu dijagnostičku analizu."

    stream = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        stream=True,
        max_tokens=2000,
    )

    async for chunk in stream:
        text = chunk.choices[0].delta.content
        if text:
            yield text


async def analyze_sensor_anomalies(
    sensor_data: Dict[str, Any],
    vehicle_info: Optional[Dict] = None,
) -> AsyncIterator[str]:

    vehicle_context = ""
    if vehicle_info:
        vehicle_context = f"Vozilo: {vehicle_info.get('year')} {vehicle_info.get('make')} {vehicle_info.get('model')}\n"

    sensor_text = json.dumps(sensor_data, indent=2)
    prompt = f"{vehicle_context}\nAnaliziraj ove senzore za anomalije:\n{sensor_text}"

    stream = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        stream=True,
        max_tokens=2000,
    )

    async for chunk in stream:
        text = chunk.choices[0].delta.content
        if text:
            yield text


async def analyze_single_code(
    code: str,
    description: str,
    vehicle_info: Optional[Dict] = None,
) -> AsyncIterator[str]:

    vehicle_context = ""
    if vehicle_info:
        vehicle_context = f"Vozilo: {vehicle_info.get('year')} {vehicle_info.get('make')} {vehicle_info.get('model')}\n"

    prompt = f"{vehicle_context}\nAnaliziraj grešku {code}: {description}"

    stream = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        stream=True,
        max_tokens=1000,
    )

    async for chunk in stream:
        text = chunk.choices[0].delta.content
        if text:
            yield text