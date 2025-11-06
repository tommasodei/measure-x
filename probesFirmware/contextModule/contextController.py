import serial
import time

class ContextController:
    
    def __init__(self, port="/dev/mhi_DUN", baudrate=115200, timeout=1.5):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial = serial.Serial(port=self.port, baudrate=self.baudrate, timeout=self.timeout)
        
    def send_at(self, cmd, timeout=2.0):
        """
        Send an AT command and return full response as text
        """
        try:
            at_cmd = (cmd + "\r").encode()
            self.serial.reset_input_buffer()
            self.serial.write(at_cmd)
            
            end_time = time.time() + timeout
            lines = []
            
            while time.time() < end_time:
                line = self.serial.readline().decode(errors="ignore").strip()
                if line:
                    lines.append(line)
                    if line == "OK" or line.startswith("ERROR"):
                        break
                        
            print(lines)
            return "\n".join(lines)
        except Exception as e:
            print(f"ContextModule ERROR sending AT '{cmd}': {e}")
            return ""
    
    def extract(self, raw, prefix):
        """
        Return first line starting with prefix
        """
        for line in raw.splitlines():
            if line.strip().startswith(prefix):
                return line.strip()
        return None
    
    def parse_qeng_servingcell(self, raw):
        """
        Example (LTE):
        +QENG: "servingcell","NOCONN","LTE","FDD",22201,51,165,6300,3,20,20,2,8,8,-95,-10,-5,14,15
        """
        line = self.extract(raw, "+QENG:")
        if not line:
            return {}

        parts = line.split(",")

        try:
            return {
                "rat": parts[2].replace('"', ''),
                "mode": parts[3].replace('"', ''),
                "plmn": parts[4],
                "tac": int(parts[5]),
                "cell_id": int(parts[6]),
                "pci": int(parts[7]),
                "arfcn": int(parts[8]),
                "bandwidth": parts[9],
                "rsrp": int(parts[-5]),
                "rsrq": int(parts[-4]),
                "rssi": int(parts[-3]),
                "sinr": int(parts[-2]),
                "cqi": int(parts[-1]),
            }
        except Exception:
            return {}

    def parse_qnwinfo(self, raw):
        """
        +QNWINFO: "FDD LTE","TIM IT","LTE BAND 3",1300
        """
        line = self.extract(raw, "+QNWINFO:")
        if not line:
            return {}

        try:
            items = line.split(":", 1)[1].split(",")
            return {
                "rat": items[0].replace('"', '').strip(),
                "operator_name": items[1].replace('"', '').strip(),
                "band": items[2].replace('"', '').strip(),
            }
        except Exception:
            return {}

    def parse_cops(self, raw):
        """
        +COPS: 0,0,"TIM",7
        """
        line = self.extract(raw, "+COPS:")
        if not line:
            return {}

        try:
            fields = line.split(",")
            operator = fields[2].replace('"', "")
            return {"operator_name": operator}
        except Exception:
            return {}
    
    def parse_csq(self, raw):
        """
        +CSQ: 15,99
        RSSI = (value * 2 - 113) dBm
        """
        line = self.extract(raw, "+CSQ:")
        if not line:
            return {}

        try:
            rssi_raw = int(line.split(":")[1].split(",")[0])
            if rssi_raw == 99:
                rssi = None
            else:
                rssi = rssi_raw * 2 - 113
            return {"rssi": rssi}
        except Exception:
            return {}
    
    def parse_creg(self, raw):
        """
        Parse registration state from +CREG response
        Example: +CREG: 0,1
        """
        if "+CREG:" not in raw:
            return {}
        try:
            state = raw.split(",")[-1].strip()
            return {"connection_state": state}
        except Exception:
            return {"connection_state": None}

        
    def read_context(self, msm_id):
        """
        Creation of the context
        """
        context = {"msm_id": msm_id}
        
        # Serving cell info
        qeng = self._send_at("AT+QENG=\"servingcell\"")
        context.update(self._parse_qeng_servingcell(qeng))

        # RAT/Operator/Band
        qnw = self._send_at("AT+QNWINFO")
        context.update(self._parse_qnwinfo(qnw))

        # Operator name
        cops = self.send_at("AT+COPS?")
        context.update(self.parse_cops(cops))

        # RSSI fallback
        csq = self._send_at("AT+CSQ")
        context.update(self._parse_csq(csq))

        # Connection registration state
        creg = self._send_at("AT+CREG?")
        context.update(self._parse_creg(creg))

        return context
