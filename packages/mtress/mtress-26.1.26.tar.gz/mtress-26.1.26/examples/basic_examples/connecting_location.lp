\* Source Pyomo model name=Model *\

min 
objective:
-0.0001 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_1____ElectricityGridConnection____sink_export_)_0)
-0.0001 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_1____ElectricityGridConnection____sink_export_)_1)
-0.0001 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_1____ElectricityGridConnection____sink_export_)_2)
-0.0001 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_1____ElectricityGridConnection____sink_export_)_3)
-0.0001 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_1____ElectricityGridConnection____sink_export_)_4)
-0.0001 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_1____ElectricityGridConnection____sink_export_)_5)
-0.0001 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_1____ElectricityGridConnection____sink_export_)_6)
-0.0001 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_1____ElectricityGridConnection____sink_export_)_7)
-0.0001 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_1____ElectricityGridConnection____sink_export_)_8)
-7.8 flow((_house_1____GasGridConnection____grid_export_)_(_house_1____GasGridConnection____sink_export_)_0)
-7.8 flow((_house_1____GasGridConnection____grid_export_)_(_house_1____GasGridConnection____sink_export_)_1)
-7.8 flow((_house_1____GasGridConnection____grid_export_)_(_house_1____GasGridConnection____sink_export_)_2)
-7.8 flow((_house_1____GasGridConnection____grid_export_)_(_house_1____GasGridConnection____sink_export_)_3)
-7.8 flow((_house_1____GasGridConnection____grid_export_)_(_house_1____GasGridConnection____sink_export_)_4)
-7.8 flow((_house_1____GasGridConnection____grid_export_)_(_house_1____GasGridConnection____sink_export_)_5)
-7.8 flow((_house_1____GasGridConnection____grid_export_)_(_house_1____GasGridConnection____sink_export_)_6)
-7.8 flow((_house_1____GasGridConnection____grid_export_)_(_house_1____GasGridConnection____sink_export_)_7)
-7.8 flow((_house_1____GasGridConnection____grid_export_)_(_house_1____GasGridConnection____sink_export_)_8)
+0.25 flow((_house_2____ElectricityGridConnection____source_import_)_(_house_2____ElectricityGridConnection____grid_import_)_0)
+0.25 flow((_house_2____ElectricityGridConnection____source_import_)_(_house_2____ElectricityGridConnection____grid_import_)_1)
+0.25 flow((_house_2____ElectricityGridConnection____source_import_)_(_house_2____ElectricityGridConnection____grid_import_)_2)
+0.25 flow((_house_2____ElectricityGridConnection____source_import_)_(_house_2____ElectricityGridConnection____grid_import_)_3)
+0.25 flow((_house_2____ElectricityGridConnection____source_import_)_(_house_2____ElectricityGridConnection____grid_import_)_4)
+0.25 flow((_house_2____ElectricityGridConnection____source_import_)_(_house_2____ElectricityGridConnection____grid_import_)_5)
+0.25 flow((_house_2____ElectricityGridConnection____source_import_)_(_house_2____ElectricityGridConnection____grid_import_)_6)
+0.25 flow((_house_2____ElectricityGridConnection____source_import_)_(_house_2____ElectricityGridConnection____grid_import_)_7)
+0.25 flow((_house_2____ElectricityGridConnection____source_import_)_(_house_2____ElectricityGridConnection____grid_import_)_8)

s.t.

c_e_BusBlock_balance((_house_1____ElectricityCarrier____distribution_)_0)_:
-1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____electrolyser_)_0)
+1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_0)
+1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_0)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____distribution_)_1)_:
-1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____electrolyser_)_1)
+1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_1)
+1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_1)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____distribution_)_2)_:
-1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____electrolyser_)_2)
+1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_2)
+1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_2)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____distribution_)_3)_:
-1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____electrolyser_)_3)
+1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_3)
+1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_3)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____distribution_)_4)_:
-1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____electrolyser_)_4)
+1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_4)
+1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_4)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____distribution_)_5)_:
-1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____electrolyser_)_5)
+1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_5)
+1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_5)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____distribution_)_6)_:
-1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____electrolyser_)_6)
+1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_6)
+1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_6)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____distribution_)_7)_:
-1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____electrolyser_)_7)
+1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_7)
+1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_7)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____distribution_)_8)_:
-1 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____electrolyser_)_8)
+1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_8)
+1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_8)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____feed_in_)_0)_:
-1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_0)
+1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____feed_in_)_0)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____feed_in_)_1)_:
-1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_1)
+1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____feed_in_)_1)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____feed_in_)_2)_:
-1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_2)
+1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____feed_in_)_2)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____feed_in_)_3)_:
-1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_3)
+1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____feed_in_)_3)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____feed_in_)_4)_:
-1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_4)
+1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____feed_in_)_4)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____feed_in_)_5)_:
-1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_5)
+1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____feed_in_)_5)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____feed_in_)_6)_:
-1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_6)
+1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____feed_in_)_6)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____feed_in_)_7)_:
-1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_7)
+1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____feed_in_)_7)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____feed_in_)_8)_:
-1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_8)
+1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____feed_in_)_8)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_export_)_0)_:
+1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_0)
-1 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_1____ElectricityGridConnection____sink_export_)_0)
-1 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_0)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_export_)_1)_:
+1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_1)
-1 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_1____ElectricityGridConnection____sink_export_)_1)
-1 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_1)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_export_)_2)_:
+1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_2)
-1 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_1____ElectricityGridConnection____sink_export_)_2)
-1 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_2)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_export_)_3)_:
+1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_3)
-1 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_1____ElectricityGridConnection____sink_export_)_3)
-1 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_3)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_export_)_4)_:
+1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_4)
-1 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_1____ElectricityGridConnection____sink_export_)_4)
-1 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_4)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_export_)_5)_:
+1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_5)
-1 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_1____ElectricityGridConnection____sink_export_)_5)
-1 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_5)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_export_)_6)_:
+1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_6)
-1 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_1____ElectricityGridConnection____sink_export_)_6)
-1 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_6)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_export_)_7)_:
+1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_7)
-1 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_1____ElectricityGridConnection____sink_export_)_7)
-1 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_7)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_export_)_8)_:
+1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_8)
-1 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_1____ElectricityGridConnection____sink_export_)_8)
-1 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_8)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_import_)_0)_:
+1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_0)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_import_)_1)_:
+1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_1)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_import_)_2)_:
+1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_2)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_import_)_3)_:
+1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_3)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_import_)_4)_:
+1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_4)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_import_)_5)_:
+1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_5)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_import_)_6)_:
+1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_6)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_import_)_7)_:
+1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_7)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_import_)_8)_:
+1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_8)
= 0

c_e_BusBlock_balance((_house_1____Ely____heat_)_0)_:
-1 flow((_house_1____Ely____heat_)_(_house_1____Ely____heat_20_50_)_0)
+1 flow((_house_1____Ely____electrolyser_)_(_house_1____Ely____heat_)_0)
= 0

c_e_BusBlock_balance((_house_1____Ely____heat_)_1)_:
-1 flow((_house_1____Ely____heat_)_(_house_1____Ely____heat_20_50_)_1)
+1 flow((_house_1____Ely____electrolyser_)_(_house_1____Ely____heat_)_1)
= 0

c_e_BusBlock_balance((_house_1____Ely____heat_)_2)_:
-1 flow((_house_1____Ely____heat_)_(_house_1____Ely____heat_20_50_)_2)
+1 flow((_house_1____Ely____electrolyser_)_(_house_1____Ely____heat_)_2)
= 0

c_e_BusBlock_balance((_house_1____Ely____heat_)_3)_:
-1 flow((_house_1____Ely____heat_)_(_house_1____Ely____heat_20_50_)_3)
+1 flow((_house_1____Ely____electrolyser_)_(_house_1____Ely____heat_)_3)
= 0

c_e_BusBlock_balance((_house_1____Ely____heat_)_4)_:
-1 flow((_house_1____Ely____heat_)_(_house_1____Ely____heat_20_50_)_4)
+1 flow((_house_1____Ely____electrolyser_)_(_house_1____Ely____heat_)_4)
= 0

c_e_BusBlock_balance((_house_1____Ely____heat_)_5)_:
-1 flow((_house_1____Ely____heat_)_(_house_1____Ely____heat_20_50_)_5)
+1 flow((_house_1____Ely____electrolyser_)_(_house_1____Ely____heat_)_5)
= 0

c_e_BusBlock_balance((_house_1____Ely____heat_)_6)_:
-1 flow((_house_1____Ely____heat_)_(_house_1____Ely____heat_20_50_)_6)
+1 flow((_house_1____Ely____electrolyser_)_(_house_1____Ely____heat_)_6)
= 0

c_e_BusBlock_balance((_house_1____Ely____heat_)_7)_:
-1 flow((_house_1____Ely____heat_)_(_house_1____Ely____heat_20_50_)_7)
+1 flow((_house_1____Ely____electrolyser_)_(_house_1____Ely____heat_)_7)
= 0

c_e_BusBlock_balance((_house_1____Ely____heat_)_8)_:
-1 flow((_house_1____Ely____heat_)_(_house_1____Ely____heat_20_50_)_8)
+1 flow((_house_1____Ely____electrolyser_)_(_house_1____Ely____heat_)_8)
= 0

