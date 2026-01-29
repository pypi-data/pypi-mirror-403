"""CDP BluetoothEmulation Domain Methods"""
from ..types import *
from .types import *
from typing import Optional, Dict, Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from ....service import Client

class BluetoothEmulationMethods:
    """
    Methods for the BluetoothEmulation domain.
    """
    def __init__(self, client: "Client"):
        """
        Initialize the BluetoothEmulation methods.
        
        Args:
            client ("Client"): The parent CDP client instance.
        """
        self.client = client

    async def enable(self, params: Optional[enableParameters]=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Enable the BluetoothEmulation domain.    
        Args:
            params (enableParameters, optional): Parameters for the enable method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the enable call.
        """
        return await self.client.send(method="BluetoothEmulation.enable", params=params,session_id=session_id)
    async def set_simulated_central_state(self, params: Optional[setSimulatedCentralStateParameters]=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Set the state of the simulated central.    
        Args:
            params (setSimulatedCentralStateParameters, optional): Parameters for the setSimulatedCentralState method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the setSimulatedCentralState call.
        """
        return await self.client.send(method="BluetoothEmulation.setSimulatedCentralState", params=params,session_id=session_id)
    async def disable(self, params: None=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Disable the BluetoothEmulation domain.    
        Args:
            params (None, optional): Parameters for the disable method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the disable call.
        """
        return await self.client.send(method="BluetoothEmulation.disable", params=params,session_id=session_id)
    async def simulate_preconnected_peripheral(self, params: Optional[simulatePreconnectedPeripheralParameters]=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Simulates a peripheral with |address|, |name| and |knownServiceUuids| that has already been connected to the system.    
        Args:
            params (simulatePreconnectedPeripheralParameters, optional): Parameters for the simulatePreconnectedPeripheral method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the simulatePreconnectedPeripheral call.
        """
        return await self.client.send(method="BluetoothEmulation.simulatePreconnectedPeripheral", params=params,session_id=session_id)
    async def simulate_advertisement(self, params: Optional[simulateAdvertisementParameters]=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Simulates an advertisement packet described in |entry| being received by the central.    
        Args:
            params (simulateAdvertisementParameters, optional): Parameters for the simulateAdvertisement method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the simulateAdvertisement call.
        """
        return await self.client.send(method="BluetoothEmulation.simulateAdvertisement", params=params,session_id=session_id)
    async def simulate_gatt_operation_response(self, params: Optional[simulateGATTOperationResponseParameters]=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Simulates the response code from the peripheral with |address| for a GATT operation of |type|. The |code| value follows the HCI Error Codes from Bluetooth Core Specification Vol 2 Part D 1.3 List Of Error Codes.    
        Args:
            params (simulateGATTOperationResponseParameters, optional): Parameters for the simulateGATTOperationResponse method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the simulateGATTOperationResponse call.
        """
        return await self.client.send(method="BluetoothEmulation.simulateGATTOperationResponse", params=params,session_id=session_id)
    async def simulate_characteristic_operation_response(self, params: Optional[simulateCharacteristicOperationResponseParameters]=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Simulates the response from the characteristic with |characteristicId| for a characteristic operation of |type|. The |code| value follows the Error Codes from Bluetooth Core Specification Vol 3 Part F 3.4.1.1 Error Response. The |data| is expected to exist when simulating a successful read operation response.    
        Args:
            params (simulateCharacteristicOperationResponseParameters, optional): Parameters for the simulateCharacteristicOperationResponse method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the simulateCharacteristicOperationResponse call.
        """
        return await self.client.send(method="BluetoothEmulation.simulateCharacteristicOperationResponse", params=params,session_id=session_id)
    async def simulate_descriptor_operation_response(self, params: Optional[simulateDescriptorOperationResponseParameters]=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Simulates the response from the descriptor with |descriptorId| for a descriptor operation of |type|. The |code| value follows the Error Codes from Bluetooth Core Specification Vol 3 Part F 3.4.1.1 Error Response. The |data| is expected to exist when simulating a successful read operation response.    
        Args:
            params (simulateDescriptorOperationResponseParameters, optional): Parameters for the simulateDescriptorOperationResponse method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the simulateDescriptorOperationResponse call.
        """
        return await self.client.send(method="BluetoothEmulation.simulateDescriptorOperationResponse", params=params,session_id=session_id)
    async def add_service(self, params: Optional[addServiceParameters]=None,session_id: Optional[str] = None) -> addServiceReturns:
        """
    Adds a service with |serviceUuid| to the peripheral with |address|.    
        Args:
            params (addServiceParameters, optional): Parameters for the addService method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    addServiceReturns: The result of the addService call.
        """
        return await self.client.send(method="BluetoothEmulation.addService", params=params,session_id=session_id)
    async def remove_service(self, params: Optional[removeServiceParameters]=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Removes the service respresented by |serviceId| from the simulated central.    
        Args:
            params (removeServiceParameters, optional): Parameters for the removeService method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the removeService call.
        """
        return await self.client.send(method="BluetoothEmulation.removeService", params=params,session_id=session_id)
    async def add_characteristic(self, params: Optional[addCharacteristicParameters]=None,session_id: Optional[str] = None) -> addCharacteristicReturns:
        """
    Adds a characteristic with |characteristicUuid| and |properties| to the service represented by |serviceId|.    
        Args:
            params (addCharacteristicParameters, optional): Parameters for the addCharacteristic method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    addCharacteristicReturns: The result of the addCharacteristic call.
        """
        return await self.client.send(method="BluetoothEmulation.addCharacteristic", params=params,session_id=session_id)
    async def remove_characteristic(self, params: Optional[removeCharacteristicParameters]=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Removes the characteristic respresented by |characteristicId| from the simulated central.    
        Args:
            params (removeCharacteristicParameters, optional): Parameters for the removeCharacteristic method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the removeCharacteristic call.
        """
        return await self.client.send(method="BluetoothEmulation.removeCharacteristic", params=params,session_id=session_id)
    async def add_descriptor(self, params: Optional[addDescriptorParameters]=None,session_id: Optional[str] = None) -> addDescriptorReturns:
        """
    Adds a descriptor with |descriptorUuid| to the characteristic respresented by |characteristicId|.    
        Args:
            params (addDescriptorParameters, optional): Parameters for the addDescriptor method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    addDescriptorReturns: The result of the addDescriptor call.
        """
        return await self.client.send(method="BluetoothEmulation.addDescriptor", params=params,session_id=session_id)
    async def remove_descriptor(self, params: Optional[removeDescriptorParameters]=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Removes the descriptor with |descriptorId| from the simulated central.    
        Args:
            params (removeDescriptorParameters, optional): Parameters for the removeDescriptor method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the removeDescriptor call.
        """
        return await self.client.send(method="BluetoothEmulation.removeDescriptor", params=params,session_id=session_id)
    async def simulate_gatt_disconnection(self, params: Optional[simulateGATTDisconnectionParameters]=None,session_id: Optional[str] = None) -> Dict[str, Any]:
        """
    Simulates a GATT disconnection from the peripheral with |address|.    
        Args:
            params (simulateGATTDisconnectionParameters, optional): Parameters for the simulateGATTDisconnection method.
            session_id (str, optional): Target session ID for flat protocol usage.
            
        Returns:
    Dict[str, Any]: The result of the simulateGATTDisconnection call.
        """
        return await self.client.send(method="BluetoothEmulation.simulateGATTDisconnection", params=params,session_id=session_id)