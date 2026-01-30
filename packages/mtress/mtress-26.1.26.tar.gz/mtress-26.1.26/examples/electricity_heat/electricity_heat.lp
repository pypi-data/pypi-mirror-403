\* Source Pyomo model name=Model *\

min 
objective:
+0.035 flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_0)
+0.035 flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_1)

s.t.

c_e_BusBlock_balance((_Qin_15____HeatPump____house_1_)_0)_:
-1 flow((_Qin_15____HeatPump____house_1_)_(_cop_15_40____HeatPump____house_1_)_0)
+1 flow((_HE_in_15____HeatPump____house_1_)_(_Qin_15____HeatPump____house_1_)_0)
= 0

c_e_BusBlock_balance((_Qin_15____HeatPump____house_1_)_1)_:
-1 flow((_Qin_15____HeatPump____house_1_)_(_cop_15_40____HeatPump____house_1_)_1)
+1 flow((_HE_in_15____HeatPump____house_1_)_(_Qin_15____HeatPump____house_1_)_1)
= 0

c_e_BusBlock_balance((_Qin_20____HeatPump____house_1_)_0)_:
-1 flow((_Qin_20____HeatPump____house_1_)_(_cop_20_40____HeatPump____house_1_)_0)
+1 flow((_HE_in_20____HeatPump____house_1_)_(_Qin_20____HeatPump____house_1_)_0)
= 0

c_e_BusBlock_balance((_Qin_20____HeatPump____house_1_)_1)_:
-1 flow((_Qin_20____HeatPump____house_1_)_(_cop_20_40____HeatPump____house_1_)_1)
+1 flow((_HE_in_20____HeatPump____house_1_)_(_Qin_20____HeatPump____house_1_)_1)
= 0

c_e_BusBlock_balance((_Qout_40____HeatPump____house_1_)_0)_:
-1 flow((_Qout_40____HeatPump____house_1_)_(_HE_out_40____HeatPump____house_1_)_0)
+1 flow((_cop_15_40____HeatPump____house_1_)_(_Qout_40____HeatPump____house_1_)_0)
+1 flow((_cop_20_40____HeatPump____house_1_)_(_Qout_40____HeatPump____house_1_)_0)
= 0

c_e_BusBlock_balance((_Qout_40____HeatPump____house_1_)_1)_:
-1 flow((_Qout_40____HeatPump____house_1_)_(_HE_out_40____HeatPump____house_1_)_1)
+1 flow((_cop_15_40____HeatPump____house_1_)_(_Qout_40____HeatPump____house_1_)_1)
+1 flow((_cop_20_40____HeatPump____house_1_)_(_Qout_40____HeatPump____house_1_)_1)
= 0

c_e_BusBlock_balance((_T_10____HeatCarrier____house_1_)_0)_:
-1 flow((_T_10____HeatCarrier____house_1_)_(_heat_10_15____ResistiveHeater____house_1_)_0)
-1 flow((_T_10____HeatCarrier____house_1_)_(_source_15____Air_HE____house_1_)_0)
+1 flow((_HE_in_15____HeatPump____house_1_)_(_T_10____HeatCarrier____house_1_)_0)
= 0

c_e_BusBlock_balance((_T_10____HeatCarrier____house_1_)_1)_:
-1 flow((_T_10____HeatCarrier____house_1_)_(_heat_10_15____ResistiveHeater____house_1_)_1)
-1 flow((_T_10____HeatCarrier____house_1_)_(_source_15____Air_HE____house_1_)_1)
+1 flow((_HE_in_15____HeatPump____house_1_)_(_T_10____HeatCarrier____house_1_)_1)
= 0

c_e_BusBlock_balance((_T_15____HeatCarrier____house_1_)_0)_:
-1 flow((_T_15____HeatCarrier____house_1_)_(_heat_15_20____ResistiveHeater____house_1_)_0)
-1 flow((_T_15____HeatCarrier____house_1_)_(_HE_in_15____HeatPump____house_1_)_0)
-1 flow((_T_15____HeatCarrier____house_1_)_(_source_20____Air_HE____house_1_)_0)
+1 flow((_heat_10_15____ResistiveHeater____house_1_)_(_T_15____HeatCarrier____house_1_)_0)
+1 flow((_HE_in_20____HeatPump____house_1_)_(_T_15____HeatCarrier____house_1_)_0)
+1 flow((_source_15____Air_HE____house_1_)_(_T_15____HeatCarrier____house_1_)_0)
= 0

c_e_BusBlock_balance((_T_15____HeatCarrier____house_1_)_1)_:
-1 flow((_T_15____HeatCarrier____house_1_)_(_heat_15_20____ResistiveHeater____house_1_)_1)
-1 flow((_T_15____HeatCarrier____house_1_)_(_HE_in_15____HeatPump____house_1_)_1)
-1 flow((_T_15____HeatCarrier____house_1_)_(_source_20____Air_HE____house_1_)_1)
+1 flow((_heat_10_15____ResistiveHeater____house_1_)_(_T_15____HeatCarrier____house_1_)_1)
+1 flow((_HE_in_20____HeatPump____house_1_)_(_T_15____HeatCarrier____house_1_)_1)
+1 flow((_source_15____Air_HE____house_1_)_(_T_15____HeatCarrier____house_1_)_1)
= 0

c_e_BusBlock_balance((_T_20____HeatCarrier____house_1_)_0)_:
-1 flow((_T_20____HeatCarrier____house_1_)_(_heat_20_30____ResistiveHeater____house_1_)_0)
-1 flow((_T_20____HeatCarrier____house_1_)_(_HE_in_20____HeatPump____house_1_)_0)
-1 flow((_T_20____HeatCarrier____house_1_)_(_source_30____Air_HE____house_1_)_0)
+1 flow((_heat_15_20____ResistiveHeater____house_1_)_(_T_20____HeatCarrier____house_1_)_0)
+1 flow((_source_20____Air_HE____house_1_)_(_T_20____HeatCarrier____house_1_)_0)
= 0

c_e_BusBlock_balance((_T_20____HeatCarrier____house_1_)_1)_:
-1 flow((_T_20____HeatCarrier____house_1_)_(_heat_20_30____ResistiveHeater____house_1_)_1)
-1 flow((_T_20____HeatCarrier____house_1_)_(_HE_in_20____HeatPump____house_1_)_1)
-1 flow((_T_20____HeatCarrier____house_1_)_(_source_30____Air_HE____house_1_)_1)
+1 flow((_heat_15_20____ResistiveHeater____house_1_)_(_T_20____HeatCarrier____house_1_)_1)
+1 flow((_source_20____Air_HE____house_1_)_(_T_20____HeatCarrier____house_1_)_1)
= 0

c_e_BusBlock_balance((_T_30____HeatCarrier____house_1_)_0)_:
-1 flow((_T_30____HeatCarrier____house_1_)_(_heat_30_40____ResistiveHeater____house_1_)_0)
-1 flow((_T_30____HeatCarrier____house_1_)_(_HE_out_40____HeatPump____house_1_)_0)
-1 flow((_T_30____HeatCarrier____house_1_)_(_source_40____Air_HE____house_1_)_0)
+1 flow((_heat_exchanger____space_heating____house_1_)_(_T_30____HeatCarrier____house_1_)_0)
+1 flow((_heat_20_30____ResistiveHeater____house_1_)_(_T_30____HeatCarrier____house_1_)_0)
+1 flow((_source_30____Air_HE____house_1_)_(_T_30____HeatCarrier____house_1_)_0)
= 0

c_e_BusBlock_balance((_T_30____HeatCarrier____house_1_)_1)_:
-1 flow((_T_30____HeatCarrier____house_1_)_(_heat_30_40____ResistiveHeater____house_1_)_1)
-1 flow((_T_30____HeatCarrier____house_1_)_(_HE_out_40____HeatPump____house_1_)_1)
-1 flow((_T_30____HeatCarrier____house_1_)_(_source_40____Air_HE____house_1_)_1)
+1 flow((_heat_exchanger____space_heating____house_1_)_(_T_30____HeatCarrier____house_1_)_1)
+1 flow((_heat_20_30____ResistiveHeater____house_1_)_(_T_30____HeatCarrier____house_1_)_1)
+1 flow((_source_30____Air_HE____house_1_)_(_T_30____HeatCarrier____house_1_)_1)
= 0

