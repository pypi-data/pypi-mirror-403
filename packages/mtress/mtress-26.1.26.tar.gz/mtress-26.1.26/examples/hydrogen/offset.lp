\* Source Pyomo model name=Model *\

min 
objective:
+1000000000.0 flow((_T_20____HeatCarrier____house_1_)_(_excess_energy____SlackNode____house_1_)_0)
+1000000000.0 flow((_T_20____HeatCarrier____house_1_)_(_excess_energy____SlackNode____house_1_)_1)
+1000000000.0 flow((_T_20____HeatCarrier____house_1_)_(_excess_energy____SlackNode____house_1_)_2)
+1000000000.0 flow((_T_40____HeatCarrier____house_1_)_(_excess_energy____SlackNode____house_1_)_0)
+1000000000.0 flow((_T_40____HeatCarrier____house_1_)_(_excess_energy____SlackNode____house_1_)_1)
+1000000000.0 flow((_T_40____HeatCarrier____house_1_)_(_excess_energy____SlackNode____house_1_)_2)
+7e-05 flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_0)
+7e-05 flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_1)
+7e-05 flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_2)
+1000000000.0 flow((_missing_energy____SlackNode____house_1_)_(_T_20____HeatCarrier____house_1_)_0)
+1000000000.0 flow((_missing_energy____SlackNode____house_1_)_(_T_20____HeatCarrier____house_1_)_1)
+1000000000.0 flow((_missing_energy____SlackNode____house_1_)_(_T_20____HeatCarrier____house_1_)_2)
+1000000000.0 flow((_missing_energy____SlackNode____house_1_)_(_T_40____HeatCarrier____house_1_)_0)
+1000000000.0 flow((_missing_energy____SlackNode____house_1_)_(_T_40____HeatCarrier____house_1_)_1)
+1000000000.0 flow((_missing_energy____SlackNode____house_1_)_(_T_40____HeatCarrier____house_1_)_2)

s.t.

c_e_BusBlock_balance((_Hydrogen_30____GasCarrier____house_1_)_0)_:
-1 flow((_Hydrogen_30____GasCarrier____house_1_)_(_input____H2_demand____house_1_)_0)
+1 flow((_electrolyser____PEM_Ely____house_1_)_(_Hydrogen_30____GasCarrier____house_1_)_0)
= 0

c_e_BusBlock_balance((_Hydrogen_30____GasCarrier____house_1_)_1)_:
-1 flow((_Hydrogen_30____GasCarrier____house_1_)_(_input____H2_demand____house_1_)_1)
+1 flow((_electrolyser____PEM_Ely____house_1_)_(_Hydrogen_30____GasCarrier____house_1_)_1)
= 0

c_e_BusBlock_balance((_Hydrogen_30____GasCarrier____house_1_)_2)_:
-1 flow((_Hydrogen_30____GasCarrier____house_1_)_(_input____H2_demand____house_1_)_2)
+1 flow((_electrolyser____PEM_Ely____house_1_)_(_Hydrogen_30____GasCarrier____house_1_)_2)
= 0

c_e_BusBlock_balance((_T_20____HeatCarrier____house_1_)_0)_:
-1 flow((_T_20____HeatCarrier____house_1_)_(_heat_20_40____PEM_Ely____house_1_)_0)
-1 flow((_T_20____HeatCarrier____house_1_)_(_excess_energy____SlackNode____house_1_)_0)
+1 flow((_missing_energy____SlackNode____house_1_)_(_T_20____HeatCarrier____house_1_)_0)
+1 flow((_heat_exchanger____heating_demand____house_1_)_(_T_20____HeatCarrier____house_1_)_0)
= 0

