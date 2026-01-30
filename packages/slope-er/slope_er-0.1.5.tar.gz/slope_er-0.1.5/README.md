#Slope Error Rate (SER)

A Python implementation of Slope Error Rate (SER), designed to provide improved sensitivity and robustness 
under class imbalance, particularly for biometric authentication systems.

#Overview

Slope Error Rate (SER) is a distance-based evaluation metric that quantifies the trade-off between False Acceptance Rate (FAR) 
and False Rejection Rate (FRR) across decision thresholds. Unlike traditional metrics such as Equal Error Rate (EER), which rely 
on a single operating point, SER captures error dynamics and provides a more informative assessment of classifier behavior.

SER is especially useful in applications where:

Data is highly imbalanced
False positives and false negatives have asymmetric costs
Threshold sensitivity matters

A lower SER value indicates better overall performance.

#Key Features
Designed for binary classification
Robust under class imbalance
Threshold-sensitive evaluation
Based on FAR and FRR geometry
Lightweight and easy to integrate
Suitable for biometrics, spoof detection, anomaly detection, and security systems

# Installation

pip install slope-er==0.1.5

# To import and use

import slope_er

# Call the function

result = slope_er.ser(0.3, 0.7,True)
print(f"The Slope Error Rate is: {result}")

or 

a = np.array([1,1,1,1,1,1,0,0,1,0,1,0])
b = np.array([1,0,1,1,1,1,0,0,1,0,1,0])
result = slope_er.ser(a, b,True)
print(f"The Slope Error Rate is: {result}")