c_e_BusBlock_balance((_house_1____GasCarrier____Hydrogen_30_)_0)_:
-1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasGridConnection____grid_export_)_0)
+1 flow((_house_1____GasCarrier____Hydrogen_60_)_(_house_1____GasCarrier____Hydrogen_30_)_0)
+1 flow((_house_1____GasGridConnection____grid_import_)_(_house_1____GasCarrier____Hydrogen_30_)_0)
= 0

c_e_BusBlock_balance((_house_1____GasCarrier____Hydrogen_30_)_1)_:
-1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasGridConnection____grid_export_)_1)
+1 flow((_house_1____GasCarrier____Hydrogen_60_)_(_house_1____GasCarrier____Hydrogen_30_)_1)
+1 flow((_house_1____GasGridConnection____grid_import_)_(_house_1____GasCarrier____Hydrogen_30_)_1)
= 0

c_e_BusBlock_balance((_house_1____GasCarrier____Hydrogen_30_)_2)_:
-1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasGridConnection____grid_export_)_2)
+1 flow((_house_1____GasCarrier____Hydrogen_60_)_(_house_1____GasCarrier____Hydrogen_30_)_2)
+1 flow((_house_1____GasGridConnection____grid_import_)_(_house_1____GasCarrier____Hydrogen_30_)_2)
= 0

c_e_BusBlock_balance((_house_1____GasCarrier____Hydrogen_30_)_3)_:
-1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasGridConnection____grid_export_)_3)
+1 flow((_house_1____GasCarrier____Hydrogen_60_)_(_house_1____GasCarrier____Hydrogen_30_)_3)
+1 flow((_house_1____GasGridConnection____grid_import_)_(_house_1____GasCarrier____Hydrogen_30_)_3)
= 0

c_e_BusBlock_balance((_house_1____GasCarrier____Hydrogen_30_)_4)_:
-1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasGridConnection____grid_export_)_4)
+1 flow((_house_1____GasCarrier____Hydrogen_60_)_(_house_1____GasCarrier____Hydrogen_30_)_4)
+1 flow((_house_1____GasGridConnection____grid_import_)_(_house_1____GasCarrier____Hydrogen_30_)_4)
= 0

c_e_BusBlock_balance((_house_1____GasCarrier____Hydrogen_30_)_5)_:
-1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasGridConnection____grid_export_)_5)
+1 flow((_house_1____GasCarrier____Hydrogen_60_)_(_house_1____GasCarrier____Hydrogen_30_)_5)
+1 flow((_house_1____GasGridConnection____grid_import_)_(_house_1____GasCarrier____Hydrogen_30_)_5)
= 0

c_e_BusBlock_balance((_house_1____GasCarrier____Hydrogen_30_)_6)_:
-1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasGridConnection____grid_export_)_6)
+1 flow((_house_1____GasCarrier____Hydrogen_60_)_(_house_1____GasCarrier____Hydrogen_30_)_6)
+1 flow((_house_1____GasGridConnection____grid_import_)_(_house_1____GasCarrier____Hydrogen_30_)_6)
= 0

c_e_BusBlock_balance((_house_1____GasCarrier____Hydrogen_30_)_7)_:
-1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasGridConnection____grid_export_)_7)
+1 flow((_house_1____GasCarrier____Hydrogen_60_)_(_house_1____GasCarrier____Hydrogen_30_)_7)
+1 flow((_house_1____GasGridConnection____grid_import_)_(_house_1____GasCarrier____Hydrogen_30_)_7)
= 0

c_e_BusBlock_balance((_house_1____GasCarrier____Hydrogen_30_)_8)_:
-1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasGridConnection____grid_export_)_8)
+1 flow((_house_1____GasCarrier____Hydrogen_60_)_(_house_1____GasCarrier____Hydrogen_30_)_8)
+1 flow((_house_1____GasGridConnection____grid_import_)_(_house_1____GasCarrier____Hydrogen_30_)_8)
= 0

c_e_BusBlock_balance((_house_1____GasCarrier____Hydrogen_60_)_0)_:
-1 flow((_house_1____GasCarrier____Hydrogen_60_)_(_house_1____GasCarrier____Hydrogen_30_)_0)
+1 flow((_house_1____Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_60_)_0)
= 0

c_e_BusBlock_balance((_house_1____GasCarrier____Hydrogen_60_)_1)_:
-1 flow((_house_1____GasCarrier____Hydrogen_60_)_(_house_1____GasCarrier____Hydrogen_30_)_1)
+1 flow((_house_1____Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_60_)_1)
= 0

c_e_BusBlock_balance((_house_1____GasCarrier____Hydrogen_60_)_2)_:
-1 flow((_house_1____GasCarrier____Hydrogen_60_)_(_house_1____GasCarrier____Hydrogen_30_)_2)
+1 flow((_house_1____Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_60_)_2)
= 0

c_e_BusBlock_balance((_house_1____GasCarrier____Hydrogen_60_)_3)_:
-1 flow((_house_1____GasCarrier____Hydrogen_60_)_(_house_1____GasCarrier____Hydrogen_30_)_3)
+1 flow((_house_1____Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_60_)_3)
= 0

c_e_BusBlock_balance((_house_1____GasCarrier____Hydrogen_60_)_4)_:
-1 flow((_house_1____GasCarrier____Hydrogen_60_)_(_house_1____GasCarrier____Hydrogen_30_)_4)
+1 flow((_house_1____Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_60_)_4)
= 0

c_e_BusBlock_balance((_house_1____GasCarrier____Hydrogen_60_)_5)_:
-1 flow((_house_1____GasCarrier____Hydrogen_60_)_(_house_1____GasCarrier____Hydrogen_30_)_5)
+1 flow((_house_1____Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_60_)_5)
= 0

c_e_BusBlock_balance((_house_1____GasCarrier____Hydrogen_60_)_6)_:
-1 flow((_house_1____GasCarrier____Hydrogen_60_)_(_house_1____GasCarrier____Hydrogen_30_)_6)
+1 flow((_house_1____Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_60_)_6)
= 0

c_e_BusBlock_balance((_house_1____GasCarrier____Hydrogen_60_)_7)_:
-1 flow((_house_1____GasCarrier____Hydrogen_60_)_(_house_1____GasCarrier____Hydrogen_30_)_7)
+1 flow((_house_1____Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_60_)_7)
= 0

c_e_BusBlock_balance((_house_1____GasCarrier____Hydrogen_60_)_8)_:
-1 flow((_house_1____GasCarrier____Hydrogen_60_)_(_house_1____GasCarrier____Hydrogen_30_)_8)
+1 flow((_house_1____Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_60_)_8)
= 0

c_e_BusBlock_balance((_house_1____GasGridConnection____grid_export_)_0)_:
+1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasGridConnection____grid_export_)_0)
-1 flow((_house_1____GasGridConnection____grid_export_)_(_house_1____GasGridConnection____sink_export_)_0)
= 0

c_e_BusBlock_balance((_house_1____GasGridConnection____grid_export_)_1)_:
+1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasGridConnection____grid_export_)_1)
-1 flow((_house_1____GasGridConnection____grid_export_)_(_house_1____GasGridConnection____sink_export_)_1)
= 0

c_e_BusBlock_balance((_house_1____GasGridConnection____grid_export_)_2)_:
+1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasGridConnection____grid_export_)_2)
-1 flow((_house_1____GasGridConnection____grid_export_)_(_house_1____GasGridConnection____sink_export_)_2)
= 0

c_e_BusBlock_balance((_house_1____GasGridConnection____grid_export_)_3)_:
+1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasGridConnection____grid_export_)_3)
-1 flow((_house_1____GasGridConnection____grid_export_)_(_house_1____GasGridConnection____sink_export_)_3)
= 0

c_e_BusBlock_balance((_house_1____GasGridConnection____grid_export_)_4)_:
+1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasGridConnection____grid_export_)_4)
-1 flow((_house_1____GasGridConnection____grid_export_)_(_house_1____GasGridConnection____sink_export_)_4)
= 0

c_e_BusBlock_balance((_house_1____GasGridConnection____grid_export_)_5)_:
+1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasGridConnection____grid_export_)_5)
-1 flow((_house_1____GasGridConnection____grid_export_)_(_house_1____GasGridConnection____sink_export_)_5)
= 0

c_e_BusBlock_balance((_house_1____GasGridConnection____grid_export_)_6)_:
+1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasGridConnection____grid_export_)_6)
-1 flow((_house_1____GasGridConnection____grid_export_)_(_house_1____GasGridConnection____sink_export_)_6)
= 0

c_e_BusBlock_balance((_house_1____GasGridConnection____grid_export_)_7)_:
+1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasGridConnection____grid_export_)_7)
-1 flow((_house_1____GasGridConnection____grid_export_)_(_house_1____GasGridConnection____sink_export_)_7)
= 0

c_e_BusBlock_balance((_house_1____GasGridConnection____grid_export_)_8)_:
+1 flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasGridConnection____grid_export_)_8)
-1 flow((_house_1____GasGridConnection____grid_export_)_(_house_1____GasGridConnection____sink_export_)_8)
= 0

c_e_BusBlock_balance((_house_1____GasGridConnection____grid_import_)_0)_:
+1 flow((_house_1____GasGridConnection____grid_import_)_(_house_1____GasCarrier____Hydrogen_30_)_0)
= 0