c_e_BusBlock_balance((_T_40____HeatCarrier____house_1_)_0)_:
-1 flow((_T_40____HeatCarrier____house_1_)_(_heat_exchanger____space_heating____house_1_)_0)
-1 flow((_T_40____HeatCarrier____house_1_)_(_heat_40_55____ResistiveHeater____house_1_)_0)
+1 flow((_heat_30_40____ResistiveHeater____house_1_)_(_T_40____HeatCarrier____house_1_)_0)
+1 flow((_HE_out_40____HeatPump____house_1_)_(_T_40____HeatCarrier____house_1_)_0)
+1 flow((_source_40____Air_HE____house_1_)_(_T_40____HeatCarrier____house_1_)_0)
= 0

c_e_BusBlock_balance((_T_40____HeatCarrier____house_1_)_1)_:
-1 flow((_T_40____HeatCarrier____house_1_)_(_heat_exchanger____space_heating____house_1_)_1)
-1 flow((_T_40____HeatCarrier____house_1_)_(_heat_40_55____ResistiveHeater____house_1_)_1)
+1 flow((_heat_30_40____ResistiveHeater____house_1_)_(_T_40____HeatCarrier____house_1_)_1)
+1 flow((_HE_out_40____HeatPump____house_1_)_(_T_40____HeatCarrier____house_1_)_1)
+1 flow((_source_40____Air_HE____house_1_)_(_T_40____HeatCarrier____house_1_)_1)
= 0

c_e_BusBlock_balance((_T_55____HeatCarrier____house_1_)_0)_:
+1 flow((_heat_40_55____ResistiveHeater____house_1_)_(_T_55____HeatCarrier____house_1_)_0)
= 0

c_e_BusBlock_balance((_T_55____HeatCarrier____house_1_)_1)_:
+1 flow((_heat_40_55____ResistiveHeater____house_1_)_(_T_55____HeatCarrier____house_1_)_1)
= 0

c_e_BusBlock_balance((_distribution____ElectricityCarrier____house_1_)_0)_:
-1 flow((_distribution____ElectricityCarrier____house_1_)_(_electricity____HeatPump____house_1_)_0)
-1 flow((_distribution____ElectricityCarrier____house_1_)_(_input____electricity_demand____house_1_)_0)
-1 flow((_distribution____ElectricityCarrier____house_1_)_(_heater____ResistiveHeater____house_1_)_0)
+1 flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_0)
= 0

c_e_BusBlock_balance((_distribution____ElectricityCarrier____house_1_)_1)_:
-1 flow((_distribution____ElectricityCarrier____house_1_)_(_electricity____HeatPump____house_1_)_1)
-1 flow((_distribution____ElectricityCarrier____house_1_)_(_input____electricity_demand____house_1_)_1)
-1 flow((_distribution____ElectricityCarrier____house_1_)_(_heater____ResistiveHeater____house_1_)_1)
+1 flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_1)
= 0

c_e_BusBlock_balance((_electricity____HeatPump____house_1_)_0)_:
+1 flow((_distribution____ElectricityCarrier____house_1_)_(_electricity____HeatPump____house_1_)_0)
-1 flow((_electricity____HeatPump____house_1_)_(_cop_15_40____HeatPump____house_1_)_0)
-1 flow((_electricity____HeatPump____house_1_)_(_cop_20_40____HeatPump____house_1_)_0)
= 0

c_e_BusBlock_balance((_electricity____HeatPump____house_1_)_1)_:
+1 flow((_distribution____ElectricityCarrier____house_1_)_(_electricity____HeatPump____house_1_)_1)
-1 flow((_electricity____HeatPump____house_1_)_(_cop_15_40____HeatPump____house_1_)_1)
-1 flow((_electricity____HeatPump____house_1_)_(_cop_20_40____HeatPump____house_1_)_1)
= 0

c_e_BusBlock_balance((_feed_in____ElectricityCarrier____house_1_)_0)_:
+1 flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_0)
= 0

c_e_BusBlock_balance((_feed_in____ElectricityCarrier____house_1_)_1)_:
+1 flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_1)
= 0

c_e_BusBlock_balance((_grid_export____ElectricityGridConnection____house_1_)_0)_:
+1 flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_0)
= 0

c_e_BusBlock_balance((_grid_export____ElectricityGridConnection____house_1_)_1)_:
+1 flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_1)
= 0

c_e_BusBlock_balance((_grid_import____ElectricityGridConnection____house_1_)_0)_:
-1 flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_0)
+1 flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_0)
= 0

c_e_BusBlock_balance((_grid_import____ElectricityGridConnection____house_1_)_1)_:
-1 flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_1)
+1 flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_1)
= 0

c_e_BusBlock_balance((_heat____ResistiveHeater____house_1_)_0)_:
-1 flow((_heat____ResistiveHeater____house_1_)_(_heat_10_15____ResistiveHeater____house_1_)_0)
-1 flow((_heat____ResistiveHeater____house_1_)_(_heat_15_20____ResistiveHeater____house_1_)_0)
-1 flow((_heat____ResistiveHeater____house_1_)_(_heat_20_30____ResistiveHeater____house_1_)_0)
-1 flow((_heat____ResistiveHeater____house_1_)_(_heat_30_40____ResistiveHeater____house_1_)_0)
-1 flow((_heat____ResistiveHeater____house_1_)_(_heat_40_55____ResistiveHeater____house_1_)_0)
+1 flow((_heater____ResistiveHeater____house_1_)_(_heat____ResistiveHeater____house_1_)_0)
= 0

c_e_BusBlock_balance((_heat____ResistiveHeater____house_1_)_1)_:
-1 flow((_heat____ResistiveHeater____house_1_)_(_heat_10_15____ResistiveHeater____house_1_)_1)
-1 flow((_heat____ResistiveHeater____house_1_)_(_heat_15_20____ResistiveHeater____house_1_)_1)
-1 flow((_heat____ResistiveHeater____house_1_)_(_heat_20_30____ResistiveHeater____house_1_)_1)
-1 flow((_heat____ResistiveHeater____house_1_)_(_heat_30_40____ResistiveHeater____house_1_)_1)
-1 flow((_heat____ResistiveHeater____house_1_)_(_heat_40_55____ResistiveHeater____house_1_)_1)
+1 flow((_heater____ResistiveHeater____house_1_)_(_heat____ResistiveHeater____house_1_)_1)
= 0

c_e_BusBlock_balance((_heat_budget____HeatPump____house_1_)_0)_:
-1 flow((_heat_budget____HeatPump____house_1_)_(_cop_15_40____HeatPump____house_1_)_0)
-1 flow((_heat_budget____HeatPump____house_1_)_(_cop_20_40____HeatPump____house_1_)_0)
+1 flow((_heat_budget_source____HeatPump____house_1_)_(_heat_budget____HeatPump____house_1_)_0)
= 0

c_e_BusBlock_balance((_heat_budget____HeatPump____house_1_)_1)_:
-1 flow((_heat_budget____HeatPump____house_1_)_(_cop_15_40____HeatPump____house_1_)_1)
-1 flow((_heat_budget____HeatPump____house_1_)_(_cop_20_40____HeatPump____house_1_)_1)
+1 flow((_heat_budget_source____HeatPump____house_1_)_(_heat_budget____HeatPump____house_1_)_1)
= 0

c_e_BusBlock_balance((_heat_source____Air_HE____house_1_)_0)_:
-1 flow((_heat_source____Air_HE____house_1_)_(_source_40____Air_HE____house_1_)_0)
-1 flow((_heat_source____Air_HE____house_1_)_(_source_30____Air_HE____house_1_)_0)
-1 flow((_heat_source____Air_HE____house_1_)_(_source_20____Air_HE____house_1_)_0)
-1 flow((_heat_source____Air_HE____house_1_)_(_source_15____Air_HE____house_1_)_0)
+1 flow((_source_reservoir____Air_HE____house_1_)_(_heat_source____Air_HE____house_1_)_0)
= 0

