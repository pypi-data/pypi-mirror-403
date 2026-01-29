import math
def ser(fn,fp, boolflag):
  error_rate = 1;
  l1p1_x = -1;
  l1p2_x = 1;
  l1p1_y = fn
  l1p2_y = fp

  if fp==fn:
    error_rate = math.sqrt(math.pow(fp,2))
    return error_rate
  else:
    slop_line_1 = (l1p2_y-l1p1_y)/(l1p2_x-l1p1_x)

    l2p1_x = (l1p1_x+l1p2_x)/2
    l2p1_y = (l1p1_y+l1p2_y)/2


    slop_line_2 = (-1/slop_line_1)


    if slop_line_2>0:
      new_p_x = l1p2_x
      new_p_y = slop_line_2 * new_p_x + (l2p1_y-(slop_line_2*l2p1_x))
    else:
      new_p_x = l1p1_x
      new_p_y = slop_line_2 * new_p_x + (l2p1_y-(slop_line_2*l2p1_x))

    x_vec = new_p_x-l2p1_x
    y_vec = new_p_y-l2p1_y


    msv = math.sqrt(math.pow(x_vec,2)+math.pow(y_vec,2))

    norm_x = x_vec/msv
    norm_y = y_vec/msv

    if slop_line_2>0:
      new_bar_x = l2p1_x + norm_x
      new_bar_y = l2p1_y + norm_y
      error_rate = math.sqrt(math.pow(l2p1_x-new_bar_x,2)+math.pow(1-new_bar_y,2))
    else:
      new_bar_x = l2p1_x - norm_x
      new_bar_y = l2p1_y + norm_y
      error_rate = math.sqrt(math.pow(l2p1_x-new_bar_x,2)+math.pow(1-new_bar_y,2))*-1

    if boolflag:
        return abs(error_rate)
    else:
        return error_rate