c_e_BusBlock_balance((_house_1____GasGridConnection____grid_import_)_1)_:
+1 flow((_house_1____GasGridConnection____grid_import_)_(_house_1____GasCarrier____Hydrogen_30_)_1)
= 0

c_e_BusBlock_balance((_house_1____GasGridConnection____grid_import_)_2)_:
+1 flow((_house_1____GasGridConnection____grid_import_)_(_house_1____GasCarrier____Hydrogen_30_)_2)
= 0

c_e_BusBlock_balance((_house_1____GasGridConnection____grid_import_)_3)_:
+1 flow((_house_1____GasGridConnection____grid_import_)_(_house_1____GasCarrier____Hydrogen_30_)_3)
= 0

c_e_BusBlock_balance((_house_1____GasGridConnection____grid_import_)_4)_:
+1 flow((_house_1____GasGridConnection____grid_import_)_(_house_1____GasCarrier____Hydrogen_30_)_4)
= 0

c_e_BusBlock_balance((_house_1____GasGridConnection____grid_import_)_5)_:
+1 flow((_house_1____GasGridConnection____grid_import_)_(_house_1____GasCarrier____Hydrogen_30_)_5)
= 0

c_e_BusBlock_balance((_house_1____GasGridConnection____grid_import_)_6)_:
+1 flow((_house_1____GasGridConnection____grid_import_)_(_house_1____GasCarrier____Hydrogen_30_)_6)
= 0

c_e_BusBlock_balance((_house_1____GasGridConnection____grid_import_)_7)_:
+1 flow((_house_1____GasGridConnection____grid_import_)_(_house_1____GasCarrier____Hydrogen_30_)_7)
= 0

c_e_BusBlock_balance((_house_1____GasGridConnection____grid_import_)_8)_:
+1 flow((_house_1____GasGridConnection____grid_import_)_(_house_1____GasCarrier____Hydrogen_30_)_8)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_20_)_0)_:
-1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____Ely____heat_20_50_)_0)
+1 flow((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_20_)_0)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_20_)_1)_:
-1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____Ely____heat_20_50_)_1)
+1 flow((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_20_)_1)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_20_)_2)_:
-1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____Ely____heat_20_50_)_2)
+1 flow((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_20_)_2)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_20_)_3)_:
-1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____Ely____heat_20_50_)_3)
+1 flow((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_20_)_3)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_20_)_4)_:
-1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____Ely____heat_20_50_)_4)
+1 flow((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_20_)_4)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_20_)_5)_:
-1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____Ely____heat_20_50_)_5)
+1 flow((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_20_)_5)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_20_)_6)_:
-1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____Ely____heat_20_50_)_6)
+1 flow((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_20_)_6)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_20_)_7)_:
-1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____Ely____heat_20_50_)_7)
+1 flow((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_20_)_7)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_20_)_8)_:
-1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____Ely____heat_20_50_)_8)
+1 flow((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_20_)_8)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_50_)_0)_:
-1 flow((_house_1____HeatCarrier____T_50_)_(_house_1____heating____heat_exchanger_)_0)
+1 flow((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_50_)_0)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_50_)_1)_:
-1 flow((_house_1____HeatCarrier____T_50_)_(_house_1____heating____heat_exchanger_)_1)
+1 flow((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_50_)_1)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_50_)_2)_:
-1 flow((_house_1____HeatCarrier____T_50_)_(_house_1____heating____heat_exchanger_)_2)
+1 flow((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_50_)_2)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_50_)_3)_:
-1 flow((_house_1____HeatCarrier____T_50_)_(_house_1____heating____heat_exchanger_)_3)
+1 flow((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_50_)_3)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_50_)_4)_:
-1 flow((_house_1____HeatCarrier____T_50_)_(_house_1____heating____heat_exchanger_)_4)
+1 flow((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_50_)_4)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_50_)_5)_:
-1 flow((_house_1____HeatCarrier____T_50_)_(_house_1____heating____heat_exchanger_)_5)
+1 flow((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_50_)_5)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_50_)_6)_:
-1 flow((_house_1____HeatCarrier____T_50_)_(_house_1____heating____heat_exchanger_)_6)
+1 flow((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_50_)_6)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_50_)_7)_:
-1 flow((_house_1____HeatCarrier____T_50_)_(_house_1____heating____heat_exchanger_)_7)
+1 flow((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_50_)_7)
= 0

c_e_BusBlock_balance((_house_1____HeatCarrier____T_50_)_8)_:
-1 flow((_house_1____HeatCarrier____T_50_)_(_house_1____heating____heat_exchanger_)_8)
+1 flow((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_50_)_8)
= 0

c_e_BusBlock_balance((_house_1____heating____output_)_0)_:
+1 flow((_house_1____heating____heat_exchanger_)_(_house_1____heating____output_)_0)
= 100

c_e_BusBlock_balance((_house_1____heating____output_)_1)_:
+1 flow((_house_1____heating____heat_exchanger_)_(_house_1____heating____output_)_1)
= 100

c_e_BusBlock_balance((_house_1____heating____output_)_2)_:
+1 flow((_house_1____heating____heat_exchanger_)_(_house_1____heating____output_)_2)
= 100

c_e_BusBlock_balance((_house_1____heating____output_)_3)_:
+1 flow((_house_1____heating____heat_exchanger_)_(_house_1____heating____output_)_3)
= 100

c_e_BusBlock_balance((_house_1____heating____output_)_4)_:
+1 flow((_house_1____heating____heat_exchanger_)_(_house_1____heating____output_)_4)
= 100

c_e_BusBlock_balance((_house_1____heating____output_)_5)_:
+1 flow((_house_1____heating____heat_exchanger_)_(_house_1____heating____output_)_5)
= 100

c_e_BusBlock_balance((_house_1____heating____output_)_6)_:
+1 flow((_house_1____heating____heat_exchanger_)_(_house_1____heating____output_)_6)
= 100

c_e_BusBlock_balance((_house_1____heating____output_)_7)_:
+1 flow((_house_1____heating____heat_exchanger_)_(_house_1____heating____output_)_7)
= 100

c_e_BusBlock_balance((_house_1____heating____output_)_8)_:
+1 flow((_house_1____heating____heat_exchanger_)_(_house_1____heating____output_)_8)
= 100

c_e_BusBlock_balance((_house_1____pv0____connection_)_0)_:
-1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____feed_in_)_0)
-1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_0)
+1 flow((_house_1____pv0____source_)_(_house_1____pv0____connection_)_0)
= 0

c_e_BusBlock_balance((_house_1____pv0____connection_)_1)_:
-1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____feed_in_)_1)
-1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_1)
+1 flow((_house_1____pv0____source_)_(_house_1____pv0____connection_)_1)
= 0

c_e_BusBlock_balance((_house_1____pv0____connection_)_2)_:
-1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____feed_in_)_2)
-1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_2)
+1 flow((_house_1____pv0____source_)_(_house_1____pv0____connection_)_2)
= 0

c_e_BusBlock_balance((_house_1____pv0____connection_)_3)_:
-1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____feed_in_)_3)
-1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_3)
+1 flow((_house_1____pv0____source_)_(_house_1____pv0____connection_)_3)
= 0

c_e_BusBlock_balance((_house_1____pv0____connection_)_4)_:
-1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____feed_in_)_4)
-1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_4)
+1 flow((_house_1____pv0____source_)_(_house_1____pv0____connection_)_4)
= 0

c_e_BusBlock_balance((_house_1____pv0____connection_)_5)_:
-1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____feed_in_)_5)
-1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_5)
+1 flow((_house_1____pv0____source_)_(_house_1____pv0____connection_)_5)
= 0

c_e_BusBlock_balance((_house_1____pv0____connection_)_6)_:
-1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____feed_in_)_6)
-1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_6)
+1 flow((_house_1____pv0____source_)_(_house_1____pv0____connection_)_6)
= 0

c_e_BusBlock_balance((_house_1____pv0____connection_)_7)_:
-1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____feed_in_)_7)
-1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_7)
+1 flow((_house_1____pv0____source_)_(_house_1____pv0____connection_)_7)
= 0

c_e_BusBlock_balance((_house_1____pv0____connection_)_8)_:
-1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____feed_in_)_8)
-1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_8)
+1 flow((_house_1____pv0____source_)_(_house_1____pv0____connection_)_8)
= 0

c_e_BusBlock_balance((_house_2____ElectricityCarrier____distribution_)_0)_:
-1 flow((_house_2____ElectricityCarrier____distribution_)_(_house_2____demand0____input_)_0)
+1 flow((_house_2____ElectricityGridConnection____grid_import_)_(_house_2____ElectricityCarrier____distribution_)_0)
= 0

c_e_BusBlock_balance((_house_2____ElectricityCarrier____distribution_)_1)_:
-1 flow((_house_2____ElectricityCarrier____distribution_)_(_house_2____demand0____input_)_1)
+1 flow((_house_2____ElectricityGridConnection____grid_import_)_(_house_2____ElectricityCarrier____distribution_)_1)
= 0

c_e_BusBlock_balance((_house_2____ElectricityCarrier____distribution_)_2)_:
-1 flow((_house_2____ElectricityCarrier____distribution_)_(_house_2____demand0____input_)_2)
+1 flow((_house_2____ElectricityGridConnection____grid_import_)_(_house_2____ElectricityCarrier____distribution_)_2)
= 0

