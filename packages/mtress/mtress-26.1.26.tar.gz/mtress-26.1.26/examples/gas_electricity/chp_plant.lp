\* Source Pyomo model name=Model *\

min 
objective:
+5e-05 flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_0)
+5 flow((_house_1____GasGridConnection____source_import_)_(_house_1____GasGridConnection____grid_import_)_0)

s.t.

c_e_BusBlock_balance((_house_1____ElectricityCarrier____distribution_)_0)_:
-1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____electricity_demand____input_)_0)
+1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_0)
+1 flow((_house_1____Gas_CHP____CHP_)_(_house_1____ElectricityCarrier____distribution_)_0)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____feed_in_)_0)_:
+1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_0)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_export_)_0)_:
+1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_0)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_import_)_0)_:
-1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_0)
+1 flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_0)
= 0

c_e_BusBlock_balance((_house_1____GasCarrier____NaturalGas_10_)_0)_:
-1 flow((_house_1____GasCarrier____NaturalGas_10_)_(_house_1____GasGridConnection____grid_export_)_0)
-1 flow((_house_1____GasCarrier____NaturalGas_10_)_(_house_1____Gas_CHP____CHP_)_0)
+1 flow((_house_1____GasGridConnection____grid_import_)_(_house_1____GasCarrier____NaturalGas_10_)_0)
= 0

c_e_BusBlock_balance((_house_1____GasGridConnection____grid_export_)_0)_:
+1 flow((_house_1____GasCarrier____NaturalGas_10_)_(_house_1____GasGridConnection____grid_export_)_0)
= 0

c_e_BusBlock_balance((_house_1____GasGridConnection____grid_import_)_0)_:
-1 flow((_house_1____GasGridConnection____grid_import_)_(_house_1____GasCarrier____NaturalGas_10_)_0)
+1 flow((_house_1____GasGridConnection____source_import_)_(_house_1____GasGridConnection____grid_import_)_0)
= 0

c_e_BusBlock_balance((_house_1____Gas_CHP____heat_)_0)_:
-1 flow((_house_1____Gas_CHP____heat_)_(_house_1____Gas_CHP____heat_20_80_)_0)
+1 flow((_house_1____Gas_CHP____CHP_)_(_house_1____Gas_CHP____heat_)_0)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_20_)_0)_:
-1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____Gas_CHP____heat_20_80_)_0)
+1 flow((_house_1____heat_demand____heat_exchanger_)_(_house_1____HeatCarrier____T_20_)_0)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_80_)_0)_:
-1 flow((_house_1____HeatCarrier____T_80_)_(_house_1____heat_demand____heat_exchanger_)_0)
+1 flow((_house_1____Gas_CHP____heat_20_80_)_(_house_1____HeatCarrier____T_80_)_0)
= 0

c_e_BusBlock_balance((_house_1____electricity_demand____input_)_0)_:
+1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____electricity_demand____input_)_0)
= 1000

c_e_BusBlock_balance((_house_1____heat_demand____output_)_0)_:
+1 flow((_house_1____heat_demand____heat_exchanger_)_(_house_1____heat_demand____output_)_0)
= 1000

c_e_ConverterBlock_relation((_house_1____heat_demand____heat_exchanger_)_(_house_1____HeatCarrier____T_80_)_(_house_1____heat_demand____output_)_0)_:
+69.66 flow((_house_1____HeatCarrier____T_80_)_(_house_1____heat_demand____heat_exchanger_)_0)
-1 flow((_house_1____heat_demand____heat_exchanger_)_(_house_1____heat_demand____output_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____heat_demand____heat_exchanger_)_(_house_1____HeatCarrier____T_80_)_(_house_1____HeatCarrier____T_20_)_0)_:
+1 flow((_house_1____HeatCarrier____T_80_)_(_house_1____heat_demand____heat_exchanger_)_0)
-1 flow((_house_1____heat_demand____heat_exchanger_)_(_house_1____HeatCarrier____T_20_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____Gas_CHP____CHP_)_(_house_1____GasCarrier____NaturalGas_10_)_(_house_1____ElectricityCarrier____distribution_)_0)_:
+5473.0 flow((_house_1____GasCarrier____NaturalGas_10_)_(_house_1____Gas_CHP____CHP_)_0)
-1 flow((_house_1____Gas_CHP____CHP_)_(_house_1____ElectricityCarrier____distribution_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____Gas_CHP____CHP_)_(_house_1____GasCarrier____NaturalGas_10_)_(_house_1____Gas_CHP____heat_)_0)_:
+5902.0 flow((_house_1____GasCarrier____NaturalGas_10_)_(_house_1____Gas_CHP____CHP_)_0)
-1 flow((_house_1____Gas_CHP____CHP_)_(_house_1____Gas_CHP____heat_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____Gas_CHP____heat_20_80_)_(_house_1____Gas_CHP____heat_)_(_house_1____HeatCarrier____T_80_)_0)_:
+1 flow((_house_1____Gas_CHP____heat_)_(_house_1____Gas_CHP____heat_20_80_)_0)
-69.66 flow((_house_1____Gas_CHP____heat_20_80_)_(_house_1____HeatCarrier____T_80_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____Gas_CHP____heat_20_80_)_(_house_1____HeatCarrier____T_20_)_(_house_1____HeatCarrier____T_80_)_0)_:
+1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____Gas_CHP____heat_20_80_)_0)
-1 flow((_house_1____Gas_CHP____heat_20_80_)_(_house_1____HeatCarrier____T_80_)_0)
= 0

bounds
   0 <= flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____electricity_demand____input_)_0) <= +inf
   0 <= flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_0) <= +inf
   0 <= flow((_house_1____GasCarrier____NaturalGas_10_)_(_house_1____GasGridConnection____grid_export_)_0) <= +inf
   0.0 <= flow((_house_1____GasCarrier____NaturalGas_10_)_(_house_1____Gas_CHP____CHP_)_0) <= 18.27151470856934
   0 <= flow((_house_1____HeatCarrier____T_20_)_(_house_1____Gas_CHP____heat_20_80_)_0) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_80_)_(_house_1____heat_demand____heat_exchanger_)_0) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_0) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_0) <= +inf
   0 <= flow((_house_1____GasGridConnection____grid_import_)_(_house_1____GasCarrier____NaturalGas_10_)_0) <= +inf
   0 <= flow((_house_1____GasGridConnection____source_import_)_(_house_1____GasGridConnection____grid_import_)_0) <= +inf
   0 <= flow((_house_1____heat_demand____heat_exchanger_)_(_house_1____heat_demand____output_)_0) <= +inf
   0 <= flow((_house_1____heat_demand____heat_exchanger_)_(_house_1____HeatCarrier____T_20_)_0) <= +inf
   0 <= flow((_house_1____Gas_CHP____heat_)_(_house_1____Gas_CHP____heat_20_80_)_0) <= +inf
   0 <= flow((_house_1____Gas_CHP____heat_20_80_)_(_house_1____HeatCarrier____T_80_)_0) <= +inf
   0 <= flow((_house_1____Gas_CHP____CHP_)_(_house_1____ElectricityCarrier____distribution_)_0) <= +inf
   0 <= flow((_house_1____Gas_CHP____CHP_)_(_house_1____Gas_CHP____heat_)_0) <= +inf
end
