import matplotlib.pyplot as plt
import pandas as pd

fg = plt.figure()
ax = fg.gca()
PATHSVG = "p_4.svg"

df0 = pd.read_csv('../../data/sixbus/lamda50/data_A_3.csv')
ax.plot(df0['ADMM_IT'][1:500], df0['P'][1:500], label = "lamda=50", linewidth=0.5)

df0 = pd.read_csv('../../data/sixbus/lamda30/data_A_3.csv')
ax.plot(df0['ADMM_IT'][1:500], df0['P'][1:500], label = "lamda=30", linewidth=0.5)

df0 = pd.read_csv('../../data/sixbus/lamda25/data_A_3.csv')
ax.plot(df0['ADMM_IT'][1:500], df0['P'][1:500], label="lamda=25", linewidth=0.5)

df0 = pd.read_csv('../../data/sixbus/lamda20/data_A_3.csv')
ax.plot(df0['ADMM_IT'][1:500], df0['P'][1:500], label="lamda=20", linewidth=0.5)

df0 = pd.read_csv('../../data/sixbus/lamda15/data_A_3.csv')
ax.plot(df0['ADMM_IT'][1:500], df0['P'][1:500], label="lamda=15", linewidth=0.5)

central = [df0['P'][1000]]*499
ax.plot(df0['ADMM_IT'][1:500], central, label = "Optimal value", linewidth=2, linestyle='--')

ax.legend()
ax.grid()
plt.xlabel("Number of iterations")
plt.ylabel("Output active power DER 1(pu)")
plt.draw()
fg.savefig(PATHSVG, bbox_inches='tight')
