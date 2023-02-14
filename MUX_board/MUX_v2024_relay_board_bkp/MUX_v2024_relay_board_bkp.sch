EESchema Schematic File Version 4
EELAYER 30 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 1 9
Title ""
Date ""
Rev ""
Comp ""
Comment1 ""
Comment2 ""
Comment3 ""
Comment4 ""
$EndDescr
$Sheet
S 1350 1250 850  350 
U 62993443
F0 "single_relay" 50
F1 "MUX_1_relay.sch" 50
F2 "VCC" U R 2200 1400 50 
F3 "GND" U R 2200 1500 50 
F4 "Electrode" U L 1350 1350 50 
F5 "Role" U L 1350 1450 50 
F6 "DI" I R 2200 1300 50 
$EndSheet
$Sheet
S 1350 1850 850  350 
U 62994142
F0 "sheet62994142" 50
F1 "MUX_1_relay.sch" 50
F2 "VCC" U R 2200 2000 50 
F3 "GND" U R 2200 2100 50 
F4 "Electrode" U L 1350 1950 50 
F5 "Role" U L 1350 2050 50 
F6 "DI" I R 2200 1900 50 
$EndSheet
$Sheet
S 1350 3050 850  350 
U 629945A0
F0 "sheet629945A0" 50
F1 "MUX_1_relay.sch" 50
F2 "VCC" U R 2200 3200 50 
F3 "GND" U R 2200 3300 50 
F4 "Electrode" U L 1350 3150 50 
F5 "Role" U L 1350 3250 50 
F6 "DI" I R 2200 3100 50 
$EndSheet
$Sheet
S 1350 3650 850  350 
U 62994D3F
F0 "sheet62994D3F" 50
F1 "MUX_1_relay.sch" 50
F2 "VCC" U R 2200 3800 50 
F3 "GND" U R 2200 3900 50 
F4 "Electrode" U L 1350 3750 50 
F5 "Role" U L 1350 3850 50 
F6 "DI" I R 2200 3700 50 
$EndSheet
$Sheet
S 1350 4250 850  350 
U 62994D46
F0 "sheet62994D46" 50
F1 "MUX_1_relay.sch" 50
F2 "VCC" U R 2200 4400 50 
F3 "GND" U R 2200 4500 50 
F4 "Electrode" U L 1350 4350 50 
F5 "Role" U L 1350 4450 50 
F6 "DI" I R 2200 4300 50 
$EndSheet
$Sheet
S 1350 4850 850  350 
U 62994D4D
F0 "sheet62994D4D" 50
F1 "MUX_1_relay.sch" 50
F2 "VCC" U R 2200 5000 50 
F3 "GND" U R 2200 5100 50 
F4 "DI" I R 2200 4900 50 
F5 "Electrode" U L 1350 4950 50 
F6 "Role" U L 1350 5050 50 
$EndSheet
Wire Wire Line
	1100 6300 1100 5650
Wire Wire Line
	1100 5650 1350 5650
Wire Wire Line
	1100 5050 1350 5050
Connection ~ 1100 5650
Wire Wire Line
	1100 5050 1100 4450
Wire Wire Line
	1100 4450 1350 4450
Connection ~ 1100 5050
Wire Wire Line
	1100 4450 1100 3850
Wire Wire Line
	1100 3850 1350 3850
Connection ~ 1100 4450
Wire Wire Line
	1100 3850 1100 3250
Wire Wire Line
	1100 3250 1350 3250
Connection ~ 1100 3850
Wire Wire Line
	1100 3250 1100 2650
Wire Wire Line
	1100 2650 1350 2650
Connection ~ 1100 3250
Wire Wire Line
	1100 2650 1100 2050
Wire Wire Line
	1100 2050 1350 2050
Connection ~ 1100 2650
Wire Wire Line
	1100 2050 1100 1450
Wire Wire Line
	1100 1450 1350 1450
Connection ~ 1100 2050
Wire Wire Line
	2200 1400 2450 1400
Wire Wire Line
	2450 1400 2450 2000
Wire Wire Line
	2200 1500 2350 1500
Wire Wire Line
	2350 1500 2350 2100
Wire Wire Line
	2200 5700 2350 5700
Connection ~ 2350 5700
Wire Wire Line
	2350 5700 2350 6300
Wire Wire Line
	2200 5100 2350 5100
Connection ~ 2350 5100
Wire Wire Line
	2350 5100 2350 5700
Wire Wire Line
	2200 4500 2350 4500
Connection ~ 2350 4500
Wire Wire Line
	2350 4500 2350 5100
Wire Wire Line
	2200 3900 2350 3900
Connection ~ 2350 3900
Wire Wire Line
	2350 3900 2350 4500
Wire Wire Line
	2200 2700 2350 2700
Connection ~ 2350 2700
Wire Wire Line
	2350 2700 2350 3900
