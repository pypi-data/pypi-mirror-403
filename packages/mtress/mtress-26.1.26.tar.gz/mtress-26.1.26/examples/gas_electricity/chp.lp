\* Source Pyomo model name=Model *\

min 
objective:
+5e-05 flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_0)
+5 flow((_source_import____GasGridConnection____house_1_)_(_grid_import____GasGridConnection____house_1_)_0)

s.t.

c_e_BusBlock_balance((_NaturalGas_10____GasCarrier____house_1_)_0)_:
-1 flow((_NaturalGas_10____GasCarrier____house_1_)_(_grid_export____GasGridConnection____house_1_)_0)
-1 flow((_NaturalGas_10____GasCarrier____house_1_)_(_mixer____Gas_CHP____house_1_)_0)
+1 flow((_grid_import____GasGridConnection____house_1_)_(_NaturalGas_10____GasCarrier____house_1_)_0)
= 0

c_e_BusBlock_balance((_T_20____HeatCarrier____house_1_)_0)_:
-1 flow((_T_20____HeatCarrier____house_1_)_(_heat_20_80____Gas_CHP____house_1_)_0)
+1 flow((_heat_exchanger____heat_demand____house_1_)_(_T_20____HeatCarrier____house_1_)_0)
= 0

c_e_BusBlock_balance((_T_80____HeatCarrier____house_1_)_0)_:
-1 flow((_T_80____HeatCarrier____house_1_)_(_heat_exchanger____heat_demand____house_1_)_0)
+1 flow((_heat_20_80____Gas_CHP____house_1_)_(_T_80____HeatCarrier____house_1_)_0)
= 0

c_e_BusBlock_balance((_distribution____ElectricityCarrier____house_1_)_0)_:
-1 flow((_distribution____ElectricityCarrier____house_1_)_(_input____electricity_demand____house_1_)_0)
+1 flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_0)
+1 flow((_splitter____Gas_CHP____house_1_)_(_distribution____ElectricityCarrier____house_1_)_0)
= 0

c_e_BusBlock_balance((_feed_in____ElectricityCarrier____house_1_)_0)_:
-1 flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_0)
+1 flow((_splitter____Gas_CHP____house_1_)_(_feed_in____ElectricityCarrier____house_1_)_0)
= 0

c_e_BusBlock_balance((_grid_export____ElectricityGridConnection____house_1_)_0)_:
+1 flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_0)
= 0

c_e_BusBlock_balance((_grid_export____GasGridConnection____house_1_)_0)_:
+1 flow((_NaturalGas_10____GasCarrier____house_1_)_(_grid_export____GasGridConnection____house_1_)_0)
= 0

c_e_BusBlock_balance((_grid_import____ElectricityGridConnection____house_1_)_0)_:
-1 flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_0)
+1 flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_0)
= 0

c_e_BusBlock_balance((_grid_import____GasGridConnection____house_1_)_0)_:
-1 flow((_grid_import____GasGridConnection____house_1_)_(_NaturalGas_10____GasCarrier____house_1_)_0)
+1 flow((_source_import____GasGridConnection____house_1_)_(_grid_import____GasGridConnection____house_1_)_0)
= 0

c_e_BusBlock_balance((_heat____Gas_CHP____house_1_)_0)_:
-1 flow((_heat____Gas_CHP____house_1_)_(_heat_20_80____Gas_CHP____house_1_)_0)
+1 flow((_CHP____Gas_CHP____house_1_)_(_heat____Gas_CHP____house_1_)_0)
= 0

c_e_BusBlock_balance((_input____electricity_demand____house_1_)_0)_:
+1 flow((_distribution____ElectricityCarrier____house_1_)_(_input____electricity_demand____house_1_)_0)
= 1000

c_e_BusBlock_balance((_mixer____Gas_CHP____house_1_)_0)_:
+1 flow((_NaturalGas_10____GasCarrier____house_1_)_(_mixer____Gas_CHP____house_1_)_0)
-1 flow((_mixer____Gas_CHP____house_1_)_(_CHP____Gas_CHP____house_1_)_0)
= 0

c_e_BusBlock_balance((_output____heat_demand____house_1_)_0)_:
+1 flow((_heat_exchanger____heat_demand____house_1_)_(_output____heat_demand____house_1_)_0)
= 1000