c_e_BusBlock_balance((_T_20____HeatCarrier____house_1_)_1)_:
-1 flow((_T_20____HeatCarrier____house_1_)_(_heat_20_40____PEM_Ely____house_1_)_1)
-1 flow((_T_20____HeatCarrier____house_1_)_(_excess_energy____SlackNode____house_1_)_1)
+1 flow((_missing_energy____SlackNode____house_1_)_(_T_20____HeatCarrier____house_1_)_1)
+1 flow((_heat_exchanger____heating_demand____house_1_)_(_T_20____HeatCarrier____house_1_)_1)
= 0

c_e_BusBlock_balance((_T_20____HeatCarrier____house_1_)_2)_:
-1 flow((_T_20____HeatCarrier____house_1_)_(_heat_20_40____PEM_Ely____house_1_)_2)
-1 flow((_T_20____HeatCarrier____house_1_)_(_excess_energy____SlackNode____house_1_)_2)
+1 flow((_missing_energy____SlackNode____house_1_)_(_T_20____HeatCarrier____house_1_)_2)
+1 flow((_heat_exchanger____heating_demand____house_1_)_(_T_20____HeatCarrier____house_1_)_2)
= 0

c_e_BusBlock_balance((_T_40____HeatCarrier____house_1_)_0)_:
-1 flow((_T_40____HeatCarrier____house_1_)_(_excess_energy____SlackNode____house_1_)_0)
-1 flow((_T_40____HeatCarrier____house_1_)_(_heat_exchanger____heating_demand____house_1_)_0)
+1 flow((_heat_20_40____PEM_Ely____house_1_)_(_T_40____HeatCarrier____house_1_)_0)
+1 flow((_missing_energy____SlackNode____house_1_)_(_T_40____HeatCarrier____house_1_)_0)
= 0

c_e_BusBlock_balance((_T_40____HeatCarrier____house_1_)_1)_:
-1 flow((_T_40____HeatCarrier____house_1_)_(_excess_energy____SlackNode____house_1_)_1)
-1 flow((_T_40____HeatCarrier____house_1_)_(_heat_exchanger____heating_demand____house_1_)_1)
+1 flow((_heat_20_40____PEM_Ely____house_1_)_(_T_40____HeatCarrier____house_1_)_1)
+1 flow((_missing_energy____SlackNode____house_1_)_(_T_40____HeatCarrier____house_1_)_1)
= 0

c_e_BusBlock_balance((_T_40____HeatCarrier____house_1_)_2)_:
-1 flow((_T_40____HeatCarrier____house_1_)_(_excess_energy____SlackNode____house_1_)_2)
-1 flow((_T_40____HeatCarrier____house_1_)_(_heat_exchanger____heating_demand____house_1_)_2)
+1 flow((_heat_20_40____PEM_Ely____house_1_)_(_T_40____HeatCarrier____house_1_)_2)
+1 flow((_missing_energy____SlackNode____house_1_)_(_T_40____HeatCarrier____house_1_)_2)
= 0

c_e_BusBlock_balance((_distribution____ElectricityCarrier____house_1_)_0)_:
-1 flow((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_0)
+1 flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_0)
= 0

c_e_BusBlock_balance((_distribution____ElectricityCarrier____house_1_)_1)_:
-1 flow((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_1)
+1 flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_1)
= 0

c_e_BusBlock_balance((_distribution____ElectricityCarrier____house_1_)_2)_:
-1 flow((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_2)
+1 flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_2)
= 0

c_e_BusBlock_balance((_feed_in____ElectricityCarrier____house_1_)_0)_:
+1 flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_0)
= 0

c_e_BusBlock_balance((_feed_in____ElectricityCarrier____house_1_)_1)_:
+1 flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_1)
= 0

c_e_BusBlock_balance((_feed_in____ElectricityCarrier____house_1_)_2)_:
+1 flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_2)
= 0

c_e_BusBlock_balance((_grid_export____ElectricityGridConnection____house_1_)_0)_:
+1 flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_0)
= 0

c_e_BusBlock_balance((_grid_export____ElectricityGridConnection____house_1_)_1)_:
+1 flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_1)
= 0