Wire Wire Line
	2200 2100 2350 2100
Connection ~ 2350 2100
Wire Wire Line
	2350 2100 2350 2700
Wire Wire Line
	2200 2000 2450 2000
Connection ~ 2450 2000
Wire Wire Line
	2450 2000 2450 2600
Wire Wire Line
	2200 2600 2450 2600
Connection ~ 2450 2600
Wire Wire Line
	2450 2600 2450 3200
Wire Wire Line
	2200 3200 2450 3200
Connection ~ 2450 3200
Wire Wire Line
	2450 3200 2450 3800
Wire Wire Line
	2200 3800 2450 3800
Connection ~ 2450 3800
Wire Wire Line
	2450 3800 2450 4400
Wire Wire Line
	2200 4400 2450 4400
Connection ~ 2450 4400
Wire Wire Line
	2450 4400 2450 5000
Wire Wire Line
	2200 5000 2450 5000
Connection ~ 2450 5000
Wire Wire Line
	2450 5000 2450 5600
Connection ~ 2450 5600
Wire Wire Line
	2450 5600 2450 6300
Wire Wire Line
	2200 5600 2450 5600
Entry Wire Line
	2600 1400 2500 1300
Wire Wire Line
	2500 1300 2200 1300
$Comp
L Connector:Screw_Terminal_01x08 J2
U 1 1 6299B393
P 1700 550
F 0 "J2" V 1664 62  50  0000 R CNN
F 1 "Screw_Terminal_01x08" V 1573 62  50  0000 R CNN
F 2 "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-8-5.08_1x08_P5.08mm_Horizontal" H 1700 550 50  0001 C CNN
F 3 "~" H 1700 550 50  0001 C CNN
	1    1700 550 
	0    -1   -1   0   
$EndComp
$Comp
L Connector:Screw_Terminal_01x08 J4
U 1 1 6299EFBA
P 3050 6800
F 0 "J4" V 2922 6312 50  0000 R CNN
F 1 "Screw_Terminal_01x08" V 3150 7150 50  0000 R CNN
F 2 "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-8-5.08_1x08_P5.08mm_Horizontal" H 3050 6800 50  0001 C CNN
F 3 "~" H 3050 6800 50  0001 C CNN
	1    3050 6800
	0    -1   1    0   
$EndComp
Entry Wire Line
	2650 6300 2750 6400
Entry Wire Line
	2750 6300 2850 6400
Entry Wire Line
	2850 6300 2950 6400
Entry Wire Line
	2950 6300 3050 6400
Entry Wire Line
	3050 6300 3150 6400
Entry Wire Line
	3150 6300 3250 6400
Entry Wire Line
	3250 6300 3350 6400
Entry Wire Line
	3350 6300 3450 6400
Entry Wire Line
	2600 5600 2500 5500
Entry Wire Line
	2600 5000 2500 4900
Entry Wire Line
	2600 4400 2500 4300
Entry Wire Line
	2600 3800 2500 3700
Entry Wire Line
	2600 3200 2500 3100
Entry Wire Line
	2600 2600 2500 2500
Entry Wire Line
	2600 2000 2500 1900
Wire Wire Line
	2200 1900 2500 1900
Wire Wire Line
	2200 2500 2500 2500
Wire Wire Line
	2200 3100 2500 3100
Wire Wire Line
	2200 3700 2500 3700
Wire Wire Line
	2200 4300 2500 4300
Wire Wire Line
	2200 4900 2500 4900
Wire Wire Line
	2200 5500 2500 5500
$Comp
L Connector:Screw_Terminal_01x01 J1
U 1 1 629B0873
P 1100 6500
F 0 "J1" V 972 6580 50  0000 L CNN
F 1 "Screw_Terminal_01x01" V 1063 6580 50  0000 L CNN
F 2 "Connector_PinHeader_2.54mm:PinHeader_1x01_P2.54mm_Vertical" H 1100 6500 50  0001 C CNN
F 3 "~" H 1100 6500 50  0001 C CNN
	1    1100 6500
	0    1    1    0   
$EndComp
Entry Wire Line
	2000 1050 2100 950 
Entry Wire Line
	1900 1050 2000 950 
Entry Wire Line
	1800 1050 1900 950 
Entry Wire Line
	1700 1050 1800 950 
Entry Wire Line
	1600 1050 1700 950 
Entry Wire Line
	1500 1050 1600 950 
Entry Wire Line
	1400 1050 1500 950 
Entry Wire Line
	1300 1050 1400 950 
Entry Wire Line
	850  1250 950  1350
Entry Wire Line
	850  1850 950  1950
Wire Wire Line
	1350 1350 950  1350
Wire Wire Line
	1350 1950 950  1950
Entry Wire Line
	850  2450 950  2550
Entry Wire Line
	850  3050 950  3150
Wire Wire Line
	950  2550 1350 2550