c_e_BusBlock_balance((_heat_source____Air_HE____house_1_)_1)_:
-1 flow((_heat_source____Air_HE____house_1_)_(_source_40____Air_HE____house_1_)_1)
-1 flow((_heat_source____Air_HE____house_1_)_(_source_30____Air_HE____house_1_)_1)
-1 flow((_heat_source____Air_HE____house_1_)_(_source_20____Air_HE____house_1_)_1)
-1 flow((_heat_source____Air_HE____house_1_)_(_source_15____Air_HE____house_1_)_1)
+1 flow((_source_reservoir____Air_HE____house_1_)_(_heat_source____Air_HE____house_1_)_1)
= 0

c_e_BusBlock_balance((_input____electricity_demand____house_1_)_0)_:
+1 flow((_distribution____ElectricityCarrier____house_1_)_(_input____electricity_demand____house_1_)_0)
= 9

c_e_BusBlock_balance((_input____electricity_demand____house_1_)_1)_:
+1 flow((_distribution____ElectricityCarrier____house_1_)_(_input____electricity_demand____house_1_)_1)
= 13

c_e_BusBlock_balance((_output____space_heating____house_1_)_0)_:
+1 flow((_heat_exchanger____space_heating____house_1_)_(_output____space_heating____house_1_)_0)
= 50

c_e_BusBlock_balance((_output____space_heating____house_1_)_1)_:
+1 flow((_heat_exchanger____space_heating____house_1_)_(_output____space_heating____house_1_)_1)
= 60

c_e_BusBlock_balance((_utilisation____Air_HE____house_1_)_0)_:
-1 flow((_utilisation____Air_HE____house_1_)_(_source_40____Air_HE____house_1_)_0)
-1 flow((_utilisation____Air_HE____house_1_)_(_source_30____Air_HE____house_1_)_0)
-1 flow((_utilisation____Air_HE____house_1_)_(_source_20____Air_HE____house_1_)_0)
-1 flow((_utilisation____Air_HE____house_1_)_(_source_15____Air_HE____house_1_)_0)
+1 flow((_source_utilisation____Air_HE____house_1_)_(_utilisation____Air_HE____house_1_)_0)
= 0

c_e_BusBlock_balance((_utilisation____Air_HE____house_1_)_1)_:
-1 flow((_utilisation____Air_HE____house_1_)_(_source_40____Air_HE____house_1_)_1)
-1 flow((_utilisation____Air_HE____house_1_)_(_source_30____Air_HE____house_1_)_1)
-1 flow((_utilisation____Air_HE____house_1_)_(_source_20____Air_HE____house_1_)_1)
-1 flow((_utilisation____Air_HE____house_1_)_(_source_15____Air_HE____house_1_)_1)
+1 flow((_source_utilisation____Air_HE____house_1_)_(_utilisation____Air_HE____house_1_)_1)
= 0

