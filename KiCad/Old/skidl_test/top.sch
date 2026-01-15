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
L Device:Solar_Cell SC1
U 1 1 696501f8
P 6050 4000
F 0 "SC1" H 6150 4100 50 000 L CNN
F 1 "Solar" H 6150 4000 50 000 L CNN
F 2 "" H 6150 4000 50 001 L CNN
   1   6050 4000
   0  1  1  0
$EndComp

$Comp
L Device:Solar_Cell SC2
U 1 1 696501f8
P 5700 3850
F 0 "SC2" H 5800 3950 50 000 L CNN
F 1 "Solar" H 5800 3850 50 000 L CNN
F 2 "" H 5800 3850 50 001 L CNN
   1   5700 3850
   -1  0  0  -1
$EndComp

$Comp
L Device:Solar_Cell SC3
U 1 1 696501f8
P 5550 4250
F 0 "SC3" H 5650 4350 50 000 L CNN
F 1 "Solar" H 5650 4250 50 000 L CNN
F 2 "" H 5650 4250 50 001 L CNN
   1   5550 4250
   0  1  1  0
$EndComp

Text HLabel 6150 3700 2    50   UnSpc ~ 0
VPLUS

Text HLabel 5450 4050 0    50   UnSpc ~ 0
GND

Wire Wire Line
  6000 3700 6150 3700
Wire Wire Line
  5850 3850 6250 3850
Wire Wire Line
  5700 3650 6000 3650
Wire Wire Line
  5750 4250 5850 4250
Wire Wire Line
  6000 3850 6000 3650
Wire Wire Line
  6250 4000 6250 3850
Wire Wire Line
  5850 4250 5850 3850

Wire Wire Line
  5150 4250 5450 4250
Wire Wire Line
  5150 4000 5950 4000
Wire Wire Line
  5450 4050 5600 4050
Wire Wire Line
  5600 4050 5600 4000
Wire Wire Line
  5150 4250 5150 4000
Wire Wire Line
  5700 4000 5700 3950

Connection ~ 6000 3700
Connection ~ 6000 3850

Connection ~ 5600 4000
Connection ~ 5700 4000







Text HLabel 6150 3700 2    50   UnSpc ~ 0
VPLUS

Text HLabel 5450 4050 0    50   UnSpc ~ 0
GND

$EndSCHEMATC