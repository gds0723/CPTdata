import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import openpyxl
from tkinter import Tk
from tkinter.filedialog import askopenfilename
##########################################################################################################################################################################
#Import Excel data. Four Columns. Depth in meters.  qc,fs,and u2 in kPa.  Built around the AGS electronic data transfer... but using kPa instead of MPa
Tk().withdraw()
file = askopenfilename(filetypes=[('EXCEL Files','*.xls')])
cptd = pd.read_excel(file,header=0,true_values=True)
##########################################################################################################################################################################
#The dataframe is 'cptd'
z  = cptd['SCPT_DPTH'].astype(int)         #Sample Depths - meters
qc = cptd['SCPT_RES'].astype(int)          #Uncorrected Cone Tip Resistance - kPa
fs = cptd['SCPT_FRES'].astype(int)         #Side Friction Resistance - kPa
u2 = cptd['SCPT_PWP2'].astype(int)         #U2 pore pressure - kPa
##########################################################################################################################################################################
#Assumptions
LOCA_ID = 'CPT01'                       #CPT Location Identifier
SCPG_WAT = 5.486                        #ground water level in meters
MAX_DPTH = max(cptd['SCPT_DPTH'])       #Maximum depth to display plots - in meters
##########################################################################################################################################################################
#Calculation and column for in-situ pore pressure (u0).   9.807 is weight of water in kN/m(3)... so u0 is in kN/m(2)= kPa
cptd['SCPT_ISPP'] = np.where(cptd['SCPT_DPTH'] < SCPG_WAT,0,((cptd['SCPT_DPTH'] - SCPG_WAT)*9.807))
##########################################################################################################################################################################
#Corrected tip resistance
cptd['SCPT_CAR']=0.7
cptd['SCPT_QT']= cptd['SCPT_RES']+(cptd['SCPT_PWP2']*(1-cptd['SCPT_CAR']))
#########################################################################################################################################################################
#Normalized friction ratio
cptd['SCPT_FRR'] = (cptd['SCPT_FRES']/cptd['SCPT_QT'])*100
##########################################################################################################################################################################
#Soil density using correlation by Robertson P.K., 2009 Interpretation of CPT - A Unified Approach. kPa per meter SCPT_BDEN is in KPa/meter
#Unit weight of water is 9.807 kPa/meter
#Atmospheric air pressure = 101.3 KPa
cptd['SCPT_BDEN'] = 9.807*((0.27*np.log10(cptd['SCPT_FRR']))+(0.36*(np.log10(cptd['SCPT_QT']/101.3)))+1.236)
##########################################################################################################################################################################
#Calcuation of total and effective overburden stresses at each sample depth
#Calculation of incremental distance between records
cptd['dz'] = cptd['SCPT_DPTH'].diff(1)
cptd.at[0,'dz']=cptd.at[0,'SCPT_DPTH']
#Calculation for the incremental soil pressure difference at each depth
cptd['dvo'] = np.multiply(cptd['dz'],cptd['SCPT_BDEN'].values)
#Calculation of total overburden stress at each depth (kPa)
cptd['SCPT_CPO'] = np.nancumsum(cptd['dvo'].values)
#Calculation of effective overburden stress at each depth (kPa)
cptd['SCPT_CPOD']= cptd['SCPT_CPO']-cptd['SCPT_ISPP']
########################################################################################################################################################################
#Soil Behaviour Type Chart Ic using Robertson, P.K., Soil Behaviour Type from the CPT. An Update (2010)
#Iteration Number 1 for the normalized cone resistance (SCPT-NQT) using n = 1.
n1 = 1.0
cptd['SCPT_NQT1'] = ((cptd['SCPT_QT']-cptd['SCPT_CPO'])/101.3)*((101.3/cptd['SCPT_CPOD'])**(n1))
#Initial calculation of Soil Behaviour Type Index (Ic1)
cptd['SCPT_CIC1'] = np.sqrt(np.power(((3.47-(np.log10(cptd['SCPT_NQT1'])))),2) + np.power(((np.log10(cptd['SCPT_FRR'])+1.22)),2))
###########################################################################################################################################################################
#Iteration Number 2 for the normalized cone resistance (SCPT-NQT) using n correlates to IC1.
n2 = (0.381*cptd['SCPT_CIC1'])+(0.05*(cptd['SCPT_CPOD']/101.3))-0.15
cptd['SCPT_NQT2'] = ((cptd['SCPT_QT']-cptd['SCPT_CPO'])/101.3)*((101.3/cptd['SCPT_CPOD'])**(n2))
#Iteration 2 of Soil Behaviour Type Index (Ic2)
cptd['SCPT_CIC2'] = np.sqrt(np.power(((3.47-(np.log10(cptd['SCPT_NQT2'])))),2) + np.power(((np.log10(cptd['SCPT_FRR'])+1.22)),2))
###########################################################################################################################################################################
#Final Iteration (Number 3) for the normalized cone resistance (SCPT-NQT) using n correlates to IC2.
n3 = (0.381*cptd['SCPT_CIC2'])+(0.05*(cptd['SCPT_CPOD']/101.3))-0.15
cptd['SCPT_NQT3'] = ((cptd['SCPT_QT']-cptd['SCPT_CPO'])/101.3)*((101.3/cptd['SCPT_CPOD'])**(n3))
#Final Iteration (Number 3) to provide Soil Behaviour Type Index (Ic3)
cptd['SCPT_CIC3'] = np.sqrt(np.power(((3.47-(np.log10(cptd['SCPT_NQT3'])))),2) + np.power(((np.log10(cptd['SCPT_FRR'])+1.22)),2))
cptd.dropna()
#############################################################################################################################################################################
#Soil Behavior Interpreted Soil Type based on third iteration of Soil Behavior Type Index
conditions = [
    ((cptd['SCPT_CIC3']) < 1.31),
    ((cptd['SCPT_CIC3']) >= 1.31) & ((cptd['SCPT_CIC3']) < 2.05),
    ((cptd['SCPT_CIC3']) >= 2.05) & ((cptd['SCPT_CIC3']) < 2.60),
    ((cptd['SCPT_CIC3']) >= 2.60) & ((cptd['SCPT_CIC3']) < 2.95),
    ((cptd['SCPT_CIC3']) >= 2.95) & ((cptd['SCPT_CIC3']) < 3.60),
    ((cptd['SCPT_CIC3']) >= 2.05),
]
values = [7,6,5,4,3,2]
cptd['SCPT_CSBT'] = np.select(conditions,values)
#############################################################################################################################################################################
#Pore Pressure Ratio Bq
cptd['scpt_BQ']=(cptd['SCPT_PWP2']-cptd['SCPT_ISPP'])/(cptd['SCPT_QT']-cptd['SCPT_CPO'])