c_e_ConverterBlock_relation((_HE_in_15____HeatPump____house_1_)_(_T_15____HeatCarrier____house_1_)_(_Qin_15____HeatPump____house_1_)_0)_:
+5.805 flow((_T_15____HeatCarrier____house_1_)_(_HE_in_15____HeatPump____house_1_)_0)
-1 flow((_HE_in_15____HeatPump____house_1_)_(_Qin_15____HeatPump____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_HE_in_15____HeatPump____house_1_)_(_T_15____HeatCarrier____house_1_)_(_T_10____HeatCarrier____house_1_)_0)_:
+1 flow((_T_15____HeatCarrier____house_1_)_(_HE_in_15____HeatPump____house_1_)_0)
-1 flow((_HE_in_15____HeatPump____house_1_)_(_T_10____HeatCarrier____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_source_30____Air_HE____house_1_)_(_T_20____HeatCarrier____house_1_)_(_T_30____HeatCarrier____house_1_)_0)_:
+1 flow((_T_20____HeatCarrier____house_1_)_(_source_30____Air_HE____house_1_)_0)
-1 flow((_source_30____Air_HE____house_1_)_(_T_30____HeatCarrier____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_source_30____Air_HE____house_1_)_(_heat_source____Air_HE____house_1_)_(_T_30____HeatCarrier____house_1_)_0)_:
+1 flow((_heat_source____Air_HE____house_1_)_(_source_30____Air_HE____house_1_)_0)
-11.61 flow((_source_30____Air_HE____house_1_)_(_T_30____HeatCarrier____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_source_30____Air_HE____house_1_)_(_utilisation____Air_HE____house_1_)_(_T_30____HeatCarrier____house_1_)_0)_:
+1 flow((_utilisation____Air_HE____house_1_)_(_source_30____Air_HE____house_1_)_0)
-0.001161 flow((_source_30____Air_HE____house_1_)_(_T_30____HeatCarrier____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_heat_15_20____ResistiveHeater____house_1_)_(_heat____ResistiveHeater____house_1_)_(_T_20____HeatCarrier____house_1_)_0)_:
+1 flow((_heat____ResistiveHeater____house_1_)_(_heat_15_20____ResistiveHeater____house_1_)_0)
-5.805 flow((_heat_15_20____ResistiveHeater____house_1_)_(_T_20____HeatCarrier____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_heat_15_20____ResistiveHeater____house_1_)_(_T_15____HeatCarrier____house_1_)_(_T_20____HeatCarrier____house_1_)_0)_:
+1 flow((_T_15____HeatCarrier____house_1_)_(_heat_15_20____ResistiveHeater____house_1_)_0)
-1 flow((_heat_15_20____ResistiveHeater____house_1_)_(_T_20____HeatCarrier____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_source_15____Air_HE____house_1_)_(_heat_source____Air_HE____house_1_)_(_T_15____HeatCarrier____house_1_)_0)_:
+1 flow((_heat_source____Air_HE____house_1_)_(_source_15____Air_HE____house_1_)_0)
-5.805 flow((_source_15____Air_HE____house_1_)_(_T_15____HeatCarrier____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_source_15____Air_HE____house_1_)_(_T_10____HeatCarrier____house_1_)_(_T_15____HeatCarrier____house_1_)_0)_:
+1 flow((_T_10____HeatCarrier____house_1_)_(_source_15____Air_HE____house_1_)_0)
-1 flow((_source_15____Air_HE____house_1_)_(_T_15____HeatCarrier____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_source_15____Air_HE____house_1_)_(_utilisation____Air_HE____house_1_)_(_T_15____HeatCarrier____house_1_)_0)_:
+1 flow((_utilisation____Air_HE____house_1_)_(_source_15____Air_HE____house_1_)_0)
-0.0005805 flow((_source_15____Air_HE____house_1_)_(_T_15____HeatCarrier____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_HE_in_20____HeatPump____house_1_)_(_T_20____HeatCarrier____house_1_)_(_Qin_20____HeatPump____house_1_)_0)_:
+5.805 flow((_T_20____HeatCarrier____house_1_)_(_HE_in_20____HeatPump____house_1_)_0)
-1 flow((_HE_in_20____HeatPump____house_1_)_(_Qin_20____HeatPump____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_HE_in_20____HeatPump____house_1_)_(_T_20____HeatCarrier____house_1_)_(_T_15____HeatCarrier____house_1_)_0)_:
+1 flow((_T_20____HeatCarrier____house_1_)_(_HE_in_20____HeatPump____house_1_)_0)
-1 flow((_HE_in_20____HeatPump____house_1_)_(_T_15____HeatCarrier____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_heat_30_40____ResistiveHeater____house_1_)_(_heat____ResistiveHeater____house_1_)_(_T_40____HeatCarrier____house_1_)_0)_:
+1 flow((_heat____ResistiveHeater____house_1_)_(_heat_30_40____ResistiveHeater____house_1_)_0)
-11.61 flow((_heat_30_40____ResistiveHeater____house_1_)_(_T_40____HeatCarrier____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_heat_30_40____ResistiveHeater____house_1_)_(_T_30____HeatCarrier____house_1_)_(_T_40____HeatCarrier____house_1_)_0)_:
+1 flow((_T_30____HeatCarrier____house_1_)_(_heat_30_40____ResistiveHeater____house_1_)_0)
-1 flow((_heat_30_40____ResistiveHeater____house_1_)_(_T_40____HeatCarrier____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_heat_20_30____ResistiveHeater____house_1_)_(_T_20____HeatCarrier____house_1_)_(_T_30____HeatCarrier____house_1_)_0)_:
+1 flow((_T_20____HeatCarrier____house_1_)_(_heat_20_30____ResistiveHeater____house_1_)_0)
-1 flow((_heat_20_30____ResistiveHeater____house_1_)_(_T_30____HeatCarrier____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_heat_20_30____ResistiveHeater____house_1_)_(_heat____ResistiveHeater____house_1_)_(_T_30____HeatCarrier____house_1_)_0)_:
+1 flow((_heat____ResistiveHeater____house_1_)_(_heat_20_30____ResistiveHeater____house_1_)_0)
-11.61 flow((_heat_20_30____ResistiveHeater____house_1_)_(_T_30____HeatCarrier____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_HE_out_40____HeatPump____house_1_)_(_Qout_40____HeatPump____house_1_)_(_T_40____HeatCarrier____house_1_)_0)_:
+1 flow((_Qout_40____HeatPump____house_1_)_(_HE_out_40____HeatPump____house_1_)_0)
-11.61 flow((_HE_out_40____HeatPump____house_1_)_(_T_40____HeatCarrier____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_HE_out_40____HeatPump____house_1_)_(_T_30____HeatCarrier____house_1_)_(_T_40____HeatCarrier____house_1_)_0)_:
+1 flow((_T_30____HeatCarrier____house_1_)_(_HE_out_40____HeatPump____house_1_)_0)
-1 flow((_HE_out_40____HeatPump____house_1_)_(_T_40____HeatCarrier____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_cop_15_40____HeatPump____house_1_)_(_electricity____HeatPump____house_1_)_(_Qout_40____HeatPump____house_1_)_0)_:
+1 flow((_electricity____HeatPump____house_1_)_(_cop_15_40____HeatPump____house_1_)_0)
-0.13850165201663067 flow((_cop_15_40____HeatPump____house_1_)_(_Qout_40____HeatPump____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_cop_15_40____HeatPump____house_1_)_(_heat_budget____HeatPump____house_1_)_(_Qout_40____HeatPump____house_1_)_0)_:
+1 flow((_heat_budget____HeatPump____house_1_)_(_cop_15_40____HeatPump____house_1_)_0)
-1 flow((_cop_15_40____HeatPump____house_1_)_(_Qout_40____HeatPump____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_cop_15_40____HeatPump____house_1_)_(_Qin_15____HeatPump____house_1_)_(_Qout_40____HeatPump____house_1_)_0)_:
+1 flow((_Qin_15____HeatPump____house_1_)_(_cop_15_40____HeatPump____house_1_)_0)
-0.8614983479833693 flow((_cop_15_40____HeatPump____house_1_)_(_Qout_40____HeatPump____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_heat_exchanger____space_heating____house_1_)_(_T_40____HeatCarrier____house_1_)_(_output____space_heating____house_1_)_0)_:
+11.61 flow((_T_40____HeatCarrier____house_1_)_(_heat_exchanger____space_heating____house_1_)_0)
-1 flow((_heat_exchanger____space_heating____house_1_)_(_output____space_heating____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_heat_exchanger____space_heating____house_1_)_(_T_40____HeatCarrier____house_1_)_(_T_30____HeatCarrier____house_1_)_0)_:
+1 flow((_T_40____HeatCarrier____house_1_)_(_heat_exchanger____space_heating____house_1_)_0)
-1 flow((_heat_exchanger____space_heating____house_1_)_(_T_30____HeatCarrier____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_source_40____Air_HE____house_1_)_(_heat_source____Air_HE____house_1_)_(_T_40____HeatCarrier____house_1_)_0)_:
+1 flow((_heat_source____Air_HE____house_1_)_(_source_40____Air_HE____house_1_)_0)
-11.61 flow((_source_40____Air_HE____house_1_)_(_T_40____HeatCarrier____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_source_40____Air_HE____house_1_)_(_T_30____HeatCarrier____house_1_)_(_T_40____HeatCarrier____house_1_)_0)_:
+1 flow((_T_30____HeatCarrier____house_1_)_(_source_40____Air_HE____house_1_)_0)
-1 flow((_source_40____Air_HE____house_1_)_(_T_40____HeatCarrier____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_source_40____Air_HE____house_1_)_(_utilisation____Air_HE____house_1_)_(_T_40____HeatCarrier____house_1_)_0)_:
+1 flow((_utilisation____Air_HE____house_1_)_(_source_40____Air_HE____house_1_)_0)
-0.001161 flow((_source_40____Air_HE____house_1_)_(_T_40____HeatCarrier____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_source_20____Air_HE____house_1_)_(_heat_source____Air_HE____house_1_)_(_T_20____HeatCarrier____house_1_)_0)_:
+1 flow((_heat_source____Air_HE____house_1_)_(_source_20____Air_HE____house_1_)_0)
-5.805 flow((_source_20____Air_HE____house_1_)_(_T_20____HeatCarrier____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_source_20____Air_HE____house_1_)_(_T_15____HeatCarrier____house_1_)_(_T_20____HeatCarrier____house_1_)_0)_:
+1 flow((_T_15____HeatCarrier____house_1_)_(_source_20____Air_HE____house_1_)_0)
-1 flow((_source_20____Air_HE____house_1_)_(_T_20____HeatCarrier____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_source_20____Air_HE____house_1_)_(_utilisation____Air_HE____house_1_)_(_T_20____HeatCarrier____house_1_)_0)_:
+1 flow((_utilisation____Air_HE____house_1_)_(_source_20____Air_HE____house_1_)_0)
-0.0005805 flow((_source_20____Air_HE____house_1_)_(_T_20____HeatCarrier____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_heat_10_15____ResistiveHeater____house_1_)_(_T_10____HeatCarrier____house_1_)_(_T_15____HeatCarrier____house_1_)_0)_:
+1 flow((_T_10____HeatCarrier____house_1_)_(_heat_10_15____ResistiveHeater____house_1_)_0)
-1 flow((_heat_10_15____ResistiveHeater____house_1_)_(_T_15____HeatCarrier____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_heat_10_15____ResistiveHeater____house_1_)_(_heat____ResistiveHeater____house_1_)_(_T_15____HeatCarrier____house_1_)_0)_:
+1 flow((_heat____ResistiveHeater____house_1_)_(_heat_10_15____ResistiveHeater____house_1_)_0)
-5.805 flow((_heat_10_15____ResistiveHeater____house_1_)_(_T_15____HeatCarrier____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_heat_40_55____ResistiveHeater____house_1_)_(_T_40____HeatCarrier____house_1_)_(_T_55____HeatCarrier____house_1_)_0)_:
+1 flow((_T_40____HeatCarrier____house_1_)_(_heat_40_55____ResistiveHeater____house_1_)_0)
-1 flow((_heat_40_55____ResistiveHeater____house_1_)_(_T_55____HeatCarrier____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_heat_40_55____ResistiveHeater____house_1_)_(_heat____ResistiveHeater____house_1_)_(_T_55____HeatCarrier____house_1_)_0)_:
+1 flow((_heat____ResistiveHeater____house_1_)_(_heat_40_55____ResistiveHeater____house_1_)_0)
-17.415 flow((_heat_40_55____ResistiveHeater____house_1_)_(_T_55____HeatCarrier____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_heater____ResistiveHeater____house_1_)_(_distribution____ElectricityCarrier____house_1_)_(_heat____ResistiveHeater____house_1_)_0)_:
+1 flow((_distribution____ElectricityCarrier____house_1_)_(_heater____ResistiveHeater____house_1_)_0)
-1 flow((_heater____ResistiveHeater____house_1_)_(_heat____ResistiveHeater____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_cop_20_40____HeatPump____house_1_)_(_electricity____HeatPump____house_1_)_(_Qout_40____HeatPump____house_1_)_0)_:
+1 flow((_electricity____HeatPump____house_1_)_(_cop_20_40____HeatPump____house_1_)_0)
-0.10769569185061777 flow((_cop_20_40____HeatPump____house_1_)_(_Qout_40____HeatPump____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_cop_20_40____HeatPump____house_1_)_(_Qin_20____HeatPump____house_1_)_(_Qout_40____HeatPump____house_1_)_0)_:
+1 flow((_Qin_20____HeatPump____house_1_)_(_cop_20_40____HeatPump____house_1_)_0)
-0.8923043081493822 flow((_cop_20_40____HeatPump____house_1_)_(_Qout_40____HeatPump____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_cop_20_40____HeatPump____house_1_)_(_heat_budget____HeatPump____house_1_)_(_Qout_40____HeatPump____house_1_)_0)_:
+1 flow((_heat_budget____HeatPump____house_1_)_(_cop_20_40____HeatPump____house_1_)_0)
-1 flow((_cop_20_40____HeatPump____house_1_)_(_Qout_40____HeatPump____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_HE_in_15____HeatPump____house_1_)_(_T_15____HeatCarrier____house_1_)_(_Qin_15____HeatPump____house_1_)_1)_:
+5.805 flow((_T_15____HeatCarrier____house_1_)_(_HE_in_15____HeatPump____house_1_)_1)
-1 flow((_HE_in_15____HeatPump____house_1_)_(_Qin_15____HeatPump____house_1_)_1)
= 0

