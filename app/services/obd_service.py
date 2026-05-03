import obd
import asyncio
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from app.core.config import settings

logger = logging.getLogger(__name__)

LIVE_PIDS = [
    obd.commands.RPM,
    obd.commands.SPEED,
    obd.commands.COOLANT_TEMP,
    obd.commands.INTAKE_TEMP,
    obd.commands.MAF,
    obd.commands.THROTTLE_POS,
    obd.commands.ENGINE_LOAD,
    obd.commands.SHORT_FUEL_TRIM_1,
    obd.commands.LONG_FUEL_TRIM_1,
    obd.commands.TIMING_ADVANCE,
    obd.commands.FUEL_LEVEL,
    obd.commands.AMBIANT_AIR_TEMP,
    obd.commands.OIL_TEMP,
]


@dataclass
class SensorReading:
    name: str
    value: Any
    unit: str
    pid: str


@dataclass
class DTCCode:
    code: str
    description: str


class OBDService:
    def __init__(self):
        self.connection: Optional[obd.OBD] = None
        self._lock = asyncio.Lock()
        self._is_connected = False

    @property
    def is_connected(self) -> bool:
        return self._is_connected and self.connection is not None and self.connection.is_connected()

    async def connect(self, port: Optional[str] = None) -> Dict[str, Any]:
        async with self._lock:
            if self.is_connected:
                await self.disconnect()
            loop = asyncio.get_event_loop()
            def _connect():
                return obd.OBD(
                    portstr=port or settings.OBD_PORT,
                    baudrate=settings.OBD_BAUDRATE,
                    fast=True,
                    timeout=10,
                )
            try:
                self.connection = await loop.run_in_executor(None, _connect)
                self._is_connected = self.connection.is_connected()
                if not self._is_connected:
                    return {"success": False, "error": "Adapter pronađen ali nema odgovora od ECU. Provjeri kontakt."}
                protocol = str(self.connection.protocol_name())
                supported = len(self.connection.supported_commands)
                return {"success": True, "protocol": protocol, "supported_commands": supported}
            except Exception as e:
                self._is_connected = False
                return {"success": False, "error": str(e)}

    async def disconnect(self):
        if self.connection:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.connection.close)
            self.connection = None
            self._is_connected = False

    async def get_dtc_codes(self) -> List[DTCCode]:
        if not self.is_connected:
            return []
        loop = asyncio.get_event_loop()
        def _get_dtc():
            response = self.connection.query(obd.commands.GET_DTC)
            if response.is_null():
                return []
            return [DTCCode(code=str(code), description=str(desc)) for code, desc in response.value]
        return await loop.run_in_executor(None, _get_dtc)

    async def clear_dtc_codes(self) -> bool:
        if not self.is_connected:
            return False
        loop = asyncio.get_event_loop()
        def _clear():
            response = self.connection.query(obd.commands.CLEAR_DTC)
            return not response.is_null()
        return await loop.run_in_executor(None, _clear)

    async def read_all_sensors(self) -> Dict[str, Any]:
        if not self.is_connected:
            return {}
        loop = asyncio.get_event_loop()
        def _read():
            sensors = {}
            for cmd in LIVE_PIDS:
                try:
                    response = self.connection.query(cmd)
                    if not response.is_null():
                        val = response.value
                        if hasattr(val, 'magnitude'):
                            sensors[cmd.name] = {
                                "name": cmd.name,
                                "value": round(val.magnitude, 2),
                                "unit": str(val.units),
                                "pid": cmd.command.decode(),
                            }
                except Exception:
                    pass
            return sensors
        return await loop.run_in_executor(None, _read)

    async def get_vin(self) -> Optional[str]:
        if not self.is_connected:
            return None
        loop = asyncio.get_event_loop()
        def _vin():
            try:
                response = self.connection.query(obd.commands.VIN)
                if not response.is_null():
                    return str(response.value)
            except Exception:
                pass
            return None
        return await loop.run_in_executor(None, _vin)

    @staticmethod
    def list_ports() -> List[str]:
        import serial.tools.list_ports
        return [port.device for port in serial.tools.list_ports.comports()]


obd_service = OBDService()