c_e_BusBlock_balance((_splitter____Gas_CHP____house_1_)_0)_:
-1 flow((_splitter____Gas_CHP____house_1_)_(_feed_in____ElectricityCarrier____house_1_)_0)
-1 flow((_splitter____Gas_CHP____house_1_)_(_distribution____ElectricityCarrier____house_1_)_0)
+1 flow((_CHP____Gas_CHP____house_1_)_(_splitter____Gas_CHP____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_CHP____Gas_CHP____house_1_)_(_mixer____Gas_CHP____house_1_)_(_heat____Gas_CHP____house_1_)_0)_:
+5902.0 flow((_mixer____Gas_CHP____house_1_)_(_CHP____Gas_CHP____house_1_)_0)
-1 flow((_CHP____Gas_CHP____house_1_)_(_heat____Gas_CHP____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_CHP____Gas_CHP____house_1_)_(_mixer____Gas_CHP____house_1_)_(_splitter____Gas_CHP____house_1_)_0)_:
+5473.0 flow((_mixer____Gas_CHP____house_1_)_(_CHP____Gas_CHP____house_1_)_0)
-1 flow((_CHP____Gas_CHP____house_1_)_(_splitter____Gas_CHP____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_heat_exchanger____heat_demand____house_1_)_(_T_80____HeatCarrier____house_1_)_(_output____heat_demand____house_1_)_0)_:
+69.66 flow((_T_80____HeatCarrier____house_1_)_(_heat_exchanger____heat_demand____house_1_)_0)
-1 flow((_heat_exchanger____heat_demand____house_1_)_(_output____heat_demand____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_heat_exchanger____heat_demand____house_1_)_(_T_80____HeatCarrier____house_1_)_(_T_20____HeatCarrier____house_1_)_0)_:
+1 flow((_T_80____HeatCarrier____house_1_)_(_heat_exchanger____heat_demand____house_1_)_0)
-1 flow((_heat_exchanger____heat_demand____house_1_)_(_T_20____HeatCarrier____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_heat_20_80____Gas_CHP____house_1_)_(_T_20____HeatCarrier____house_1_)_(_T_80____HeatCarrier____house_1_)_0)_:
+1 flow((_T_20____HeatCarrier____house_1_)_(_heat_20_80____Gas_CHP____house_1_)_0)
-1 flow((_heat_20_80____Gas_CHP____house_1_)_(_T_80____HeatCarrier____house_1_)_0)
= 0

c_e_ConverterBlock_relation((_heat_20_80____Gas_CHP____house_1_)_(_heat____Gas_CHP____house_1_)_(_T_80____HeatCarrier____house_1_)_0)_:
+1 flow((_heat____Gas_CHP____house_1_)_(_heat_20_80____Gas_CHP____house_1_)_0)
-69.66 flow((_heat_20_80____Gas_CHP____house_1_)_(_T_80____HeatCarrier____house_1_)_0)
= 0

bounds
   0 <= flow((_distribution____ElectricityCarrier____house_1_)_(_input____electricity_demand____house_1_)_0) <= +inf
   0 <= flow((_feed_in____ElectricityCarrier____house_1_)_(_grid_export____ElectricityGridConnection____house_1_)_0) <= +inf
   0 <= flow((_NaturalGas_10____GasCarrier____house_1_)_(_grid_export____GasGridConnection____house_1_)_0) <= +inf
   0 <= flow((_NaturalGas_10____GasCarrier____house_1_)_(_mixer____Gas_CHP____house_1_)_0) <= +inf
   0 <= flow((_T_20____HeatCarrier____house_1_)_(_heat_20_80____Gas_CHP____house_1_)_0) <= +inf
   0 <= flow((_T_80____HeatCarrier____house_1_)_(_heat_exchanger____heat_demand____house_1_)_0) <= +inf
   0 <= flow((_grid_import____ElectricityGridConnection____house_1_)_(_distribution____ElectricityCarrier____house_1_)_0) <= +inf
   0 <= flow((_source_import____ElectricityGridConnection____house_1_)_(_grid_import____ElectricityGridConnection____house_1_)_0) <= +inf
   0 <= flow((_grid_import____GasGridConnection____house_1_)_(_NaturalGas_10____GasCarrier____house_1_)_0) <= +inf
   0 <= flow((_source_import____GasGridConnection____house_1_)_(_grid_import____GasGridConnection____house_1_)_0) <= +inf
   0 <= flow((_heat____Gas_CHP____house_1_)_(_heat_20_80____Gas_CHP____house_1_)_0) <= +inf
   0 <= flow((_heat_20_80____Gas_CHP____house_1_)_(_T_80____HeatCarrier____house_1_)_0) <= +inf
   0 <= flow((_splitter____Gas_CHP____house_1_)_(_feed_in____ElectricityCarrier____house_1_)_0) <= +inf
   0 <= flow((_splitter____Gas_CHP____house_1_)_(_distribution____ElectricityCarrier____house_1_)_0) <= +inf
   0.0 <= flow((_mixer____Gas_CHP____house_1_)_(_CHP____Gas_CHP____house_1_)_0) <= 18.27151470856934
   0 <= flow((_CHP____Gas_CHP____house_1_)_(_heat____Gas_CHP____house_1_)_0) <= +inf
   0 <= flow((_CHP____Gas_CHP____house_1_)_(_splitter____Gas_CHP____house_1_)_0) <= +inf
   0 <= flow((_heat_exchanger____heat_demand____house_1_)_(_output____heat_demand____house_1_)_0) <= +inf
   0 <= flow((_heat_exchanger____heat_demand____house_1_)_(_T_20____HeatCarrier____house_1_)_0) <= +inf
end