c_e_ConverterBlock_relation((_HE_in_15____HeatPump____house_1_)_(_T_15____HeatCarrier____house_1_)_(_T_10____HeatCarrier____house_1_)_1)_:
+1 flow((_T_15____HeatCarrier____house_1_)_(_HE_in_15____HeatPump____house_1_)_1)
-1 flow((_HE_in_15____HeatPump____house_1_)_(_T_10____HeatCarrier____house_1_)_1)
= 0

c_e_ConverterBlock_relation((_source_30____Air_HE____house_1_)_(_T_20____HeatCarrier____house_1_)_(_T_30____HeatCarrier____house_1_)_1)_:
+1 flow((_T_20____HeatCarrier____house_1_)_(_source_30____Air_HE____house_1_)_1)
-1 flow((_source_30____Air_HE____house_1_)_(_T_30____HeatCarrier____house_1_)_1)
= 0

c_e_ConverterBlock_relation((_source_30____Air_HE____house_1_)_(_heat_source____Air_HE____house_1_)_(_T_30____HeatCarrier____house_1_)_1)_:
+1 flow((_heat_source____Air_HE____house_1_)_(_source_30____Air_HE____house_1_)_1)
-11.61 flow((_source_30____Air_HE____house_1_)_(_T_30____HeatCarrier____house_1_)_1)
= 0

c_e_ConverterBlock_relation((_source_30____Air_HE____house_1_)_(_utilisation____Air_HE____house_1_)_(_T_30____HeatCarrier____house_1_)_1)_:
+1 flow((_utilisation____Air_HE____house_1_)_(_source_30____Air_HE____house_1_)_1)
-0.001161 flow((_source_30____Air_HE____house_1_)_(_T_30____HeatCarrier____house_1_)_1)
= 0

c_e_ConverterBlock_relation((_heat_15_20____ResistiveHeater____house_1_)_(_heat____ResistiveHeater____house_1_)_(_T_20____HeatCarrier____house_1_)_1)_:
+1 flow((_heat____ResistiveHeater____house_1_)_(_heat_15_20____ResistiveHeater____house_1_)_1)
-5.805 flow((_heat_15_20____ResistiveHeater____house_1_)_(_T_20____HeatCarrier____house_1_)_1)
= 0

c_e_ConverterBlock_relation((_heat_15_20____ResistiveHeater____house_1_)_(_T_15____HeatCarrier____house_1_)_(_T_20____HeatCarrier____house_1_)_1)_:
+1 flow((_T_15____HeatCarrier____house_1_)_(_heat_15_20____ResistiveHeater____house_1_)_1)
-1 flow((_heat_15_20____ResistiveHeater____house_1_)_(_T_20____HeatCarrier____house_1_)_1)
= 0

c_e_ConverterBlock_relation((_source_15____Air_HE____house_1_)_(_heat_source____Air_HE____house_1_)_(_T_15____HeatCarrier____house_1_)_1)_:
+1 flow((_heat_source____Air_HE____house_1_)_(_source_15____Air_HE____house_1_)_1)
-5.805 flow((_source_15____Air_HE____house_1_)_(_T_15____HeatCarrier____house_1_)_1)
= 0

c_e_ConverterBlock_relation((_source_15____Air_HE____house_1_)_(_T_10____HeatCarrier____house_1_)_(_T_15____HeatCarrier____house_1_)_1)_:
+1 flow((_T_10____HeatCarrier____house_1_)_(_source_15____Air_HE____house_1_)_1)
-1 flow((_source_15____Air_HE____house_1_)_(_T_15____HeatCarrier____house_1_)_1)
= 0

c_e_ConverterBlock_relation((_source_15____Air_HE____house_1_)_(_utilisation____Air_HE____house_1_)_(_T_15____HeatCarrier____house_1_)_1)_:
+1 flow((_utilisation____Air_HE____house_1_)_(_source_15____Air_HE____house_1_)_1)
-0.0005805 flow((_source_15____Air_HE____house_1_)_(_T_15____HeatCarrier____house_1_)_1)
= 0

c_e_ConverterBlock_relation((_HE_in_20____HeatPump____house_1_)_(_T_20____HeatCarrier____house_1_)_(_Qin_20____HeatPump____house_1_)_1)_:
+5.805 flow((_T_20____HeatCarrier____house_1_)_(_HE_in_20____HeatPump____house_1_)_1)
-1 flow((_HE_in_20____HeatPump____house_1_)_(_Qin_20____HeatPump____house_1_)_1)
= 0

c_e_ConverterBlock_relation((_HE_in_20____HeatPump____house_1_)_(_T_20____HeatCarrier____house_1_)_(_T_15____HeatCarrier____house_1_)_1)_:
+1 flow((_T_20____HeatCarrier____house_1_)_(_HE_in_20____HeatPump____house_1_)_1)
-1 flow((_HE_in_20____HeatPump____house_1_)_(_T_15____HeatCarrier____house_1_)_1)
= 0

c_e_ConverterBlock_relation((_heat_30_40____ResistiveHeater____house_1_)_(_heat____ResistiveHeater____house_1_)_(_T_40____HeatCarrier____house_1_)_1)_:
+1 flow((_heat____ResistiveHeater____house_1_)_(_heat_30_40____ResistiveHeater____house_1_)_1)
-11.61 flow((_heat_30_40____ResistiveHeater____house_1_)_(_T_40____HeatCarrier____house_1_)_1)
= 0

c_e_ConverterBlock_relation((_heat_30_40____ResistiveHeater____house_1_)_(_T_30____HeatCarrier____house_1_)_(_T_40____HeatCarrier____house_1_)_1)_:
+1 flow((_T_30____HeatCarrier____house_1_)_(_heat_30_40____ResistiveHeater____house_1_)_1)
-1 flow((_heat_30_40____ResistiveHeater____house_1_)_(_T_40____HeatCarrier____house_1_)_1)
= 0

c_e_ConverterBlock_relation((_heat_20_30____ResistiveHeater____house_1_)_(_T_20____HeatCarrier____house_1_)_(_T_30____HeatCarrier____house_1_)_1)_:
+1 flow((_T_20____HeatCarrier____house_1_)_(_heat_20_30____ResistiveHeater____house_1_)_1)
-1 flow((_heat_20_30____ResistiveHeater____house_1_)_(_T_30____HeatCarrier____house_1_)_1)
= 0

c_e_ConverterBlock_relation((_heat_20_30____ResistiveHeater____house_1_)_(_heat____ResistiveHeater____house_1_)_(_T_30____HeatCarrier____house_1_)_1)_:
+1 flow((_heat____ResistiveHeater____house_1_)_(_heat_20_30____ResistiveHeater____house_1_)_1)
-11.61 flow((_heat_20_30____ResistiveHeater____house_1_)_(_T_30____HeatCarrier____house_1_)_1)
= 0

c_e_ConverterBlock_relation((_HE_out_40____HeatPump____house_1_)_(_Qout_40____HeatPump____house_1_)_(_T_40____HeatCarrier____house_1_)_1)_:
+1 flow((_Qout_40____HeatPump____house_1_)_(_HE_out_40____HeatPump____house_1_)_1)
-11.61 flow((_HE_out_40____HeatPump____house_1_)_(_T_40____HeatCarrier____house_1_)_1)
= 0

c_e_ConverterBlock_relation((_HE_out_40____HeatPump____house_1_)_(_T_30____HeatCarrier____house_1_)_(_T_40____HeatCarrier____house_1_)_1)_:
+1 flow((_T_30____HeatCarrier____house_1_)_(_HE_out_40____HeatPump____house_1_)_1)
-1 flow((_HE_out_40____HeatPump____house_1_)_(_T_40____HeatCarrier____house_1_)_1)
= 0

