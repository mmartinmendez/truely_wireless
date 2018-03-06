import pyshark
import access_points as ap
import netifaces as ni
import matplotlib.pyplot as plt

readMode = True

def main():
    filename = 'save4.pcap'
    accessPointName = 'FRITZ!Box Fon 7360 - extended'
    interfaceName = 'en0'

    get_network_card(interfaceName)
    filter = get_access_point_mac(accessPointName)
    if(readMode == False):
        timeout = 20
        capture_packet(filename, timeout, interfaceName, filter)
    print_from_file(filename, filter)
    # addresses_list('./sav2.pcap')

def capture_packet(filename, timeout, interface, filter):
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


""" 
    Values compared between 5 distances
    The average value of signal strength, signal noise and snr from captured data is stored into an array
    This data is then plotted against distance at which the packets were captured
    
    Run only after confirming if all the files needed are present 
"""
def scenerio_distance(no_files):
    #TODO


"""
    Investigate if interference causes degradation of signal strength
    Find point at which the access point switches node

    Find gradient with distance away from this point. See if there is a big variation close to this point.
"""
def scenerio_interference():
    #TODO

"""
    Investigate the difference the access point model contributes towards the signal strength
"""
def scenerio_manufacturer():
    #TODO

"""
    Investigate the improvement/degradation caused by channel hop
"""
def scenerio_channel():
    #TODO

main()

