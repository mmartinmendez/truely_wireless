Scenerios:

* Different distances to the Access point
* interference when at the range of two access points
* Different Access points by manufacturer
* Strength in different channels


Steps:

* ifconfig (to find the mac of the network card) (windows - ipconfig)
* ip route (to find the ip of the default device to communicate to) (mac - route -n get default; windows - route print)
* ping -c 10 <ip of default device>
* filter in wireshark: icmp
* filter in wireshark: eth.dst == < destination mac from icmp filter>