c_e_ConverterBlock_relation((_cop_15_40____HeatPump____house_1_)_(_electricity____HeatPump____house_1_)_(_Qout_40____HeatPump____house_1_)_1)_:
+1 flow((_electricity____HeatPump____house_1_)_(_cop_15_40____HeatPump____house_1_)_1)
-0.13850165201663067 flow((_cop_15_40____HeatPump____house_1_)_(_Qout_40____HeatPump____house_1_)_1)
= 0

c_e_ConverterBlock_relation((_cop_15_40____HeatPump____house_1_)_(_heat_budget____HeatPump____house_1_)_(_Qout_40____HeatPump____house_1_)_1)_:
+1 flow((_heat_budget____HeatPump____house_1_)_(_cop_15_40____HeatPump____house_1_)_1)
-1 flow((_cop_15_40____HeatPump____house_1_)_(_Qout_40____HeatPump____house_1_)_1)
= 0

c_e_ConverterBlock_relation((_cop_15_40____HeatPump____house_1_)_(_Qin_15____HeatPump____house_1_)_(_Qout_40____HeatPump____house_1_)_1)_:
+1 flow((_Qin_15____HeatPump____house_1_)_(_cop_15_40____HeatPump____house_1_)_1)
-0.8614983479833693 flow((_cop_15_40____HeatPump____house_1_)_(_Qout_40____HeatPump____house_1_)_1)
= 0

c_e_ConverterBlock_relation((_heat_exchanger____space_heating____house_1_)_(_T_40____HeatCarrier____house_1_)_(_output____space_heating____house_1_)_1)_:
+11.61 flow((_T_40____HeatCarrier____house_1_)_(_heat_exchanger____space_heating____house_1_)_1)
-1 flow((_heat_exchanger____space_heating____house_1_)_(_output____space_heating____house_1_)_1)
= 0

c_e_ConverterBlock_relation((_heat_exchanger____space_heating____house_1_)_(_T_40____HeatCarrier____house_1_)_(_T_30____HeatCarrier____house_1_)_1)_:
+1 flow((_T_40____HeatCarrier____house_1_)_(_heat_exchanger____space_heating____house_1_)_1)
-1 flow((_heat_exchanger____space_heating____house_1_)_(_T_30____HeatCarrier____house_1_)_1)
= 0

c_e_ConverterBlock_relation((_source_40____Air_HE____house_1_)_(_heat_source____Air_HE____house_1_)_(_T_40____HeatCarrier____house_1_)_1)_:
+1 flow((_heat_source____Air_HE____house_1_)_(_source_40____Air_HE____house_1_)_1)
-11.61 flow((_source_40____Air_HE____house_1_)_(_T_40____HeatCarrier____house_1_)_1)
= 0

c_e_ConverterBlock_relation((_source_40____Air_HE____house_1_)_(_T_30____HeatCarrier____house_1_)_(_T_40____HeatCarrier____house_1_)_1)_:
+1 flow((_T_30____HeatCarrier____house_1_)_(_source_40____Air_HE____house_1_)_1)
-1 flow((_source_40____Air_HE____house_1_)_(_T_40____HeatCarrier____house_1_)_1)
= 0

c_e_ConverterBlock_relation((_source_40____Air_HE____house_1_)_(_utilisation____Air_HE____house_1_)_(_T_40____HeatCarrier____house_1_)_1)_:
+1 flow((_utilisation____Air_HE____house_1_)_(_source_40____Air_HE____house_1_)_1)
-0.001161 flow((_source_40____Air_HE____house_1_)_(_T_40____HeatCarrier____house_1_)_1)
= 0

c_e_ConverterBlock_relation((_source_20____Air_HE____house_1_)_(_heat_source____Air_HE____house_1_)_(_T_20____HeatCarrier____house_1_)_1)_:
+1 flow((_heat_source____Air_HE____house_1_)_(_source_20____Air_HE____house_1_)_1)
-5.805 flow((_source_20____Air_HE____house_1_)_(_T_20____HeatCarrier____house_1_)_1)
= 0

c_e_ConverterBlock_relation((_source_20____Air_HE____house_1_)_(_T_15____HeatCarrier____house_1_)_(_T_20____HeatCarrier____house_1_)_1)_:
+1 flow((_T_15____HeatCarrier____house_1_)_(_source_20____Air_HE____house_1_)_1)
-1 flow((_source_20____Air_HE____house_1_)_(_T_20____HeatCarrier____house_1_)_1)
= 0

c_e_ConverterBlock_relation((_source_20____Air_HE____house_1_)_(_utilisation____Air_HE____house_1_)_(_T_20____HeatCarrier____house_1_)_1)_:
+1 flow((_utilisation____Air_HE____house_1_)_(_source_20____Air_HE____house_1_)_1)
-0.0005805 flow((_source_20____Air_HE____house_1_)_(_T_20____HeatCarrier____house_1_)_1)
= 0

c_e_ConverterBlock_relation((_heat_10_15____ResistiveHeater____house_1_)_(_T_10____HeatCarrier____house_1_)_(_T_15____HeatCarrier____house_1_)_1)_:
+1 flow((_T_10____HeatCarrier____house_1_)_(_heat_10_15____ResistiveHeater____house_1_)_1)
-1 flow((_heat_10_15____ResistiveHeater____house_1_)_(_T_15____HeatCarrier____house_1_)_1)
= 0

c_e_ConverterBlock_relation((_heat_10_15____ResistiveHeater____house_1_)_(_heat____ResistiveHeater____house_1_)_(_T_15____HeatCarrier____house_1_)_1)_:
+1 flow((_heat____ResistiveHeater____house_1_)_(_heat_10_15____ResistiveHeater____house_1_)_1)
-5.805 flow((_heat_10_15____ResistiveHeater____house_1_)_(_T_15____HeatCarrier____house_1_)_1)
= 0

c_e_ConverterBlock_relation((_heat_40_55____ResistiveHeater____house_1_)_(_T_40____HeatCarrier____house_1_)_(_T_55____HeatCarrier____house_1_)_1)_:
+1 flow((_T_40____HeatCarrier____house_1_)_(_heat_40_55____ResistiveHeater____house_1_)_1)
-1 flow((_heat_40_55____ResistiveHeater____house_1_)_(_T_55____HeatCarrier____house_1_)_1)
= 0

c_e_ConverterBlock_relation((_heat_40_55____ResistiveHeater____house_1_)_(_heat____ResistiveHeater____house_1_)_(_T_55____HeatCarrier____house_1_)_1)_:
+1 flow((_heat____ResistiveHeater____house_1_)_(_heat_40_55____ResistiveHeater____house_1_)_1)
-17.415 flow((_heat_40_55____ResistiveHeater____house_1_)_(_T_55____HeatCarrier____house_1_)_1)
= 0

c_e_ConverterBlock_relation((_heater____ResistiveHeater____house_1_)_(_distribution____ElectricityCarrier____house_1_)_(_heat____ResistiveHeater____house_1_)_1)_:
+1 flow((_distribution____ElectricityCarrier____house_1_)_(_heater____ResistiveHeater____house_1_)_1)
-1 flow((_heater____ResistiveHeater____house_1_)_(_heat____ResistiveHeater____house_1_)_1)
= 0

c_e_ConverterBlock_relation((_cop_20_40____HeatPump____house_1_)_(_electricity____HeatPump____house_1_)_(_Qout_40____HeatPump____house_1_)_1)_:
+1 flow((_electricity____HeatPump____house_1_)_(_cop_20_40____HeatPump____house_1_)_1)
-0.10769569185061777 flow((_cop_20_40____HeatPump____house_1_)_(_Qout_40____HeatPump____house_1_)_1)
= 0

c_e_ConverterBlock_relation((_cop_20_40____HeatPump____house_1_)_(_Qin_20____HeatPump____house_1_)_(_Qout_40____HeatPump____house_1_)_1)_:
+1 flow((_Qin_20____HeatPump____house_1_)_(_cop_20_40____HeatPump____house_1_)_1)
-0.8923043081493822 flow((_cop_20_40____HeatPump____house_1_)_(_Qout_40____HeatPump____house_1_)_1)
= 0