c_e_BusBlock_balance((_grid_export____ElectricityGridConnection____house_1_)_2)_:
+1 flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_2)
= 0

c_e_BusBlock_balance((_grid_import____ElectricityGridConnection____house_1_)_0)_:
-1 flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_0)
+1 flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_0)
= 0

c_e_BusBlock_balance((_grid_import____ElectricityGridConnection____house_1_)_1)_:
-1 flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_1)
+1 flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_1)
= 0

c_e_BusBlock_balance((_grid_import____ElectricityGridConnection____house_1_)_2)_:
-1 flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_2)
+1 flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_2)
= 0

c_e_BusBlock_balance((_heat____PEM_Ely____house_1_)_0)_:
-1 flow((_heat____PEM_Ely____house_1_)_(_heat_20_40____PEM_Ely____house_1_)_0)
+1 flow((_electrolyser____PEM_Ely____house_1_)_(_heat____PEM_Ely____house_1_)_0)
= 0

c_e_BusBlock_balance((_heat____PEM_Ely____house_1_)_1)_:
-1 flow((_heat____PEM_Ely____house_1_)_(_heat_20_40____PEM_Ely____house_1_)_1)
+1 flow((_electrolyser____PEM_Ely____house_1_)_(_heat____PEM_Ely____house_1_)_1)
= 0

c_e_BusBlock_balance((_heat____PEM_Ely____house_1_)_2)_:
-1 flow((_heat____PEM_Ely____house_1_)_(_heat_20_40____PEM_Ely____house_1_)_2)
+1 flow((_electrolyser____PEM_Ely____house_1_)_(_heat____PEM_Ely____house_1_)_2)
= 0

c_e_BusBlock_balance((_input____H2_demand____house_1_)_0)_:
+1 flow((_Hydrogen_30____GasCarrier____house_1_)_(_input____H2_demand____house_1_)_0)
= 0.5

c_e_BusBlock_balance((_input____H2_demand____house_1_)_1)_:
+1 flow((_Hydrogen_30____GasCarrier____house_1_)_(_input____H2_demand____house_1_)_1)
= 2.5

c_e_BusBlock_balance((_input____H2_demand____house_1_)_2)_:
+1 flow((_Hydrogen_30____GasCarrier____house_1_)_(_input____H2_demand____house_1_)_2)
= 1.5

c_e_BusBlock_balance((_output____heating_demand____house_1_)_0)_:
+1 flow((_heat_exchanger____heating_demand____house_1_)_(_output____heating_demand____house_1_)_0)
= 3000

c_e_BusBlock_balance((_output____heating_demand____house_1_)_1)_:
+1 flow((_heat_exchanger____heating_demand____house_1_)_(_output____heating_demand____house_1_)_1)
= 3000

c_e_BusBlock_balance((_output____heating_demand____house_1_)_2)_:
+1 flow((_heat_exchanger____heating_demand____house_1_)_(_output____heating_demand____house_1_)_2)
= 3000

c_e_ConverterBlock_relation((_heat_exchanger____heating_demand____house_1_)_(_T_40____HeatCarrier____house_1_)_(_output____heating_demand____house_1_)_0)_:
+23.22 flow((_T_40____HeatCarrier____house_1_)_(_heat_exchanger____heating_demand____house_1_)_0)
-1 flow((_heat_exchanger____heating_demand____house_1_)_(_output____heating_demand____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_heat_exchanger____heating_demand____house_1_)_(_T_40____HeatCarrier____house_1_)_(_T_20____HeatCarrier____house_1_)_0)_:
+1 flow((_T_40____HeatCarrier____house_1_)_(_heat_exchanger____heating_demand____house_1_)_0)
-1 flow((_heat_exchanger____heating_demand____house_1_)_(_T_20____HeatCarrier____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_heat_20_40____PEM_Ely____house_1_)_(_T_20____HeatCarrier____house_1_)_(_T_40____HeatCarrier____house_1_)_0)_:
+1 flow((_T_20____HeatCarrier____house_1_)_(_heat_20_40____PEM_Ely____house_1_)_0)
-1 flow((_heat_20_40____PEM_Ely____house_1_)_(_T_40____HeatCarrier____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_heat_20_40____PEM_Ely____house_1_)_(_heat____PEM_Ely____house_1_)_(_T_40____HeatCarrier____house_1_)_0)_:
+1 flow((_heat____PEM_Ely____house_1_)_(_heat_20_40____PEM_Ely____house_1_)_0)
-23.22 flow((_heat_20_40____PEM_Ely____house_1_)_(_T_40____HeatCarrier____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_heat_exchanger____heating_demand____house_1_)_(_T_40____HeatCarrier____house_1_)_(_output____heating_demand____house_1_)_1)_:
+23.22 flow((_T_40____HeatCarrier____house_1_)_(_heat_exchanger____heating_demand____house_1_)_1)
-1 flow((_heat_exchanger____heating_demand____house_1_)_(_output____heating_demand____house_1_)_1)
= 0