#qtm = qt/1000                                                                               #qt MPa
#Su_15 = qn / 15                                                                             #Su Nkt = 15
#qt_norm = qn / sig1_vo                                                                      #normalised qc
#fr_norm = ((fs * 1000) / qn) * 100                                                          #normalised fs
#print(cptd['SCPT_DPTH'],cptd['dz'])
#cptd.to_excel("cpttoic.xlsx")
#################################################################################################################################################################################
#Plot the Figure
plt.figure()
ax = plt.axes(projection='3d')
ax.invert_zaxis()
z = cptd['SCPT_DPTH']
x = cptd['SCPT_FRR']
y = cptd['SCPT_QT']/1000
cmap = plt.get_cmap('hot',None)
norm = mpl.colors.BoundaryNorm(boundaries=[1,2,3,4,5,6,7],ncolors=4)
ax.scatter(x,np.log(y),z,c=cptd['SCPT_CSBT'],cmap=cmap,norm=norm)
#ax.xaxis()set_scale('log')
#ax.yaxis.set_scale('log')
#ax.plot3D(x,y,z,'bo')
#ax.plot3d(cptd['SCPT_FRR'],cptd['SCPT_NQT3'],cptd['SCPT_DPTH'])
#plt.plot(cptd['SCPT_FRR'], cptd['SCPT_NQT3'],'bo')
#plt.zlabel('Depth (m)')
ax.set_xlabel('Normalized Friction Ratio - Fr (%))')
ax.set_ylabel('Normalized Cone Resistance - log(Qtn) (MPa)')
ax.set_zlabel('Depth (m)')
plt.title('SOIL BEHAVIOUR TYPE CHART')
sm = plt.cm.ScalarMappable(cmap=cmap,norm=norm)
sm.set_array([])
plt.colorbar(sm,ticks=np.linspace(1,7))
plt.grid(True)
#plt.figure()
#plt.plot(qc, z)
#plt.xlabel('time (s)')
#plt.ylabel('voltage (mV)')
#plt.title('About as simple as it gets, folks')
#plt.grid(True)
plt.show()