c_e_ConverterBlock_relation((_cop_20_40____HeatPump____house_1_)_(_heat_budget____HeatPump____house_1_)_(_Qout_40____HeatPump____house_1_)_1)_:
+1 flow((_heat_budget____HeatPump____house_1_)_(_cop_20_40____HeatPump____house_1_)_1)
-1 flow((_cop_20_40____HeatPump____house_1_)_(_Qout_40____HeatPump____house_1_)_1)
= 0

bounds
   0 <= flow((_distribution____ElectricityCarrier____house_1_)_(_electricity____HeatPump____house_1_)_0) <= +inf
   0 <= flow((_distribution____ElectricityCarrier____house_1_)_(_electricity____HeatPump____house_1_)_1) <= +inf
   0 <= flow((_distribution____ElectricityCarrier____house_1_)_(_input____electricity_demand____house_1_)_0) <= +inf
   0 <= flow((_distribution____ElectricityCarrier____house_1_)_(_input____electricity_demand____house_1_)_1) <= +inf
   0 <= flow((_distribution____ElectricityCarrier____house_1_)_(_heater____ResistiveHeater____house_1_)_0) <= +inf
   0 <= flow((_distribution____ElectricityCarrier____house_1_)_(_heater____ResistiveHeater____house_1_)_1) <= +inf
   0 <= flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_0) <= +inf
   0 <= flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_1) <= +inf
   0 <= flow((_T_10____HeatCarrier____house_1_)_(_heat_10_15____ResistiveHeater____house_1_)_0) <= +inf
   0 <= flow((_T_10____HeatCarrier____house_1_)_(_heat_10_15____ResistiveHeater____house_1_)_1) <= +inf
   0 <= flow((_T_10____HeatCarrier____house_1_)_(_source_15____Air_HE____house_1_)_0) <= +inf
   0 <= flow((_T_10____HeatCarrier____house_1_)_(_source_15____Air_HE____house_1_)_1) <= +inf
   0 <= flow((_T_15____HeatCarrier____house_1_)_(_heat_15_20____ResistiveHeater____house_1_)_0) <= +inf
   0 <= flow((_T_15____HeatCarrier____house_1_)_(_heat_15_20____ResistiveHeater____house_1_)_1) <= +inf
   0 <= flow((_T_15____HeatCarrier____house_1_)_(_HE_in_15____HeatPump____house_1_)_0) <= +inf
   0 <= flow((_T_15____HeatCarrier____house_1_)_(_HE_in_15____HeatPump____house_1_)_1) <= +inf
   0 <= flow((_T_15____HeatCarrier____house_1_)_(_source_20____Air_HE____house_1_)_0) <= +inf
   0 <= flow((_T_15____HeatCarrier____house_1_)_(_source_20____Air_HE____house_1_)_1) <= +inf
   0 <= flow((_T_20____HeatCarrier____house_1_)_(_heat_20_30____ResistiveHeater____house_1_)_0) <= +inf
   0 <= flow((_T_20____HeatCarrier____house_1_)_(_heat_20_30____ResistiveHeater____house_1_)_1) <= +inf
   0 <= flow((_T_20____HeatCarrier____house_1_)_(_HE_in_20____HeatPump____house_1_)_0) <= +inf
   0 <= flow((_T_20____HeatCarrier____house_1_)_(_HE_in_20____HeatPump____house_1_)_1) <= +inf
   0 <= flow((_T_20____HeatCarrier____house_1_)_(_source_30____Air_HE____house_1_)_0) <= +inf
   0 <= flow((_T_20____HeatCarrier____house_1_)_(_source_30____Air_HE____house_1_)_1) <= +inf
   0 <= flow((_T_30____HeatCarrier____house_1_)_(_heat_30_40____ResistiveHeater____house_1_)_0) <= +inf
   0 <= flow((_T_30____HeatCarrier____house_1_)_(_heat_30_40____ResistiveHeater____house_1_)_1) <= +inf
   0 <= flow((_T_30____HeatCarrier____house_1_)_(_HE_out_40____HeatPump____house_1_)_0) <= +inf
   0 <= flow((_T_30____HeatCarrier____house_1_)_(_HE_out_40____HeatPump____house_1_)_1) <= +inf
   0 <= flow((_T_30____HeatCarrier____house_1_)_(_source_40____Air_HE____house_1_)_0) <= +inf
   0 <= flow((_T_30____HeatCarrier____house_1_)_(_source_40____Air_HE____house_1_)_1) <= +inf
   0 <= flow((_T_40____HeatCarrier____house_1_)_(_heat_exchanger____space_heating____house_1_)_0) <= +inf
   0 <= flow((_T_40____HeatCarrier____house_1_)_(_heat_exchanger____space_heating____house_1_)_1) <= +inf
   0 <= flow((_T_40____HeatCarrier____house_1_)_(_heat_40_55____ResistiveHeater____house_1_)_0) <= +inf
   0 <= flow((_T_40____HeatCarrier____house_1_)_(_heat_40_55____ResistiveHeater____house_1_)_1) <= +inf
   0 <= flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_0) <= +inf
   0 <= flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_1) <= +inf
   0 <= flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_0) <= +inf
   0 <= flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_1) <= +inf
   0 <= flow((_electricity____HeatPump____house_1_)_(_cop_15_40____HeatPump____house_1_)_0) <= +inf
   0 <= flow((_electricity____HeatPump____house_1_)_(_cop_15_40____HeatPump____house_1_)_1) <= +inf
   0 <= flow((_electricity____HeatPump____house_1_)_(_cop_20_40____HeatPump____house_1_)_0) <= +inf
   0 <= flow((_electricity____HeatPump____house_1_)_(_cop_20_40____HeatPump____house_1_)_1) <= +inf
   0 <= flow((_heat_budget____HeatPump____house_1_)_(_cop_15_40____HeatPump____house_1_)_0) <= +inf
   0 <= flow((_heat_budget____HeatPump____house_1_)_(_cop_15_40____HeatPump____house_1_)_1) <= +inf
   0 <= flow((_heat_budget____HeatPump____house_1_)_(_cop_20_40____HeatPump____house_1_)_0) <= +inf
   0 <= flow((_heat_budget____HeatPump____house_1_)_(_cop_20_40____HeatPump____house_1_)_1) <= +inf
   0 <= flow((_heat_budget_source____HeatPump____house_1_)_(_heat_budget____HeatPump____house_1_)_0) <= +inf
   0 <= flow((_heat_budget_source____HeatPump____house_1_)_(_heat_budget____HeatPump____house_1_)_1) <= +inf
   0 <= flow((_heat_exchanger____space_heating____house_1_)_(_output____space_heating____house_1_)_0) <= +inf
   0 <= flow((_heat_exchanger____space_heating____house_1_)_(_output____space_heating____house_1_)_1) <= +inf
   0 <= flow((_heat_exchanger____space_heating____house_1_)_(_T_30____HeatCarrier____house_1_)_0) <= +inf
   0 <= flow((_heat_exchanger____space_heating____house_1_)_(_T_30____HeatCarrier____house_1_)_1) <= +inf
   0 <= flow((_heat____ResistiveHeater____house_1_)_(_heat_10_15____ResistiveHeater____house_1_)_0) <= +inf
   0 <= flow((_heat____ResistiveHeater____house_1_)_(_heat_10_15____ResistiveHeater____house_1_)_1) <= +inf
   0 <= flow((_heat____ResistiveHeater____house_1_)_(_heat_15_20____ResistiveHeater____house_1_)_0) <= +inf
   0 <= flow((_heat____ResistiveHeater____house_1_)_(_heat_15_20____ResistiveHeater____house_1_)_1) <= +inf
   0 <= flow((_heat____ResistiveHeater____house_1_)_(_heat_20_30____ResistiveHeater____house_1_)_0) <= +inf
   0 <= flow((_heat____ResistiveHeater____house_1_)_(_heat_20_30____ResistiveHeater____house_1_)_1) <= +inf
   0 <= flow((_heat____ResistiveHeater____house_1_)_(_heat_30_40____ResistiveHeater____house_1_)_0) <= +inf
   0 <= flow((_heat____ResistiveHeater____house_1_)_(_heat_30_40____ResistiveHeater____house_1_)_1) <= +inf
   0 <= flow((_heat____ResistiveHeater____house_1_)_(_heat_40_55____ResistiveHeater____house_1_)_0) <= +inf
   0 <= flow((_heat____ResistiveHeater____house_1_)_(_heat_40_55____ResistiveHeater____house_1_)_1) <= +inf
   0 <= flow((_heat_10_15____ResistiveHeater____house_1_)_(_T_15____HeatCarrier____house_1_)_0) <= +inf
   0 <= flow((_heat_10_15____ResistiveHeater____house_1_)_(_T_15____HeatCarrier____house_1_)_1) <= +inf
   0 <= flow((_heat_15_20____ResistiveHeater____house_1_)_(_T_20____HeatCarrier____house_1_)_0) <= +inf
   0 <= flow((_heat_15_20____ResistiveHeater____house_1_)_(_T_20____HeatCarrier____house_1_)_1) <= +inf
   0 <= flow((_heat_20_30____ResistiveHeater____house_1_)_(_T_30____HeatCarrier____house_1_)_0) <= +inf
   0 <= flow((_heat_20_30____ResistiveHeater____house_1_)_(_T_30____HeatCarrier____house_1_)_1) <= +inf
   0 <= flow((_heat_30_40____ResistiveHeater____house_1_)_(_T_40____HeatCarrier____house_1_)_0) <= +inf
   0 <= flow((_heat_30_40____ResistiveHeater____house_1_)_(_T_40____HeatCarrier____house_1_)_1) <= +inf
   0 <= flow((_heat_40_55____ResistiveHeater____house_1_)_(_T_55____HeatCarrier____house_1_)_0) <= +inf
   0 <= flow((_heat_40_55____ResistiveHeater____house_1_)_(_T_55____HeatCarrier____house_1_)_1) <= +inf
   0 <= flow((_heater____ResistiveHeater____house_1_)_(_heat____ResistiveHeater____house_1_)_0) <= +inf
   0 <= flow((_heater____ResistiveHeater____house_1_)_(_heat____ResistiveHeater____house_1_)_1) <= +inf
   0 <= flow((_Qout_40____HeatPump____house_1_)_(_HE_out_40____HeatPump____house_1_)_0) <= +inf
   0 <= flow((_Qout_40____HeatPump____house_1_)_(_HE_out_40____HeatPump____house_1_)_1) <= +inf
   0 <= flow((_HE_out_40____HeatPump____house_1_)_(_T_40____HeatCarrier____house_1_)_0) <= +inf
   0 <= flow((_HE_out_40____HeatPump____house_1_)_(_T_40____HeatCarrier____house_1_)_1) <= +inf
   0 <= flow((_Qin_15____HeatPump____house_1_)_(_cop_15_40____HeatPump____house_1_)_0) <= +inf
   0 <= flow((_Qin_15____HeatPump____house_1_)_(_cop_15_40____HeatPump____house_1_)_1) <= +inf
   0 <= flow((_HE_in_15____HeatPump____house_1_)_(_Qin_15____HeatPump____house_1_)_0) <= +inf
   0 <= flow((_HE_in_15____HeatPump____house_1_)_(_Qin_15____HeatPump____house_1_)_1) <= +inf
   0 <= flow((_HE_in_15____HeatPump____house_1_)_(_T_10____HeatCarrier____house_1_)_0) <= +inf
   0 <= flow((_HE_in_15____HeatPump____house_1_)_(_T_10____HeatCarrier____house_1_)_1) <= +inf
   0 <= flow((_cop_15_40____HeatPump____house_1_)_(_Qout_40____HeatPump____house_1_)_0) <= +inf
   0 <= flow((_cop_15_40____HeatPump____house_1_)_(_Qout_40____HeatPump____house_1_)_1) <= +inf
   0 <= flow((_Qin_20____HeatPump____house_1_)_(_cop_20_40____HeatPump____house_1_)_0) <= +inf
   0 <= flow((_Qin_20____HeatPump____house_1_)_(_cop_20_40____HeatPump____house_1_)_1) <= +inf
   0 <= flow((_HE_in_20____HeatPump____house_1_)_(_Qin_20____HeatPump____house_1_)_0) <= +inf
   0 <= flow((_HE_in_20____HeatPump____house_1_)_(_Qin_20____HeatPump____house_1_)_1) <= +inf
   0 <= flow((_HE_in_20____HeatPump____house_1_)_(_T_15____HeatCarrier____house_1_)_0) <= +inf
   0 <= flow((_HE_in_20____HeatPump____house_1_)_(_T_15____HeatCarrier____house_1_)_1) <= +inf
   0 <= flow((_cop_20_40____HeatPump____house_1_)_(_Qout_40____HeatPump____house_1_)_0) <= +inf
   0 <= flow((_cop_20_40____HeatPump____house_1_)_(_Qout_40____HeatPump____house_1_)_1) <= +inf
   0.0 <= flow((_heat_source____Air_HE____house_1_)_(_source_40____Air_HE____house_1_)_0) <= 0.0
   0.0 <= flow((_heat_source____Air_HE____house_1_)_(_source_40____Air_HE____house_1_)_1) <= 0.0
   0.0 <= flow((_heat_source____Air_HE____house_1_)_(_source_30____Air_HE____house_1_)_0) <= 0.0
   0.0 <= flow((_heat_source____Air_HE____house_1_)_(_source_30____Air_HE____house_1_)_1) <= 0.0
   0.0 <= flow((_heat_source____Air_HE____house_1_)_(_source_20____Air_HE____house_1_)_0) <= 10000.0
   0.0 <= flow((_heat_source____Air_HE____house_1_)_(_source_20____Air_HE____house_1_)_1) <= 10000.0
   0.0 <= flow((_heat_source____Air_HE____house_1_)_(_source_15____Air_HE____house_1_)_0) <= 10000.0
   0.0 <= flow((_heat_source____Air_HE____house_1_)_(_source_15____Air_HE____house_1_)_1) <= 10000.0
   0.0 <= flow((_source_reservoir____Air_HE____house_1_)_(_heat_source____Air_HE____house_1_)_0) <= 10000.0
   0.0 <= flow((_source_reservoir____Air_HE____house_1_)_(_heat_source____Air_HE____house_1_)_1) <= 10000.0
   0 <= flow((_utilisation____Air_HE____house_1_)_(_source_40____Air_HE____house_1_)_0) <= +inf
   0 <= flow((_utilisation____Air_HE____house_1_)_(_source_40____Air_HE____house_1_)_1) <= +inf
   0 <= flow((_utilisation____Air_HE____house_1_)_(_source_30____Air_HE____house_1_)_0) <= +inf
   0 <= flow((_utilisation____Air_HE____house_1_)_(_source_30____Air_HE____house_1_)_1) <= +inf
   0 <= flow((_utilisation____Air_HE____house_1_)_(_source_20____Air_HE____house_1_)_0) <= +inf
   0 <= flow((_utilisation____Air_HE____house_1_)_(_source_20____Air_HE____house_1_)_1) <= +inf
   0 <= flow((_utilisation____Air_HE____house_1_)_(_source_15____Air_HE____house_1_)_0) <= +inf
   0 <= flow((_utilisation____Air_HE____house_1_)_(_source_15____Air_HE____house_1_)_1) <= +inf
   0 <= flow((_source_utilisation____Air_HE____house_1_)_(_utilisation____Air_HE____house_1_)_0) <= 1
   0 <= flow((_source_utilisation____Air_HE____house_1_)_(_utilisation____Air_HE____house_1_)_1) <= 1
   0 <= flow((_source_40____Air_HE____house_1_)_(_T_40____HeatCarrier____house_1_)_0) <= +inf
   0 <= flow((_source_40____Air_HE____house_1_)_(_T_40____HeatCarrier____house_1_)_1) <= +inf
   0 <= flow((_source_30____Air_HE____house_1_)_(_T_30____HeatCarrier____house_1_)_0) <= +inf
   0 <= flow((_source_30____Air_HE____house_1_)_(_T_30____HeatCarrier____house_1_)_1) <= +inf
   0 <= flow((_source_20____Air_HE____house_1_)_(_T_20____HeatCarrier____house_1_)_0) <= +inf
   0 <= flow((_source_20____Air_HE____house_1_)_(_T_20____HeatCarrier____house_1_)_1) <= +inf
   0 <= flow((_source_15____Air_HE____house_1_)_(_T_15____HeatCarrier____house_1_)_0) <= +inf
   0 <= flow((_source_15____Air_HE____house_1_)_(_T_15____HeatCarrier____house_1_)_1) <= +inf
end