Wire Wire Line
	950  3150 1350 3150
Entry Wire Line
	850  3650 950  3750
Wire Wire Line
	1100 5050 1100 5650
Wire Wire Line
	950  3750 1350 3750
Wire Wire Line
	1350 4350 950  4350
Entry Wire Line
	850  4250 950  4350
Entry Wire Line
	850  4850 950  4950
Entry Wire Line
	850  5450 950  5550
Wire Wire Line
	950  5550 1350 5550
Wire Wire Line
	950  4950 1350 4950
$Comp
L Connector:Screw_Terminal_01x02 J3
U 1 1 629C2738
P 2450 6500
F 0 "J3" V 2322 6580 50  0000 L CNN
F 1 "Screw_Terminal_01x02" V 3050 6100 50  0000 L CNN
F 2 "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal" H 2450 6500 50  0001 C CNN
F 3 "~" H 2450 6500 50  0001 C CNN
	1    2450 6500
	0    1    1    0   
$EndComp
$Sheet
S 1350 5450 850  350 
U 62994D54
F0 "sheet62994D54" 50
F1 "MUX_1_relay.sch" 50
F2 "DI" I R 2200 5500 50 
F3 "VCC" U R 2200 5600 50 
F4 "GND" U R 2200 5700 50 
F5 "Electrode" U L 1350 5550 50 
F6 "Role" U L 1350 5650 50 
$EndSheet
$Sheet
S 1350 2450 850  350 
U 62994599
F0 "sheet62994599" 50
F1 "MUX_1_relay.sch" 50
F2 "VCC" U R 2200 2600 50 
F3 "GND" U R 2200 2700 50 
F4 "Electrode" U L 1350 2550 50 
F5 "Role" U L 1350 2650 50 
F6 "DI" I R 2200 2500 50 
$EndSheet
Text Label 1200 1350 0    50   ~ 0
E8
Text Label 1200 1950 0    50   ~ 0
E7
Text Label 1200 2550 0    50   ~ 0
E6
Text Label 1200 3150 0    50   ~ 0
E5
Text Label 1200 3750 0    50   ~ 0
E4
Text Label 1200 4350 0    50   ~ 0
E3
Text Label 1200 4950 0    50   ~ 0
E2
Text Label 1200 5550 0    50   ~ 0
E1
Wire Wire Line
	2100 750  2100 950 
Wire Wire Line
	2000 750  2000 950 
Wire Wire Line
	1900 750  1900 950 
Wire Wire Line
	1800 750  1800 950 
Wire Wire Line
	1700 750  1700 950 
Wire Wire Line
	1600 750  1600 950 
Wire Wire Line
	1500 750  1500 950 
Wire Wire Line
	1400 750  1400 950 
Text Label 2100 850  0    50   ~ 0
E8
Text Label 2000 850  0    50   ~ 0
E7
Text Label 1900 850  0    50   ~ 0
E6
Text Label 1800 850  0    50   ~ 0
E5
Text Label 1700 850  0    50   ~ 0
E4
Text Label 1600 850  0    50   ~ 0
E3
Text Label 1500 850  0    50   ~ 0
E2
Text Label 1400 850  0    50   ~ 0
E1
Wire Wire Line
	3450 6400 3450 6600
Wire Wire Line
	3350 6600 3350 6400
Wire Wire Line
	3250 6600 3250 6400
Wire Wire Line
	3150 6600 3150 6400
Wire Wire Line
	3050 6400 3050 6600
Wire Wire Line
	2950 6600 2950 6400
Wire Wire Line
	2850 6600 2850 6400
Wire Wire Line
	2750 6600 2750 6400
Wire Bus Line
	850  1050 850  5450
Wire Bus Line
	850  1050 2000 1050
Wire Bus Line
	2600 1400 2600 6300
Wire Bus Line
	2600 6300 3350 6300
Text Label 2750 6600 1    50   ~ 0
DI1
Text Label 2850 6600 1    50   ~ 0
DI2
Text Label 2950 6600 1    50   ~ 0
DI3
Text Label 3050 6600 1    50   ~ 0
DI4
Text Label 3150 6600 1    50   ~ 0
DI5
Text Label 3250 6600 1    50   ~ 0
DI6
Text Label 3350 6600 1    50   ~ 0
DI7
Text Label 3450 6600 1    50   ~ 0
DI8
Text Label 2200 5500 0    50   ~ 0
DI1
Text Label 2200 4900 0    50   ~ 0
DI2
Text Label 2200 4300 0    50   ~ 0
DI3
Text Label 2200 3700 0    50   ~ 0
DI4
Text Label 2200 3100 0    50   ~ 0
DI5
Text Label 2200 2500 0    50   ~ 0
DI6
Text Label 2200 1900 0    50   ~ 0
DI7
Text Label 2200 1300 0    50   ~ 0
DI8
$EndSCHEMATC