c_e_BusBlock_balance((_house_2____ElectricityCarrier____distribution_)_3)_:
-1 flow((_house_2____ElectricityCarrier____distribution_)_(_house_2____demand0____input_)_3)
+1 flow((_house_2____ElectricityGridConnection____grid_import_)_(_house_2____ElectricityCarrier____distribution_)_3)
= 0

c_e_BusBlock_balance((_house_2____ElectricityCarrier____distribution_)_4)_:
-1 flow((_house_2____ElectricityCarrier____distribution_)_(_house_2____demand0____input_)_4)
+1 flow((_house_2____ElectricityGridConnection____grid_import_)_(_house_2____ElectricityCarrier____distribution_)_4)
= 0

c_e_BusBlock_balance((_house_2____ElectricityCarrier____distribution_)_5)_:
-1 flow((_house_2____ElectricityCarrier____distribution_)_(_house_2____demand0____input_)_5)
+1 flow((_house_2____ElectricityGridConnection____grid_import_)_(_house_2____ElectricityCarrier____distribution_)_5)
= 0

c_e_BusBlock_balance((_house_2____ElectricityCarrier____distribution_)_6)_:
-1 flow((_house_2____ElectricityCarrier____distribution_)_(_house_2____demand0____input_)_6)
+1 flow((_house_2____ElectricityGridConnection____grid_import_)_(_house_2____ElectricityCarrier____distribution_)_6)
= 0

c_e_BusBlock_balance((_house_2____ElectricityCarrier____distribution_)_7)_:
-1 flow((_house_2____ElectricityCarrier____distribution_)_(_house_2____demand0____input_)_7)
+1 flow((_house_2____ElectricityGridConnection____grid_import_)_(_house_2____ElectricityCarrier____distribution_)_7)
= 0

c_e_BusBlock_balance((_house_2____ElectricityCarrier____distribution_)_8)_:
-1 flow((_house_2____ElectricityCarrier____distribution_)_(_house_2____demand0____input_)_8)
+1 flow((_house_2____ElectricityGridConnection____grid_import_)_(_house_2____ElectricityCarrier____distribution_)_8)
= 0

c_e_BusBlock_balance((_house_2____ElectricityCarrier____feed_in_)_0)_:
+1 flow((_house_2____ElectricityCarrier____feed_in_)_(_house_2____ElectricityGridConnection____grid_export_)_0)
= 0

c_e_BusBlock_balance((_house_2____ElectricityCarrier____feed_in_)_1)_:
+1 flow((_house_2____ElectricityCarrier____feed_in_)_(_house_2____ElectricityGridConnection____grid_export_)_1)
= 0

c_e_BusBlock_balance((_house_2____ElectricityCarrier____feed_in_)_2)_:
+1 flow((_house_2____ElectricityCarrier____feed_in_)_(_house_2____ElectricityGridConnection____grid_export_)_2)
= 0

c_e_BusBlock_balance((_house_2____ElectricityCarrier____feed_in_)_3)_:
+1 flow((_house_2____ElectricityCarrier____feed_in_)_(_house_2____ElectricityGridConnection____grid_export_)_3)
= 0

c_e_BusBlock_balance((_house_2____ElectricityCarrier____feed_in_)_4)_:
+1 flow((_house_2____ElectricityCarrier____feed_in_)_(_house_2____ElectricityGridConnection____grid_export_)_4)
= 0

c_e_BusBlock_balance((_house_2____ElectricityCarrier____feed_in_)_5)_:
+1 flow((_house_2____ElectricityCarrier____feed_in_)_(_house_2____ElectricityGridConnection____grid_export_)_5)
= 0

c_e_BusBlock_balance((_house_2____ElectricityCarrier____feed_in_)_6)_:
+1 flow((_house_2____ElectricityCarrier____feed_in_)_(_house_2____ElectricityGridConnection____grid_export_)_6)
= 0

c_e_BusBlock_balance((_house_2____ElectricityCarrier____feed_in_)_7)_:
+1 flow((_house_2____ElectricityCarrier____feed_in_)_(_house_2____ElectricityGridConnection____grid_export_)_7)
= 0

c_e_BusBlock_balance((_house_2____ElectricityCarrier____feed_in_)_8)_:
+1 flow((_house_2____ElectricityCarrier____feed_in_)_(_house_2____ElectricityGridConnection____grid_export_)_8)
= 0

c_e_BusBlock_balance((_house_2____ElectricityGridConnection____grid_export_)_0)_:
+1 flow((_house_2____ElectricityCarrier____feed_in_)_(_house_2____ElectricityGridConnection____grid_export_)_0)
= 0

c_e_BusBlock_balance((_house_2____ElectricityGridConnection____grid_export_)_1)_:
+1 flow((_house_2____ElectricityCarrier____feed_in_)_(_house_2____ElectricityGridConnection____grid_export_)_1)
= 0

c_e_BusBlock_balance((_house_2____ElectricityGridConnection____grid_export_)_2)_:
+1 flow((_house_2____ElectricityCarrier____feed_in_)_(_house_2____ElectricityGridConnection____grid_export_)_2)
= 0

c_e_BusBlock_balance((_house_2____ElectricityGridConnection____grid_export_)_3)_:
+1 flow((_house_2____ElectricityCarrier____feed_in_)_(_house_2____ElectricityGridConnection____grid_export_)_3)
= 0

c_e_BusBlock_balance((_house_2____ElectricityGridConnection____grid_export_)_4)_:
+1 flow((_house_2____ElectricityCarrier____feed_in_)_(_house_2____ElectricityGridConnection____grid_export_)_4)
= 0

c_e_BusBlock_balance((_house_2____ElectricityGridConnection____grid_export_)_5)_:
+1 flow((_house_2____ElectricityCarrier____feed_in_)_(_house_2____ElectricityGridConnection____grid_export_)_5)
= 0

c_e_BusBlock_balance((_house_2____ElectricityGridConnection____grid_export_)_6)_:
+1 flow((_house_2____ElectricityCarrier____feed_in_)_(_house_2____ElectricityGridConnection____grid_export_)_6)
= 0

c_e_BusBlock_balance((_house_2____ElectricityGridConnection____grid_export_)_7)_:
+1 flow((_house_2____ElectricityCarrier____feed_in_)_(_house_2____ElectricityGridConnection____grid_export_)_7)
= 0

c_e_BusBlock_balance((_house_2____ElectricityGridConnection____grid_export_)_8)_:
+1 flow((_house_2____ElectricityCarrier____feed_in_)_(_house_2____ElectricityGridConnection____grid_export_)_8)
= 0

c_e_BusBlock_balance((_house_2____ElectricityGridConnection____grid_import_)_0)_:
+1 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_0)
-1 flow((_house_2____ElectricityGridConnection____grid_import_)_(_house_2____ElectricityCarrier____distribution_)_0)
+1 flow((_house_2____ElectricityGridConnection____source_import_)_(_house_2____ElectricityGridConnection____grid_import_)_0)
= 0

c_e_BusBlock_balance((_house_2____ElectricityGridConnection____grid_import_)_1)_:
+1 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_1)
-1 flow((_house_2____ElectricityGridConnection____grid_import_)_(_house_2____ElectricityCarrier____distribution_)_1)
+1 flow((_house_2____ElectricityGridConnection____source_import_)_(_house_2____ElectricityGridConnection____grid_import_)_1)
= 0

c_e_BusBlock_balance((_house_2____ElectricityGridConnection____grid_import_)_2)_:
+1 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_2)
-1 flow((_house_2____ElectricityGridConnection____grid_import_)_(_house_2____ElectricityCarrier____distribution_)_2)
+1 flow((_house_2____ElectricityGridConnection____source_import_)_(_house_2____ElectricityGridConnection____grid_import_)_2)
= 0

c_e_BusBlock_balance((_house_2____ElectricityGridConnection____grid_import_)_3)_:
+1 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_3)
-1 flow((_house_2____ElectricityGridConnection____grid_import_)_(_house_2____ElectricityCarrier____distribution_)_3)
+1 flow((_house_2____ElectricityGridConnection____source_import_)_(_house_2____ElectricityGridConnection____grid_import_)_3)
= 0

c_e_BusBlock_balance((_house_2____ElectricityGridConnection____grid_import_)_4)_:
+1 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_4)
-1 flow((_house_2____ElectricityGridConnection____grid_import_)_(_house_2____ElectricityCarrier____distribution_)_4)
+1 flow((_house_2____ElectricityGridConnection____source_import_)_(_house_2____ElectricityGridConnection____grid_import_)_4)
= 0

c_e_BusBlock_balance((_house_2____ElectricityGridConnection____grid_import_)_5)_:
+1 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_5)
-1 flow((_house_2____ElectricityGridConnection____grid_import_)_(_house_2____ElectricityCarrier____distribution_)_5)
+1 flow((_house_2____ElectricityGridConnection____source_import_)_(_house_2____ElectricityGridConnection____grid_import_)_5)
= 0

