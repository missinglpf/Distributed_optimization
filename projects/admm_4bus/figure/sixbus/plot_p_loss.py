import matplotlib.pyplot as plt
import pandas as pd
import matplotlib
matplotlib.rcParams.update({'font.size': 17})
fg = plt.figure()
ax = fg.gca()
PATHSVG = "p_loss.svg"

df0 = pd.read_csv('../../data/sixbus/lamda50/data_A_0.csv')
df1 = pd.read_csv('../../data/sixbus/lamda50/data_A_1.csv')
df2 = pd.read_csv('../../data/sixbus/lamda50/data_A_2.csv')
p_total = df0['P'][2:502]+df1['P'][2:502]+df2['P'][2:502] - [2.1]*500
ax.plot(df0['ADMM_IT'][1:501], p_total, label="lamda=50", linewidth=0.5)

df0 = pd.read_csv('../../data/sixbus/lamda30/data_A_0.csv')
df1 = pd.read_csv('../../data/sixbus/lamda30/data_A_1.csv')
df2 = pd.read_csv('../../data/sixbus/lamda30/data_A_2.csv')
q_total = df0['P'][2:502]+df1['P'][2:502]+df2['P'][2:502] - [2.1]*500
ax.plot(df0['ADMM_IT'][1:501], p_total, label="lamda=30", linewidth=0.5)

df0 = pd.read_csv('../../data/sixbus/lamda25/data_A_0.csv')
df1 = pd.read_csv('../../data/sixbus/lamda25/data_A_1.csv')
df2 = pd.read_csv('../../data/sixbus/lamda25/data_A_2.csv')
p_total = df0['P'][2:502]+df1['P'][2:502]+df2['P'][2:502] - [2.1]*500
ax.plot(df0['ADMM_IT'][1:501], p_total, label="lamda=25", linewidth=0.5)

df0 = pd.read_csv('../../data/sixbus/lamda20/data_A_0.csv')
df1 = pd.read_csv('../../data/sixbus/lamda20/data_A_1.csv')
df2 = pd.read_csv('../../data/sixbus/lamda20/data_A_2.csv')
p_total = df0['P'][2:502]+df1['P'][2:502]+df2['P'][2:502] - [2.1]*500
ax.plot(df0['ADMM_IT'][1:501], p_total, label="lamda=20", linewidth=0.5)

df0 = pd.read_csv('../../data/sixbus/lamda15/data_A_0.csv')
df1 = pd.read_csv('../../data/sixbus/lamda15/data_A_1.csv')
df2 = pd.read_csv('../../data/sixbus/lamda15/data_A_2.csv')
p_total = df0['P'][2:502]+df1['P'][2:502]+df2['P'][2:502] - [2.1]*500
ax.plot(df0['ADMM_IT'][1:501], p_total, label="lamda=15", linewidth=0.5)

p_total = [df0['P'][502]+df1['P'][502]+df2['P'][502] - 2.1]*500
ax.plot(df0['ADMM_IT'][1:501], p_total, label = "Consensus value", linewidth=2, linestyle='--')
print(p_total[1])

ax.legend()
ax.grid()
plt.xlabel("Number of iterations")
plt.ylabel("Active power loss(pu)")
plt.draw()
fg.savefig(PATHSVG, bbox_inches='tight')
