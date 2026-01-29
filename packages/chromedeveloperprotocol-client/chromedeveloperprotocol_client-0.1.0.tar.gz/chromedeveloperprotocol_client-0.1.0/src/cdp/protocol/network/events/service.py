"""CDP Network Domain Events"""
from ..types import *
from .types import *
from typing import Optional, Dict, Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from ....service import Client

class NetworkEvents:
    """
    Events for the Network domain.
    """
    def __init__(self, client: "Client"):
        """
        Initialize the Network events.
        
        Args:
            client ("Client"): The parent CDP client instance.
        """
        self.client = client

    def on_data_received(self, callback: Callable[[dataReceivedEvent,Optional[str]], None]=None) -> None:
        """
    Fired when data chunk was received over the network.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: dataReceivedEvent, session_id: Optional[str]).
        """
        self.client.on('Network.dataReceived', callback)
    def on_event_source_message_received(self, callback: Callable[[eventSourceMessageReceivedEvent,Optional[str]], None]=None) -> None:
        """
    Fired when EventSource message is received.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: eventSourceMessageReceivedEvent, session_id: Optional[str]).
        """
        self.client.on('Network.eventSourceMessageReceived', callback)
    def on_loading_failed(self, callback: Callable[[loadingFailedEvent,Optional[str]], None]=None) -> None:
        """
    Fired when HTTP request has failed to load.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: loadingFailedEvent, session_id: Optional[str]).
        """
        self.client.on('Network.loadingFailed', callback)
    def on_loading_finished(self, callback: Callable[[loadingFinishedEvent,Optional[str]], None]=None) -> None:
        """
    Fired when HTTP request has finished loading.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: loadingFinishedEvent, session_id: Optional[str]).
        """
        self.client.on('Network.loadingFinished', callback)
    def on_request_served_from_cache(self, callback: Callable[[requestServedFromCacheEvent,Optional[str]], None]=None) -> None:
        """
    Fired if request ended up loading from cache.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: requestServedFromCacheEvent, session_id: Optional[str]).
        """
        self.client.on('Network.requestServedFromCache', callback)
    def on_request_will_be_sent(self, callback: Callable[[requestWillBeSentEvent,Optional[str]], None]=None) -> None:
        """
    Fired when page is about to send HTTP request.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: requestWillBeSentEvent, session_id: Optional[str]).
        """
        self.client.on('Network.requestWillBeSent', callback)
    def on_resource_changed_priority(self, callback: Callable[[resourceChangedPriorityEvent,Optional[str]], None]=None) -> None:
        """
    Fired when resource loading priority is changed    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: resourceChangedPriorityEvent, session_id: Optional[str]).
        """
        self.client.on('Network.resourceChangedPriority', callback)
    def on_signed_exchange_received(self, callback: Callable[[signedExchangeReceivedEvent,Optional[str]], None]=None) -> None:
        """
    Fired when a signed exchange was received over the network    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: signedExchangeReceivedEvent, session_id: Optional[str]).
        """
        self.client.on('Network.signedExchangeReceived', callback)
    def on_response_received(self, callback: Callable[[responseReceivedEvent,Optional[str]], None]=None) -> None:
        """
    Fired when HTTP response is available.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: responseReceivedEvent, session_id: Optional[str]).
        """
        self.client.on('Network.responseReceived', callback)
    def on_web_socket_closed(self, callback: Callable[[webSocketClosedEvent,Optional[str]], None]=None) -> None:
        """
    Fired when WebSocket is closed.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: webSocketClosedEvent, session_id: Optional[str]).
        """
        self.client.on('Network.webSocketClosed', callback)
    def on_web_socket_created(self, callback: Callable[[webSocketCreatedEvent,Optional[str]], None]=None) -> None:
        """
    Fired upon WebSocket creation.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: webSocketCreatedEvent, session_id: Optional[str]).
        """
        self.client.on('Network.webSocketCreated', callback)
    def on_web_socket_frame_error(self, callback: Callable[[webSocketFrameErrorEvent,Optional[str]], None]=None) -> None:
        """
    Fired when WebSocket message error occurs.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: webSocketFrameErrorEvent, session_id: Optional[str]).
        """
        self.client.on('Network.webSocketFrameError', callback)
    def on_web_socket_frame_received(self, callback: Callable[[webSocketFrameReceivedEvent,Optional[str]], None]=None) -> None:
        """
    Fired when WebSocket message is received.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: webSocketFrameReceivedEvent, session_id: Optional[str]).
        """
        self.client.on('Network.webSocketFrameReceived', callback)
    def on_web_socket_frame_sent(self, callback: Callable[[webSocketFrameSentEvent,Optional[str]], None]=None) -> None:
        """
    Fired when WebSocket message is sent.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: webSocketFrameSentEvent, session_id: Optional[str]).
        """
        self.client.on('Network.webSocketFrameSent', callback)
    def on_web_socket_handshake_response_received(self, callback: Callable[[webSocketHandshakeResponseReceivedEvent,Optional[str]], None]=None) -> None:
        """
    Fired when WebSocket handshake response becomes available.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: webSocketHandshakeResponseReceivedEvent, session_id: Optional[str]).
        """
        self.client.on('Network.webSocketHandshakeResponseReceived', callback)
    def on_web_socket_will_send_handshake_request(self, callback: Callable[[webSocketWillSendHandshakeRequestEvent,Optional[str]], None]=None) -> None:
        """
    Fired when WebSocket is about to initiate handshake.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: webSocketWillSendHandshakeRequestEvent, session_id: Optional[str]).
        """
        self.client.on('Network.webSocketWillSendHandshakeRequest', callback)
    def on_web_transport_created(self, callback: Callable[[webTransportCreatedEvent,Optional[str]], None]=None) -> None:
        """
    Fired upon WebTransport creation.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: webTransportCreatedEvent, session_id: Optional[str]).
        """
        self.client.on('Network.webTransportCreated', callback)
    def on_web_transport_connection_established(self, callback: Callable[[webTransportConnectionEstablishedEvent,Optional[str]], None]=None) -> None:
        """
    Fired when WebTransport handshake is finished.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: webTransportConnectionEstablishedEvent, session_id: Optional[str]).
        """
        self.client.on('Network.webTransportConnectionEstablished', callback)
    def on_web_transport_closed(self, callback: Callable[[webTransportClosedEvent,Optional[str]], None]=None) -> None:
        """
    Fired when WebTransport is disposed.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: webTransportClosedEvent, session_id: Optional[str]).
        """
        self.client.on('Network.webTransportClosed', callback)
    def on_direct_tcp_socket_created(self, callback: Callable[[directTCPSocketCreatedEvent,Optional[str]], None]=None) -> None:
        """
    Fired upon direct_socket.TCPSocket creation.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: directTCPSocketCreatedEvent, session_id: Optional[str]).
        """
        self.client.on('Network.directTCPSocketCreated', callback)
    def on_direct_tcp_socket_opened(self, callback: Callable[[directTCPSocketOpenedEvent,Optional[str]], None]=None) -> None:
        """
    Fired when direct_socket.TCPSocket connection is opened.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: directTCPSocketOpenedEvent, session_id: Optional[str]).
        """
        self.client.on('Network.directTCPSocketOpened', callback)
    def on_direct_tcp_socket_aborted(self, callback: Callable[[directTCPSocketAbortedEvent,Optional[str]], None]=None) -> None:
        """
    Fired when direct_socket.TCPSocket is aborted.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: directTCPSocketAbortedEvent, session_id: Optional[str]).
        """
        self.client.on('Network.directTCPSocketAborted', callback)
    def on_direct_tcp_socket_closed(self, callback: Callable[[directTCPSocketClosedEvent,Optional[str]], None]=None) -> None:
        """
    Fired when direct_socket.TCPSocket is closed.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: directTCPSocketClosedEvent, session_id: Optional[str]).
        """
        self.client.on('Network.directTCPSocketClosed', callback)
    def on_direct_tcp_socket_chunk_sent(self, callback: Callable[[directTCPSocketChunkSentEvent,Optional[str]], None]=None) -> None:
        """
    Fired when data is sent to tcp direct socket stream.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: directTCPSocketChunkSentEvent, session_id: Optional[str]).
        """
        self.client.on('Network.directTCPSocketChunkSent', callback)
    def on_direct_tcp_socket_chunk_received(self, callback: Callable[[directTCPSocketChunkReceivedEvent,Optional[str]], None]=None) -> None:
        """
    Fired when data is received from tcp direct socket stream.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: directTCPSocketChunkReceivedEvent, session_id: Optional[str]).
        """
        self.client.on('Network.directTCPSocketChunkReceived', callback)
    def on_direct_udp_socket_joined_multicast_group(self, callback: Callable[[directUDPSocketJoinedMulticastGroupEvent,Optional[str]], None]=None) -> None:
        """
    No description available for directUDPSocketJoinedMulticastGroup.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: directUDPSocketJoinedMulticastGroupEvent, session_id: Optional[str]).
        """
        self.client.on('Network.directUDPSocketJoinedMulticastGroup', callback)
    def on_direct_udp_socket_left_multicast_group(self, callback: Callable[[directUDPSocketLeftMulticastGroupEvent,Optional[str]], None]=None) -> None:
        """
    No description available for directUDPSocketLeftMulticastGroup.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: directUDPSocketLeftMulticastGroupEvent, session_id: Optional[str]).
        """
        self.client.on('Network.directUDPSocketLeftMulticastGroup', callback)
    def on_direct_udp_socket_created(self, callback: Callable[[directUDPSocketCreatedEvent,Optional[str]], None]=None) -> None:
        """
    Fired upon direct_socket.UDPSocket creation.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: directUDPSocketCreatedEvent, session_id: Optional[str]).
        """
        self.client.on('Network.directUDPSocketCreated', callback)
    def on_direct_udp_socket_opened(self, callback: Callable[[directUDPSocketOpenedEvent,Optional[str]], None]=None) -> None:
        """
    Fired when direct_socket.UDPSocket connection is opened.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: directUDPSocketOpenedEvent, session_id: Optional[str]).
        """
        self.client.on('Network.directUDPSocketOpened', callback)
    def on_direct_udp_socket_aborted(self, callback: Callable[[directUDPSocketAbortedEvent,Optional[str]], None]=None) -> None:
        """
    Fired when direct_socket.UDPSocket is aborted.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: directUDPSocketAbortedEvent, session_id: Optional[str]).
        """
        self.client.on('Network.directUDPSocketAborted', callback)
    def on_direct_udp_socket_closed(self, callback: Callable[[directUDPSocketClosedEvent,Optional[str]], None]=None) -> None:
        """
    Fired when direct_socket.UDPSocket is closed.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: directUDPSocketClosedEvent, session_id: Optional[str]).
        """
        self.client.on('Network.directUDPSocketClosed', callback)
    def on_direct_udp_socket_chunk_sent(self, callback: Callable[[directUDPSocketChunkSentEvent,Optional[str]], None]=None) -> None:
        """
    Fired when message is sent to udp direct socket stream.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: directUDPSocketChunkSentEvent, session_id: Optional[str]).
        """
        self.client.on('Network.directUDPSocketChunkSent', callback)
    def on_direct_udp_socket_chunk_received(self, callback: Callable[[directUDPSocketChunkReceivedEvent,Optional[str]], None]=None) -> None:
        """
    Fired when message is received from udp direct socket stream.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: directUDPSocketChunkReceivedEvent, session_id: Optional[str]).
        """
        self.client.on('Network.directUDPSocketChunkReceived', callback)
    def on_request_will_be_sent_extra_info(self, callback: Callable[[requestWillBeSentExtraInfoEvent,Optional[str]], None]=None) -> None:
        """
    Fired when additional information about a requestWillBeSent event is available from the network stack. Not every requestWillBeSent event will have an additional requestWillBeSentExtraInfo fired for it, and there is no guarantee whether requestWillBeSent or requestWillBeSentExtraInfo will be fired first for the same request.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: requestWillBeSentExtraInfoEvent, session_id: Optional[str]).
        """
        self.client.on('Network.requestWillBeSentExtraInfo', callback)
    def on_response_received_extra_info(self, callback: Callable[[responseReceivedExtraInfoEvent,Optional[str]], None]=None) -> None:
        """
    Fired when additional information about a responseReceived event is available from the network stack. Not every responseReceived event will have an additional responseReceivedExtraInfo for it, and responseReceivedExtraInfo may be fired before or after responseReceived.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: responseReceivedExtraInfoEvent, session_id: Optional[str]).
        """
        self.client.on('Network.responseReceivedExtraInfo', callback)
    def on_response_received_early_hints(self, callback: Callable[[responseReceivedEarlyHintsEvent,Optional[str]], None]=None) -> None:
        """
    Fired when 103 Early Hints headers is received in addition to the common response. Not every responseReceived event will have an responseReceivedEarlyHints fired. Only one responseReceivedEarlyHints may be fired for eached responseReceived event.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: responseReceivedEarlyHintsEvent, session_id: Optional[str]).
        """
        self.client.on('Network.responseReceivedEarlyHints', callback)
    def on_trust_token_operation_done(self, callback: Callable[[trustTokenOperationDoneEvent,Optional[str]], None]=None) -> None:
        """
    Fired exactly once for each Trust Token operation. Depending on the type of the operation and whether the operation succeeded or failed, the event is fired before the corresponding request was sent or after the response was received.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: trustTokenOperationDoneEvent, session_id: Optional[str]).
        """
        self.client.on('Network.trustTokenOperationDone', callback)
    def on_policy_updated(self, callback: Callable[[policyUpdatedEvent,Optional[str]], None]=None) -> None:
        """
    Fired once security policy has been updated.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: policyUpdatedEvent, session_id: Optional[str]).
        """
        self.client.on('Network.policyUpdated', callback)
    def on_reporting_api_report_added(self, callback: Callable[[reportingApiReportAddedEvent,Optional[str]], None]=None) -> None:
        """
    Is sent whenever a new report is added. And after 'enableReportingApi' for all existing reports.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: reportingApiReportAddedEvent, session_id: Optional[str]).
        """
        self.client.on('Network.reportingApiReportAdded', callback)
    def on_reporting_api_report_updated(self, callback: Callable[[reportingApiReportUpdatedEvent,Optional[str]], None]=None) -> None:
        """
    No description available for reportingApiReportUpdated.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: reportingApiReportUpdatedEvent, session_id: Optional[str]).
        """
        self.client.on('Network.reportingApiReportUpdated', callback)
    def on_reporting_api_endpoints_changed_for_origin(self, callback: Callable[[reportingApiEndpointsChangedForOriginEvent,Optional[str]], None]=None) -> None:
        """
    No description available for reportingApiEndpointsChangedForOrigin.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: reportingApiEndpointsChangedForOriginEvent, session_id: Optional[str]).
        """
        self.client.on('Network.reportingApiEndpointsChangedForOrigin', callback)
    def on_device_bound_sessions_added(self, callback: Callable[[deviceBoundSessionsAddedEvent,Optional[str]], None]=None) -> None:
        """
    Triggered when the initial set of device bound sessions is added.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: deviceBoundSessionsAddedEvent, session_id: Optional[str]).
        """
        self.client.on('Network.deviceBoundSessionsAdded', callback)
    def on_device_bound_session_event_occurred(self, callback: Callable[[deviceBoundSessionEventOccurredEvent,Optional[str]], None]=None) -> None:
        """
    Triggered when a device bound session event occurs.    
        Args:
            callback (callable, optional): Function called when the event is fired. 
                The callback receives (params: deviceBoundSessionEventOccurredEvent, session_id: Optional[str]).
        """
        self.client.on('Network.deviceBoundSessionEventOccurred', callback)