c_e_BusBlock_balance((_house_2____ElectricityGridConnection____grid_import_)_6)_:
+1 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_6)
-1 flow((_house_2____ElectricityGridConnection____grid_import_)_(_house_2____ElectricityCarrier____distribution_)_6)
+1 flow((_house_2____ElectricityGridConnection____source_import_)_(_house_2____ElectricityGridConnection____grid_import_)_6)
= 0

c_e_BusBlock_balance((_house_2____ElectricityGridConnection____grid_import_)_7)_:
+1 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_7)
-1 flow((_house_2____ElectricityGridConnection____grid_import_)_(_house_2____ElectricityCarrier____distribution_)_7)
+1 flow((_house_2____ElectricityGridConnection____source_import_)_(_house_2____ElectricityGridConnection____grid_import_)_7)
= 0

c_e_BusBlock_balance((_house_2____ElectricityGridConnection____grid_import_)_8)_:
+1 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_8)
-1 flow((_house_2____ElectricityGridConnection____grid_import_)_(_house_2____ElectricityCarrier____distribution_)_8)
+1 flow((_house_2____ElectricityGridConnection____source_import_)_(_house_2____ElectricityGridConnection____grid_import_)_8)
= 0

c_e_BusBlock_balance((_house_2____demand0____input_)_0)_:
+1 flow((_house_2____ElectricityCarrier____distribution_)_(_house_2____demand0____input_)_0)
= 500

c_e_BusBlock_balance((_house_2____demand0____input_)_1)_:
+1 flow((_house_2____ElectricityCarrier____distribution_)_(_house_2____demand0____input_)_1)
= 500

c_e_BusBlock_balance((_house_2____demand0____input_)_2)_:
+1 flow((_house_2____ElectricityCarrier____distribution_)_(_house_2____demand0____input_)_2)
= 500

c_e_BusBlock_balance((_house_2____demand0____input_)_3)_:
+1 flow((_house_2____ElectricityCarrier____distribution_)_(_house_2____demand0____input_)_3)
= 500

c_e_BusBlock_balance((_house_2____demand0____input_)_4)_:
+1 flow((_house_2____ElectricityCarrier____distribution_)_(_house_2____demand0____input_)_4)
= 500

c_e_BusBlock_balance((_house_2____demand0____input_)_5)_:
+1 flow((_house_2____ElectricityCarrier____distribution_)_(_house_2____demand0____input_)_5)
= 500

c_e_BusBlock_balance((_house_2____demand0____input_)_6)_:
+1 flow((_house_2____ElectricityCarrier____distribution_)_(_house_2____demand0____input_)_6)
= 500

c_e_BusBlock_balance((_house_2____demand0____input_)_7)_:
+1 flow((_house_2____ElectricityCarrier____distribution_)_(_house_2____demand0____input_)_7)
= 500

c_e_BusBlock_balance((_house_2____demand0____input_)_8)_:
+1 flow((_house_2____ElectricityCarrier____distribution_)_(_house_2____demand0____input_)_8)
= 500

c_e_ConverterBlock_relation((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_50_)_(_house_1____heating____output_)_0)_:
+34.83 flow((_house_1____HeatCarrier____T_50_)_(_house_1____heating____heat_exchanger_)_0)
-1 flow((_house_1____heating____heat_exchanger_)_(_house_1____heating____output_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_50_)_(_house_1____HeatCarrier____T_20_)_0)_:
+1 flow((_house_1____HeatCarrier____T_50_)_(_house_1____heating____heat_exchanger_)_0)
-1 flow((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_20_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____Ely____electrolyser_)_(_house_1____ElectricityCarrier____distribution_)_(_house_1____GasCarrier____Hydrogen_60_)_0)_:
+1.89018901890189e-05 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____electrolyser_)_0)
-1 flow((_house_1____Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_60_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____Ely____electrolyser_)_(_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____heat_)_0)_:
+0.25 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____electrolyser_)_0)
-1 flow((_house_1____Ely____electrolyser_)_(_house_1____Ely____heat_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____Ely____heat_20_50_)_(_house_1____Ely____heat_)_(_house_1____HeatCarrier____T_50_)_0)_:
+1 flow((_house_1____Ely____heat_)_(_house_1____Ely____heat_20_50_)_0)
-34.83 flow((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_50_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_20_)_(_house_1____HeatCarrier____T_50_)_0)_:
+1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____Ely____heat_20_50_)_0)
-1 flow((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_50_)_0)
= 0

c_e_ConverterBlock_relation((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_50_)_(_house_1____heating____output_)_1)_:
+34.83 flow((_house_1____HeatCarrier____T_50_)_(_house_1____heating____heat_exchanger_)_1)
-1 flow((_house_1____heating____heat_exchanger_)_(_house_1____heating____output_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_50_)_(_house_1____HeatCarrier____T_20_)_1)_:
+1 flow((_house_1____HeatCarrier____T_50_)_(_house_1____heating____heat_exchanger_)_1)
-1 flow((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_20_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____Ely____electrolyser_)_(_house_1____ElectricityCarrier____distribution_)_(_house_1____GasCarrier____Hydrogen_60_)_1)_:
+1.89018901890189e-05 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____electrolyser_)_1)
-1 flow((_house_1____Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_60_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____Ely____electrolyser_)_(_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____heat_)_1)_:
+0.25 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____electrolyser_)_1)
-1 flow((_house_1____Ely____electrolyser_)_(_house_1____Ely____heat_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____Ely____heat_20_50_)_(_house_1____Ely____heat_)_(_house_1____HeatCarrier____T_50_)_1)_:
+1 flow((_house_1____Ely____heat_)_(_house_1____Ely____heat_20_50_)_1)
-34.83 flow((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_50_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_20_)_(_house_1____HeatCarrier____T_50_)_1)_:
+1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____Ely____heat_20_50_)_1)
-1 flow((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_50_)_1)
= 0

c_e_ConverterBlock_relation((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_50_)_(_house_1____heating____output_)_2)_:
+34.83 flow((_house_1____HeatCarrier____T_50_)_(_house_1____heating____heat_exchanger_)_2)
-1 flow((_house_1____heating____heat_exchanger_)_(_house_1____heating____output_)_2)
= 0

c_e_ConverterBlock_relation((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_50_)_(_house_1____HeatCarrier____T_20_)_2)_:
+1 flow((_house_1____HeatCarrier____T_50_)_(_house_1____heating____heat_exchanger_)_2)
-1 flow((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_20_)_2)
= 0

c_e_ConverterBlock_relation((_house_1____Ely____electrolyser_)_(_house_1____ElectricityCarrier____distribution_)_(_house_1____GasCarrier____Hydrogen_60_)_2)_:
+1.89018901890189e-05 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____electrolyser_)_2)
-1 flow((_house_1____Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_60_)_2)
= 0

c_e_ConverterBlock_relation((_house_1____Ely____electrolyser_)_(_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____heat_)_2)_:
+0.25 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____electrolyser_)_2)
-1 flow((_house_1____Ely____electrolyser_)_(_house_1____Ely____heat_)_2)
= 0

c_e_ConverterBlock_relation((_house_1____Ely____heat_20_50_)_(_house_1____Ely____heat_)_(_house_1____HeatCarrier____T_50_)_2)_:
+1 flow((_house_1____Ely____heat_)_(_house_1____Ely____heat_20_50_)_2)
-34.83 flow((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_50_)_2)
= 0

c_e_ConverterBlock_relation((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_20_)_(_house_1____HeatCarrier____T_50_)_2)_:
+1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____Ely____heat_20_50_)_2)
-1 flow((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_50_)_2)
= 0

c_e_ConverterBlock_relation((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_50_)_(_house_1____heating____output_)_3)_:
+34.83 flow((_house_1____HeatCarrier____T_50_)_(_house_1____heating____heat_exchanger_)_3)
-1 flow((_house_1____heating____heat_exchanger_)_(_house_1____heating____output_)_3)
= 0

c_e_ConverterBlock_relation((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_50_)_(_house_1____HeatCarrier____T_20_)_3)_:
+1 flow((_house_1____HeatCarrier____T_50_)_(_house_1____heating____heat_exchanger_)_3)
-1 flow((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_20_)_3)
= 0

c_e_ConverterBlock_relation((_house_1____Ely____electrolyser_)_(_house_1____ElectricityCarrier____distribution_)_(_house_1____GasCarrier____Hydrogen_60_)_3)_:
+1.89018901890189e-05 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____electrolyser_)_3)
-1 flow((_house_1____Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_60_)_3)
= 0

c_e_ConverterBlock_relation((_house_1____Ely____electrolyser_)_(_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____heat_)_3)_:
+0.25 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____electrolyser_)_3)
-1 flow((_house_1____Ely____electrolyser_)_(_house_1____Ely____heat_)_3)
= 0

c_e_ConverterBlock_relation((_house_1____Ely____heat_20_50_)_(_house_1____Ely____heat_)_(_house_1____HeatCarrier____T_50_)_3)_:
+1 flow((_house_1____Ely____heat_)_(_house_1____Ely____heat_20_50_)_3)
-34.83 flow((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_50_)_3)
= 0

c_e_ConverterBlock_relation((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_20_)_(_house_1____HeatCarrier____T_50_)_3)_:
+1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____Ely____heat_20_50_)_3)
-1 flow((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_50_)_3)
= 0

