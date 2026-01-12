EESchema Schematic File Version 4
EELAYER 30 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 1 1
Title "SKiDL-Generated Schematic"
Date "2026-1-12"
Rev "v0.1"
Comp ""
Comment1 ""
Comment2 ""
Comment3 ""
Comment4 ""
$EndDescr

$Comp
L Device:Battery BT1
U 1 1 696483d4
P 6000 4200
F 0 "BT1" H 6100 4300 50 000 L CNN
F 1 "9V" H 6100 4200 50 000 L CNN
F 2 "Battery_SMD:Battery_9V" H 6100 4200 50 001 L CNN
   1   6000 4200
   1  0  0  -1
$EndComp

$Comp
L Device:Battery BT2
U 1 1 696483d4
P 5750 4200
F 0 "BT2" H 5850 4300 50 000 L CNN
F 1 "9V" H 5850 4200 50 000 L CNN
F 2 "Battery_SMD:Battery_9V" H 5850 4200 50 001 L CNN
   1   5750 4200
   -1  0  0  -1
$EndComp

Text HLabel 5900 4700 3    50   UnSpc ~ 0
GND_TOP

Text HLabel 5850 3700 1    50   UnSpc ~ 0
VPLUS_TOP

Wire Wire Line
  5750 3950 6000 3950
Wire Wire Line
  5850 3950 5850 3700
Wire Wire Line
  6000 4000 6000 3950
Wire Wire Line
  5750 4000 5750 3950

Wire Wire Line
  5750 4500 5900 4500
Wire Wire Line
  5900 4400 6000 4400
Wire Wire Line
  5750 4500 5750 4400
Wire Wire Line
  5900 4700 5900 4400

Connection ~ 5850 3950

Connection ~ 5900 4500





Text HLabel 5900 4700 3    50   UnSpc ~ 0
GND_TOP

Text HLabel 5850 3700 1    50   UnSpc ~ 0
VPLUS_TOP

$EndSCHEMATC