c_e_ConverterBlock_relation((_heat_exchanger____heating_demand____house_1_)_(_T_40____HeatCarrier____house_1_)_(_T_20____HeatCarrier____house_1_)_1)_:
+1 flow((_T_40____HeatCarrier____house_1_)_(_heat_exchanger____heating_demand____house_1_)_1)
-1 flow((_heat_exchanger____heating_demand____house_1_)_(_T_20____HeatCarrier____house_1_)_1)
= 0

c_e_ConverterBlock_relation((_heat_20_40____PEM_Ely____house_1_)_(_T_20____HeatCarrier____house_1_)_(_T_40____HeatCarrier____house_1_)_1)_:
+1 flow((_T_20____HeatCarrier____house_1_)_(_heat_20_40____PEM_Ely____house_1_)_1)
-1 flow((_heat_20_40____PEM_Ely____house_1_)_(_T_40____HeatCarrier____house_1_)_1)
= 0

c_e_ConverterBlock_relation((_heat_20_40____PEM_Ely____house_1_)_(_heat____PEM_Ely____house_1_)_(_T_40____HeatCarrier____house_1_)_1)_:
+1 flow((_heat____PEM_Ely____house_1_)_(_heat_20_40____PEM_Ely____house_1_)_1)
-23.22 flow((_heat_20_40____PEM_Ely____house_1_)_(_T_40____HeatCarrier____house_1_)_1)
= 0

c_e_ConverterBlock_relation((_heat_exchanger____heating_demand____house_1_)_(_T_40____HeatCarrier____house_1_)_(_output____heating_demand____house_1_)_2)_:
+23.22 flow((_T_40____HeatCarrier____house_1_)_(_heat_exchanger____heating_demand____house_1_)_2)
-1 flow((_heat_exchanger____heating_demand____house_1_)_(_output____heating_demand____house_1_)_2)
= 0

c_e_ConverterBlock_relation((_heat_exchanger____heating_demand____house_1_)_(_T_40____HeatCarrier____house_1_)_(_T_20____HeatCarrier____house_1_)_2)_:
+1 flow((_T_40____HeatCarrier____house_1_)_(_heat_exchanger____heating_demand____house_1_)_2)
-1 flow((_heat_exchanger____heating_demand____house_1_)_(_T_20____HeatCarrier____house_1_)_2)
= 0

c_e_ConverterBlock_relation((_heat_20_40____PEM_Ely____house_1_)_(_T_20____HeatCarrier____house_1_)_(_T_40____HeatCarrier____house_1_)_2)_:
+1 flow((_T_20____HeatCarrier____house_1_)_(_heat_20_40____PEM_Ely____house_1_)_2)
-1 flow((_heat_20_40____PEM_Ely____house_1_)_(_T_40____HeatCarrier____house_1_)_2)
= 0

