# Hello my name is Arsalan Rahman Mirza
# I have wrote this program for calculating the SER which is the Slope Error Rate
# If you have any question about the implementation you can directly contact me
# arsalan.mirza@soran.edu.iq or ersalen@gmail.com
# Feel free to use
import math
import numpy as np

def ser(input1, input2, boolflag=False):
  FN = None
  FP = None

  # Case 1: input1 and input2 are floats or integers between 0 and 1
  if (isinstance(input1, (float, int)) and isinstance(input2, (float, int))):
    if (0 <= input1 <= 1) and (0 <= input2 <= 1):
      FN = input1
      FP = input2
    else:
      raise ValueError("One of the parameters are not between 0 and 1.")
  # Case 2: input1 and input2 are 1D numpy arrays of the same length
  elif isinstance(input1, np.ndarray) and isinstance(input2, np.ndarray):
    if len(input1.shape) != 1 or len(input2.shape) != 1:
      raise ValueError("Both NumPy arrays must be 1-dimensional.")
    if len(input1) != len(input2):
      raise ValueError("Input NumPy arrays must have the same length.")
    if len(input1) == 0:
      raise ValueError("Input NumPy arrays cannot be empty.")

    FN = np.sum((input1 == 1) & (input2 == 0)) / len(input1)
    FP = np.sum((input1 == 0) & (input2 == 1)) / len(input2)
  else:
    raise TypeError("Inputs must be either both floats/integers or both 1D NumPy arrays.")

  # The rest of the ser calculation remains the same
  error_rate = 1;
  l1p1_x = -1;
  l1p2_x = 1;
  l1p1_y = FN
  l1p2_y = FP

  if FP == FN:
    # If FN and FP are equal, the line is horizontal (slop_line_1 = 0)
    # The error_rate would be the FN (or FP) value itself, if we consider it
    # as distance from origin to (0, FN).
    # The previous code returned math.sqrt(math.pow(FP,2)) which is abs(FP).
    return abs(FP)
  else:
    slop_line_1 = (l1p2_y - l1p1_y) / (l1p2_x - l1p1_x)

    l2p1_x = (l1p1_x + l1p2_x) / 2
    l2p1_y = (l1p1_y + l1p2_y) / 2

    # slop_line_1 cannot be zero here because FP != FN
    slop_line_2 = (-1 / slop_line_1)

    # Determine the point on the line perpendicular to (0,1) passing through the midpoint
    if slop_line_2 > 0:
      new_p_x = l1p2_x
      new_p_y = slop_line_2 * new_p_x + (l2p1_y - (slop_line_2 * l2p1_x))
    else:
      new_p_x = l1p1_x
      new_p_y = slop_line_2 * new_p_x + (l2p1_y - (slop_line_2 * l2p1_x))

    x_vec = new_p_x - l2p1_x
    y_vec = new_p_y - l2p1_y

    msv = math.sqrt(math.pow(x_vec, 2) + math.pow(y_vec, 2))

    # msv should not be zero under current problem constraints (l1p1_x=-1, l1p2_x=1, FP!=FN)
    norm_x = x_vec / msv
    norm_y = y_vec / msv

    if slop_line_2 > 0:
      new_bar_x = l2p1_x + norm_x
      new_bar_y = l2p1_y + norm_y
      error_rate = math.sqrt(math.pow(l2p1_x - new_bar_x, 2) + math.pow(1 - new_bar_y, 2))
    else:
      new_bar_x = l2p1_x - norm_x
      new_bar_y = l2p1_y + norm_y
      error_rate = math.sqrt(math.pow(l2p1_x - new_bar_x, 2) + math.pow(1 - new_bar_y, 2)) * -1

    if boolflag:
        return abs(error_rate)
    else:
        return error_rate