import pyshark
import os, os.path
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

def calculate_average(filename, filter):
    flt = 'wlan.ta == ' + str(filter)
    cap = pyshark.FileCapture(filename, display_filter=flt)
    sum = 0
    i = 0
    for pkt in cap
        snr = int(pkt.radiotap.dbm_antsignal)-int(pkt.radiotap.dbm_antnoise)
        sum += snr
        i += 1
    average = sum/i
    return average

def get_snr_values(files):
    snr = []
    for i in range(n_files):
        snr.append(calculate_average(files[i], flt))
    return snr

""" 
    Values compared between 5 distances
    The average value of signal strength, signal noise and snr from captured data is stored into an array
    This data is then plotted against distance at which the packets were captured
    
    Run only after confirming if all the files needed are present 
    20m, 15m, 10m, 5m, <1m
"""
def scenerio_distance(n_files):
    #TODO
    DIR = './distances'
    print len([name for name in os.listdir(DIR) if os.path.isfile(os.path.join(DIR, name))])
    files = {'dt1.pcap', 'dt2.pcap', 'dt3.pcap', 'dt4.pcap', 'dt5.pcap'}
    distance = {1, 5, 10, 15, 20}

    snr = get_snr_values(files)

    plt.plot(snr,distance)
    plt.title('SNR fluctuation with distance to the access point')
    plt.xlabel('Distance')
    plt.ylabel('SNR')
    plt.savefig("distance_plot.pdf", bbox_inches='tight', pad_inches=0.5)
    plt.close()

"""
    Investigate if interference causes degradation of signal strength
    Find point at which the access point switches node

    Find gradient with distance away from this point. See if there is a big variation close to this point.
"""
def scenerio_interference():
    #TODO
    DIR = './interference'
    print len([name for name in os.listdir(DIR) if os.path.isfile(os.path.join(DIR, name))])
    files = {'inter1.pcap', 'inter2.pcap', 'inter3.pcap'}
    distance = {1,2,3,4,5}

    snr = get_snr_values(files)

    plt.plot(snr, distance)
    plt.title('SNR fluctuation with distance from the interference point')
    plt.xlabel('Distance')
    plt.ylabel('SNR')
    plt.savefig("interference_plot.pdf", bbox_inches='tight', pad_inches=0.5)
    plt.close()

"""
    Investigate the difference the access point model contributes towards the signal strength
    Take values at a distance of 5m from the access points
"""
def scenerio_manufacturer():
    #TODO
    DIR = './manufacturer'
    print len([name for name in os.listdir(DIR) if os.path.isfile(os.path.join(DIR, name))])

    files = {'tp_link.pcap', 'fritzbox.pcap'}
    snr = get_snr_values(files)

    plt.plot(snr)
    plt.title('SNR fluctuation with different access points')
    plt.xlabel('Manufacturer')
    plt.ylabel('SNR')
    plt.savefig("manufacturer_plot.pdf", bbox_inches='tight', pad_inches=0.5)
    plt.close()

"""
    Investigate the improvement/degradation caused by channel hop
"""
def scenerio_channel():
    #TODO
    DIR = './channels'
    print len([name for name in os.listdir(DIR) if os.path.isfile(os.path.join(DIR, name))])

    files = {'channel1.pcap', 'channel2.pcap', 'channel3.pcap'}
    snr = get_snr_values(files)

    plt.plot(snr)
    plt.title('SNR fluctuation with different channels')
    plt.xlabel('Channel')
    plt.ylabel('SNR')
    plt.savefig("manufacturer_plot.pdf", bbox_inches='tight', pad_inches=0.5)
    plt.close()

main()

