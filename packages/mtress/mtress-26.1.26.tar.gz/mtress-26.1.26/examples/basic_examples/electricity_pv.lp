\* Source Pyomo model name=Model *\

min 
objective:
+35 flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_0)
+35 flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_1)
+35 flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_2)
+35 flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_3)
+35 flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_4)
+35 flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_5)
+35 flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_6)
+35 flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_7)
+35 flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_8)
+50 flow((_house_2____ElectricityGridConnection____source_import_)_(_house_2____ElectricityGridConnection____grid_import_)_0)
+50 flow((_house_2____ElectricityGridConnection____source_import_)_(_house_2____ElectricityGridConnection____grid_import_)_1)
+50 flow((_house_2____ElectricityGridConnection____source_import_)_(_house_2____ElectricityGridConnection____grid_import_)_2)
+50 flow((_house_2____ElectricityGridConnection____source_import_)_(_house_2____ElectricityGridConnection____grid_import_)_3)
+50 flow((_house_2____ElectricityGridConnection____source_import_)_(_house_2____ElectricityGridConnection____grid_import_)_4)
+50 flow((_house_2____ElectricityGridConnection____source_import_)_(_house_2____ElectricityGridConnection____grid_import_)_5)
+50 flow((_house_2____ElectricityGridConnection____source_import_)_(_house_2____ElectricityGridConnection____grid_import_)_6)
+50 flow((_house_2____ElectricityGridConnection____source_import_)_(_house_2____ElectricityGridConnection____grid_import_)_7)
+50 flow((_house_2____ElectricityGridConnection____source_import_)_(_house_2____ElectricityGridConnection____grid_import_)_8)

s.t.

c_e_BusBlock_balance((_house_1____ElectricityCarrier____distribution_)_0)_:
+1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_0)
+1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_0)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____distribution_)_1)_:
+1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_1)
+1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_1)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____distribution_)_2)_:
+1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_2)
+1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_2)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____distribution_)_3)_:
+1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_3)
+1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_3)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____distribution_)_4)_:
+1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_4)
+1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_4)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____distribution_)_5)_:
+1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_5)
+1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_5)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____distribution_)_6)_:
+1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_6)
+1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_6)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____distribution_)_7)_:
+1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_7)
+1 flow((_house_1____pv0____connection_)_(_house_1____ElectricityCarrier____distribution_)_7)
= 0

c_e_BusBlock_balance((_house_1____ElectricityCarrier____distribution_)_8)_:
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
-1 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_0)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_export_)_1)_:
+1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_1)
-1 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_1)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_export_)_2)_:
+1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_2)
-1 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_2)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_export_)_3)_:
+1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_3)
-1 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_3)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_export_)_4)_:
+1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_4)
-1 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_4)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_export_)_5)_:
+1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_5)
-1 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_5)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_export_)_6)_:
+1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_6)
-1 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_6)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_export_)_7)_:
+1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_7)
-1 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_7)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_export_)_8)_:
+1 flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_8)
-1 flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_8)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_import_)_0)_:
-1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_0)
+1 flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_0)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_import_)_1)_:
-1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_1)
+1 flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_1)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_import_)_2)_:
-1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_2)
+1 flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_2)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_import_)_3)_:
-1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_3)
+1 flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_3)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_import_)_4)_:
-1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_4)
+1 flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_4)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_import_)_5)_:
-1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_5)
+1 flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_5)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_import_)_6)_:
-1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_6)
+1 flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_6)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_import_)_7)_:
-1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_7)
+1 flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_7)
= 0

c_e_BusBlock_balance((_house_1____ElectricityGridConnection____grid_import_)_8)_:
-1 flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_8)
+1 flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_8)
= 0

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
= 10

c_e_BusBlock_balance((_house_2____demand0____input_)_1)_:
+1 flow((_house_2____ElectricityCarrier____distribution_)_(_house_2____demand0____input_)_1)
= 10

c_e_BusBlock_balance((_house_2____demand0____input_)_2)_:
+1 flow((_house_2____ElectricityCarrier____distribution_)_(_house_2____demand0____input_)_2)
= 10

c_e_BusBlock_balance((_house_2____demand0____input_)_3)_:
+1 flow((_house_2____ElectricityCarrier____distribution_)_(_house_2____demand0____input_)_3)
= 10

c_e_BusBlock_balance((_house_2____demand0____input_)_4)_:
+1 flow((_house_2____ElectricityCarrier____distribution_)_(_house_2____demand0____input_)_4)
= 10

c_e_BusBlock_balance((_house_2____demand0____input_)_5)_:
+1 flow((_house_2____ElectricityCarrier____distribution_)_(_house_2____demand0____input_)_5)
= 10

c_e_BusBlock_balance((_house_2____demand0____input_)_6)_:
+1 flow((_house_2____ElectricityCarrier____distribution_)_(_house_2____demand0____input_)_6)
= 10

c_e_BusBlock_balance((_house_2____demand0____input_)_7)_:
+1 flow((_house_2____ElectricityCarrier____distribution_)_(_house_2____demand0____input_)_7)
= 10

c_e_BusBlock_balance((_house_2____demand0____input_)_8)_:
+1 flow((_house_2____ElectricityCarrier____distribution_)_(_house_2____demand0____input_)_8)
= 10

bounds
   0 <= flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_0) <= +inf
   0 <= flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_1) <= +inf
   0 <= flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_2) <= +inf
   0 <= flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_3) <= +inf
   0 <= flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_4) <= +inf
   0 <= flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_5) <= +inf
   0 <= flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_6) <= +inf
   0 <= flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_7) <= +inf
   0 <= flow((_house_1____ElectricityCarrier____feed_in_)_(_house_1____ElectricityGridConnection____grid_export_)_8) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_0) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_1) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_2) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_3) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_4) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_5) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_6) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_7) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_import_)_(_house_1____ElectricityCarrier____distribution_)_8) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_0) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_1) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_2) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_3) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_4) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_5) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_6) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_7) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____grid_export_)_(_house_2____ElectricityGridConnection____grid_import_)_8) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_0) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_1) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_2) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_3) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_4) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_5) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_6) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_7) <= +inf
   0 <= flow((_house_1____ElectricityGridConnection____source_import_)_(_house_1____ElectricityGridConnection____grid_import_)_8) <= +inf
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
   0 <= flow((_house_1____pv0____source_)_(_house_1____pv0____connection_)_0) <= 0.0
   0 <= flow((_house_1____pv0____source_)_(_house_1____pv0____connection_)_1) <= 0.0
   0 <= flow((_house_1____pv0____source_)_(_house_1____pv0____connection_)_2) <= 0.0
   0 <= flow((_house_1____pv0____source_)_(_house_1____pv0____connection_)_3) <= 0.0
   0 <= flow((_house_1____pv0____source_)_(_house_1____pv0____connection_)_4) <= 0.0
   0 <= flow((_house_1____pv0____source_)_(_house_1____pv0____connection_)_5) <= 0.0
   0 <= flow((_house_1____pv0____source_)_(_house_1____pv0____connection_)_6) <= 0.12388913781941269
   0 <= flow((_house_1____pv0____source_)_(_house_1____pv0____connection_)_7) <= 0.9941573400250271
   0 <= flow((_house_1____pv0____source_)_(_house_1____pv0____connection_)_8) <= 2.058517724884022
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