c_e_ConverterBlock_relation((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_50_)_(_house_1____heating____output_)_4)_:
+34.83 flow((_house_1____HeatCarrier____T_50_)_(_house_1____heating____heat_exchanger_)_4)
-1 flow((_house_1____heating____heat_exchanger_)_(_house_1____heating____output_)_4)
= 0

c_e_ConverterBlock_relation((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_50_)_(_house_1____HeatCarrier____T_20_)_4)_:
+1 flow((_house_1____HeatCarrier____T_50_)_(_house_1____heating____heat_exchanger_)_4)
-1 flow((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_20_)_4)
= 0

c_e_ConverterBlock_relation((_house_1____Ely____electrolyser_)_(_house_1____ElectricityCarrier____distribution_)_(_house_1____GasCarrier____Hydrogen_60_)_4)_:
+1.89018901890189e-05 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____electrolyser_)_4)
-1 flow((_house_1____Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_60_)_4)
= 0

c_e_ConverterBlock_relation((_house_1____Ely____electrolyser_)_(_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____heat_)_4)_:
+0.25 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____electrolyser_)_4)
-1 flow((_house_1____Ely____electrolyser_)_(_house_1____Ely____heat_)_4)
= 0

c_e_ConverterBlock_relation((_house_1____Ely____heat_20_50_)_(_house_1____Ely____heat_)_(_house_1____HeatCarrier____T_50_)_4)_:
+1 flow((_house_1____Ely____heat_)_(_house_1____Ely____heat_20_50_)_4)
-34.83 flow((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_50_)_4)
= 0

c_e_ConverterBlock_relation((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_20_)_(_house_1____HeatCarrier____T_50_)_4)_:
+1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____Ely____heat_20_50_)_4)
-1 flow((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_50_)_4)
= 0

c_e_ConverterBlock_relation((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_50_)_(_house_1____heating____output_)_5)_:
+34.83 flow((_house_1____HeatCarrier____T_50_)_(_house_1____heating____heat_exchanger_)_5)
-1 flow((_house_1____heating____heat_exchanger_)_(_house_1____heating____output_)_5)
= 0

c_e_ConverterBlock_relation((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_50_)_(_house_1____HeatCarrier____T_20_)_5)_:
+1 flow((_house_1____HeatCarrier____T_50_)_(_house_1____heating____heat_exchanger_)_5)
-1 flow((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_20_)_5)
= 0

c_e_ConverterBlock_relation((_house_1____Ely____electrolyser_)_(_house_1____ElectricityCarrier____distribution_)_(_house_1____GasCarrier____Hydrogen_60_)_5)_:
+1.89018901890189e-05 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____electrolyser_)_5)
-1 flow((_house_1____Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_60_)_5)
= 0

c_e_ConverterBlock_relation((_house_1____Ely____electrolyser_)_(_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____heat_)_5)_:
+0.25 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____electrolyser_)_5)
-1 flow((_house_1____Ely____electrolyser_)_(_house_1____Ely____heat_)_5)
= 0

c_e_ConverterBlock_relation((_house_1____Ely____heat_20_50_)_(_house_1____Ely____heat_)_(_house_1____HeatCarrier____T_50_)_5)_:
+1 flow((_house_1____Ely____heat_)_(_house_1____Ely____heat_20_50_)_5)
-34.83 flow((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_50_)_5)
= 0

c_e_ConverterBlock_relation((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_20_)_(_house_1____HeatCarrier____T_50_)_5)_:
+1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____Ely____heat_20_50_)_5)
-1 flow((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_50_)_5)
= 0

c_e_ConverterBlock_relation((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_50_)_(_house_1____heating____output_)_6)_:
+34.83 flow((_house_1____HeatCarrier____T_50_)_(_house_1____heating____heat_exchanger_)_6)
-1 flow((_house_1____heating____heat_exchanger_)_(_house_1____heating____output_)_6)
= 0

c_e_ConverterBlock_relation((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_50_)_(_house_1____HeatCarrier____T_20_)_6)_:
+1 flow((_house_1____HeatCarrier____T_50_)_(_house_1____heating____heat_exchanger_)_6)
-1 flow((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_20_)_6)
= 0

c_e_ConverterBlock_relation((_house_1____Ely____electrolyser_)_(_house_1____ElectricityCarrier____distribution_)_(_house_1____GasCarrier____Hydrogen_60_)_6)_:
+1.89018901890189e-05 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____electrolyser_)_6)
-1 flow((_house_1____Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_60_)_6)
= 0

c_e_ConverterBlock_relation((_house_1____Ely____electrolyser_)_(_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____heat_)_6)_:
+0.25 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____electrolyser_)_6)
-1 flow((_house_1____Ely____electrolyser_)_(_house_1____Ely____heat_)_6)
= 0

c_e_ConverterBlock_relation((_house_1____Ely____heat_20_50_)_(_house_1____Ely____heat_)_(_house_1____HeatCarrier____T_50_)_6)_:
+1 flow((_house_1____Ely____heat_)_(_house_1____Ely____heat_20_50_)_6)
-34.83 flow((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_50_)_6)
= 0

c_e_ConverterBlock_relation((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_20_)_(_house_1____HeatCarrier____T_50_)_6)_:
+1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____Ely____heat_20_50_)_6)
-1 flow((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_50_)_6)
= 0

c_e_ConverterBlock_relation((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_50_)_(_house_1____heating____output_)_7)_:
+34.83 flow((_house_1____HeatCarrier____T_50_)_(_house_1____heating____heat_exchanger_)_7)
-1 flow((_house_1____heating____heat_exchanger_)_(_house_1____heating____output_)_7)
= 0

c_e_ConverterBlock_relation((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_50_)_(_house_1____HeatCarrier____T_20_)_7)_:
+1 flow((_house_1____HeatCarrier____T_50_)_(_house_1____heating____heat_exchanger_)_7)
-1 flow((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_20_)_7)
= 0

c_e_ConverterBlock_relation((_house_1____Ely____electrolyser_)_(_house_1____ElectricityCarrier____distribution_)_(_house_1____GasCarrier____Hydrogen_60_)_7)_:
+1.89018901890189e-05 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____electrolyser_)_7)
-1 flow((_house_1____Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_60_)_7)
= 0

c_e_ConverterBlock_relation((_house_1____Ely____electrolyser_)_(_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____heat_)_7)_:
+0.25 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____electrolyser_)_7)
-1 flow((_house_1____Ely____electrolyser_)_(_house_1____Ely____heat_)_7)
= 0

c_e_ConverterBlock_relation((_house_1____Ely____heat_20_50_)_(_house_1____Ely____heat_)_(_house_1____HeatCarrier____T_50_)_7)_:
+1 flow((_house_1____Ely____heat_)_(_house_1____Ely____heat_20_50_)_7)
-34.83 flow((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_50_)_7)
= 0

c_e_ConverterBlock_relation((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_20_)_(_house_1____HeatCarrier____T_50_)_7)_:
+1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____Ely____heat_20_50_)_7)
-1 flow((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_50_)_7)
= 0

c_e_ConverterBlock_relation((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_50_)_(_house_1____heating____output_)_8)_:
+34.83 flow((_house_1____HeatCarrier____T_50_)_(_house_1____heating____heat_exchanger_)_8)
-1 flow((_house_1____heating____heat_exchanger_)_(_house_1____heating____output_)_8)
= 0

c_e_ConverterBlock_relation((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_50_)_(_house_1____HeatCarrier____T_20_)_8)_:
+1 flow((_house_1____HeatCarrier____T_50_)_(_house_1____heating____heat_exchanger_)_8)
-1 flow((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_20_)_8)
= 0

c_e_ConverterBlock_relation((_house_1____Ely____electrolyser_)_(_house_1____ElectricityCarrier____distribution_)_(_house_1____GasCarrier____Hydrogen_60_)_8)_:
+1.89018901890189e-05 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____electrolyser_)_8)
-1 flow((_house_1____Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_60_)_8)
= 0

c_e_ConverterBlock_relation((_house_1____Ely____electrolyser_)_(_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____heat_)_8)_:
+0.25 flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____electrolyser_)_8)
-1 flow((_house_1____Ely____electrolyser_)_(_house_1____Ely____heat_)_8)
= 0

c_e_ConverterBlock_relation((_house_1____Ely____heat_20_50_)_(_house_1____Ely____heat_)_(_house_1____HeatCarrier____T_50_)_8)_:
+1 flow((_house_1____Ely____heat_)_(_house_1____Ely____heat_20_50_)_8)
-34.83 flow((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_50_)_8)
= 0

c_e_ConverterBlock_relation((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_20_)_(_house_1____HeatCarrier____T_50_)_8)_:
+1 flow((_house_1____HeatCarrier____T_20_)_(_house_1____Ely____heat_20_50_)_8)
-1 flow((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_50_)_8)
= 0

