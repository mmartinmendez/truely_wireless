import pyshark
import access_points as ap
import netifaces as ni
import matplotlib.pyplot as plt

readMode = True

def main():
    filename = 'save4.pcap'
    get_network_card('en0')
    filter = get_access_point_mac('FRITZ!Box Fon 7360 - extended')
    if(readMode == False):
        timeout = 20
        capture_packet(filename, timeout, 'en0', filter)
    print_from_file(filename, filter)
    # addresses_list('./sav2.pcap')

def capture_packet(filename, timeout, interface, filter):
    flt = 'wlan.ta == '+str(filter)
    cap = pyshark.LiveCapture(output_file=filename, interface=interface, monitor_mode=True)
    cap.sniff(timeout=timeout)

def print_from_file(filename, filter):
    flt = 'wlan.ta == ' + str(filter)
    print flt
    cap = pyshark.FileCapture(filename, display_filter=flt)

    i = 0
    for pkt in cap:
        if(hasattr(pkt.radiotap, 'datarate') and hasattr(pkt.radiotap, 'dbm_antnoise') and hasattr(pkt.radiotap, 'dbm_antsignal')):
            data_rate = pkt.radiotap.datarate
            signal_noise = int(pkt.radiotap.dbm_antnoise)
            signal_strength = int(pkt.radiotap.dbm_antsignal)

            print('Data rate: {}, Signal strength: {}, Signal noise: {}'.format(data_rate,signal_strength,signal_noise))
            print('SNR value: {}'.format((signal_strength-signal_noise)))
            i = i+1
    print i

def get_network_card(ifname):
    gws = ni.gateways()
    print('Gateway ip: {}'.format(gws['default'][ni.AF_INET][0]))  # default gateway ip
    ip = ni.ifaddresses(ifname)[ni.AF_INET][0]['addr']
    print('Network card ip: {}'.format(ip))  # network card ip
    print('Network card mac addr: {}'.format(ni.ifaddresses(ifname)[ni.AF_LINK][0]['addr']))

def addresses_list(filename):
    cap = pyshark.FileCapture(filename)
    for pkt in cap:
        if(hasattr(pkt.wlan, 'addr') and hasattr(pkt.wlan, 'bssid')):
            print pkt.wlan.addr
            print pkt.wlan.bssid
            print("\n")

def get_access_point_mac(node_name):
    wifi = ap.get_scanner().get_access_points()
    for node in wifi:
        if(node['ssid'] == node_name):
            print('Gateway mac addr: {}'.format(node['bssid']))
            print "\n"
            return str(node['bssid'])


main()