c_e_ConverterBlock_relation((_heat_20_40____PEM_Ely____house_1_)_(_heat____PEM_Ely____house_1_)_(_T_40____HeatCarrier____house_1_)_2)_:
+1 flow((_heat____PEM_Ely____house_1_)_(_heat_20_40____PEM_Ely____house_1_)_2)
-23.22 flow((_heat_20_40____PEM_Ely____house_1_)_(_T_40____HeatCarrier____house_1_)_2)
= 0

c_e_NonConvexFlowBlock_status_nominal_constraint((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_0)_:
+1 NonConvexFlowBlock_status_nominal((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_0)
-150000.0 NonConvexFlowBlock_status((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_0)
= 0

c_e_NonConvexFlowBlock_status_nominal_constraint((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_1)_:
+1 NonConvexFlowBlock_status_nominal((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_1)
-150000.0 NonConvexFlowBlock_status((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_1)
= 0

c_e_NonConvexFlowBlock_status_nominal_constraint((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_2)_:
+1 NonConvexFlowBlock_status_nominal((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_2)
-150000.0 NonConvexFlowBlock_status((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_2)
= 0

c_u_NonConvexFlowBlock_min((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_0)_:
-1 flow((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_0)
+0.15 NonConvexFlowBlock_status_nominal((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_0)
<= 0

c_u_NonConvexFlowBlock_min((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_1)_:
-1 flow((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_1)
+0.15 NonConvexFlowBlock_status_nominal((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_1)
<= 0

c_u_NonConvexFlowBlock_min((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_2)_:
-1 flow((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_2)
+0.15 NonConvexFlowBlock_status_nominal((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_2)
<= 0

c_u_NonConvexFlowBlock_max((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_0)_:
+1 flow((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_0)
-1 NonConvexFlowBlock_status_nominal((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_0)
<= 0

c_u_NonConvexFlowBlock_max((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_1)_:
+1 flow((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_1)
-1 NonConvexFlowBlock_status_nominal((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_1)
<= 0

c_u_NonConvexFlowBlock_max((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_2)_:
+1 flow((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_2)
-1 NonConvexFlowBlock_status_nominal((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_2)
<= 0

c_e_OffsetConverterBlock_relation((_electrolyser____PEM_Ely____house_1_)_(_distribution____ElectricityCarrier____house_1_)_(_Hydrogen_30____GasCarrier____house_1_)_0)_:
+1.8531264891195e-05 flow((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_0)
-1 flow((_electrolyser____PEM_Ely____house_1_)_(_Hydrogen_30____GasCarrier____house_1_)_0)
+3.7062529782390055e-07 NonConvexFlowBlock_status_nominal((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_0)
= 0

c_e_OffsetConverterBlock_relation((_electrolyser____PEM_Ely____house_1_)_(_distribution____ElectricityCarrier____house_1_)_(_heat____PEM_Ely____house_1_)_0)_:
+0.25882352941176473 flow((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_0)
-1 flow((_electrolyser____PEM_Ely____house_1_)_(_heat____PEM_Ely____house_1_)_0)
-0.00882352941176473 NonConvexFlowBlock_status_nominal((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_0)
= 0

c_e_OffsetConverterBlock_relation((_electrolyser____PEM_Ely____house_1_)_(_distribution____ElectricityCarrier____house_1_)_(_Hydrogen_30____GasCarrier____house_1_)_1)_:
+1.8531264891195e-05 flow((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_1)
-1 flow((_electrolyser____PEM_Ely____house_1_)_(_Hydrogen_30____GasCarrier____house_1_)_1)
+3.7062529782390055e-07 NonConvexFlowBlock_status_nominal((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_1)
= 0

c_e_OffsetConverterBlock_relation((_electrolyser____PEM_Ely____house_1_)_(_distribution____ElectricityCarrier____house_1_)_(_heat____PEM_Ely____house_1_)_1)_:
+0.25882352941176473 flow((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_1)
-1 flow((_electrolyser____PEM_Ely____house_1_)_(_heat____PEM_Ely____house_1_)_1)
-0.00882352941176473 NonConvexFlowBlock_status_nominal((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_1)
= 0

c_e_OffsetConverterBlock_relation((_electrolyser____PEM_Ely____house_1_)_(_distribution____ElectricityCarrier____house_1_)_(_Hydrogen_30____GasCarrier____house_1_)_2)_:
+1.8531264891195e-05 flow((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_2)
-1 flow((_electrolyser____PEM_Ely____house_1_)_(_Hydrogen_30____GasCarrier____house_1_)_2)
+3.7062529782390055e-07 NonConvexFlowBlock_status_nominal((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_2)
= 0

c_e_OffsetConverterBlock_relation((_electrolyser____PEM_Ely____house_1_)_(_distribution____ElectricityCarrier____house_1_)_(_heat____PEM_Ely____house_1_)_2)_:
+0.25882352941176473 flow((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_2)
-1 flow((_electrolyser____PEM_Ely____house_1_)_(_heat____PEM_Ely____house_1_)_2)
-0.00882352941176473 NonConvexFlowBlock_status_nominal((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_2)
= 0

bounds
   0 <= flow((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_0) <= 150000.0
   0 <= flow((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_1) <= 150000.0
   0 <= flow((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_2) <= 150000.0
   0 <= flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_0) <= +inf
   0 <= flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_1) <= +inf
   0 <= flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_2) <= +inf
   0 <= flow((_Hydrogen_30____GasCarrier____house_1_)_(_input____H2_demand____house_1_)_0) <= +inf
   0 <= flow((_Hydrogen_30____GasCarrier____house_1_)_(_input____H2_demand____house_1_)_1) <= +inf
   0 <= flow((_Hydrogen_30____GasCarrier____house_1_)_(_input____H2_demand____house_1_)_2) <= +inf
   0 <= flow((_T_20____HeatCarrier____house_1_)_(_heat_20_40____PEM_Ely____house_1_)_0) <= +inf
   0 <= flow((_T_20____HeatCarrier____house_1_)_(_heat_20_40____PEM_Ely____house_1_)_1) <= +inf
   0 <= flow((_T_20____HeatCarrier____house_1_)_(_heat_20_40____PEM_Ely____house_1_)_2) <= +inf
   0 <= flow((_T_20____HeatCarrier____house_1_)_(_excess_energy____SlackNode____house_1_)_0) <= +inf
   0 <= flow((_T_20____HeatCarrier____house_1_)_(_excess_energy____SlackNode____house_1_)_1) <= +inf
   0 <= flow((_T_20____HeatCarrier____house_1_)_(_excess_energy____SlackNode____house_1_)_2) <= +inf
   0 <= flow((_T_40____HeatCarrier____house_1_)_(_excess_energy____SlackNode____house_1_)_0) <= +inf
   0 <= flow((_T_40____HeatCarrier____house_1_)_(_excess_energy____SlackNode____house_1_)_1) <= +inf
   0 <= flow((_T_40____HeatCarrier____house_1_)_(_excess_energy____SlackNode____house_1_)_2) <= +inf
   0 <= flow((_T_40____HeatCarrier____house_1_)_(_heat_exchanger____heating_demand____house_1_)_0) <= +inf
   0 <= flow((_T_40____HeatCarrier____house_1_)_(_heat_exchanger____heating_demand____house_1_)_1) <= +inf
   0 <= flow((_T_40____HeatCarrier____house_1_)_(_heat_exchanger____heating_demand____house_1_)_2) <= +inf
   0 <= flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_0) <= +inf
   0 <= flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_1) <= +inf
   0 <= flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_2) <= +inf
   0 <= flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_0) <= +inf
   0 <= flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_1) <= +inf
   0 <= flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_2) <= +inf
   0 <= flow((_heat____PEM_Ely____house_1_)_(_heat_20_40____PEM_Ely____house_1_)_0) <= +inf
   0 <= flow((_heat____PEM_Ely____house_1_)_(_heat_20_40____PEM_Ely____house_1_)_1) <= +inf
   0 <= flow((_heat____PEM_Ely____house_1_)_(_heat_20_40____PEM_Ely____house_1_)_2) <= +inf
   0 <= flow((_heat_20_40____PEM_Ely____house_1_)_(_T_40____HeatCarrier____house_1_)_0) <= +inf
   0 <= flow((_heat_20_40____PEM_Ely____house_1_)_(_T_40____HeatCarrier____house_1_)_1) <= +inf
   0 <= flow((_heat_20_40____PEM_Ely____house_1_)_(_T_40____HeatCarrier____house_1_)_2) <= +inf
   0 <= flow((_electrolyser____PEM_Ely____house_1_)_(_Hydrogen_30____GasCarrier____house_1_)_0) <= +inf
   0 <= flow((_electrolyser____PEM_Ely____house_1_)_(_Hydrogen_30____GasCarrier____house_1_)_1) <= +inf
   0 <= flow((_electrolyser____PEM_Ely____house_1_)_(_Hydrogen_30____GasCarrier____house_1_)_2) <= +inf
   0 <= flow((_electrolyser____PEM_Ely____house_1_)_(_heat____PEM_Ely____house_1_)_0) <= +inf
   0 <= flow((_electrolyser____PEM_Ely____house_1_)_(_heat____PEM_Ely____house_1_)_1) <= +inf
   0 <= flow((_electrolyser____PEM_Ely____house_1_)_(_heat____PEM_Ely____house_1_)_2) <= +inf
   0 <= flow((_missing_energy____SlackNode____house_1_)_(_T_20____HeatCarrier____house_1_)_0) <= +inf
   0 <= flow((_missing_energy____SlackNode____house_1_)_(_T_20____HeatCarrier____house_1_)_1) <= +inf
   0 <= flow((_missing_energy____SlackNode____house_1_)_(_T_20____HeatCarrier____house_1_)_2) <= +inf
   0 <= flow((_missing_energy____SlackNode____house_1_)_(_T_40____HeatCarrier____house_1_)_0) <= +inf
   0 <= flow((_missing_energy____SlackNode____house_1_)_(_T_40____HeatCarrier____house_1_)_1) <= +inf
   0 <= flow((_missing_energy____SlackNode____house_1_)_(_T_40____HeatCarrier____house_1_)_2) <= +inf
   0 <= flow((_heat_exchanger____heating_demand____house_1_)_(_output____heating_demand____house_1_)_0) <= +inf
   0 <= flow((_heat_exchanger____heating_demand____house_1_)_(_output____heating_demand____house_1_)_1) <= +inf
   0 <= flow((_heat_exchanger____heating_demand____house_1_)_(_output____heating_demand____house_1_)_2) <= +inf
   0 <= flow((_heat_exchanger____heating_demand____house_1_)_(_T_20____HeatCarrier____house_1_)_0) <= +inf
   0 <= flow((_heat_exchanger____heating_demand____house_1_)_(_T_20____HeatCarrier____house_1_)_1) <= +inf
   0 <= flow((_heat_exchanger____heating_demand____house_1_)_(_T_20____HeatCarrier____house_1_)_2) <= +inf
   0 <= NonConvexFlowBlock_status_nominal((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_0) <= +inf
   0 <= NonConvexFlowBlock_status_nominal((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_1) <= +inf
   0 <= NonConvexFlowBlock_status_nominal((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_2) <= +inf
   0 <= NonConvexFlowBlock_status((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_0) <= 1
   0 <= NonConvexFlowBlock_status((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_1) <= 1
   0 <= NonConvexFlowBlock_status((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_2) <= 1
binary
  NonConvexFlowBlock_status((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_0)
  NonConvexFlowBlock_status((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_1)
  NonConvexFlowBlock_status((_distribution____ElectricityCarrier____house_1_)_(_electrolyser____PEM_Ely____house_1_)_2)
end