bounds
   0 <= flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____electrolyser_)_0) <= 1000
   0 <= flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____electrolyser_)_1) <= 1000
   0 <= flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____electrolyser_)_2) <= 1000
   0 <= flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____electrolyser_)_3) <= 1000
   0 <= flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____electrolyser_)_4) <= 1000
   0 <= flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____electrolyser_)_5) <= 1000
   0 <= flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____electrolyser_)_6) <= 1000
   0 <= flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____electrolyser_)_7) <= 1000
   0 <= flow((_house_1____ElectricityCarrier____distribution_)_(_house_1____Ely____electrolyser_)_8) <= 1000
   0 <= flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_0) <= +inf
   0 <= flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_1) <= +inf
   0 <= flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_2) <= +inf
   0 <= flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_3) <= +inf
   0 <= flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_4) <= +inf
   0 <= flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_5) <= +inf
   0 <= flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_6) <= +inf
   0 <= flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_7) <= +inf
   0 <= flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_8) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasGridConnection____grid_export_)_0) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasGridConnection____grid_export_)_1) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasGridConnection____grid_export_)_2) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasGridConnection____grid_export_)_3) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasGridConnection____grid_export_)_4) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasGridConnection____grid_export_)_5) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasGridConnection____grid_export_)_6) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasGridConnection____grid_export_)_7) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_30_)_(_house_1____GasGridConnection____grid_export_)_8) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_60_)_(_house_1____GasCarrier____Hydrogen_30_)_0) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_60_)_(_house_1____GasCarrier____Hydrogen_30_)_1) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_60_)_(_house_1____GasCarrier____Hydrogen_30_)_2) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_60_)_(_house_1____GasCarrier____Hydrogen_30_)_3) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_60_)_(_house_1____GasCarrier____Hydrogen_30_)_4) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_60_)_(_house_1____GasCarrier____Hydrogen_30_)_5) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_60_)_(_house_1____GasCarrier____Hydrogen_30_)_6) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_60_)_(_house_1____GasCarrier____Hydrogen_30_)_7) <= +inf
   0 <= flow((_house_1____GasCarrier____Hydrogen_60_)_(_house_1____GasCarrier____Hydrogen_30_)_8) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_20_)_(_house_1____Ely____heat_20_50_)_0) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_20_)_(_house_1____Ely____heat_20_50_)_1) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_20_)_(_house_1____Ely____heat_20_50_)_2) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_20_)_(_house_1____Ely____heat_20_50_)_3) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_20_)_(_house_1____Ely____heat_20_50_)_4) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_20_)_(_house_1____Ely____heat_20_50_)_5) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_20_)_(_house_1____Ely____heat_20_50_)_6) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_20_)_(_house_1____Ely____heat_20_50_)_7) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_20_)_(_house_1____Ely____heat_20_50_)_8) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_50_)_(_house_1____heating____heat_exchanger_)_0) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_50_)_(_house_1____heating____heat_exchanger_)_1) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_50_)_(_house_1____heating____heat_exchanger_)_2) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_50_)_(_house_1____heating____heat_exchanger_)_3) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_50_)_(_house_1____heating____heat_exchanger_)_4) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_50_)_(_house_1____heating____heat_exchanger_)_5) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_50_)_(_house_1____heating____heat_exchanger_)_6) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_50_)_(_house_1____heating____heat_exchanger_)_7) <= +inf
   0 <= flow((_house_1____HeatCarrier____T_50_)_(_house_1____heating____heat_exchanger_)_8) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_0) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_1) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_2) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_3) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_4) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_5) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_6) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_7) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_8) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_1____ElectricityGridConnection____sink_export_)_0) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_1____ElectricityGridConnection____sink_export_)_1) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_1____ElectricityGridConnection____sink_export_)_2) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_1____ElectricityGridConnection____sink_export_)_3) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_1____ElectricityGridConnection____sink_export_)_4) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_1____ElectricityGridConnection____sink_export_)_5) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_1____ElectricityGridConnection____sink_export_)_6) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_1____ElectricityGridConnection____sink_export_)_7) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_1____ElectricityGridConnection____sink_export_)_8) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_0) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_1) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_2) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_3) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_4) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_5) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_6) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_7) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_8) <= +inf
   0 <= flow((_house_1____GasGridConnection____grid_export_)_(_house_1____GasGridConnection____sink_export_)_0) <= +inf
   0 <= flow((_house_1____GasGridConnection____grid_export_)_(_house_1____GasGridConnection____sink_export_)_1) <= +inf
   0 <= flow((_house_1____GasGridConnection____grid_export_)_(_house_1____GasGridConnection____sink_export_)_2) <= +inf
   0 <= flow((_house_1____GasGridConnection____grid_export_)_(_house_1____GasGridConnection____sink_export_)_3) <= +inf
   0 <= flow((_house_1____GasGridConnection____grid_export_)_(_house_1____GasGridConnection____sink_export_)_4) <= +inf
   0 <= flow((_house_1____GasGridConnection____grid_export_)_(_house_1____GasGridConnection____sink_export_)_5) <= +inf
   0 <= flow((_house_1____GasGridConnection____grid_export_)_(_house_1____GasGridConnection____sink_export_)_6) <= +inf
   0 <= flow((_house_1____GasGridConnection____grid_export_)_(_house_1____GasGridConnection____sink_export_)_7) <= +inf
   0 <= flow((_house_1____GasGridConnection____grid_export_)_(_house_1____GasGridConnection____sink_export_)_8) <= +inf
   0 <= flow((_house_1____GasGridConnection____grid_import_)_(_house_1____GasCarrier____Hydrogen_30_)_0) <= +inf
   0 <= flow((_house_1____GasGridConnection____grid_import_)_(_house_1____GasCarrier____Hydrogen_30_)_1) <= +inf
   0 <= flow((_house_1____GasGridConnection____grid_import_)_(_house_1____GasCarrier____Hydrogen_30_)_2) <= +inf
   0 <= flow((_house_1____GasGridConnection____grid_import_)_(_house_1____GasCarrier____Hydrogen_30_)_3) <= +inf
   0 <= flow((_house_1____GasGridConnection____grid_import_)_(_house_1____GasCarrier____Hydrogen_30_)_4) <= +inf
   0 <= flow((_house_1____GasGridConnection____grid_import_)_(_house_1____GasCarrier____Hydrogen_30_)_5) <= +inf
   0 <= flow((_house_1____GasGridConnection____grid_import_)_(_house_1____GasCarrier____Hydrogen_30_)_6) <= +inf
   0 <= flow((_house_1____GasGridConnection____grid_import_)_(_house_1____GasCarrier____Hydrogen_30_)_7) <= +inf
   0 <= flow((_house_1____GasGridConnection____grid_import_)_(_house_1____GasCarrier____Hydrogen_30_)_8) <= +inf
   0 <= flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____feed_in_)_0) <= +inf
   0 <= flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____feed_in_)_1) <= +inf
   0 <= flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____feed_in_)_2) <= +inf
   0 <= flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____feed_in_)_3) <= +inf
   0 <= flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____feed_in_)_4) <= +inf
   0 <= flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____feed_in_)_5) <= +inf
   0 <= flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____feed_in_)_6) <= +inf
   0 <= flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____feed_in_)_7) <= +inf
   0 <= flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____feed_in_)_8) <= +inf
   0 <= flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_0) <= +inf
   0 <= flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_1) <= +inf
   0 <= flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_2) <= +inf
   0 <= flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_3) <= +inf
   0 <= flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_4) <= +inf
   0 <= flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_5) <= +inf
   0 <= flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_6) <= +inf
   0 <= flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_7) <= +inf
   0 <= flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_8) <= +inf
   0 <= flow((_house_1____pv0____source_)_(_house_1____pv0____connection_)_0) <= 249334.62414485688
   0 <= flow((_house_1____pv0____source_)_(_house_1____pv0____connection_)_1) <= 280538.9551033166
   0 <= flow((_house_1____pv0____source_)_(_house_1____pv0____connection_)_2) <= 314055.2876142387
   0 <= flow((_house_1____pv0____source_)_(_house_1____pv0____connection_)_3) <= 327259.6370236386
   0 <= flow((_house_1____pv0____source_)_(_house_1____pv0____connection_)_4) <= 331322.4562918944
   0 <= flow((_house_1____pv0____source_)_(_house_1____pv0____connection_)_5) <= 326240.6960833115
   0 <= flow((_house_1____pv0____source_)_(_house_1____pv0____connection_)_6) <= 297833.30579593
   0 <= flow((_house_1____pv0____source_)_(_house_1____pv0____connection_)_7) <= 272947.7771798363
   0 <= flow((_house_1____pv0____source_)_(_house_1____pv0____connection_)_8) <= 219861.68235153612
   0 <= flow((_house_1____heating____heat_exchanger_)_(_house_1____heating____output_)_0) <= +inf
   0 <= flow((_house_1____heating____heat_exchanger_)_(_house_1____heating____output_)_1) <= +inf
   0 <= flow((_house_1____heating____heat_exchanger_)_(_house_1____heating____output_)_2) <= +inf
   0 <= flow((_house_1____heating____heat_exchanger_)_(_house_1____heating____output_)_3) <= +inf
   0 <= flow((_house_1____heating____heat_exchanger_)_(_house_1____heating____output_)_4) <= +inf
   0 <= flow((_house_1____heating____heat_exchanger_)_(_house_1____heating____output_)_5) <= +inf
   0 <= flow((_house_1____heating____heat_exchanger_)_(_house_1____heating____output_)_6) <= +inf
   0 <= flow((_house_1____heating____heat_exchanger_)_(_house_1____heating____output_)_7) <= +inf
   0 <= flow((_house_1____heating____heat_exchanger_)_(_house_1____heating____output_)_8) <= +inf
   0 <= flow((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_20_)_0) <= +inf
   0 <= flow((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_20_)_1) <= +inf
   0 <= flow((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_20_)_2) <= +inf
   0 <= flow((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_20_)_3) <= +inf
   0 <= flow((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_20_)_4) <= +inf
   0 <= flow((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_20_)_5) <= +inf
   0 <= flow((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_20_)_6) <= +inf
   0 <= flow((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_20_)_7) <= +inf
   0 <= flow((_house_1____heating____heat_exchanger_)_(_house_1____HeatCarrier____T_20_)_8) <= +inf
   0 <= flow((_house_1____Ely____heat_)_(_house_1____Ely____heat_20_50_)_0) <= +inf
   0 <= flow((_house_1____Ely____heat_)_(_house_1____Ely____heat_20_50_)_1) <= +inf
   0 <= flow((_house_1____Ely____heat_)_(_house_1____Ely____heat_20_50_)_2) <= +inf
   0 <= flow((_house_1____Ely____heat_)_(_house_1____Ely____heat_20_50_)_3) <= +inf
   0 <= flow((_house_1____Ely____heat_)_(_house_1____Ely____heat_20_50_)_4) <= +inf
   0 <= flow((_house_1____Ely____heat_)_(_house_1____Ely____heat_20_50_)_5) <= +inf
   0 <= flow((_house_1____Ely____heat_)_(_house_1____Ely____heat_20_50_)_6) <= +inf
   0 <= flow((_house_1____Ely____heat_)_(_house_1____Ely____heat_20_50_)_7) <= +inf
   0 <= flow((_house_1____Ely____heat_)_(_house_1____Ely____heat_20_50_)_8) <= +inf
   0 <= flow((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_50_)_0) <= +inf
   0 <= flow((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_50_)_1) <= +inf
   0 <= flow((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_50_)_2) <= +inf
   0 <= flow((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_50_)_3) <= +inf
   0 <= flow((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_50_)_4) <= +inf
   0 <= flow((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_50_)_5) <= +inf
   0 <= flow((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_50_)_6) <= +inf
   0 <= flow((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_50_)_7) <= +inf
   0 <= flow((_house_1____Ely____heat_20_50_)_(_house_1____HeatCarrier____T_50_)_8) <= +inf
   0 <= flow((_house_1____Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_60_)_0) <= +inf
   0 <= flow((_house_1____Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_60_)_1) <= +inf
   0 <= flow((_house_1____Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_60_)_2) <= +inf
   0 <= flow((_house_1____Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_60_)_3) <= +inf
   0 <= flow((_house_1____Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_60_)_4) <= +inf
   0 <= flow((_house_1____Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_60_)_5) <= +inf
   0 <= flow((_house_1____Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_60_)_6) <= +inf
   0 <= flow((_house_1____Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_60_)_7) <= +inf
   0 <= flow((_house_1____Ely____electrolyser_)_(_house_1____GasCarrier____Hydrogen_60_)_8) <= +inf
   0 <= flow((_house_1____Ely____electrolyser_)_(_house_1____Ely____heat_)_0) <= +inf
   0 <= flow((_house_1____Ely____electrolyser_)_(_house_1____Ely____heat_)_1) <= +inf
   0 <= flow((_house_1____Ely____electrolyser_)_(_house_1____Ely____heat_)_2) <= +inf
   0 <= flow((_house_1____Ely____electrolyser_)_(_house_1____Ely____heat_)_3) <= +inf
   0 <= flow((_house_1____Ely____electrolyser_)_(_house_1____Ely____heat_)_4) <= +inf
   0 <= flow((_house_1____Ely____electrolyser_)_(_house_1____Ely____heat_)_5) <= +inf
   0 <= flow((_house_1____Ely____electrolyser_)_(_house_1____Ely____heat_)_6) <= +inf
   0 <= flow((_house_1____Ely____electrolyser_)_(_house_1____Ely____heat_)_7) <= +inf
   0 <= flow((_house_1____Ely____electrolyser_)_(_house_1____Ely____heat_)_8) <= +inf
   0 <= flow((_house_2____ElectricityCarrier____distribution_)_(_house_2____demand0____input_)_0) <= +inf
   0 <= flow((_house_2____ElectricityCarrier____distribution_)_(_house_2____demand0____input_)_1) <= +inf
   0 <= flow((_house_2____ElectricityCarrier____distribution_)_(_house_2____demand0____input_)_2) <= +inf
   0 <= flow((_house_2____ElectricityCarrier____distribution_)_(_house_2____demand0____input_)_3) <= +inf
   0 <= flow((_house_2____ElectricityCarrier____distribution_)_(_house_2____demand0____input_)_4) <= +inf
   0 <= flow((_house_2____ElectricityCarrier____distribution_)_(_house_2____demand0____input_)_5) <= +inf
   0 <= flow((_house_2____ElectricityCarrier____distribution_)_(_house_2____demand0____input_)_6) <= +inf
   0 <= flow((_house_2____ElectricityCarrier____distribution_)_(_house_2____demand0____input_)_7) <= +inf
   0 <= flow((_house_2____ElectricityCarrier____distribution_)_(_house_2____demand0____input_)_8) <= +inf
   0 <= flow((_house_2____ElectricityCarrier____feed_in_)_(_house_2____ElectricityGridConnection____grid_export_)_0) <= +inf
   0 <= flow((_house_2____ElectricityCarrier____feed_in_)_(_house_2____ElectricityGridConnection____grid_export_)_1) <= +inf
   0 <= flow((_house_2____ElectricityCarrier____feed_in_)_(_house_2____ElectricityGridConnection____grid_export_)_2) <= +inf
   0 <= flow((_house_2____ElectricityCarrier____feed_in_)_(_house_2____ElectricityGridConnection____grid_export_)_3) <= +inf
   0 <= flow((_house_2____ElectricityCarrier____feed_in_)_(_house_2____ElectricityGridConnection____grid_export_)_4) <= +inf
   0 <= flow((_house_2____ElectricityCarrier____feed_in_)_(_house_2____ElectricityGridConnection____grid_export_)_5) <= +inf
   0 <= flow((_house_2____ElectricityCarrier____feed_in_)_(_house_2____ElectricityGridConnection____grid_export_)_6) <= +inf
   0 <= flow((_house_2____ElectricityCarrier____feed_in_)_(_house_2____ElectricityGridConnection____grid_export_)_7) <= +inf
   0 <= flow((_house_2____ElectricityCarrier____feed_in_)_(_house_2____ElectricityGridConnection____grid_export_)_8) <= +inf
   0 <= flow((_house_2____ElectricityGridConnection____grid_import_)_(_house_2____ElectricityCarrier____distribution_)_0) <= +inf
   0 <= flow((_house_2____ElectricityGridConnection____grid_import_)_(_house_2____ElectricityCarrier____distribution_)_1) <= +inf
   0 <= flow((_house_2____ElectricityGridConnection____grid_import_)_(_house_2____ElectricityCarrier____distribution_)_2) <= +inf
   0 <= flow((_house_2____ElectricityGridConnection____grid_import_)_(_house_2____ElectricityCarrier____distribution_)_3) <= +inf
   0 <= flow((_house_2____ElectricityGridConnection____grid_import_)_(_house_2____ElectricityCarrier____distribution_)_4) <= +inf
   0 <= flow((_house_2____ElectricityGridConnection____grid_import_)_(_house_2____ElectricityCarrier____distribution_)_5) <= +inf
   0 <= flow((_house_2____ElectricityGridConnection____grid_import_)_(_house_2____ElectricityCarrier____distribution_)_6) <= +inf
   0 <= flow((_house_2____ElectricityGridConnection____grid_import_)_(_house_2____ElectricityCarrier____distribution_)_7) <= +inf
   0 <= flow((_house_2____ElectricityGridConnection____grid_import_)_(_house_2____ElectricityCarrier____distribution_)_8) <= +inf
   0 <= flow((_house_2____ElectricityGridConnection____source_import_)_(_house_2____ElectricityGridConnection____grid_import_)_0) <= +inf
   0 <= flow((_house_2____ElectricityGridConnection____source_import_)_(_house_2____ElectricityGridConnection____grid_import_)_1) <= +inf
   0 <= flow((_house_2____ElectricityGridConnection____source_import_)_(_house_2____ElectricityGridConnection____grid_import_)_2) <= +inf
   0 <= flow((_house_2____ElectricityGridConnection____source_import_)_(_house_2____ElectricityGridConnection____grid_import_)_3) <= +inf
   0 <= flow((_house_2____ElectricityGridConnection____source_import_)_(_house_2____ElectricityGridConnection____grid_import_)_4) <= +inf
   0 <= flow((_house_2____ElectricityGridConnection____source_import_)_(_house_2____ElectricityGridConnection____grid_import_)_5) <= +inf
   0 <= flow((_house_2____ElectricityGridConnection____source_import_)_(_house_2____ElectricityGridConnection____grid_import_)_6) <= +inf
   0 <= flow((_house_2____ElectricityGridConnection____source_import_)_(_house_2____ElectricityGridConnection____grid_import_)_7) <= +inf
   0 <= flow((_house_2____ElectricityGridConnection____source_import_)_(_house_2____ElectricityGridConnection____grid_import_)_8) <= +inf
end
