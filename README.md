<h1 align="center">StrainDAQ</h1>
<h3 align="center">Digital Strain Measurement and Data Acquisition System</h3>

<p align="center">
An embedded instrumentation platform for accurate strain measurement using a Wheatstone Bridge, HX711, Raspberry Pi and Analog Discovery 3.
</p>

---


<p align="center">
<img src="Media/banner.png" width="900">
</p>

---

# Project Demonstration

## 🎥 Demo Video

[calibration video](Media/calibration_video.mp4)


---

# Project Overview

StrainDAQ (**Strain Data Acquisition**) is an embedded instrumentation project developed to accurately measure mechanical strain using a **350 Ω foil strain gauge**, **Wheatstone bridge**, **HX711 24-bit ADC**, **Raspberry Pi**, and **Analog Discovery 3**.

The project focuses on designing a complete signal acquisition chain—from sensing mechanical deformation to displaying digital measurements.

---

# System Architecture

<p align="center">
<img src="Media/system_architecture.png" width="800">
</p>

---

# Working with Y3 Module

```
Mechanical Load
        │
        ▼
 Beam Deformation
        │
        ▼
350 Ω Strain Gauge
        │
        ▼
    Y3 Module 
        │
        ▼
Analog Discovery 3
        │
        ▼
 Raspberry Pi
        │
        ▼
       GUI
```
---
# Working with custom wheatstone

```
Mechanical Load
        │
        ▼
 Beam Deformation
        │
        ▼
350 Ω Strain Gauge
        │
        ▼
Wheatstone bridge 
        │
        ▼       
 Microcontroller
        │
        ▼
       GUI
```
---

# Hardware Components

| Component | Purpose |
|-----------|----------|
| 350 Ω Strain Gauge | Strain sensing |
| Wheatstone Bridge | Resistance-to-voltage conversion |
| HX711 | Signal amplification |
| Raspberry Pi | Processing |
| Analog Discovery 3 | Y3 Module data aqauisition |

---

# Hardware Gallery

| Component | Image |
|-----------|-------|
| Strain Gauge | <img src="Media/strain_gauge.png" width="220"> |
| Wheatstone Bridge | <img src="Media/bridge.png" width="220"> |
|Analog Discovery3|<img src="Media/ad3.png" width="220">|
| HX711 | <img src="Media/hx711.png" width="220"> |
| Raspberry Pi | <img src="Media/r_pi.png" width="220"> |
| Y3 Module | <img src="Media/Y3.png" width="220"> |

---

# Experimental Setup

<p align="center">
<img src="Media/e_setup.png" width="700">
</p>


---

# Development Timeline

## Week 1

*Ideation and understanding of the problem  
development of basic idea to work on*

<p align="center">
<img src="Media/week1.png" width="700">
</p>
The Idea
  
---

## Week 2–3

*Hardware familiarization and Analog Discovery 3 integration*

<p align="center">
<img src="Media/week2.png" width="330">
<img src="Media/week3.png" width="330">
</p>

---

## Week 4

*GUI Development with python  
test codes documented on assigned folder*

<p align="center">
<img src="Media/week4.png" width="700">
</p>

---

## Week 5–6

*Experimental testing and debugging*

<p align="center">
<img src="Media/week5.png" width="330">
<img src="Media/week6.png" width="330">
</p>

---

## Week 7

*After Y3 module failure and non availibility of that specific module we switched to a cutom bridge.  
Custom Wheatstone Bridge*

<p align="center">
<img src="Media/week7.png" width="700">
</p>

---

## Week 8

*calibrating with known weights*

<p align="center">
<img src="Media/week8.png" width="700">
</p>

---

# Results


## Output Readings
*deflections for each 10g coin put at the end of beam*
<p align="center">
<img src="Media/results.png" width="700">
</p>

*strain is proportional to force at end for bending so these deflection can be mapped to strain by getting a correct proportionality constant*

---

# Future Improvements

- Automatic Young's Modulus calculation
- Temperature compensation
- Wireless monitoring
- Multi-channel acquisition
- PCB implementation
- Cloud dashboard
- Real-time plotting

---
