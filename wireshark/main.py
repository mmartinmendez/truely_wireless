import pyshark
import os, os.path
import access_points as ap
import netifaces as ni
import numpy as np
import matplotlib.pyplot as plt

readMode = True

distanceCapture = False
interferenceCapture = False
manufacturerCapture = True
channelCapture = False

abs_filter = '3c:08:f6:fb:31:db'
fritz_box = 'c8:0e:14:d7:0a:86'

def main():
    DIR = './distances/'
    filename = DIR+'dt1.pcap'
    accessPointName = 'My Iphone'
    interfaceName = 'en0'

    get_network_card(interfaceName)
    filter = get_access_point_mac(accessPointName)
    if(readMode == False):
        timeout = 60
        capture_packet(filename, timeout, interfaceName)
    else:
        # print_from_file(filename, filter)
        # print_from_file('sample.pcap', filter)
        if(distanceCapture):
            scenerio_distance(3, filter)
        if (interferenceCapture):
            scenerio_interference()
        if (manufacturerCapture):
            scenerio_manufacturer()
        if (channelCapture):
            scenerio_channel(filter)

    # addresses_list('./sav2.pcap')
    # print calculate_average('./manufacturer/iphone.pcap', 'wlan.ta == 7e:04:d0:67:78:91')

def capture_packet(filename, timeout, interface):
    cap = pyshark.LiveCapture(output_file=filename, interface=interface, monitor_mode=True)
    cap.sniff(timeout=timeout)

    print '\n'
    print('Wifi channel: {}'.format(cap[0].wlan_radio.channel))
    print('Wifi frequency: {}'.format(cap[0].wlan_radio.frequency))

def print_from_file(filename, filter=abs_filter):
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

def get_network_card(ifname):
    gws = ni.gateways()
    print '\n'
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
            print('Gateway quality: {}'.format(node.quality))
            print "\n"
            return str(node['bssid'])

def calculate_average(filename, filter='2e:20:0b:40:d1:67'):
    cap = pyshark.FileCapture(filename, display_filter=filter)
    sum = 0
    j = 0
    for pkt in cap:
        if (hasattr(pkt.radiotap, 'datarate') and hasattr(pkt.radiotap, 'dbm_antnoise') and hasattr(pkt.radiotap, 'dbm_antsignal')):
            snr = int(pkt.radiotap.dbm_antsignal)-int(pkt.radiotap.dbm_antnoise)
            sum += snr
            j += 1
    average = sum/j
    return average

def get_snr_values(files, flt):
    snr = []
    # for pkt, ft in zip(files, flt):
    for i in range(len(files)):
        snr.append(calculate_average(files[i], flt[i]))
    return snr

""" 
    Values compared between 5 distances
    The average value of signal strength, signal noise and snr from captured data is stored into an array
    This data is then plotted against distance at which the packets were captured
    
    Run only after confirming if all the files needed are present 
    20m, 15m, 10m, 5m, <1m
"""
def scenerio_distance(n_files, flt=abs_filter):
    #TODO
    DIR = './distances'
    print len([name for name in os.listdir(DIR) if os.path.isfile(os.path.join(DIR, name))])
    files = {'dt1.pcap', 'dt2.pcap', 'dt3.pcap', 'dt4.pcap', 'dt5.pcap'}
    distance = {1, 5, 10, 15, 20}

    snr = get_snr_values(files, flt)

    plt.plot(snr, distance)
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
def scenerio_interference(flt=abs_filter):
    #TODO
    DIR = './interference'
    print len([name for name in os.listdir(DIR) if os.path.isfile(os.path.join(DIR, name))])
    files = {'inter1.pcap', 'inter2.pcap', 'inter3.pcap'}
    distance = {1,2,3,4,5}

    snr = get_snr_values(files, flt)

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
def scenerio_manufacturer(flt=abs_filter):
    #TODO
    DIR = './manufacturer'
    print len([name for name in os.listdir(DIR) if os.path.isfile(os.path.join(DIR, name))])

    # files = ['iphone.pcap', 'cisco.pcap', 'onePlus.pcap', 'ubee.pcap', 'fritzbox.pcap']
    # mac = ['wlan.ta == 7e:04:d0:67:78:91', 'wlan.ta == 3c:08:f6:fb:31:db', 'wlan.sa == 94:65:2d:8c:bc:c1', 'wlan.ta == 1c:3e:84:83:5b:66', 'wlan.ta == ']
    # snr = get_snr_values(files, mac)

    x = np.arange(5)
    plt.bar(x, height=[46,51,34,49,38])
    plt.xticks(x + .5, ['iphone 7', 'cisco', 'onePlus 5', 'ubee', 'fritzbox']);
    plt.xlabel('Manufacturer')
    plt.ylabel('SNR')
    plt.savefig("manufacturer_plot.pdf", bbox_inches='tight', pad_inches=0.5)
    plt.show()

"""
    Investigate the improvement/degradation caused by channel hop
"""
def scenerio_channel(flt='c8:0e:14:d7:0a:86'):
    #TODO
    DIR = './channels'
    print len([name for name in os.listdir(DIR) if os.path.isfile(os.path.join(DIR, name))])

    files = {'channel1.pcap', 'channel2.pcap', 'channel3.pcap', 'channel4.pcap', 'channel5.pcap'}
    snr = get_snr_values(files, flt)

    x = np.arange(5)
    plt.bar(x, height=[46, 51, 34, 49, 38])
    plt.xticks(x + .5, ['iphone', 'cisco', 'onePlus', 'ubee', 'fritzbox']);

    plt.title('SNR fluctuation with different channels')
    plt.xlabel('Channel')
    plt.ylabel('SNR')
    plt.savefig("channel_plot.pdf", bbox_inches='tight', pad_inches=0.5)
    plt.close()

main()

