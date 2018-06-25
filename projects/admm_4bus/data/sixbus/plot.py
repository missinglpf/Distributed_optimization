import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime

# df0 = pd.read_csv('lamda300/data_A_0.csv')
# df1 = pd.read_csv('lamda300/data_A_0.csv')
# df0 = pd.read_csv('lamda200/data_A_0.csv')
# df3 = pd.read_csv('lamda100/data_A_0.csv')

df0 = pd.read_csv('lamda50/data_A_0.csv')
df1 = pd.read_csv('lamda50/data_A_1.csv')
df2 = pd.read_csv('lamda50/data_A_2.csv')

p_total = df0['Q'][2:502]+df1['Q'][2:502]+df2['Q'][2:502] - [2.1]*500
plt.plot(df0['ADMM_IT'][1:501], p_total, label="lamda=50", linewidth=0.5)

df0 = pd.read_csv('lamda30/data_A_0.csv')
df1 = pd.read_csv('lamda30/data_A_1.csv')
df2 = pd.read_csv('lamda30/data_A_2.csv')

p_total = df0['Q'][2:502]+df1['Q'][2:502]+df2['Q'][2:502] - [2.1]*500
plt.plot(df0['ADMM_IT'][1:501], p_total, label = "lamda=30", linewidth=0.5)

df0 = pd.read_csv('lamda25/data_A_0.csv')
df1 = pd.read_csv('lamda25/data_A_1.csv')
df2 = pd.read_csv('lamda25/data_A_2.csv')

p_total = df0['Q'][2:502]+df1['Q'][2:502]+df2['Q'][2:502] - [2.1]*500
plt.plot(df0['ADMM_IT'][1:501], p_total, label = "lamda=25", linewidth=0.5)

df0 = pd.read_csv('lamda20/data_A_0.csv')
df1 = pd.read_csv('lamda20/data_A_1.csv')
df2 = pd.read_csv('lamda20/data_A_2.csv')

p_total = df0['Q'][2:502]+df1['Q'][2:502]+df2['Q'][2:502] - [2.1]*500
plt.plot(df0['ADMM_IT'][1:501], p_total, label = "lamda=20", linewidth=0.5)

df0 = pd.read_csv('lamda15/data_A_0.csv')
df1 = pd.read_csv('lamda15/data_A_1.csv')
df2 = pd.read_csv('lamda15/data_A_2.csv')

p_total = df0['Q'][2:502]+df1['Q'][2:502]+df2['Q'][2:502] - [2.1]*500
plt.plot(df0['ADMM_IT'][1:501], p_total, label = "lamda=15", linewidth=0.5)

df0 = pd.read_csv('lamda15/data_A_0.csv')
df1 = pd.read_csv('lamda15/data_A_1.csv')
df2 = pd.read_csv('lamda15/data_A_2.csv')


p_total = [df0['Q'][502]+df1['Q'][502]+df2['Q'][502] - 2.1]*500
plt.plot(df0['ADMM_IT'][1:501], p_total, label = "Optimal value", linewidth=2, linestyle='--')

# df0 = pd.read_csv('lamda10/data_A_0.csv')
# df1 = pd.read_csv('lamda10/data_A_1.csv')
# df2 = pd.read_csv('lamda10/data_A_2.csv')
#
# p_total = df0['P'][2:502]+df1['P'][2:502]+df2['P'][2:502] - [2.1]*500
# plt.plot(df0['ADMM_IT'][1:501], p_total, label = "lamda=10", linewidth=0.5)

# df5 = pd.read_csv('lamda25/data_A_2.csv')
# df6 = pd.read_csv('lamda15/data_A_2.csv')
# df7 = pd.read_csv('lamda20/data_A_2.csv')
# df8 = pd.read_csv('lamda30/data_A_2.csv')
# df2 = pd.read_csv('lamda300/data_A_2.csv')
# df3 = pd.read_csv('lamda300/data_A_3.csv')
# df4 = pd.read_csv('lamda300/data_A_4.csv')
# df5 = pd.read_csv('lamda300/data_A_5.csv')
# df['Time'] = df['Time'].map(lambda x: datetime.strptime(str(x), '%Y/%m/%d %H:%M:%S.%f'))
# plt.plot(df0['ADMM_IT'][1:6000], df0['P'][1:6000], label = "lamda=200")
# plt.plot(df0['ADMM_IT'][1:6000], df1['P'][1:6000], label = "lamda=300")
# plt.plot(df4['ADMM_IT'][1:3000], df3['Q'][1:3000], label = "lamda=100")

# central = [df5['P'][1000]]*1001
# plt.plot(df4['ADMM_IT'][1:500], df4['P'][1:500], label = "lamda=50", linewidth=0.5)
# plt.plot(df6['ADMM_IT'][1:500], df8['P'][1:500], label = "lamda=30", linewidth=0.5)
# plt.plot(df6['ADMM_IT'][1:500], df5['P'][1:500], label = "lamda=25", linewidth=0.5)
# plt.plot(df6['ADMM_IT'][1:500], df7['P'][1:500], label = "lamda=20", linewidth=0.5)
# plt.plot(df6['ADMM_IT'][1:500], df6['P'][1:500], label = "lamda=15", linewidth=0.5)
# plt.plot(df6['ADMM_IT'][1:500], central[1:500], label = "Optimal value", linewidth=2, linestyle='--')

# central = [df5['Q'][1000]]*1001
# plt.plot(df4['ADMM_IT'][1:500], df4['Q'][1:500], label = "lamda=50", linewidth=0.5)
# plt.plot(df6['ADMM_IT'][1:500], df8['Q'][1:500], label = "lamda=30", linewidth=0.5)
# plt.plot(df6['ADMM_IT'][1:500], df5['Q'][1:500], label = "lamda=25", linewidth=0.5)
# plt.plot(df6['ADMM_IT'][1:500], df7['Q'][1:500], label = "lamda=20", linewidth=0.5)
# plt.plot(df6['ADMM_IT'][1:500], df6['Q'][1:500], label = "lamda=15", linewidth=0.5)
# plt.plot(df6['ADMM_IT'][1:500], central[1:500], label = "Optimal value", linewidth=2, linestyle='--')

# plt.plot(df1['Time'][1:15000], df1['X_real'][1:15000])
# plt.plot(df2['Time'][1:15000], df2['X_real'][1:15000])
plt.legend()
plt.xlabel("Number of iterations")
plt.ylabel("Reactive power loss(pu)")
# plt.ylabel("Reactive power(pu)")
plt.show()

