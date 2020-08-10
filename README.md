
# Battery Charge

Analysis of battery charging degradation take home coding test 

## Table of Contents

1. [Context](README.md#context)
1. [Dataset](README.md#dataset)
1. [Results](README.md#results)
1. [Scaling](README.md#scaling)
1. [Setup](README.md#setup)
1. [Run Instructions](README.md#run-instructions)

## Context 

The purpose of the task is the determine when a battery cannot receive a charge due to a fault.
When a battery is getting full, the expected behavior of the battery is a reduction in 
it's ability to receive a charge, and those points should be excluded from the analysis.

## Dataset 

Data consists of time series of battery variables over roughly 4 months of 2017 with the following variables: 
```
pW_EnergyRemaining  - energy left in battery [Wh]
PW_FullPackEnergyAvailable - total energy capacity of battery [Wh]
PW_AvailableChargePower - max power capacity that battery can charge at this time [W]
```
Available charge power is expected to be 3300 W or greater except when it derates.
State of energy (soe) battery is defined as energy remaining over full energy 
(PW_EnergyRemaining / PW_FullPackEnergyAvailable), and is considered to be full when 
soe > 90% is starting to get full.

## Results 

![alt text](images/battery_charge1.png "hover text")

*Fig 1: Monthly average charge power availability for battery 1, without any
consideration of state of energy battery.*

![alt text](images/battery_charge2.png "hover text")

*Fig 2: Monthly average charge power availability for battery 1, excluding
derating times when battery is full (soe > 90%).*

![alt text](images/battery_charge3.png "hover text")

*Fig 3: Monthly average charge power availability for all batteries, excluding
derating times when battery is full (soe > 90%).*

## Setup

I ran this analysis on my local laptop since the data set is so small.
I also did not set up an environment for this analysis since it uses standard 
Python libraries such as Pandas, Numpy and Matplotlib

## Run instructions

This script can be run from the repository directory with the following command 

```
./src/run.sh
```
