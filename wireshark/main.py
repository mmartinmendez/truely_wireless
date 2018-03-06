import pyshark
import os, os.path
import access_points as ap
import netifaces as ni
import numpy as np
import matplotlib.pyplot as plt

# Flag to switch between read and liveCapture mode
readMode = True

# Flags to set which scenerios to compute
distanceCapture = True
manufacturerCapture = True
channelCapture = True


abs_filter = '3c:08:f6:fb:31:db'
fritz_box = 'c8:0e:14:d7:0a:86'



# Prints out the netwoek information and depending on the flags captures data/analyses captured data
def main():
    DIR = './distances/'
    filename = DIR+'dt1.pcap'
    accessPointName = 'eduroam'
    interfaceName = 'en0'

    get_network_card(interfaceName)
    filter = get_access_point_mac(accessPointName)
    if(readMode == False):
        timeout = 60
        capture_packet(filename, timeout, interfaceName)
    else:
        # print_from_file(filename, filter)
        if(distanceCapture):
            scenerio_distance(3, filter)
        if (manufacturerCapture):
            scenerio_manufacturer()
        if (channelCapture):
            scenerio_channel(filter)

    # addresses_list('./sav2.pcap')
    # print calculate_average('./distances/dt8.pcap', 'wlan.ta == 1c:3e:84:83:5b:66')

# Captures packets from the interface provided (en0); Also outputs channel and frequency information
def capture_packet(filename, timeout, interface):
    cap = pyshark.LiveCapture(output_file=filename, interface=interface, monitor_mode=True)
    cap.sniff(timeout=timeout)

    print '\n'
    print('Wifi channel: {}'.format(cap[0].wlan_radio.channel))
    print('Wifi frequency: {}'.format(cap[0].wlan_radio.frequency))

# Prints relevant signal information
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


# outputs NIC information
def get_network_card(ifname):
    gws = ni.gateways()
    print '\n'
    print('Gateway ip: {}'.format(gws['default'][ni.AF_INET][0]))  # default gateway ip
    ip = ni.ifaddresses(ifname)[ni.AF_INET][0]['addr']
    print('Network card ip: {}'.format(ip))  # network card ip
    print('Network card mac addr: {}'.format(ni.ifaddresses(ifname)[ni.AF_LINK][0]['addr']))

# outputs the destination and source addresses
def addresses_list(filename):
    cap = pyshark.FileCapture(filename)
    for pkt in cap:
        if(hasattr(pkt.wlan, 'addr') and hasattr(pkt.wlan, 'bssid')):
            print pkt.wlan.addr
            print pkt.wlan.bssid
            print("\n")

# outputs the currently connected access point information
def get_access_point_mac(node_name):
    wifi = ap.get_scanner().get_access_points()
    for node in wifi:
        if(node['ssid'] == node_name):
            print('Gateway mac addr: {}'.format(node['bssid']))
            print('Gateway quality: {}'.format(node.quality))
            print "\n"
            return str(node['bssid'])

# calculates the average SNR value from the different frames in a particular situation
def calculate_average(filename, filter='2e:20:0b:40:d1:67'):
    cap = pyshark.FileCapture(filename, display_filter=filter)
    sum = 0
    j = 0
    print cap[0]
    for pkt in cap:
        if (hasattr(pkt.radiotap, 'datarate') and hasattr(pkt.radiotap, 'dbm_antnoise') and hasattr(pkt.radiotap, 'dbm_antsignal')):
            snr = int(pkt.radiotap.dbm_antsignal)-int(pkt.radiotap.dbm_antnoise)
            sum += snr
            j += 1
    average = sum/j
    return average

# Store and return an array containing the snr values
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
    
    45m, 40m, 35m, 30m, 25m, 20m, 15m, 10m, 5m, <1m
"""
def scenerio_distance(n_files, flt=abs_filter):
    DIR = './distances'
    print len([name for name in os.listdir(DIR) if os.path.isfile(os.path.join(DIR, name))])
    # files = ['dt1.pcap', 'dt2.pcap', 'dt3.pcap', 'dt4.pcap', 'dt5.pcap', 'dt6.pcap', 'dt7.pcap', 'dt8.pcap', 'dt9.pcap', 'dt10.pcap']
    # snr = get_snr_values(files, flt)

    snr = [57,56,35,29,26,24,29,10,4,-14]
    distance = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45]

    plt.bar(distance, height=[57,56,35,29,26,24,29,10,4,-14], width=[4,4,4,4,4,4,4,4,4,4])
    plt.xticks(distance, ['<1', '5', '10', '15', '20', '25', '30', '35', '40', '45']);
    plt.hold(True)
    plt.plot(distance, snr, 'r-')
    plt.xlabel('Distance [m]')
    plt.ylabel('SNR')
    plt.savefig("distance_plot.pdf", bbox_inches='tight', pad_inches=0.5)
    plt.show()

"""
    Investigate the difference the access point model contributes towards the signal strength
    Take values at a distance of 5m from the access points
"""
def scenerio_manufacturer(flt=abs_filter):
    DIR = './manufacturer'
    print len([name for name in os.listdir(DIR) if os.path.isfile(os.path.join(DIR, name))])

    # files = ['iphone.pcap', 'cisco.pcap', 'onePlus.pcap', 'ubee.pcap', 'fritzbox.pcap']
    # mac = ['wlan.ta == 7e:04:d0:67:78:91', 'wlan.ta == 3c:08:f6:fb:31:db', 'wlan.sa == 94:65:2d:8c:bc:c1', 'wlan.ta == 1c:3e:84:83:5b:66', 'wlan.ta == c8:0e:14:d7:0a:86']
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
    DIR = './channels'
    print len([name for name in os.listdir(DIR) if os.path.isfile(os.path.join(DIR, name))])

    # files = ['channel1.pcap', 'channel2.pcap', 'channel3.pcap', 'channel4.pcap', 'channel5.pcap', 'channel6.pcap', 'channel7.pcap', 'channel8.pcap', 'channel9.pcap', 'channel10.pcap', 'channel11.pcap', 'channel12.pcap', 'channel13.pcap']
    # snr = get_snr_values(files, flt)

    x = np.arange(13)
    plt.bar(x, height=[38,46,42,48,48,42,41,41,43,49,46,50,47])
    plt.xticks(x+0.5, ['1','2','3','4','5','6','7','8','9','10','11','12','13']);
    plt.xlabel('Channel')
    plt.ylabel('SNR')
    plt.savefig("channel_plot.pdf", bbox_inches='tight', pad_inches=0.5)
    plt.show()

main()

