import urllib.parse
import datetime
from .Types import MODE_VALUES, SEGMENT

def encodeURIComponent(string):
    o = {"!": "%21", "'": "%27", "(": "%28", ")": "%29", "~": "%7E", "%20": "+", "%00": "\0"}
    encoded_string = urllib.parse.quote(string,safe='*')
    for char, encoded_char in o.items():
        encoded_string = encoded_string.replace(char, encoded_char)
    return encoded_string


def buf2Uint32(data):
    if len(data) != 4:
        raise ValueError("Input data must have exactly 4 bytes")
    uint32_value = int.from_bytes(data, byteorder='big')
    return uint32_value

def buf2Uint16(data):
    if len(data) != 2:
        raise ValueError("Input data must have exactly 2 bytes")
    uint16_value = int.from_bytes(data, byteorder='big')
    return uint16_value

def split_packets(data):
    t = 2
    packets = []
    length = buf2Uint16(data[:2])
    for _ in range(length):
        packet_length = buf2Uint16(data[t:t + 2])
        packet_data = data[t + 2:t + 2 + packet_length]
        packets.append(packet_data)
        t += 2 + packet_length
    return packets
import datetime

def date_to_string(date_obj):
    year = str(date_obj.year)
    month = str(date_obj.month).zfill(2)
    day = str(date_obj.day).zfill(2)
    hour = str(date_obj.hour).zfill(2)
    minute = str(date_obj.minute).zfill(2)
    second = str(date_obj.second).zfill(2)
    return f"{year}-{month}-{day} {hour}:{minute}:{second}"

def calculate_change(entry):
    t = s = i = n = 0
    if 'closePrice' in entry.keys():
        s = entry['lastPrice'] - entry['closePrice']
        t = 100 * s / entry['closePrice']
    if 'openPrice' in entry.keys():
        i = entry['lastPrice'] - entry['openPrice']
        n = 100 * i / entry['openPrice']
    return {
        'change': t,
        'absoluteChange': s,
        'openChange': i,
        'openChangePercent': n
    }


def parse_binary(data):
    if len(data) == 1:
        return None
    packets = split_packets(data)
    result = {}
    for packet in packets:
        token = buf2Uint32(packet[:4])
        segment = token & 255
        divisor = 100
        
        
        if segment == SEGMENT.segmentNseCD:
            divisor = 1e7
        elif not (segment != SEGMENT.segmentBseCD and segment != SEGMENT.segmentNseCOM):
            divisor = 1e4
        if len(packet) == 8:
            result[str(token)] = {
                'mode': MODE_VALUES.modeLTP,
                'isTradeable': True,
                'token': token,
                'lastPrice': buf2Uint32(packet[4:8]) / divisor
            }
        elif len(packet) == 12:
            entry = {
                'mode': MODE_VALUES.modeLTPC,
                'isTradeable': True,
                'token': token,
                'lastPrice': buf2Uint32(packet[4:8]) / divisor,
                'closePrice': buf2Uint32(packet[8:12]) / divisor
            }
            entry.update(calculate_change(entry))
            result[str(token)] = entry
        elif len(packet) in [28, 32]:
            entry = {
                'mode': MODE_VALUES.modeFull,
                'isTradeable': False,
                'token': token,
                'lastPrice': buf2Uint32(packet[4:8]) / divisor,
                'highPrice': buf2Uint32(packet[8:12]) / divisor,
                'lowPrice': buf2Uint32(packet[12:16]) / divisor,
                'openPrice': buf2Uint32(packet[16:20]) / divisor,
                'closePrice': buf2Uint32(packet[20:24]) / divisor
            }
            entry.update(calculate_change(entry))
            result[str(token)] = entry
        elif len(packet) == 492:
            entry = {
                'mode': MODE_VALUES.modeFull,
                'token': token,
                'extendedDepth': {
                    'buy': [],
                    'sell': []
                }
            }
            offset = 12
            depth_data = packet[offset:492]
            for _ in range(40):
                quantity = buf2Uint32(depth_data[:4])
                price = buf2Uint32(depth_data[4:8]) / divisor
                orders = buf2Uint32(depth_data[8:12])
                entry['extendedDepth']['buy' if _ < 20 else 'sell'].append({
                    'quantity': quantity,
                    'price': price,
                    'orders': orders
                })
                depth_data = depth_data[12:]
            result[str(token)] = entry
        elif len(packet) in [164, 184]:
            entry = {
                'mode': MODE_VALUES.modeQuote,
                'token': token,
                'isTradeable': True,
                'volume': buf2Uint32(packet[16:20]),
                'lastQuantity': buf2Uint32(packet[8:12]),
                'totalBuyQuantity': buf2Uint32(packet[20:24]),
                'totalSellQuantity': buf2Uint32(packet[24:28]),
                'lastPrice': buf2Uint32(packet[4:8]) / divisor,
                'averagePrice': buf2Uint32(packet[12:16]) / divisor,
                'openPrice': buf2Uint32(packet[28:32]) / divisor,
                'highPrice': buf2Uint32(packet[32:36]) / divisor,
                'lowPrice': buf2Uint32(packet[36:40]) / divisor,
                'closePrice': buf2Uint32(packet[40:44]) / divisor
            }
            entry.update(calculate_change(entry))
            if len(packet) == 184:
                # 184-byte packet: OI data at 44-60, exchange timestamp at 60-64, depth at 64-184
                entry['lastTradedTime'] = date_to_string(datetime.datetime.fromtimestamp(buf2Uint32(packet[44:48])))
                entry['oi'] = buf2Uint32(packet[48:52])
                entry['oiDayHigh'] = buf2Uint32(packet[52:56])
                entry['oiDayLow'] = buf2Uint32(packet[56:60])
                offset = 64  # Depth starts after OI data + exchange timestamp
            else:
                # 164-byte packet: no OI data, depth starts right after closePrice
                offset = 44
            depth_data = packet[offset:offset+120]
            entry['mode'] = MODE_VALUES.modeFull
            entry['depth'] = {'buy': [], 'sell': []}
            for _ in range(10):
                quantity = buf2Uint32(depth_data[:4])
                price = buf2Uint32(depth_data[4:8]) / divisor
                orders = buf2Uint16(depth_data[8:10])
                entry['depth']['buy' if _ < 5 else 'sell'].append({
                    'quantity': quantity,
                    'price': price,
                    'orders': orders
                })
                depth_data = depth_data[12:]
            #result.append(entry)
            result[str(token)] = entry
    return result
