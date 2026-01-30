import ubluetooth

class BLETransport:
    def __init__(self):
        self.ble = ubluetooth.BLE()
        self.ble.active(True)
        self.connections = set()
        self.buffer = []

        self.SERVICE_UUID = ubluetooth.UUID("12345678-1234-1234-1234-1234567890ab")
        self.CHAR_UUID    = ubluetooth.UUID("abcd1234-5678-90ab-cdef-1234567890ab")

        ((self.tx_char,),) = self.ble.gatts_register_services(
            [(self.SERVICE_UUID, ubluetooth.FLAG_WRITE | ubluetooth.FLAG_NOTIFY)]
        )
        self.ble.irq(self._irq)

    def _irq(self, event, data):
        if event == 1:  # connect
            conn_handle, _, _ = data
            self.connections.add(conn_handle)
        elif event == 2:  # disconnect
            conn_handle, _, _ = data
            self.connections.discard(conn_handle)
        elif event == 3:  # write
            conn_handle, value_handle = data
            msg = self.ble.gatts_read(value_handle).decode()
            self.buffer.append(msg)

    def send(self, msg):
        for conn in self.connections:
            self.ble.gatts_notify(conn, self.tx_char, msg)

    def receive(self):
        buf = self.buffer[:]
        self.buffer = []
        return buf
