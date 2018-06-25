import matplotlib.pyplot as plt
import pandas as pd
import matplotlib
matplotlib.rcParams.update({'font.size': 17})
fg = plt.figure()
ax = fg.gca()
PATHSVG = "q_3.svg"

df0 = pd.read_csv('../../data/sixbus/lamda50/data_A_2.csv')
ax.plot(df0['ADMM_IT'][1:500], df0['Q'][1:500], label = "lamda=50", linewidth=0.5)

df0 = pd.read_csv('../../data/sixbus/lamda30/data_A_2.csv')
ax.plot(df0['ADMM_IT'][1:500], df0['Q'][1:500], label = "lamda=30", linewidth=0.5)

df0 = pd.read_csv('../../data/sixbus/lamda25/data_A_2.csv')
ax.plot(df0['ADMM_IT'][1:500], df0['Q'][1:500], label="lamda=25", linewidth=0.5)

df0 = pd.read_csv('../../data/sixbus/lamda20/data_A_2.csv')
ax.plot(df0['ADMM_IT'][1:500], df0['Q'][1:500], label="lamda=20", linewidth=0.5)

df0 = pd.read_csv('../../data/sixbus/lamda15/data_A_2.csv')
ax.plot(df0['ADMM_IT'][1:500], df0['Q'][1:500], label="lamda=15", linewidth=0.5)

central = [df0['Q'][1000]]*499
ax.plot(df0['ADMM_IT'][1:500], central, label = "Consensus value", linewidth=2, linestyle='--')
print(central[1])
ax.legend()
ax.grid()
plt.xlabel("Number of iterations")
plt.ylabel("Reactive power (pu)")
plt.draw()
fg.savefig(PATHSVG, bbox_inches='tight')
